import contextlib
import os
import shutil
import tempfile

import os.path as op

SUPPORT_SYMLINK = hasattr(os, "symlink")

DYLIB_DIRECTORY = op.join(op.dirname(__file__), "data")

FILE_TO_RPATH = {
    op.join(DYLIB_DIRECTORY, "foo.dylib"): [],
    op.join(DYLIB_DIRECTORY, "foo_rpath.dylib"): ["@loader_path/../lib"],
    op.join(DYLIB_DIRECTORY, "foo_rpath_legacy_plahold.dylib"): ["/PLACEHOLD" * 20],
}

MACHO_ARCH_TO_FILE = {
    "x86": op.join(DYLIB_DIRECTORY, "foo_x86"),
    "amd64": op.join(DYLIB_DIRECTORY, "foo_amd64"),
}

@contextlib.contextmanager
def mkdtemp():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

