import collections
import sys
import unittest

from enstaller.enpkg import Enpkg
from enstaller.store.indexed import IndexedStore

from enstaller.main import _create_enstaller_update_enpkg

PYVER = ".".join(str(i) for i in sys.version_info[:2])

class PackageMetadata(object):
    def __init__(self, name, version, build, python=None, packages=None, type="egg"):
        self.name = name
        self.version = version
        self.build = build
        if python is None:
            self.python = PYVER
        else:
            self.python = python
        if packages is None:
            self.packages = []
        else:
            self.packages = packages
        self.type = type


    def to_spec(self):
        return {"name": self.name, "version": self.version,
                "build": self.build, "python": self.python,
                "packages": self.packages, "type":
                self.type}


    @property
    def eggname(self):
        return "{}-{}-{}.egg".format(self.name, self.version, self.build)

class DummyStore(IndexedStore):
    def __init__(self, metadata):
        self._metadata = metadata
        self.name = self.__class__.__name__

    def connect(self, auth=None):
        self._index = dict((v.eggname, v.to_spec()) for v in self._metadata)
        for spec in self._index.itervalues():
            spec['name'] = spec['name'].lower()
            spec['type'] = 'egg'
            spec['repo_dispname'] = self.name
        self._groups = collections.defaultdict(list)
        for key, info in self._index.iteritems():
            self._groups[info['name']].append(key)

    def get_data(self, key):
        pass

class TestEnstallerHack(unittest.TestCase):
    def test_scenario1(self):
        """Test that we upgrade when remote is more recent than local."""
        remote_versions = [("4.6.1", "1")]
        local_version = "4.6.0"

        actions = self._compute_actions(remote_versions, local_version)
        self.assertNotEqual(actions, [])

    def test_scenario2(self):
        """Test that we don't upgrade when remote is less recent than local."""
        remote_versions = [("4.6.1", "1")]
        local_version = "4.6.2"

        actions = self._compute_actions(remote_versions, local_version)
        self.assertEqual(actions, [])

    def _compute_actions(self, remote_versions, local_version):
        prefixes = [sys.prefix]

        repo = DummyStore(
                [PackageMetadata("enstaller", version, build) 
                 for version, build in remote_versions])
        enpkg = Enpkg(repo, prefixes=prefixes, hook=None,
                      evt_mgr=None, verbose=False)
        new_enpkg = _create_enstaller_update_enpkg(enpkg, local_version)
        return new_enpkg._install_actions_enstaller(local_version)


if __name__ == "__main__":
    unittest.main()
