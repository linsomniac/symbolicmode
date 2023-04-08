#!/usr/bin/env python3

"""
This module implements code for handling symbolic permissions in the way that GNU
chmod from coreutils does.  For example: "a=rx,u+w" for 755

Written by Sean Reifschneider and ChatGPT, 2023-03
"""

import os
import re
from typing import Union, Iterator, Tuple


def symbolic_to_numeric_permissions(
    symbolic_perm: str,
    initial_mode: int = 0,
    is_directory: bool = False,
    umask: Union[int, None] = None,
) -> int:
    """
    Convert a symbolic file permission string to its numeric equivalent.

    The function takes a symbolic permission description string in the format of
    `user[=,+,-]permissions,group[=,+,-]permissions,other[=,+,-]permissions`.
    The available permission characters are `r` (read), `w` (write), `x` (execute),
    `X` (execute if a directory), `s` (setuid/setgid), and `t` (sticky bit), or a single
    character from: 'u', 'g', 'o'.

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

    def update_perm(operation: str, instruction_perms: int, current_perm: int) -> int:
        "Helper function to apply `operation` to the current perms and the instruction_perms"
        if operation == "=":
            return instruction_perms
        if operation == "+":
            return current_perm | instruction_perms
        return current_perm & ~instruction_perms

    def parse_instructions(permstr: str) -> Iterator[Tuple[str, str, str]]:
        """Helper to parse the instruction into (lhs, op, rhs).  This also expands
        multi-operation expressions into multiple u/op/perm tuples."""
        rx = re.compile(r"([=+-][rwxXstugo]*)")
        for instruction in permstr.split(","):
            m = rx.split(instruction)
            if not m:
                raise ValueError(f"Invalid instruction: {instruction}")
            user = m[0]
            for op, perm in [(op_perm[0], op_perm[1:]) for op_perm in m[1::2]]:
                yield ((user, op, perm))

    # Define a mapping of symbolic permission characters to their corresponding numeric values
    perm_values = {"r": 4, "w": 2, "x": 1, "X": 1 if is_directory else 0, "-": 0}

    #  bits to shift based on u/g/o
    shift_by_user = {"u": 6, "g": 3, "o": 0}

    # Extract initial permissions and special bits
    user_perms = (initial_mode >> 6) & 0o7
    group_perms = (initial_mode >> 3) & 0o7
    other_perms = (initial_mode >> 0) & 0o7
    perms = {"u": user_perms, "g": group_perms, "o": other_perms}
    setuid_bit = 4 if initial_mode & 0o4000 else 0
    setgid_bit = 2 if initial_mode & 0o2000 else 0
    sticky_bit = 1 if initial_mode & 0o1000 else 0

    if umask is None:
        umask = os.umask(0)
        os.umask(umask)

    for users, operation, perms_str in parse_instructions(symbolic_perm):
        #  set X value for executable based on current perms
        if not is_directory:
            perm_values["X"] = (
                1 if perms["u"] & 1 or perms["g"] & 1 or perms["o"] & 1 else 0
            )

        # calculate PERMS value
        perm_set = set(perms_str)
        if "x" in perm_set and "X" in perm_set:
            perm_set.remove("X")  # prevent doubling "x" bit
        perm_sum = sum(
            perm_values.get(p, perm_values.get(p.upper(), 0)) for p in perm_set
        )

        #  handle u/g/o in PERMS
        if ("u" in perms_str or "g" in perms_str or "o" in perms_str) and len(
            perms_str
        ) != 1:
            raise ValueError(
                "If u/g/o specified on RHS, only a single letter of u/g/o can be specified"
            )
        perm_sum = perms["u"] if perms_str == "u" else perm_sum
        perm_sum = perms["g"] if perms_str == "g" else perm_sum
        perm_sum = perms["o"] if perms_str == "o" else perm_sum

        # Update the numeric file mode variables based on the users and operation
        effective_users = ("u", "g", "o") if users == "" or "a" in users else users
        for user in effective_users:
            apply_mask = (~umask if users == "" else 0o7777) >> shift_by_user[user]
            perms[user] = update_perm(operation, perm_sum & apply_mask, perms[user])
            if user == "u":
                if "s" in perms_str:
                    setuid_bit = 4 if operation in "+=" else 0
                setuid_bit = (
                    0
                    if "s" not in perms_str and operation == "=" and not is_directory
                    else setuid_bit
                )
            if user == "g":
                if "s" in perms_str:
                    setgid_bit = 2 if operation in "+=" else 0
                setgid_bit = (
                    0
                    if "s" not in perms_str and operation == "=" and not is_directory
                    else setgid_bit
                )
            if user == "o":
                if "t" in perms_str:
                    sticky_bit = 1 if operation in "+=" else 0
                sticky_bit = (
                    0 if "t" not in perms_str and operation == "=" else sticky_bit
                )

    # Combine the numeric file modes for the owner, group, and others into a single numeric file mode
    return (
        ((setuid_bit + setgid_bit + sticky_bit) << 9)
        | (perms["u"] << 6)
        | (perms["g"] << 3)
        | (perms["o"])
    )
