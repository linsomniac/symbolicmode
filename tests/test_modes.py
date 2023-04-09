#!/usr/bin/env python3

import unittest
from symbolicmode import symbolic_to_numeric_permissions


class TestSymbolicToNumericPermissions(unittest.TestCase):
    def test_basic_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r"), 0o754)
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o="), 0o640)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=,o="), 0o700)
        self.assertEqual(symbolic_to_numeric_permissions("a=r"), 0o444)
        self.assertEqual(symbolic_to_numeric_permissions("a=-,ug+r,u+w"), 0o640)
        self.assertEqual(symbolic_to_numeric_permissions("+X", 0o500), 0o511)
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rwx,g+rwx,o=rwx", 0o000), 0o777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rwx,g+rwx,o=rwx", 0o000, True), 0o777
        )

    def test_add_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o=,ug+w"), 0o660)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,u+w"), 0o754)

    def test_remove_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o=,ug-w"), 0o440)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,u-w"), 0o554)
        self.assertEqual(symbolic_to_numeric_permissions("a=rwxs,u-s"), 0o2777)
        pass

    def test_special_X_permission(self):
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwX", is_directory=False), 0o600
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwX", is_directory=True), 0o700
        )

    def test_special_s_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rws,g=rx,o=r"), 0o4654)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rs,o=r"), 0o2744)

    def test_special_t_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=rt"), 0o1754)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rt,o=rx"), 0o745)

    def test_special_X_permission_with_directory(self):
        # For directories, the "X" permission should behave like the "x" permission
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rX,g=rX,o=rX", is_directory=True), 0o555
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rX,g=rX,o=rX", is_directory=False), 0o444
        )

    def test_sticky_bit_with_directory(self):
        # The sticky bit "t" should be set correctly for directories
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rx,o=rt", is_directory=True), 0o1754
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rt,o=rx", is_directory=True), 0o0745
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,a+t", is_directory=True),
            0o1754,
        )

    def test_initial_modes(self):
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw", 0o777, False), 0o777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw", 0o777, True), 0o777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw", 0o666, False), 0o666
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o666, True), 0o777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o666, False), 0o666
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o766, False), 0o777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o656, False), 0o777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o4656, False), 0o4777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o2656, False), 0o2777
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u+rw,g+rw,o+rw,a+X", 0o1656, False), 0o1777
        )
        self.assertEqual(symbolic_to_numeric_permissions("a=", 0o7777, False), 0o0)
        self.assertEqual(symbolic_to_numeric_permissions("a=", 0o7777, True), 0o6000)
        self.assertEqual(symbolic_to_numeric_permissions("o+t,a=", 0o4226, False), 0o0)
        self.assertEqual(symbolic_to_numeric_permissions("o+t,a=", 0o4226, True), 0o4000)
        self.assertEqual(
            symbolic_to_numeric_permissions("a=t,ug+srt", 0o737, False), 0o7440
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("a=t,ug+srt,o=X", 0o737, False), 0o6440
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("a=t,ug+srt,o=X", 0o737, True), 0o6441
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("a=t,ug+srt,o=Xx", 0o737, True), 0o6441
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("a=t,ug+srt,o=Xx", 0o737, False), 0o6441
        )

    def test_umask(self):
        self.assertEqual(
            symbolic_to_numeric_permissions("=rw", 0o4777, False, 0o027), 0o640
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("=rw", 0o4777, True, 0o027), 0o4640
        )

    def test_ugo_perms(self):
        self.assertEqual(symbolic_to_numeric_permissions("g=u", 0o4755, False), 0o4775)
        self.assertEqual(symbolic_to_numeric_permissions("a=u", 0o4755, False), 0o777)
        self.assertEqual(symbolic_to_numeric_permissions("a=u", 0o4755, True), 0o4777)
        self.assertEqual(symbolic_to_numeric_permissions("og=u", 0o4755, False), 0o4777)
        self.assertEqual(symbolic_to_numeric_permissions("og=u", 0o4755, True), 0o4777)
        self.assertEqual(symbolic_to_numeric_permissions("og+u", 0o4755, False), 0o4777)
        self.assertEqual(symbolic_to_numeric_permissions("og-u", 0o4755, False), 0o4700)
        with self.assertRaises(ValueError):
            symbolic_to_numeric_permissions("u=go", 0o4777, True)
        with self.assertRaises(ValueError):
            symbolic_to_numeric_permissions("u=gr", 0o4777, True)

    def test_multi_operator(self):
        self.assertEqual(symbolic_to_numeric_permissions("g=u", 0o4755, False), 0o4775)
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw-x,g=r-x,o=r", 0o0777, False), 0o644
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw-x,g=r-x,o=r", 0o0777, True), 0o644
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=r+x,g=u-x,o=g", 0o0777, False), 0o544
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=r+x,g=u-x,o=g", 0o0777, True), 0o544
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw,g=u-x,o=g+r", 0o0777, False), 0o666
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw,g=u-x,o=g+r", 0o0777, True), 0o666
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=u-wx,o=r", 0o0777, False), 0o744
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=u-wx,o=r", 0o0777, True), 0o744
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw,g=w,o=x", 0o0777, False), 0o621
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw,g=w,o=x", 0o0777, True), 0o621
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw-x,g=rw,o=g-x", 0o0777, False), 0o666
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw-x,g=rw,o=g-x", 0o0777, True), 0o666
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=r-x,g=wx,o=rw", 0o0777, False), 0o436
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=r-x,g=wx,o=rw", 0o0777, True), 0o436
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw,g=u+x,o=g-rx", 0o0777, False), 0o672
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rw,g=u+x,o=g-rx", 0o0777, True), 0o672
        )


# Run the unit tests
if __name__ == "__main__":
    unittest.main()
