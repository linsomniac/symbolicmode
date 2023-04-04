# Fuzzing Chmod vs SymbolicMode

This directory contains tools for fuzz testing symbolicmode against the system chmod.

genfuzz will generate the fuzz data in the form of a umask, initial permission, and
symbolic permission string.  It generates them infinitely, so you probably want to
run it as "genfuzz | head -1000" or something.

testmodes reads the fuzzing commands as generated from genfuzz, and then creates
files and directories based on that information and uses the system "chmod" command
to change the mode, and records it.  It then calls the symbolicmode library to
generate a mode from the same information, and if the results of the library differs
from what chmod results are, it adds a "#" comment to the end of the results line.

So a typical way of running it would be:

    ./genfuzz | head -10000 | ./testmodes | grep '#'

<!-- vim: ts=4 sw=4 ai et tw=85
-->
