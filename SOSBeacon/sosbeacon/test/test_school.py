import unittest
import mock

from google.appengine.ext import testbed

class TestModelSchool(unittest.TestCase):
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
        from datetime import datetime
        from sosbeacon.school import School

        school_dict = {
            'name': 'ly hoang long',
            }

        school = School.from_dict(school_dict)

        self.assertEqual(school_dict['name'], school.name)

        self.assertFalse(memcache_delete_mock.call_count)

    @unittest.skip('Figure out if this test has any value.')
    def test_to_from_composition(self):
        """Ensure to_dict(from_dict(x)) returns a correctly setup object."""
        from datetime import datetime
        from sosbeacon.school import School

        school_dict = {
            'name': 'ly hoang long',
            }

        school = School.from_dict(school_dict)
        school.put()

        new_school = school.to_dict()

        self.assertEqual(school_dict, new_school)