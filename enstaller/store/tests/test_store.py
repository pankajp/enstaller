import json
import os
import shutil
import tempfile
import unittest

import os.path as op

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from egginst.testing_utils import network
from enstaller.store.indexed import LocalIndexedStore, RemoteHTTPIndexedStore

from .common import DUMMY_EGG

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
