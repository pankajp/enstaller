import contextlib
import os
import shutil
import tempfile

SUPPORT_SYMLINK = hasattr(os, "symlink")

@contextlib.contextmanager
def mkdtemp():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

