import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import os.path as op

import mock

from egginst.eggmeta import APPINST_PATH
from egginst.main import EggInst, get_installed, main
from egginst.utils import makedirs, zip_write_symlink

from .common import DUMMY_EGG_WITH_APPINST, PYTHON_VERSION, SUPPORT_SYMLINK, mkdtemp

DUMMY_EGG = op.join(op.dirname(__file__), "data", "dummy-1.0.0-1.egg")
DUMMY_EGG_WITH_ENTRY_POINTS = op.join(op.dirname(__file__), "data", "dummy_with_entry_points-1.0.0-1.egg")

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
        # XXX: this is lousy test: we'd like to at least ensure we're printing
        # the correct version, but capturing the stdout is a bit tricky. Once
        # we replace print by proper logging, we should be able to do better.
        main(["--version"])

    def test_list(self):
        # XXX: this is lousy test: we'd like to at least ensure we're printing
        # the correct packages, but capturing the stdout is a bit tricky. Once
        # we replace print by proper logging, we should be able to do better.
        main(["--list"])

    def test_install_simple(self):
        with mkdtemp() as d:
            main([DUMMY_EGG, "--prefix={0}".format(d)])

            self.assertTrue(op.basename(DUMMY_EGG) in list(get_installed(d)))

            main(["-r", DUMMY_EGG, "--prefix={0}".format(d)])

            self.assertFalse(op.basename(DUMMY_EGG) in list(get_installed(d)))

    def test_get_installed(self):
        r_installed_eggs = sorted([
            op.basename(DUMMY_EGG),
            op.basename(DUMMY_EGG_WITH_ENTRY_POINTS),
        ])

        with mkdtemp() as d:
            egginst = EggInst(DUMMY_EGG, d)
            egginst.install()

            egginst = EggInst(DUMMY_EGG_WITH_ENTRY_POINTS, d)
            egginst.install()

            installed_eggs = list(get_installed(d))
            self.assertEqual(installed_eggs, r_installed_eggs)

class TestEggInstInstall(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        cmd = ["virtualenv", "-p", sys.executable, self.base_dir]
        subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if sys.platform == "win32":
            self.bindir = op.join(self.base_dir, "Scripts")
            self.executable = op.join(self.base_dir, "python")
            self.site_packages = op.join(self.base_dir, "lib", "site-packages")
        else:
            self.bindir = op.join(self.base_dir, "bin")
            self.executable = op.join(self.base_dir, "bin", "python")
            self.site_packages = op.join(self.base_dir, "lib", "python" + PYTHON_VERSION, "site-packages")

        self.meta_dir = op.join(self.base_dir, "EGG-INFO")

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    def test_simple(self):
        egginst = EggInst(DUMMY_EGG, self.base_dir)

        egginst.install()
        self.assertTrue(op.exists(op.join(self.site_packages, "dummy.py")))

        egginst.remove()
        self.assertFalse(op.exists(op.join(self.site_packages, "dummy.py")))

    def test_entry_points(self):
        """
        Test we install console entry points correctly.
        """
        egginst = EggInst(DUMMY_EGG_WITH_ENTRY_POINTS, self.base_dir)

        egginst.install()
        self.assertTrue(op.exists(op.join(self.site_packages, "dummy.py")))
        self.assertTrue(op.exists(op.join(self.bindir, "dummy")))

        egginst.remove()
        self.assertFalse(op.exists(op.join(self.site_packages, "dummy.py")))
        self.assertFalse(op.exists(op.join(self.bindir, "dummy")))

    def test_appinst(self):
        """
        Test we install appinst bits correctly.
        """
        egg_path = DUMMY_EGG_WITH_APPINST
        appinst_path = op.join(self.meta_dir, "dummy_with_appinst", APPINST_PATH)

        egginst = EggInst(egg_path, self.base_dir)

        mocked_appinst = mock.Mock()
        with mock.patch("appinst.install_from_dat", mocked_appinst.install_from_dat):
            egginst.install()
            mocked_appinst.install_from_dat.assert_called_with(appinst_path, self.base_dir)

        with mock.patch("appinst.uninstall_from_dat", mocked_appinst.uninstall_from_dat):
            egginst.remove()
            mocked_appinst.install_from_dat.assert_called_with(appinst_path, self.base_dir)
