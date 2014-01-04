import os.path
import unittest

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from egginst.tests.common import mkdtemp, DUMMY_EGG

from enstaller.enpkg import Enpkg
from enstaller.main import disp_store_info, info_option, \
    install_time_string, main, name_egg, update_enstaller
from enstaller.store.tests.common import MetadataOnlyStore

from .common import dummy_enpkg_entry_factory, patched_read

class TestEnstallerMainActions(unittest.TestCase):
    def test_print_version(self):
        # XXX: this is lousy test: we'd like to at least ensure we're printing
        # the correct version, but capturing the stdout is a bit tricky. Once
        # we replace print by proper logging, we should be able to do better.
        try:
            main(["--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_help_runs_and_exits_correctly(self):
        try:
            main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_print_env(self):
        try:
            main(["--env"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

class TestEnstallerUpdate(unittest.TestCase):
    @mock.patch("enstaller.config.read", lambda: patched_read(autoupdate=False))
    def test_no_update_enstaller(self):
        enpkg = Enpkg()
        self.assertFalse(update_enstaller(enpkg, {}))

    def _test_update_enstaller(self, low_version, high_version):
        enstaller_eggs = [
            EnpkgS3IndexEntry(product="free", build=1,
                              egg_basename="enstaller", version=low_version,
                              available=True),
            EnpkgS3IndexEntry(product="free", build=1,
                              egg_basename="enstaller", version=high_version,
                              available=True),
        ]
        store = MetadataOnlyStore(enstaller_eggs)
        with mock.patch("__builtin__.raw_input", lambda ignored: "y"):
            with mock.patch("enstaller.main.install_req", lambda *args: None):
                enpkg = Enpkg(remote=store)
                opts = mock.Mock()
                opts.no_deps = False
                return update_enstaller(enpkg, opts)

    @mock.patch("enstaller.config.read", lambda: patched_read(autoupdate=True))
    @mock.patch("enstaller.__version__", "4.6.3")
    @mock.patch("enstaller.main.__ENSTALLER_VERSION__", "4.6.3")
    @mock.patch("enstaller.main.IS_RELEASED", True)
    def test_update_enstaller_higher_available(self):
        # low/high versions are below/above any realistic enstaller version
        low_version, high_version = "1.0.0", "666.0.0"
        self.assertTrue(self._test_update_enstaller(low_version, high_version))

    @mock.patch("enstaller.config.read", lambda: patched_read(autoupdate=True))
    @mock.patch("enstaller.__version__", "4.6.3")
    @mock.patch("enstaller.main.__ENSTALLER_VERSION__", "4.6.3")
    @mock.patch("enstaller.main.IS_RELEASED", True)
    def test_update_enstaller_higher_unavailable(self):
        # both low/high versions are below current enstaller version
        low_version, high_version = "1.0.0", "2.0.0"
        self.assertFalse(self._test_update_enstaller(low_version, high_version))

class TestMisc(unittest.TestCase):
    def test_disp_store_info(self):
        info = {"store_location": "https://api.enthought.com/eggs/osx-64/"}
        self.assertEqual(disp_store_info(info), "api osx-64")

        info = {"store_location": "https://api.enthought.com/eggs/win-32/"}
        self.assertEqual(disp_store_info(info), "api win-32")

        info = {}
        self.assertEqual(disp_store_info(info), "-")

    def test_name_egg(self):
        name = "foo-1.0.0-1.egg"
        self.assertEqual(name_egg(name), "foo")

        name = "fu_bar-1.0.0-1.egg"
        self.assertEqual(name_egg(name), "fu_bar")

        with self.assertRaises(AssertionError):
            name = "some/dir/fu_bar-1.0.0-1.egg"
            name_egg(name)

def _create_prefix_with_eggs(prefix, installed_eggs, remote_entries=None):
    if remote_entries is None:
        remote_entries = []
    repo = MetadataOnlyStore(remote_entries)
    repo.connect()

    enpkg = Enpkg(repo, prefixes=[prefix], hook=None,
                  evt_mgr=None, verbose=False)
    for egg in installed_eggs:
        enpkg.ec.install(os.path.basename(egg), os.path.dirname(egg))
    return enpkg

class TestInfoStrings(unittest.TestCase):
    def test_print_install_time(self):
        with mkdtemp() as d:
            enpkg = _create_prefix_with_eggs(d, [DUMMY_EGG])

            self.assertRegexpMatches(install_time_string(enpkg, "dummy"),
                                     "dummy-1.0.1-1.egg was installed on:")

            self.assertEqual(install_time_string(enpkg, "ddummy"), "")

    def test_info_option(self):
        with mkdtemp() as d:
            entries = [dummy_enpkg_entry_factory("enstaller", "4.6.2", 1),
                       dummy_enpkg_entry_factory("enstaller", "4.6.3", 1)]
            enpkg = _create_prefix_with_eggs(d, [], entries)

            info_option(enpkg, "enstaller")
