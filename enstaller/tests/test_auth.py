import unittest
from mock import patch

import enstaller.config as config


basic_user = dict(first_name="Jane", last_name="Doe", is_authenticated=True,
        has_subscription=True)
free_user = dict(first_name="John", last_name="Smith", is_authenticated=True,
        has_subscription=False)
anon_user = dict(is_authenticated=False)
old_auth_user = {}


@patch('enstaller.config.change_auth')
class CheckedChangeAuthTestCase(unittest.TestCase):

    @patch('enstaller.config.authenticate', return_value=basic_user)
    def test_basic_user(self, mock1, mock2):
        usr = config.checked_change_auth('usr', 'password')
        self.assertTrue(config.change_auth.called)
        self.assertTrue(usr.get('is_authenticated'))
        self.assertTrue(usr.get('has_subscription'))

    @patch('enstaller.config.authenticate', return_value=free_user)
    def test_free_user(self, mock1, mock2):
        usr = config.checked_change_auth('usr', 'password')
        self.assertTrue(config.change_auth.called)
        self.assertTrue(usr.get('is_authenticated'))
        self.assertFalse(usr.get('has_subscription'))

    @patch('enstaller.config.authenticate',
            side_effect=config.AuthFailedError())
    def test_no_acct(self, mock1, mock2):
        usr = config.checked_change_auth('usr', 'password')
        self.assertFalse(config.change_auth.called)
        self.assertFalse(usr.get('is_authenticated', False))
        self.assertEqual(usr, {})

    @patch('enstaller.config.authenticate', return_value=old_auth_user)
    def test_remote_success(self, mock1, mock2):
        usr = config.checked_change_auth('usr', 'password')
        self.assertTrue(config.change_auth.called)
        self.assertFalse(usr.get('is_authenticated', False))
        self.assertEqual(usr, {})

    @patch('enstaller.config.authenticate',
            side_effect=config.AuthFailedError())
    def test_nones(self, mock1, mock2):
        usr = config.checked_change_auth(None, None)
        self.assertTrue(config.change_auth.called)
        self.assertFalse(usr.get('is_authenticated', False))
        self.assertEqual(usr, {})

    @patch('enstaller.config.authenticate',
            side_effect=config.AuthFailedError())
    def test_empty_strings(self, mock1, mock2):
        usr = config.checked_change_auth('', '')
        self.assertTrue(config.change_auth.called)
        self.assertFalse(usr.get('is_authenticated', False))
        self.assertEqual(usr, {})



class SearchTestCase(unittest.TestCase):
    pass


class InstallTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
