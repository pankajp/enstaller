import unittest

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from enstaller.enpkg import Enpkg
from enstaller.main import main, update_enstaller
from enstaller.store.tests.common import MetadataOnlyStore

from .common import patched_read

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
