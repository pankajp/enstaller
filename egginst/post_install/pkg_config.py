import logging
import re

import os.path as op

from egginst.utils import safe_write

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
