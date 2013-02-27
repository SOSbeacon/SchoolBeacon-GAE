import unittest
import mock

from google.appengine.ext import testbed

class TestModelStudent(unittest.TestCase):
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
        from sosbeacon.student import Student

        student_dict = {
            'name': 'ly hoang long',
            'groups': [],
            'is_direct': False,
        }

        student = Student.from_dict(student_dict)

        self.assertEqual(student_dict['name'], student.name)
        self.assertEqual(student_dict['groups'], student.groups)
        self.assertEqual(student_dict['is_direct'], student.is_direct)

        self.assertFalse(memcache_delete_mock.call_count)

    @unittest.skip('Figure out if this test has any value.')
    def test_to_from_composition(self):
        """Ensure to_dict(from_dict(x)) returns a correctly setup object."""
        from datetime import datetime
        from sosbeacon.student import Student

        student_dict = {
            'name': 'ly hoang long',
            'added': datetime(2012, 8, 30, 7, 37),
            'groups': [],
            'is_direct': False,
        }

        student = Student.from_dict(student_dict)
        student.put()

        new_student = student.to_dict()

        self.assertEqual(student_dict, new_student)
