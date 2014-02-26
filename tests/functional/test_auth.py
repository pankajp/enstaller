import sys
import tempfile

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import mock

from enstaller.main import main

from enstaller.tests.common import (
    without_default_configuration, mock_print, make_default_configuration_path,
    fail_authenticate, mock_input_auth)


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

    @fail_authenticate
    def test_userpass_with_config(self):
        """
        Ensure enpkg --userpass doesn't crash when creds are invalid
        """
        r_output = "Could not authenticate, please try again (did you enter " \
                   "the right credentials ?).\nNo modification was written\n"

        with tempfile.NamedTemporaryFile(delete=False) as fp:
            filename = fp.name

        with mock_print() as m:
            with make_default_configuration_path(filename):
                with mock_input_auth("nono", "robot"):
                    with self.assertRaises(SystemExit):
                        main(["--userpass"])

        self.assertMultiLineEqual(m.value, r_output)
