# SymbolicMode -- Code to handle symbolic file permissions

This python library parses symbolic file permission modes as used by GNU chmod, part
of the coreutils package.  For example:

    >>> from symbolicmode import *
    >>> oct(symbolic_to_numeric_permissions('a=rx,u+w'))
    '0o755'   

## Status

This library is fully compatible with GNU Coreutils 8.32-4.1ubuntu1, the version on
my system which I have extensively tested using fuzz testing, with the following
exceptions:

- It does not yet implement the "umask" based permissions setting (when no user
  portion is specified on the left hand side of the operator, for example "=rx").
- It does not yet implement the "ugo" permissions (when a "ugo" appears on the
  right hand side of the operator, for example "go=u").

## Fuzz Testing

In the "fuzzchmod" directory is a set of programs for fuzz testing SymbolicMode
against the system "chmod" to try to ensure correctness for even unusual inputs.

## License

CC0 1.0 Universal, see LICENSE file for more information.

<!-- vim: ts=4 sw=4 ai et tw=85
-->
