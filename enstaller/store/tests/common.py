import collections
import os

import os.path as op

from enstaller.store.indexed import LocalIndexedStore

_EGGINST_COMMON_DATA = op.join(op.dirname(__file__), os.pardir, os.pardir, os.pardir,
                               "egginst", "tests", "data")
DUMMY_EGG = op.join(_EGGINST_COMMON_DATA, "dummy-1.0.0-1.egg")

__st = os.stat(DUMMY_EGG)
DUMMY_EGG_MTIME = __st.st_mtime
DUMMY_EGG_SIZE = __st.st_size
DUMMY_EGG_MD5 = "561dd1eb5b26fa20df6279c4f3ed1f51"

class DummyIndexedStore(LocalIndexedStore):
    """
    A simple store implementation where entries are given at creation time.
    """
    def __init__(self, entries):
        super(DummyIndexedStore, self).__init__("")
        self._entries = entries

    def connect(self, auth=None):
        self._index = self.get_index()
        self._groups = collections.defaultdict(list)

        for entry in self._entries:
            self._groups[entry.name].append(entry.s3index_key)

    def get_index(self):
        return dict((entry.s3index_key, entry.s3index_data) for entry in self._entries)
