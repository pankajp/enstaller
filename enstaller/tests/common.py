import contextlib

from cStringIO import StringIO

import mock

from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

import enstaller.config

from enstaller.utils import PY_VER

def patched_read(**kw):
    config = {}
    config.update(enstaller.config.default)
    config.update(**kw)
    return config

def dummy_enpkg_entry_factory(name, version, build):
    data = {"egg_basename": name, "packages": [], "python": PY_VER,
            "size": 1024, "version": version, "build": build,
            "available": True}
    return EnpkgS3IndexEntry.from_data(data)

class MockedPrint(object):
    def __init__(self):
        self.s = StringIO()

    def __call__(self, *a):
        self.s.write(" ".join(a) + "\n")

    @property
    def value(self):
        return self.s.getvalue()

@contextlib.contextmanager
def mock_print():
    m = MockedPrint()

    with mock.patch("__builtin__.print", m):
        yield m
