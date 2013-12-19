import collections
import os
import os.path

import os.path as op

from enstaller.store.indexed import LocalIndexedStore


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
