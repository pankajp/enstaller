import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import os.path as op

from egginst.main import EggInst, main
from egginst.utils import makedirs, zip_write_symlink

SUPPORT_SYMLINK = hasattr(os, "symlink")

DUMMY_EGG = op.join(op.dirname(__file__), "data", "dummy-1.0.0-1.egg")

PYTHON_VERSION = ".".join(str(i) for i in sys.version_info[:2])

def _create_egg_with_symlink(filename, name):
    with zipfile.ZipFile(filename, "w") as fp:
        fp.writestr("EGG-INFO/usr/include/foo.h", "/* header */")
        zip_write_symlink(fp, "EGG-INFO/usr/HEADERS", "include")

class TestEggInst(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        makedirs(self.base_dir)
        self.prefix = op.join(self.base_dir, "prefix")

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    @unittest.skipIf(not SUPPORT_SYMLINK, "this platform does not support symlink")
    def test_symlink(self):
        """Test installing an egg with softlink in it."""
        egg_filename = op.join(self.base_dir, "foo-1.0.egg")
        _create_egg_with_symlink(egg_filename, "foo")

        installer = EggInst(egg_filename, prefix=self.prefix)
        installer.install()

        incdir = op.join(self.prefix, "include")
        header = op.join(incdir, "foo.h")
        link = op.join(self.prefix, "HEADERS")

        self.assertTrue(op.exists(header))
        self.assertTrue(op.exists(link))
        self.assertTrue(op.islink(link))
        self.assertEqual(os.readlink(link), "include")
        self.assertTrue(op.exists(op.join(link, "foo.h")))

class TestEggInstMain(unittest.TestCase):
    def test_print_version(self):
        main(["--version"])

class TestEggInstInstall(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        cmd = ["virtualenv", "-p", sys.executable, self.base_dir]
        subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if sys.platform == "win32":
            self.executable = op.join(self.base_dir, "python")
            self.site_packages = op.join(self.base_dir, "lib", "site-packages")
        else:
            self.executable = op.join(self.base_dir, "bin", "python")
            self.site_packages = op.join(self.base_dir, "lib", "python" + PYTHON_VERSION, "site-packages")

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    def test_simple(self):
        egginst = EggInst(DUMMY_EGG, self.base_dir)

        egginst.install()
        self.assertTrue(op.exists(op.join(self.site_packages, "dummy.py")))

        egginst.remove()
        self.assertFalse(op.exists(op.join(self.site_packages, "dummy.py")))
