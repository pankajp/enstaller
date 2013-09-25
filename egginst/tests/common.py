import contextlib
import os
import shutil
import sys
import tempfile

import os.path as op

SUPPORT_SYMLINK = hasattr(os, "symlink")

MACHO_DIRECTORY = op.join(op.dirname(__file__), "data", "macho")

LEGACY_PLACEHOLD_FILE = op.join(MACHO_DIRECTORY, "foo_legacy_placehold.dylib")
NOLEGACY_RPATH_FILE = op.join(MACHO_DIRECTORY, "foo_rpath.dylib")

PYEXT_WITH_LEGACY_PLACEHOLD_DEPENDENCY = op.join(MACHO_DIRECTORY, "foo.so")
PYEXT_DEPENDENCY = op.join(MACHO_DIRECTORY, "libfoo.dylib")

FILE_TO_RPATHS = {
    NOLEGACY_RPATH_FILE: ["@loader_path/../lib"],
    LEGACY_PLACEHOLD_FILE: ["/PLACEHOLD" * 20],
}

MACHO_ARCH_TO_FILE = {
    "x86": op.join(MACHO_DIRECTORY, "foo_x86"),
    "amd64": op.join(MACHO_DIRECTORY, "foo_amd64"),
}

PYTHON_VERSION = ".".join(str(i) for i in sys.version_info[:2])

DUMMY_EGG_WITH_INST_TARGETS = op.join(MACHO_DIRECTORY, "dummy_with_target_dat-1.0.0-1.egg")

@contextlib.contextmanager
def mkdtemp():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

