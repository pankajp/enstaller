import contextlib
import os
import shutil
import sys
import tempfile

import os.path as op

SUPPORT_SYMLINK = hasattr(os, "symlink")

MACHO_DIRECTORY = os.path.join(os.path.dirname(__file__), "data", "macho")

LEGACY_PLACEHOLD_FILE = os.path.join(MACHO_DIRECTORY, "foo_legacy_placehold.dylib")
NOLEGACY_RPATH_FILE = os.path.join(MACHO_DIRECTORY, "foo_rpath.dylib")

PYEXT_WITH_LEGACY_PLACEHOLD_DEPENDENCY = os.path.join(MACHO_DIRECTORY, "foo.so")
PYEXT_DEPENDENCY = os.path.join(MACHO_DIRECTORY, "libfoo.dylib")

FILE_TO_RPATHS = {
    NOLEGACY_RPATH_FILE: ["@loader_path/../lib"],
    LEGACY_PLACEHOLD_FILE: ["/PLACEHOLD" * 20],
}

MACHO_ARCH_TO_FILE = {
    "x86": os.path.join(MACHO_DIRECTORY, "foo_x86"),
    "amd64": os.path.join(MACHO_DIRECTORY, "foo_amd64"),
}

PYTHON_VERSION = ".".join(str(i) for i in sys.version_info[:2])

DUMMY_EGG_WITH_INST_TARGETS = os.path.join(MACHO_DIRECTORY, "dummy_with_target_dat-1.0.0-1.egg")
DUMMY_EGG_WITH_APPINST = os.path.join(os.path.dirname(__file__), "data", "dummy_with_appinst-1.0.0-1.egg")

NOSE_1_2_1 = os.path.join(os.path.dirname(__file__), "data", "nose-1.2.1-1.egg")
NOSE_1_3_0 = os.path.join(os.path.dirname(__file__), "data", "nose-1.3.0-1.egg")

@contextlib.contextmanager
def mkdtemp():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

