import unittest
import enstaller.config as config
from functools import partial


users = {('jdoe', 'password1'): dict(first_name="Jane", last_name="Doe",
            is_authenticated=True, has_subscription=True),  # EPD Basic and up
         ('jsmith', 'password2'): dict(first_name="John", last_name="Smith",
             is_authenticated=True, has_subscription=False),  # EPD Free
         }

badusers = (('fakeuser1', 'fakepassword1'), ('fakeuser2', 'fakepassword2'))


def mock_authenticate(auth, remote, use_webservice):
    try:
        if use_webservice:
            return users[auth]
        else:
            users[auth]
            return {}
    except Exception():
        raise config.AuthFailedError()


class CheckedChangeAuthTestCaseBase(object):

    def mock_change_auth(self, username, password):
        self.changed_auth = True

    def commonSetUp(self):
        """Replace authenticate and change_auth with mocks."""
        self.old_authenticate = config.authenticate
        self.old_change_auth = config.change_auth
        config.change_auth = self.mock_change_auth
        self.changed_auth = False

    def commonTearDown(self):
        """Restore authenticate and change_auth."""
        config.authenticate = self.old_authenticate
        config.change_auth = self.old_change_auth
        self.changed_auth = False


class CheckedChangeAuthWebserviceTestCase(unittest.TestCase, CheckedChangeAuthTestCaseBase):

    def setUp(self):
        self.commonSetUp()
        config.authenticate = partial(mock_authenticate, use_webservice=True)

    def test_basic_acct_good(self):
        username, password = ('jdoe', 'password1')
        usr = config.checked_change_auth(username, password)
        self.assertTrue(self.changed_auth)
        self.assertTrue(usr.get('is_authenticated'))
        self.assertTrue(usr.get('has_subscription'))

    def test_basic_acct_bad(self):
        username, password = ('jdoe', 'wrong')
        usr = config.checked_change_auth(username, password)
        self.assertFalse(self.changed_auth)
        self.assertEqual(usr, {})

    def test_free_acct_good(self):
        username, password = ('jsmith', 'password2')
        usr = config.checked_change_auth(username, password)
        self.assertTrue(self.changed_auth)
        self.assertTrue(usr.get('is_authenticated'))
        self.assertFalse(usr.get('has_subscription'))

    def test_free_acct_bad(self):
        username, password = ('jsmith', 'wrong')
        usr = config.checked_change_auth(username, password)
        self.assertFalse(self.changed_auth)
        self.assertEqual(usr, {})

    def test_no_acct(self):
        username, password = ('fakeuser', 'wrong')
        usr = config.checked_change_auth(username, password)
        self.assertFalse(self.changed_auth)
        self.assertEqual(usr, {})

    def test_empty_strings(self):
        username, password = ('', '')
        usr = config.checked_change_auth(username, password)
        self.assertTrue(self.changed_auth)
        self.assertEqual(usr, {})

    def test_nones(self):
        username, password = (None, None)
        usr = config.checked_change_auth(username, password)
        self.assertTrue(self.changed_auth)
        self.assertEqual(usr, {})

    def test_bad_users(self):
        for auth in badusers:
            usr = config.checked_change_auth(*auth)
            self.assertFalse(self.changed_auth)
            self.assertEqual(usr, {})

    def tearDown(self):
        self.commonTearDown()


class CheckedChangeAuthNoWebserviceTestCase(unittest.TestCase, CheckedChangeAuthTestCaseBase):

    def setUp(self):
        """Replace authenticate and change_auth with mocks."""
        self.commonSetUp()
        config.authenticate = partial(mock_authenticate, use_webservice=False)

    def test_good_users(self):
        for auth in users.keys() + [('', ''), (None, None)]:
            usr = config.checked_change_auth(*auth)
            self.assertTrue(self.changed_auth)
            self.assertEqual(usr, {})

    def test_bad_users(self):
        for auth in badusers:
            usr = config.checked_change_auth(*auth)
            self.assertFalse(self.changed_auth)
            self.assertEqual(usr, {})

    def tearDown(self):
        self.commonTearDown()


class SearchTestCase(unittest.TestCase):
    pass


class InstallTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
