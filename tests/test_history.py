import unittest
from os.path import dirname, join

from enstaller.history import History


PATH = join(dirname(__file__), 'history')


class TestHistory(unittest.TestCase):

    def setUp(self):
        self.history = History('<dummy prefix>')
        self.history._log_path = PATH

    def test_get_state(self):
        self.assertEqual(self.history.get_state(0),
                         set(['appinst-2.1.0-1.egg',
                              'basemap-1.0.1-1.egg',
                              'biopython-1.57-2.egg']))
        self.assertEqual(self.history.get_state(),
                         set(['basemap-1.0.2-1.egg',
                              'biopython-1.57-2.egg',
                              'numpy-1.7.0-1.egg']))


if __name__ == '__main__':
    unittest.main()
