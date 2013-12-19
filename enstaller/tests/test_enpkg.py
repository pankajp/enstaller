import os.path
import shutil
import sys
import tempfile

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from egginst.main import EggInst
from egginst.tests.common import mkdtemp
from egginst.tests.test_egginst import DUMMY_EGG
from egginst.utils import makedirs

from enstaller.eggcollect import EggCollection, JoinedEggCollection
from enstaller.enpkg import Enpkg, EnpkgError
from enstaller.main import _create_enstaller_update_enpkg, create_joined_store
from enstaller.store.indexed import LocalIndexedStore, RemoteHTTPIndexedStore
from enstaller.store.tests.common import DummyIndexedStore

PYVER = ".".join(str(i) for i in sys.version_info[:2])

def dummy_enpkg_entry_factory(name, version, build):
    data = {"egg_basename": name, "packages": [], "python": PYVER,
            "size": 1024, "version": version, "build": build,
            "available": True}
    return EnpkgS3IndexEntry.from_data(data)

class TestEnstallerUpdateHack(unittest.TestCase):
    def test_scenario1(self):
        """Test that we upgrade when remote is more recent than local."""
        remote_versions = [("4.6.1", 1)]
        local_version = "4.6.0"

        actions = self._compute_actions(remote_versions, local_version)
        self.assertNotEqual(actions, [])

    def test_scenario2(self):
        """Test that we don't upgrade when remote is less recent than local."""
        remote_versions = [("4.6.1", 1)]
        local_version = "4.6.2"

        actions = self._compute_actions(remote_versions, local_version)
        self.assertEqual(actions, [])

    def _compute_actions(self, remote_versions, local_version):
        prefixes = [sys.prefix]

        entries = [dummy_enpkg_entry_factory("enstaller", version, build) \
                   for version, build in remote_versions]
        repo = DummyIndexedStore(entries)
        repo.connect()

        enpkg = Enpkg(repo, prefixes=prefixes, hook=None,
                      evt_mgr=None, verbose=False)
        new_enpkg = _create_enstaller_update_enpkg(enpkg, local_version)
        return new_enpkg._install_actions_enstaller(local_version)

class TestCreateJoinedStores(unittest.TestCase):
    def test_simple_dir(self):
        with mkdtemp() as d:
            urls = [d]
            store = create_joined_store(urls)
            self.assertEqual(len(store.repos), 1)

            store = store.repos[0]
            self.assertTrue(isinstance(store, LocalIndexedStore))
            self.assertEqual(store.root, d)

    def test_simple_file_scheme(self):
        urls = ["file:///foo"]
        store = create_joined_store(urls)
        self.assertEqual(len(store.repos), 1)

        store = store.repos[0]
        self.assertTrue(isinstance(store, LocalIndexedStore))
        self.assertEqual(store.root, "/foo")

    def test_simple_http_scheme(self):
        urls = ["http://acme.com/repo"]
        store = create_joined_store(urls)
        self.assertEqual(len(store.repos), 1)

        store = store.repos[0]
        self.assertTrue(isinstance(store, RemoteHTTPIndexedStore))
        self.assertEqual(store.root, urls[0])

    def test_invalid_scheme(self):
        urls = ["ftp://acme.com/repo"]
        with self.assertRaises(Exception):
            create_joined_store(urls)

class TestEnpkg(unittest.TestCase):
    def test_info_list_names(self):
        entries = [
            dummy_enpkg_entry_factory("numpy", "1.6.1", 1),
            dummy_enpkg_entry_factory("numpy", "1.8.0", 2),
            dummy_enpkg_entry_factory("numpy", "1.7.1", 1),
        ]

        repo = DummyIndexedStore(entries)
        repo.connect()

        with mkdtemp() as d:
            enpkg = Enpkg(repo, prefixes=[d], hook=None,
                          evt_mgr=None, verbose=False)
            queried_entries = enpkg.info_list_name("numpy")

            self.assertEqual(len(queried_entries), 3)
            self.assertEqual([q["version"] for q in queried_entries],
                             ["1.6.1", "1.7.1", "1.8.0"])

    def test_info_list_names_invalid_version(self):
        entries = [
            dummy_enpkg_entry_factory("numpy", "1.6.1", 1),
            dummy_enpkg_entry_factory("numpy", "1.8k", 2),
        ]

        repo = DummyIndexedStore(entries)
        repo.connect()

        with mkdtemp() as d:
            enpkg = Enpkg(repo, prefixes=[d], hook=None,
                          evt_mgr=None, verbose=False)
            queried_entries = enpkg.info_list_name("numpy")

            self.assertEqual(len(queried_entries), 2)
            self.assertEqual([q["version"] for q in queried_entries],
                             ["1.6.1", "1.8k"])

class TestEnpkgActions(unittest.TestCase):
    def test_install_simple(self):
        entries = [
            dummy_enpkg_entry_factory("numpy", "1.6.1", 1),
            dummy_enpkg_entry_factory("numpy", "1.8.0", 2),
            dummy_enpkg_entry_factory("numpy", "1.7.1", 2),
        ]

        r_actions = [
            ('fetch_0', 'numpy-1.8.0-2.egg'),
            ('install', 'numpy-1.8.0-2.egg')
        ]

        repo = DummyIndexedStore(entries)
        repo.connect()

        with mkdtemp() as d:
            enpkg = Enpkg(repo, prefixes=[d], hook=None,
                          evt_mgr=None, verbose=False)
            actions = enpkg.install_actions("numpy")

            self.assertEqual(actions, r_actions)

    def test_install_no_egg_entry(self):
        entries = [
            dummy_enpkg_entry_factory("numpy", "1.6.1", 1),
            dummy_enpkg_entry_factory("numpy", "1.8.0", 2),
        ]

        repo = DummyIndexedStore(entries)
        repo.connect()

        with mkdtemp() as d:
            enpkg = Enpkg(repo, prefixes=[d], hook=None,
                          evt_mgr=None, verbose=False)
            with self.assertRaises(EnpkgError):
                enpkg.install_actions("scipy")

    def test_remove(self):
        repo = DummyIndexedStore([])
        repo.connect()

        with mkdtemp() as d:
            makedirs(d)

            for egg in [DUMMY_EGG]:
                egginst = EggInst(egg, d)
                egginst.install()

            local_repo = JoinedEggCollection([EggCollection(d, False, None)])
            enpkg = Enpkg(repo, prefixes=[d], hook=None,
                          evt_mgr=None, verbose=False)
            enpkg.ec = local_repo
            enpkg.remove_actions("dummy")

    def test_remove_non_existing(self):
        entries = [
            dummy_enpkg_entry_factory("numpy", "1.6.1", 1),
           dummy_enpkg_entry_factory("numpy", "1.8.0", 2),
        ]

        repo = DummyIndexedStore(entries)
        repo.connect()

        with mkdtemp() as d:
            enpkg = Enpkg(repo, prefixes=[d], hook=None,
                          evt_mgr=None, verbose=False)
            with self.assertRaises(EnpkgError):
                enpkg.remove_actions("numpy")

class TestEnpkgExecute(unittest.TestCase):
    def setUp(self):
        self.prefixes = [tempfile.mkdtemp()]

    def tearDown(self):
        for prefix in self.prefixes:
            shutil.rmtree(prefix)

    def test_simple_fetch(self):
        egg = "yoyo.egg"
        fetch_opcode = 0

        repo = DummyIndexedStore([])
        repo.connect()

        with mock.patch("enstaller.enpkg.Enpkg.fetch") as mocked_fetch:
            enpkg = Enpkg(repo, prefixes=self.prefixes, hook=None,
                          evt_mgr=None, verbose=False)
            enpkg.ec = mock.MagicMock()
            enpkg.execute([("fetch_{0}".format(fetch_opcode), egg)])

            self.assertTrue(mocked_fetch.called)
            self.assertTrue(mocked_fetch.called_arg_list,
                            [(egg, fetch_opcode)])

    def test_simple_install(self):
        egg = DUMMY_EGG
        fetch_opcode = 0

        entries = [
            EnpkgS3IndexEntry(product="free", build=1,
                              egg_basename="dummy", version="1.0.0",
                              available=True),
        ]

        repo = DummyIndexedStore(entries)
        repo.connect()

        with mock.patch("enstaller.enpkg.Enpkg.fetch") as mocked_fetch:
            enpkg = Enpkg(repo, prefixes=self.prefixes, hook=None,
                          evt_mgr=None, verbose=False)
            local_repo = JoinedEggCollection([
                EggCollection(prefix, False, None) for prefix in
                self.prefixes])
            local_repo.install = mock.MagicMock()
            enpkg.ec = local_repo

            actions = enpkg.install_actions("dummy")
            enpkg.execute(actions)

            self.assertTrue(mocked_fetch.called_arg_list,
                            [(egg, fetch_opcode)])
            self.assertTrue(local_repo.install.called_arg_list,
                            [(egg, enpkg.local_dir, None)])
