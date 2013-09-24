import os
import unittest

import os.path as op

import mock

from egginst.links import create
from egginst.main import EggInst

from .common import mkdtemp, SUPPORT_SYMLINK

DUMMY_EGG_WITH_PROXY_SOFTLINK = op.join(op.dirname(__file__), "data",
                                        "dummy_with_proxy_softlink-1.0.0-1.egg")

class TestLinks(unittest.TestCase):
    @unittest.skipIf(not SUPPORT_SYMLINK, "this platform does not support symlink")
    def test_simple(self):
        r_link = "libfoo.so"
        r_source = "libfoo.so.0.0.0"

        with mkdtemp() as d:
            egginst = EggInst(DUMMY_EGG_WITH_PROXY_SOFTLINK, d)
            egginst.install()

            link = op.join(d, "lib", r_link)
            source = op.join(d, "lib", r_source)
            self.assertTrue(op.exists(link))
            self.assertTrue(op.exists(source))
            self.assertTrue(op.islink(link))
            self.assertEqual(os.readlink(link), op.basename(source))
