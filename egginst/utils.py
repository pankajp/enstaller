import logging
import sys
import os
import re
import shutil
import tempfile
import uuid

from os.path import basename, isdir, isfile, islink, join


on_win = bool(sys.platform == 'win32')

if on_win:
    bin_dir_name = 'Scripts'
    rel_site_packages = r'Lib\site-packages'
else:
    bin_dir_name = 'bin'
    rel_site_packages = 'lib/python%i.%i/site-packages' % sys.version_info[:2]


def rm_empty_dir(path):
    """
    Remove the directory `path` if it is a directory and empty.
    If the directory does not exist or is not empty, do nothing.
    """
    try:
        os.rmdir(path)
    except OSError: # directory might not exist or not be empty
        pass


def rm_rf(path, verbose=False):
    if not on_win and islink(path):
        # Note that we have to check if the destination is a link because
        # exists('/path/to/dead-link') will return False, although
        # islink('/path/to/dead-link') is True.
        if verbose:
            print "Removing: %r (link)" % path
        os.unlink(path)

    elif isfile(path):
        if verbose:
            print "Removing: %r (file)" % path
        if on_win:
            try:
                os.unlink(path)
            except (WindowsError, IOError):
                os.rename(path, join(tempfile.mkdtemp(), basename(path)))
        else:
            os.unlink(path)

    elif isdir(path):
        if verbose:
            print "Removing: %r (directory)" % path
        if on_win:
            try:
                shutil.rmtree(path)
            except (WindowsError, IOError):
                os.rename(path, join(tempfile.mkdtemp(), basename(path)))
        else:
            shutil.rmtree(path)


def get_executable(prefix):
    if on_win:
        path = join(prefix, 'python.exe')
        if isfile(path):
            return path
    else:
        path = join(prefix, bin_dir_name, 'python')
        if isfile(path):
            from subprocess import Popen, PIPE
            cmd = [path, '-c', 'import sys;print sys.executable']
            p = Popen(cmd, stdout=PIPE)
            return p.communicate()[0].strip()
    return sys.executable


def human_bytes(n):
    """
    Return the number of bytes n in more human readable form.
    """
    if n < 1024:
        return '%i B' % n
    k = (n - 1) / 1024 + 1
    if k < 1024:
        return '%i KB' % k
    return '%.2f MB' % (float(n) / (2**20))

def safe_write(target, writer, mode="wb"):
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
