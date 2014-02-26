import sys

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import mock

from enstaller.main import main

from enstaller.tests.common import without_default_configuration, mock_print


class TestAuth(unittest.TestCase):
    @without_default_configuration
    def test_auth_requested_without_config(self):
        """
        Ensure we ask for authentication if no .enstaller4rc is found.
        """
        with mock_print() as m:
            with self.assertRaises(SystemExit):
                main()

        self.assertEqual(m.value, "No authentication configured, required "
                                  "to continue.To login, type 'enpkg --userpass'.\n")

    @without_default_configuration
    def test_userpass_without_config(self):
        """
        Ensure we don't crash when empty information is input in --userpass
        prompt (no .enstaller4rc found).
        """
        with mock.patch("__builtin__.raw_input", return_value="") as m:
            with self.assertRaises(SystemExit):
                main(["--userpass"])

        self.assertEqual(m.call_count, 3)
