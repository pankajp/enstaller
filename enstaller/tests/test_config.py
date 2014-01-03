import os.path
import unittest

import mock

import enstaller.config

from enstaller.config import get_path

class TestGetPath(unittest.TestCase):
    def test_home_config_exists(self):
        def mocked_isfile(p):
            if p == enstaller.config.home_config_path:
                return True
            else:
                return os.path.isfile(p)

        with mock.patch("enstaller.config.isfile", mocked_isfile):
            self.assertEqual(get_path(), enstaller.config.home_config_path)

    def test_home_config_doesnt_exist(self):
        def mocked_isfile(p):
            if p == enstaller.config.home_config_path:
                return False
            elif p == enstaller.config.system_config_path:
                return True
            else:
                return os.path.isfile(p)

        with mock.patch("enstaller.config.isfile", mocked_isfile):
            self.assertEqual(get_path(), enstaller.config.system_config_path)

    def test_no_config(self):
        def mocked_isfile(p):
            if p in (enstaller.config.home_config_path,
                     enstaller.config.system_config_path):
                return False
            else:
                return os.path.isfile(p)

        with mock.patch("enstaller.config.isfile", mocked_isfile):
            self.assertEqual(get_path(), None)
