# SymbolicMode -- Code to handle symbolic file permissions

This python library parses symbolic file permission modes as used by GNU chmod, part
of the coreutils package.  For example:

    >>> from symbolicmode import *
    >>> oct(symbolic_to_numeric_permissions('a=rx,u+w'))
    '0o755'   

It also has a "chmod" function:

    >>> chmod('a=rx,u+w', '/tmp/foo')
    >>> chmod('755', '/tmp/foo')
    >>> chmod(0o755, '/tmp/foo')

For convenience it can take permissions in the form of an integer, a numeric string
or the symbolic permissions.

## Status

This library is fully compatible with GNU Coreutils "chmod" command. It fully implements
all mode specifiers except for the purely numeric versions ("755") that chmod does,
as verified by manual, unit, and extensive fuzz testing.

My fuzz testing was against version 8.32-4.1ubuntu1).  Fuzz testing tools are in the
"fuzzchmod" directory.

## Docstring - symbolic\_to\_numeric\_permissions

Convert a symbolic file permission string to its numeric equivalent.

The function takes a symbolic permission description string in the format of
`user[=,+,-]permissions,group[=,+,-]permissions,other[=,+,-]permissions`.
The available permission characters are `r` (read), `w` (write), `x` (execute),
`X` (execute if a directory), `s` (setuid/setgid), and `t` (sticky bit), or a single
character from: 'u', 'g', 'o'.

Args:
- `symbolic_perm` (str): The symbolic permission description string.
- `initial_mode` (int, optional): The mode to start off with.  If changing mode of an
        existing file, this is it's current mode, and can also impact 'X'.
- `is_directory` (bool, optional): A boolean indicating whether the file is a directory.
        This affects the behavior of the `X` permission. Defaults to False.
- `umask` (int, optional): Umask to use for "=[modes]" operation.  If not specified, the
        system umask will be used.

Returns:
- int: The numeric (octal) representation of the file permissions.

Raises:
- ValueError: When the permissions contain some invalid instruction.

Examples:

    >>> symbolic_to_numeric_permissions("u=rwx,g=rx,o=r")
    0o754
    >>> symbolic_to_numeric_permissions("u=rwX", is_directory=True)
    0o700
    >>> symbolic_to_numeric_permissions("u=rws,g=rx,o=r")
    0o4754
    >>> symbolic_to_numeric_permissions("=rw", initial_mode=0o4777, is_directory=False, umask=0o027)
    0o640

## Docstring - chmod

Change the mode (permissions) of a specified file or directory.

The mode can be specified as an integer, a string representing an octal integer
or as a string representing symbolic permissions (e.g., 'u=rwx,g=r,o=r').

Parameters:
- mode : int or str
    The mode (permissions) to be applied to the file or directory. The mode can
    be specified either as an integer, a string of digits (which are parsed as
    an octal integer), or as a string representing symbolic permissions (e.g.,
    'u=rwx,g=r,o=r').
- path : str or Path
    The path to the file or directory whose mode is to be changed.

Returns: None

Raises:
- FileNotFoundError
    If the specified file or directory does not exist.
- PermissionError
    If the user does not have sufficient privileges to change the mode.
- ValueError
    If the specified mode is invalid.

Examples:

    # Change the mode of a file using an octal integer:
    chmod(0o755, '/path/to/file')

    # Change the mode of a file using a digit string:
    chmod('755', '/path/to/file')

    # Change the mode of a directory using symbolic permissions
    chmod('u=rwx,g=rx,o=r', '/path/to/directory')

## Permissions Instructions

Permission instructions are 1 or more comma separated values of the form:
"[ugoa...][[=+-][PERMS...]...]".

USERS can be:

- u: Set permissions for the owner.
- g: Set permissions for group access.
- o: Set permissions for all others.
- a: All of the above.
- "": The empty string, only allowed with "=" for the operator.  Applies to all (like
  "a"), but applies the umask to the permissions set.

Operators are:

- -: Remove the PERMS to the file permissions.
- +: Add the PERMS to the file permissions.
- =: Set the permissions to exactly PERMS.

PERMS can be a combination of the following (except for u/g/o which if specified must
be the only, single, PERM provided:

- r: Allow read access, if a directory allow reading files within.
- w: Allow write access, if a directory allow writing or creating files.
- x: Allow execute, or list contents if a directory.
- X: Set "x" but only if file permissions already had an "x" set for any user, or if
  the object is a directory.
- s: Set UID/GID on execution, allows a program to take on the user/group permissions
  of the executable file.
- t: Sticky bit or restrict deletion to the file owner if a directory.  Note that
  some system settings may prevent root from writing to non-root files in a
  restricted deletion directory.  See "fs.protected\_regular" sysctl setting.
- u: Take on the permissions granted to the user ("go=u").  Must be the only PERM if
  specified.
- g: Take on the group permissions.  Must be the only PERM if specified.
- o: Take on the permissions granted to others.  Must be the only PERM if specified.

Notes on instructions:

- "=[PERMS]" sets the permissions based on the umask.  This acts like "a" was
  specified for the USER, the PERMS are masked with the umask when applied for u/g/o.
- "-[PERMS]" and "+[PERMS]" are not defined as meaning anything in the chmod manpage.
  If given to chmod, chmod will make a permissions change and then error out saying
  that the change was not the expected change.  Because of this, SymbolicMode will
  raise a ValueError on either of these instructions.

## Fuzz Testing

In the "fuzzchmod" directory is a set of programs for fuzz testing SymbolicMode
against the system "chmod" to try to ensure correctness for even unusual inputs.

## License

CC0 1.0 Universal, see LICENSE file for more information.

<!-- vim: ts=4 sw=4 ai et tw=85
-->
