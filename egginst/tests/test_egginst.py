import os
import os.path
import shutil
import subprocess
import sys
import tempfile

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import mock

from egginst.eggmeta import APPINST_PATH
from egginst.main import EggInst, get_installed, main
from egginst.testing_utils import slow
from egginst.utils import makedirs, zip_write_symlink, ZipFile

from .common import DUMMY_EGG, DUMMY_EGG_WITH_APPINST, \
        DUMMY_EGG_WITH_ENTRY_POINTS, PYTHON_VERSION, SUPPORT_SYMLINK, mkdtemp

def _create_egg_with_symlink(filename, name):
    with ZipFile(filename, "w") as fp:
        fp.writestr("EGG-INFO/usr/include/foo.h", "/* header */")
        zip_write_symlink(fp, "EGG-INFO/usr/HEADERS", "include")

class TestEggInst(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        makedirs(self.base_dir)
        self.prefix = os.path.join(self.base_dir, "prefix")

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    @slow
    @unittest.skipIf(not SUPPORT_SYMLINK, "this platform does not support symlink")
    def test_symlink(self):
        """Test installing an egg with softlink in it."""
        egg_filename = os.path.join(self.base_dir, "foo-1.0.egg")
        _create_egg_with_symlink(egg_filename, "foo")

        installer = EggInst(egg_filename, prefix=self.prefix)
        installer.install()

        incdir = os.path.join(self.prefix, "include")
        header = os.path.join(incdir, "foo.h")
        link = os.path.join(self.prefix, "HEADERS")

        self.assertTrue(os.path.exists(header))
        self.assertTrue(os.path.exists(link))
        self.assertTrue(os.path.islink(link))
        self.assertEqual(os.readlink(link), "include")
        self.assertTrue(os.path.exists(os.path.join(link, "foo.h")))

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

            self.assertTrue(os.path.basename(DUMMY_EGG) in list(get_installed(d)))

            main(["-r", DUMMY_EGG, "--prefix={0}".format(d)])

            self.assertFalse(os.path.basename(DUMMY_EGG) in list(get_installed(d)))

    def test_get_installed(self):
        r_installed_eggs = sorted([
            os.path.basename(DUMMY_EGG),
            os.path.basename(DUMMY_EGG_WITH_ENTRY_POINTS),
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
        if os.environ.get("ENSTALLER_TEST_USE_VENV", None):
            cmd = ["venv", "-s", self.base_dir]
        else:
            cmd = ["virtualenv", "-p", sys.executable, self.base_dir]
        subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if sys.platform == "win32":
            self.bindir = os.path.join(self.base_dir, "Scripts")
            self.executable = os.path.join(self.base_dir, "python")
            self.site_packages = os.path.join(self.base_dir, "lib", "site-packages")
        else:
            self.bindir = os.path.join(self.base_dir, "bin")
            self.executable = os.path.join(self.base_dir, "bin", "python")
            self.site_packages = os.path.join(self.base_dir, "lib", "python" + PYTHON_VERSION, "site-packages")

        self.meta_dir = os.path.join(self.base_dir, "EGG-INFO")

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    @slow
    def test_simple(self):
        egginst = EggInst(DUMMY_EGG, self.base_dir)

        egginst.install()
        self.assertTrue(os.path.exists(os.path.join(self.site_packages, "dummy.py")))

        egginst.remove()
        self.assertFalse(os.path.exists(os.path.join(self.site_packages, "dummy.py")))

    @slow
    def test_entry_points(self):
        """
        Test we install console entry points correctly.
        """
        egginst = EggInst(DUMMY_EGG_WITH_ENTRY_POINTS, self.base_dir)

        egginst.install()
        self.assertTrue(os.path.exists(os.path.join(self.site_packages, "dummy.py")))
        self.assertTrue(os.path.exists(os.path.join(self.bindir, "dummy")))

        egginst.remove()
        self.assertFalse(os.path.exists(os.path.join(self.site_packages, "dummy.py")))
        self.assertFalse(os.path.exists(os.path.join(self.bindir, "dummy")))

    @slow
    def test_appinst(self):
        """
        Test we install appinst bits correctly.
        """
        egg_path = DUMMY_EGG_WITH_APPINST
        appinst_path = os.path.join(self.meta_dir, "dummy_with_appinst", APPINST_PATH)

        egginst = EggInst(egg_path, self.base_dir)

        with mock.patch("appinst.install_from_dat", autospec=True) as m:
            egginst.install()
            m.assert_called_with(appinst_path, self.base_dir)

        with mock.patch("appinst.uninstall_from_dat", autospec=True) as m:
            egginst.remove()
            m.assert_called_with(appinst_path, self.base_dir)

    @slow
    def test_old_appinst(self):
        """
        Test that we still work with old (<= 2.1.1) appinst, where
        [un]install_from_dat only takes one argument (no prefix).
        """
        egg_path = DUMMY_EGG_WITH_APPINST
        appinst_path = os.path.join(self.meta_dir, "dummy_with_appinst", APPINST_PATH)

        egginst = EggInst(egg_path, self.base_dir)

        def mocked_old_install_from_dat(x):
            pass
        def mocked_old_uninstall_from_dat(x):
            pass

        # XXX: we use autospec to enforce function taking exactly one argument,
        # otherwise the proper TypeError exception is not raised when calling
        # it with two arguments, which is how old vs new appinst is detected.
        with mock.patch("appinst.install_from_dat", autospec=mocked_old_install_from_dat) as m:
            egginst.install()
            m.assert_called_with(appinst_path)

        with mock.patch("appinst.uninstall_from_dat", autospec=mocked_old_uninstall_from_dat) as m:
            egginst.remove()
            m.assert_called_with(appinst_path)
