import os
import tempfile
import unittest

from egginst.post_install import update_pkg_config_prefix

class TestSafeWrite(unittest.TestCase):
    def setUp(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        self.filename = f.name
        f.close()

    def tearDown(self):
        os.remove(self.filename)

    def test_simple(self):
        """Test whether the file content is correctly written when using string."""
        data = """\
prefix=/home/vagrant/pisi/tmp/Qt-4.8.2-2/usr
exec_prefix=${prefix}
libdir=${prefix}/lib
"""

        r_data = """\
prefix=/foo/bar
exec_prefix=${prefix}
libdir=${prefix}/lib
"""
        with tempfile.NamedTemporaryFile(suffix=".pc", delete=False) as fp:
            pc_file = fp.name
            fp.write(data)
            fp.close()

            update_pkg_config_prefix(pc_file, "/foo/bar")

            with open(pc_file) as r_fp:
                self.assertEqual(r_fp.read(), r_data)
