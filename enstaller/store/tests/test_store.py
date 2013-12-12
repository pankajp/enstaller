import json
import os
import shutil
import tempfile
import unittest
import uuid

import os.path as op

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from egginst.testing_utils import network
from enstaller.store.indexed import LocalIndexedStore, RemoteHTTPIndexedStore
from enstaller.store.joined import JoinedStore

from .common import DUMMY_EGG, DUMMY_WITH_PROXY_EGG

DUMMY_URL = "http://example.com"
API_URL = "http://api.enthought.com/eggs/rh5-64"

class TestRemoteHTTPStore(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_simple_query(self):
        dummy_entry = EnpkgS3IndexEntry.from_egg(DUMMY_EGG, "free", True)
        dummy_index = {
            dummy_entry.egg_basename: dummy_entry.to_dict()
        }
        with mock.patch("enstaller.store.indexed.RemoteHTTPIndexedStore.get_index",
                        lambda ignored: dummy_index):
            store = RemoteHTTPIndexedStore(DUMMY_URL, self.d)
            store.connect()
            result = list(store.query(name="dummy"))

            self.assertEqual(len(result), 1)

    @network
    def test_simple_query_connected(self):
        # FIXME: this is a dumb test, but it allows us to check basic network
        # operations for now.
        store = RemoteHTTPIndexedStore(API_URL, self.d)
        store.connect()
        result = list(store.query(name="numpy"))

        self.assertTrue(len(result) > 1)

class TestLocalIndexedStore(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_simple_query(self):
        dummy_entry = EnpkgS3IndexEntry.from_egg(DUMMY_EGG, "free", True)
        dummy_index = {
            dummy_entry.egg_basename: dummy_entry.to_dict()
        }

        with open(op.join(self.d, "index.json"), "wt") as fp:
            json.dump(dummy_index, fp)

        store = LocalIndexedStore(self.d)
        store.connect()

        params = {"type": "egg"}
        result = list(store.query(**params))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "dummy")

        result = list(store.query_keys(**params))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "dummy")

        params = {"type": "fubar"}
        result = list(store.query(**params))
        self.assertEqual(len(result), 0)

        result = list(store.query_keys(**params))
        self.assertEqual(len(result), 0)

    def test_get_data_missing_key(self):
        with open(op.join(self.d, "index.json"), "wt") as fp:
            json.dump({}, fp)

        store = LocalIndexedStore(self.d)
        store.connect()

        self.assertRaises(KeyError, lambda: store.get_data("dummy_key"))

def _local_store_factory(entries, basedir):
    d = op.join(basedir, str(uuid.uuid4())[:8])
    os.makedirs(d)

    dummy_index = {}
    for entry in entries:
        dummy_index[entry.egg_basename] = entry.to_dict()

    with open(op.join(d, "index.json"), "wt") as fp:
        json.dump(dummy_index, fp)

    return LocalIndexedStore(d)

class TestJoinedStore(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.d)

    def _build_simple_joined_store(self, repo1_entries, repo2_entries):
        store1 = _local_store_factory(repo1_entries, self.d)

        store2 = _local_store_factory(repo2_entries, self.d)

        store = JoinedStore([store1, store2])

        return store

    def test_simple_query(self):
        dummy_entry = EnpkgS3IndexEntry.from_egg(DUMMY_EGG, "free", True)
        dummy_with_proxy_entry = EnpkgS3IndexEntry.from_egg(DUMMY_WITH_PROXY_EGG, "free", True)

        r_dummy_metadata = dummy_entry.to_dict()

        store = self._build_simple_joined_store([dummy_entry], [dummy_with_proxy_entry])
        store.connect()

        metadata = store.get_metadata("dummy")
        metadata.pop("store_location")

        self.assertEqual(metadata, dummy_entry.to_dict())

    def test_exists(self):
        dummy_entry = EnpkgS3IndexEntry.from_egg(DUMMY_EGG, "free", True)
        dummy_with_proxy_entry = EnpkgS3IndexEntry.from_egg(DUMMY_WITH_PROXY_EGG, "free", True)

        store = self._build_simple_joined_store([dummy_entry], [dummy_with_proxy_entry])
        store.connect()

        self.assertTrue(store.exists(dummy_entry.egg_basename))
        self.assertTrue(store.exists(dummy_with_proxy_entry.egg_basename))
        self.assertFalse(store.exists("floupiga"))
