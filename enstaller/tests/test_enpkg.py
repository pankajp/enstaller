import collections
import sys
import unittest

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from enstaller.enpkg import Enpkg
from enstaller.store.indexed import IndexedStore

from enstaller.main import _create_enstaller_update_enpkg

from enstaller.tests.common import DummyIndexedStore

def dummy_enpk_entry_factory(name, version, build):
    data = {"egg_basename": name, "packages": [], "python": "2.7",
            "size": 1024, "version": version, "build": build,
            "available": True}
    return EnpkgS3IndexEntry.from_data(data)

class TestEnstallerHack(unittest.TestCase):
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

        entries = [dummy_enpk_entry_factory("enstaller", version, build) \
                   for version, build in remote_versions]
        repo = DummyIndexedStore(entries)
        repo.connect()

        enpkg = Enpkg(repo, prefixes=prefixes, hook=None,
                      evt_mgr=None, verbose=False)
        new_enpkg = _create_enstaller_update_enpkg(enpkg, local_version)
        return new_enpkg._install_actions_enstaller(local_version)


if __name__ == "__main__":
    unittest.main()
