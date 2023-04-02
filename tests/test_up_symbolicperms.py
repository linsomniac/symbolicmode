#!/usr/bin/env python3

import unittest
from chmod import symbolic_to_numeric_permissions


class TestSymbolicToNumericPermissions(unittest.TestCase):
    def test_basic_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r"), 0o754)
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o="), 0o640)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=,o="), 0o700)
        self.assertEqual(symbolic_to_numeric_permissions("a=r"), 0o444)
        self.assertEqual(symbolic_to_numeric_permissions("a=-,ug+r,u+w"), 0o640)

    def test_add_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o=,ug+w"), 0o660)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,u+w"), 0o754)

    def test_remove_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o=,ug-w"), 0o440)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,u-w"), 0o554)
        self.assertEqual(symbolic_to_numeric_permissions("a=rwxs,u-s"), 0o2777)
        pass

    def test_special_X_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwX", False), 0o600)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwX", True), 0o700)

    def test_special_s_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rws,g=rx,o=r"), 0o4654)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rs,o=r"), 0o2744)

    def test_special_t_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=rt"), 0o1754)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rt,o=rx"), 0o745)

    def test_special_X_permission_with_directory(self):
        # For directories, the "X" permission should behave like the "x" permission
        self.assertEqual(symbolic_to_numeric_permissions("u=rX,g=rX,o=rX", True), 0o555)
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rX,g=rX,o=rX", False), 0o444
        )

    def test_sticky_bit_with_directory(self):
        # The sticky bit "t" should be set correctly for directories
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rx,o=rt", True), 0o1754
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rt,o=rx", True), 0o0745
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,a+t", True), 0o1754
        )


# Run the unit tests
if __name__ == "__main__":
    unittest.main()
