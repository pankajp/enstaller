from enstaller.store.indexed import LocalIndexedStore

class DummyIndexedStore(LocalIndexedStore):
    """
    A simple store implementation where entries are given at creation time.
    """
    def __init__(self, entries):
        super(DummyIndexedStore, self).__init__("")
        self._entries = entries

    def get_index(self):
        return dict((entry.s3index_key, entry.s3index_data) for entry in self._entries)
