import random
import sys
import unittest

from egginst.main import name_version_fn
from enstaller.utils import canonical, comparable_version, path_to_uri, uri_to_path


class TestUtils(unittest.TestCase):

    def test_canonical(self):
        for name, cname in [
            ('NumPy', 'numpy'),
            ('MySql-python', 'mysql_python'),
            ('Python-dateutil', 'python_dateutil'),
            ]:
            self.assertEqual(canonical(name), cname)

    def test_naming(self):
        for fn, name, ver, cname in [
            ('NumPy-1.5-py2.6-win32.egg', 'NumPy', '1.5-py2.6-win32', 'numpy'),
            ('NumPy-1.5-2.egg', 'NumPy', '1.5-2', 'numpy'),
            ('NumPy-1.5.egg', 'NumPy', '1.5', 'numpy'),
            ]:
            self.assertEqual(name_version_fn(fn), (name, ver))
            self.assertEqual(name.lower(), cname)
            self.assertEqual(canonical(name), cname)

    def test_comparable_version(self):
        for versions in (
            ['1.0.4', '1.2.1', '1.3.0b1', '1.3.0', '1.3.10',
             '1.3.11.dev7', '1.3.11.dev12', '1.3.11.dev111',
             '1.3.11', '1.3.143',
             '1.4.0.dev7749', '1.4.0rc1', '1.4.0rc2', '1.4.0'],
            ['2008j', '2008k', '2009b', '2009h', '2010b'],
            ['0.99', '1.0a2', '1.0b1', '1.0rc1', '1.0', '1.0.1'],
            ['2.0.8', '2.0.10', '2.0.10.1', '2.0.11'],
            ['0.10.1', '0.10.2', '0.11.dev1324', '0.11'],
            ):
            org = list(versions)
            random.shuffle(versions)
            versions.sort(key=comparable_version)
            self.assertEqual(versions, org)


class TestUri(unittest.TestCase):
    def test_posix_path_to_uri_simple(self):
        """Ensure path to uri conversion works for posix paths."""
        r_uri = "file:///home/vagrant/yo"

        uri = path_to_uri("/home/vagrant/yo")
        self.assertEqual(r_uri, uri)

    def test_win32_path_to_uri_simple(self):
        """Ensure path to uri conversion works for win32 paths."""
        r_uri = "file:///C:/Users/vagrant/yo"

        uri = path_to_uri("C:\\Users\\vagrant\\yo")
        self.assertEqual(r_uri, uri)

        ## XXX: C:/Users get translated to file:///C://Users. This smells like a
        ## bug in python pathname2url ?
        #uri = path_to_uri("C:/Users/vagrant/yo")
        #self.assertEqual(r_uri, uri)

    def test_uri_to_path_simple(self):
        # XXX: this is a bit ugly, but urllib does not allow to select which OS
        # we want (there is no 'nturllib' or 'posixurllib' as there is for path.
        if sys.platform == "win32":
            r_path = "C:\\Users\\vagrant\\yo"
            uri = "file:///C:/Users/vagrant/yo"
        else:
            r_path = "/home/vagrant/yo"
            uri = "file:///home/vagrant/yo"

        path = uri_to_path(uri)
        self.assertEqual(r_path, path)


if __name__ == '__main__':
    unittest.main()
