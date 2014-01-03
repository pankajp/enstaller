import os.path
import tempfile
import unittest

import mock

import enstaller.config

from enstaller.config import clear_cache, get, get_default_url, get_path, input_auth, write

FAKE_USER = "john.doe"
FAKE_PASSWORD = "fake_password"

FAKE_CREDS = "{0}:{1}".format(FAKE_USER, FAKE_PASSWORD).encode("base64").rstrip()

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

class TestInputAuth(unittest.TestCase):
    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    def test_simple(self):
        with mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER):
            self.assertEqual(input_auth(), (FAKE_USER, FAKE_PASSWORD))

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    def test_empty(self):
        with mock.patch("__builtin__.raw_input", lambda ignored: ""):
            self.assertEqual(input_auth(), (None, None))

class TestWriteConfig(unittest.TestCase):
    def tearDown(self):
        clear_cache()

    def _mocked_open_factory(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        def mocked_open(ignored, ignored2):
            return f

        return mocked_open, f

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    @mock.patch("enstaller.config.keyring", None)
    @mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER)
    def test_cleared_cache(self):
        mocked_open, f = self._mocked_open_factory()
        with mock.patch("__builtin__.open", mocked_open):
            m = mock.MagicMock()
            with mock.patch("enstaller.config.clear_cache", m):
                write()
            self.assertTrue(m.called)

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    @mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER)
    def test_simple(self):
        mocked_open, f = self._mocked_open_factory()
        with mock.patch("__builtin__.open", mocked_open):
            write()

        with mock.patch("enstaller.config.get_path", lambda: f.name):
            self.assertEqual(get("EPD_auth"), FAKE_CREDS)
            self.assertEqual(get("autoupdate"), True)
            self.assertEqual(get("proxy"), None)
            self.assertEqual(get("use_webservice"), True)
            self.assertEqual(get("webservice_entry_point"), get_default_url())

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    @mock.patch("enstaller.config.keyring", None)
    @mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER)
    def test_simple_with_proxy(self):
        mocked_open, f = self._mocked_open_factory()
        with mock.patch("__builtin__.open", mocked_open):
            write(proxy="http://acme.com:3128")

        with mock.patch("enstaller.config.get_path", lambda: f.name):
            self.assertEqual(get("proxy"), "http://acme.com:3128")

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    @mock.patch("enstaller.config.keyring", None)
    @mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER)
    def test_simple_with_username_password(self):
        user, password = "dummy", "dummy"
        creds = "{0}:{1}".format(user, password).encode("base64").rstrip()

        mocked_open, f = self._mocked_open_factory()
        with mock.patch("__builtin__.open", mocked_open):
            write(username=user, password=password)

        with mock.patch("enstaller.config.get_path", lambda: f.name):
            self.assertEqual(get("EPD_auth"), creds)

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    @mock.patch("enstaller.config.keyring", None)
    @mock.patch("enstaller.config.sys.platform", "linux2")
    @mock.patch("enstaller.config.os.getuid", lambda: 0)
    @mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER)
    def test_use_system_path_under_root(self):
        with mock.patch("__builtin__.open") as m:
            write()
            self.assertEqual(m.call_args[0][0], enstaller.config.system_config_path)

    @mock.patch("enstaller.config.getpass", lambda ignored: FAKE_PASSWORD)
    @mock.patch("__builtin__.raw_input", lambda ignored: FAKE_USER)
    def test_keyring_call(self):
        with mock.patch("__builtin__.open"):
            mocked_keyring = mock.MagicMock()
            mocked_keyring.set_password = mock.MagicMock()
            with mock.patch("enstaller.config.keyring", mocked_keyring):
                write()
                self.assertEqual(mocked_keyring.set_password.call_args[0],
                                 ("Enthought.com", FAKE_USER, FAKE_PASSWORD))
