#!/usr/bin/env python3

"""
This module implements code for handling symbolic permissions in the way that GNU
chmod from coreutils does.  For example: "a=rx,u+w" for 755

Written by Sean Reifschneider and ChatGPT, 2023-04
"""

import os
import re
from typing import Union, Iterator, Tuple
from pathlib import Path
import stat


def symbolic_to_numeric_permissions(
    symbolic_perm: str,
    initial_mode: int = 0,
    is_directory: bool = False,
    umask: Union[int, None] = None,
) -> int:
    """
    Convert a symbolic file permission string to its numeric equivalent.

    The function takes a symbolic permission description string in the format of
    `[ugoa][=,+,-][PERMS][,...]`.

    `ugoa` means "user", "group", "other", or "all" (short for "ugo"), representing
    the permissions to be set.  If none of "ugoa" are listed, it acts as if "a" was
    given, but applies the umask to the permission bits that are set.

    The available permission characters are `r` (read), `w` (write), `x` (execute),
    `X` (execute if a directory), `s` (setuid/setgid), and `t` (sticky bit), or a single
    character from: 'u', 'g', 'o'.

    Multiple operators+permissions may be specified after the "ugoa", as with the "chown"
    tool: "u=r+w-x".

    Args:
        symbolic_perm (str): The symbolic permission description string.
        initial_mode (int, optional): The mode to start off with.  If changing mode of an
                existing file, this is it's current mode, and can also impact 'X'.
        is_directory (bool, optional): A boolean indicating whether the file is a directory.
                This affects the behavior of the `X` permission. Defaults to False.
        umask (int, optional): Umask to use for "=[modes]" operation.  If not specified, the
                system umask will be used.

    Returns:
        int: The numeric (octal) representation of the file permissions.

    Raises:
        ValueError: When the permissions contain some invalid instruction.

    Examples:
        >>> symbolic_to_numeric_permissions("u=rwx,g=rx,o=r")
        0o754
        >>> symbolic_to_numeric_permissions("u=rwX", is_directory=True)
        0o700
        >>> symbolic_to_numeric_permissions("u=rws,g=rx,o=r")
        0o4754
        >>> symbolic_to_numeric_permissions("=rw", initial_mode=0o4777, is_directory=False, umask=0o027)
        0o640
    """

    #  Helpers
    def update_perm(operation: str, instruction_perms: int, current_perm: int) -> int:
        "Apply `operation` to the current perms and the instruction_perms"
        if operation == "=":
            return instruction_perms
        if operation == "+":
            return current_perm | instruction_perms
        return current_perm & ~instruction_perms

    def parse_instructions(permstr: str) -> Iterator[Tuple[str, str, str]]:
        """Parse the instruction into (lhs, op, rhs).  This also expands
        multi-operation expressions into multiple u/op/perm tuples."""
        rx = re.compile(r"([=+-][rwxXstugo]*)")
        for instruction in permstr.split(","):
            m = rx.split(instruction)
            if not m:
                raise ValueError(f"Invalid instruction: {instruction}")
            user = m[0]
            for op, perm in [(op_perm[0], op_perm[1:]) for op_perm in m[1::2]]:
                yield ((user, op, perm))

    def sum_premissions(perms_str: str) -> int:
        "Turn the permissions part of the statement into the numeric bits set"
        unique_perms = set(perms_str)
        if "x" in unique_perms and "X" in unique_perms:
            unique_perms.remove("X")  # prevent doubling "x" bit
        perms_sum = sum(
            perm_values.get(p, perm_values.get(p.upper(), 0)) for p in unique_perms
        )

        #  handle u/g/o in PERMS
        if ("u" in perms_str or "g" in perms_str or "o" in perms_str) and len(
            perms_str
        ) != 1:
            raise ValueError(
                "If u/g/o specified on RHS, only a single letter of u/g/o can be specified"
            )
        perms_sum = perms["u"] if perms_str == "u" else perms_sum
        perms_sum = perms["g"] if perms_str == "g" else perms_sum
        perms_sum = perms["o"] if perms_str == "o" else perms_sum

        return perms_sum

    def calc_special_bit(
        value: int,
        perms_str: str,
        operation: str,
        mode_char: str,
        bit_value: int,
        override: bool,
    ) -> int:
        "Calculate the special bits (suid/sgid/sticky)"
        if mode_char in perms_str:
            value = bit_value if operation in "+=" else 0
        value = (
            0
            if mode_char not in perms_str and operation == "=" and not override
            else value
        )
        return value

    # Define a mapping of symbolic permission characters to their corresponding numeric values
    perm_values = {"r": 4, "w": 2, "x": 1, "X": 1 if is_directory else 0, "-": 0}

    #  bits to shift based on u/g/o
    shift_by_user = {"u": 6, "g": 3, "o": 0}

    # Extract initial permissions and special bits
    perms = {
        "u": (initial_mode >> 6) & 0o7,
        "g": (initial_mode >> 3) & 0o7,
        "o": initial_mode & 0o7,
    }
    setuid_bit = 4 if initial_mode & 0o4000 else 0
    setgid_bit = 2 if initial_mode & 0o2000 else 0
    sticky_bit = 1 if initial_mode & 0o1000 else 0

    #  get umask from system if not specified
    if umask is None:
        umask = os.umask(0)
        os.umask(umask)

    for users, operation, perms_str in parse_instructions(symbolic_perm):
        #  if file: set X value if current perms have any 'x' bit set
        if not is_directory:
            perm_values["X"] = (
                1 if perms["u"] & 1 or perms["g"] & 1 or perms["o"] & 1 else 0
            )

        perm_sum = sum_premissions(perms_str)

        # Update the numeric file mode variables based on the users and operation
        effective_users = ("u", "g", "o") if users == "" or "a" in users else users
        for user in effective_users:
            apply_mask = (~umask if users == "" else 0o7777) >> shift_by_user[user]
            perms[user] = update_perm(operation, perm_sum & apply_mask, perms[user])

            #  set special bits
            if user == "u":
                setuid_bit = calc_special_bit(
                    setuid_bit, perms_str, operation, "s", 4, is_directory
                )
            if user == "g":
                setgid_bit = calc_special_bit(
                    setgid_bit, perms_str, operation, "s", 2, is_directory
                )
            if user == "o":
                sticky_bit = calc_special_bit(
                    sticky_bit, perms_str, operation, "t", 1, False
                )

    # Combine the numeric file modes for the owner, group, and others into a single numeric file mode
    return (
        ((setuid_bit + setgid_bit + sticky_bit) << 9)
        | (perms["u"] << 6)
        | (perms["g"] << 3)
        | (perms["o"])
    )


def chmod(path: Union[str, Path], mode: Union[int, str], recurse: bool = False) -> None:
    """
    Change the mode (permissions) of a specified file or directory.

    The mode can be specified as an integer, a string representing an octal integer
    or as a string representing symbolic permissions (e.g., 'u=rwx,g=r,o=r').

    Parameters
    ----------
    path : str or Path
        The path to the file or directory whose mode is to be changed.
    mode : int or str
        The mode (permissions) to be applied to the file or directory. The mode can
        be specified either as an integer, a string of digits (which are parsed as
        an octal integer), or as a string representing symbolic permissions (e.g.,
        'u=rwx,g=r,o=r').
    recurse : bool (default False)
        If true and "path" is a directory, do a depth-first recursion applying `mode`
        to the directory and all objects below it.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        If the specified file or directory does not exist.
    PermissionError
        If the user does not have sufficient privileges to change the mode.
    ValueError
        If the specified mode is invalid.

    Examples
    --------
    # Change the mode of a file using an octal integer:
    chmod('/path/to/file', 0o755)

    # Change the mode of a file using a digit string:
    chmod('/path/to/file', '755')

    # Change the mode of a directory using symbolic permissions
    chmod('/path/to/directory', 'u=rwx,g=rx,o=r')
    """

    def recurse_chmod(directory: Union[str, Path], mode: Union[int, str]) -> None:
        "Recursively apply chmod"
        for dir_path, dirnames, filenames in os.walk(directory, topdown=False):
            for filename in filenames:
                chmod(os.path.join(dir_path, filename), mode, recurse=False)
            for dirname in dirnames:
                chmod(os.path.join(dir_path, dirname), mode, recurse=False)

    mode_is_sym_str = type(mode) is str and not set(mode).issubset("01234567")

    if recurse or mode_is_sym_str:
        path_stat = os.stat(path)
        path_is_directory = stat.S_ISDIR(path_stat.st_mode)
        if path_is_directory and recurse:
            recurse_chmod(path, mode)

    if type(mode) is str:
        if not mode_is_sym_str:
            mode = int(mode, 8)
        else:
            path_mode = stat.S_IMODE(path_stat.st_mode)  # type: ignore
            mode = symbolic_to_numeric_permissions(
                mode, initial_mode=path_mode, is_directory=path_is_directory  # type: ignore
            )

    os.chmod(path, mode)  # type: ignore
