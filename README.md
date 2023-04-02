# SymbolicMode -- Code to handle symbolic file permissions

This python library parses symbolic file permission modes as used by GNU chmod, part
of the coreutils package.  For example:

    >>> from symbolicmode import *
    >>> oct(symbolic_to_numeric_permissions('a=rx,u+w'))
    '0o755'   

## License

CC0 1.0 Universal, see LICENSE file for more information.

<!-- vim: ts=4 sw=4 ai et tw=85
-->
