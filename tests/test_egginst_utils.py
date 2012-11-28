import os
import tempfile
import unittest

from egginst.utils import safe_write

class TestSafeWrite(unittest.TestCase):
    def setUp(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        self.filename = f.name
        f.close()

    def tearDown(self):
        os.remove(self.filename)

    def test_simple(self):
        """Test whether the file content is correctly written when using string."""
        name = self.filename
        safe_write(name, "foo")

        with open(name) as fp:
            self.assertEqual(fp.read(), "foo")

    def test_simple_callable(self):
        """Test whether the file content is correctly written when using callable."""
        name = self.filename
        safe_write(name, lambda fp: fp.write("foo"))

        with open(name) as fp:
            self.assertEqual(fp.read(), "foo")

    def test_simple_error(self):
        """Test whether the file content is not half written if error happens."""
        name = self.filename
        safe_write(name, "foo")

        def simulate_interrupted(fp):
            fp.write("bar")
            raise KeyboardInterrupt()
            fp.write("foo")

        self.assertRaises(KeyboardInterrupt, safe_write, name, simulate_interrupted)

        with open(name) as fp:
            self.assertEqual(fp.read(), "foo")
