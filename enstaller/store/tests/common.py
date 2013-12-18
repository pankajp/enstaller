import collections
import os

import os.path as op

from enstaller.store.indexed import LocalIndexedStore

_EGGINST_COMMON_DATA = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir,
                               "egginst", "tests", "data")
DUMMY_EGG = os.path.join(_EGGINST_COMMON_DATA, "dummy-1.0.0-1.egg")
DUMMY_WITH_PROXY_EGG = os.path.join(_EGGINST_COMMON_DATA, "dummy_with_proxy-1.3.40-3.egg")

__st = os.stat(DUMMY_EGG)
DUMMY_EGG_MTIME = __st.st_mtime
DUMMY_EGG_SIZE = __st.st_size
DUMMY_EGG_MD5 = "1ec1f69526c55db7420b0d480c9b955e"

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
