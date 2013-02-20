import unittest
import mock

from google.appengine.ext import testbed

class TestModelUser(unittest.TestCase):
    """Test that Student to/from dict methods work as expected."""
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    @mock.patch('google.appengine.api.memcache.delete')
    def test_from_dict(self, memcache_delete_mock):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.user import User

        user_dict = {
            'name': 'ly hoang long',
            'password': 'abc123',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'schools': []
        }

        user = User.from_dict(user_dict)

        self.assertEqual(user_dict['name'], user.name)

        self.assertFalse(memcache_delete_mock.call_count)

    @unittest.skip('Figure out if this test has any value.')
    def test_to_from_composition(self):
        """Ensure to_dict(from_dict(x)) returns a correctly setup object."""
        from sosbeacon.user import User

        user_dict = {
            'name': 'ly hoang long',
            'password': 'abc123',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'schools': []
        }


        user = User.from_dict(user_dict)
        user.put()

        new_user = user.to_dict()

        self.assertEqual(user_dict, new_user)