#!/usr/bin/env python3

import unittest
from symbolicmode import chmod
import tempfile
import os
import stat


class TestChmod(unittest.TestCase):
    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        os.unlink(self.tmp_file.name)
        self.tmp_dir.cleanup()

    def test_chmod_octal_integer(self):
        new_mode = 0o755
        chmod(0o755, self.tmp_file.name)
        self.assertEqual(stat.S_IMODE(os.stat(self.tmp_file.name).st_mode), 0o755)

    def test_chmod_octal_string(self):
        chmod("755", self.tmp_file.name)
        self.assertEqual(stat.S_IMODE(os.stat(self.tmp_file.name).st_mode), 0o755)

    def test_chmod_symbolic_permissions(self):
        new_mode = "u=rwx,g=rx,o=r"
        chmod(new_mode, self.tmp_dir.name)
        self.assertEqual(stat.S_IMODE(os.stat(self.tmp_dir.name).st_mode), 0o754)

    def test_recursive(self):
        topdir = os.path.join(self.tmp_dir.name, "topdir")
        os.mkdir(topdir)
        topfile = os.path.join(topdir, "topfile")
        with open(topfile, "w") as fp:
            fp.write("TopFile")
        lowerdir = os.path.join(topdir, "lowerdir")
        os.mkdir(lowerdir)
        lowerfile = os.path.join(lowerdir, "lowerfile")
        with open(lowerfile, "w") as fp:
            fp.write("LowerFile")

        chmod("u=rx,go=", topdir, recurse=True)
        self.assertEqual(stat.S_IMODE(os.stat(topdir).st_mode), 0o500)
        self.assertEqual(stat.S_IMODE(os.stat(topfile).st_mode), 0o500)
        self.assertEqual(stat.S_IMODE(os.stat(lowerdir).st_mode), 0o500)
        self.assertEqual(stat.S_IMODE(os.stat(lowerfile).st_mode), 0o500)

        #  clean up, allow removal
        chmod("u=rwx,go=", topdir, recurse=True)


# Run the unit tests
if __name__ == "__main__":
    unittest.main()
