import os
import shutil
import unittest

import os.path as op

import mock

from machotools.rpath import list_rpaths

from egginst.object_code import fix_object_code, get_object_type

from .common import FILE_TO_RPATHS, LEGACY_PLACEHOLD_FILE, NOLEGACY_RPATH_FILE, MACHO_ARCH_TO_FILE, mkdtemp

class TestObjectCode(unittest.TestCase):
    def test_get_object_type(self):
        self.assertEqual(get_object_type(MACHO_ARCH_TO_FILE["x86"]), "MachO-i386")
        self.assertEqual(get_object_type(MACHO_ARCH_TO_FILE["amd64"]), "MachO-x86_64")

        self.assertEqual(get_object_type("dummy_no_exist"), None)
        self.assertEqual(get_object_type(__file__), None)

    def test_fix_object_code_legacy_macho(self):
        """
        Test that we handle correctly our legacy egg with the /PLACHOLD * 20 hack.
        """
        with mkdtemp() as d:
            copy = op.join(d, "foo.dylib")
            shutil.copy(LEGACY_PLACEHOLD_FILE, copy)

            with mock.patch("egginst.object_code._targets", [d]):
                fix_object_code(copy)
                rpaths = list_rpaths(copy)

                self.assertEqual(rpaths[0], [d])

    def test_fix_object_code_wo_legacy_macho(self):
        """
        Test that we handle correctly egg *without* the /PLACHOLD (i.e. we
        don't touch them).
        """
        r_rpaths = FILE_TO_RPATHS[NOLEGACY_RPATH_FILE]
        with mkdtemp() as d:
            copy = op.join(d, "foo.dylib")
            shutil.copy(NOLEGACY_RPATH_FILE, copy)

            with mock.patch("egginst.object_code._targets", [d]):
                fix_object_code(copy)
                rpaths = list_rpaths(copy)[0]

                self.assertEqual(rpaths, r_rpaths)
