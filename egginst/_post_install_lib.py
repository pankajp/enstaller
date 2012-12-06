import logging
import os
import re
import tempfile
import uuid

import os.path as op

def safe_write(target, writer, mode="wt"):
    """a 'safe' way to write to files.

    Instead of writing directly into a file, this function writes to a
    temporary file, and then rename the file to the target if no error occured.
    On most platforms, rename is atomic, so this avoids leaving stale files in
    inconsistent states.

    Parameters
    ----------
    target: str
        destination to write to
    writer: callable or data
        if callable, assumed to be function which takes one argument, a file
        descriptor, and writes content to it. Otherwise, assumed to be data
        to be directly written to target.
    mode: str
        opening mode
    """
    if not callable(writer):
        data = writer
        writer = lambda fp: fp.write(data)

    tmp_target = "%s.tmp%s" % (target, uuid.uuid4().hex)
    f = open(tmp_target, mode)
    try:
        writer(f)
    finally:
        f.close()
    os.rename(tmp_target, target)

def pkg_config_dir(prefix):
    """Return the full path of the pkgconfig directory for the given prefix."""
    return op.join(prefix, "lib", "pkgconfig")

def update_pkg_config_prefix(pc_file, prefix):
    """Overwrite the prefix variable for the given .pc pkg-config file with the
    given prefix.

    The .pc file is written in-place
    """
    if not op.isabs(pc_file):
        pc_file = op.join(pkg_config_dir(prefix), pc_file)

    pat = re.compile(r"^prefix=(.*)$", re.M)
    if op.exists(pc_file):
        with open(pc_file) as fp:
            data = fp.read()
            data = pat.sub("prefix={0}".format(prefix), data)
        safe_write(pc_file, data, "wt")
    else:
        # FIXME: should this be an error ?
        logging.warn("%s not found" % pc_file)
