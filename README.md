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

- It does not yet implement the "ugo" permissions (when a "ugo" appears on the
  right hand side of the operator, for example "go=u").

## Permissions Instructions

Permission instructions are 1 or more comma separated values of the form:
"[USERS][=+-][PERMS]".

USERS can be:

- u: Set permissions for the owner.
- g: Set permissions for group access.
- o: Set permissions for all others.
- a: All of the above.
- "": The empty string, only allowed with "=" for the operator.  Applies to all (like
  "a"), but applies the umask to the permissions set.

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
