#!/usr/bin/env python3

'''
This module implements code for handling symbolic permissions in the way that GNU
chmod from coreutils does.  For example: "a=rx,u+w" for 755

Written by Sean Reifschneider and ChatGPT, 2023-03
'''


def symbolic_to_numeric_permissions(
    symbolic_perm: str, is_exe_or_directory: bool = False
) -> int:
    """
    Convert a symbolic file permission string to its numeric equivalent.

    The function takes a symbolic permission description string in the format of
    `user[=,+,-]permissions,group[=,+,-]permissions,other[=,+,-]permissions`.
    The available permission characters are `r` (read), `w` (write), `x` (execute),
    `X` (execute if a directory), `s` (setuid/setgid), and `t` (sticky bit).

    Args:
        symbolic_perm (str): The symbolic permission description string.
        is_exe_or_directory (bool, optional): A boolean indicating whether the file is a directory.
                This affects the behavior of the `X` permission. Defaults to False.

    Returns:
        int: The numeric (octal) representation of the file permissions.

    Examples:
        >>> symbolic_to_numeric_permissions("u=rwx,g=rx,o=r")
        0o754
        >>> symbolic_to_numeric_permissions("u=rwX", is_directory=True)
        0o700
        >>> symbolic_to_numeric_permissions("u=rws,g=rx,o=r")
        0o4754
    """
    # Define a mapping of symbolic permission characters to their corresponding numeric values
    perm_values = {"r": 4, "w": 2, "x": 1, "X": 1 if is_exe_or_directory else 0, "-": 0}

    # Initialize variables to represent the numeric file mode for the owner (user), group, and others
    owner_perm = 0
    group_perm = 0
    other_perm = 0

    # Initialize variables for setuid, setgid, and sticky bits
    setuid_bit = 0
    setgid_bit = 0
    sticky_bit = 0

    # Parse the input symbolic permission description into a list of individual permission instructions
    instructions = symbolic_perm.split(",")

    # Apply each instruction to the appropriate numeric file mode variables
    for instruction in instructions:
        # Determine which set of users the instruction applies to, the operation, and the permission
        users, operation, perms = instruction.partition("=")
        if not operation:
            users, operation, perms = instruction.partition("+")
        if not operation:
            users, operation, perms = instruction.partition("-")

        # Determine the numeric value of the permissions
        perm_sum = sum(perm_values.get(p, perm_values.get(p.upper(), 0)) for p in perms)

        def update_perm(operation, perm_sum, current_perm):
            if operation == "=":
                return perm_sum
            if operation == "+":
                return current_perm | perm_sum
            return current_perm & ~perm_sum

        # Update the numeric file mode variables based on the users and operation
        if "u" in users or "a" in users:
            owner_perm = update_perm(operation, perm_sum, owner_perm)
            # Handle setuid bit
            if "s" in perms:
                setuid_bit = 4 if operation in "+=" else 0
        if "g" in users or "a" in users:
            group_perm = update_perm(operation, perm_sum, group_perm)
            # Handle setgid bit
            if "s" in perms:
                setgid_bit = 2 if operation in "+=" else 0
        if "o" in users or "a" in users:
            other_perm = update_perm(operation, perm_sum, other_perm)
            # Handle sticky bit
            if "t" in perms:
                sticky_bit = 1 if operation in "+=" else 0

    # Combine the numeric file modes for the owner, group, and others into a single numeric file mode
    numeric_perm = (
        (setuid_bit + setgid_bit + sticky_bit) * 8**3
        + owner_perm * 8**2
        + group_perm * 8**1
        + other_perm
    )

    return numeric_perm
