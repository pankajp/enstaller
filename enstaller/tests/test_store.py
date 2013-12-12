import os
import shutil
import tempfile
import unittest

import os.path as op

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

from egginst.testing_utils import network
from enstaller.store.indexed import RemoteHTTPIndexedStore

DUMMY_URL = "http://example.com"
API_URL = "http://api.enthought.com/eggs/rh5-64"

_EGGINST_COMMON_DATA = op.join(op.dirname(__file__), os.pardir, os.pardir,
                               "egginst", "tests", "data")
DUMMY_EGG = op.join(_EGGINST_COMMON_DATA, "dummy-1.0.0-1.egg")

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
