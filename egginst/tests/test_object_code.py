import unittest

import mock

from egginst.object_code import get_object_type

from .common import MACHO_ARCH_TO_FILE

class TestObjectCode(unittest.TestCase):
    def test_get_object_type(self):
        self.assertEqual(get_object_type(MACHO_ARCH_TO_FILE["x86"]), "MachO-i386")
        self.assertEqual(get_object_type(MACHO_ARCH_TO_FILE["amd64"]), "MachO-x86_64")

        self.assertEqual(get_object_type("dummy_no_exist"), None)
        self.assertEqual(get_object_type(__file__), None)
