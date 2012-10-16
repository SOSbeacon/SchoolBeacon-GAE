
import copy
import unittest

from google.appengine.ext import testbed


class TestStudentMarkerMerge(unittest.TestCase):
    """Test that StudentMarker merge logic functions as expected."""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def test_merge_no_name(self):
        """Ensure merging without name."""
        from sosbeacon.event.student_marker import StudentMarker

        left = StudentMarker()
        right = StudentMarker()
        left.merge(right)
        self.assertFalse(left.name)

    def test_merge_no_name_with_name(self):
        """Ensure merging missing name with name."""
        from sosbeacon.event.student_marker import StudentMarker

        left = StudentMarker()
        right = StudentMarker(name="joe", )
        left.merge(right)
        self.assertEqual("joe", left.name)

    def test_merge_name_with_no_name(self):
        """Ensure merging name with missing name."""
        from sosbeacon.event.student_marker import StudentMarker

        left = StudentMarker(name="joe")
        right = StudentMarker()
        left.merge(right)
        self.assertEqual("joe", left.name)

    def test_merge_names(self):
        """Ensure merging with same name."""
        from sosbeacon.event.student_marker import StudentMarker

        left = StudentMarker(name="joe")
        right = StudentMarker(name="joe")
        left.merge(right)
        self.assertEqual("joe", left.name)

    def test_merge_different_names(self):
        """Ensure merging with different name."""
        from sosbeacon.event.student_marker import StudentMarker

        left = StudentMarker(name="billy")
        right = StudentMarker(name="joe")
        left.merge(right)
        self.assertEqual("billy", left.name)

    def test_merge_non_broadcasts(self):
        """Ensure merging two non-broadcast."""
        from sosbeacon.event.student_marker import StudentMarker

        left = StudentMarker(last_broadcast=None)
        right = StudentMarker(last_broadcast=None)
        left.merge(right)
        self.assertFalse(left.last_broadcast)

    def test_merge_non_broadcast_with_broadcaset(self):
        """Ensure merging a broadcast marker with non-broadcast marker."""
        from datetime import datetime

        from sosbeacon.event.student_marker import StudentMarker

        broadcasted = datetime.now()

        left = StudentMarker(last_broadcast=None)
        right = StudentMarker(last_broadcast=broadcasted)
        left.merge(right)
        self.assertEqual(broadcasted, left.last_broadcast)

    def test_merge_broadcast_with_non_broadcast(self):
        """Ensure merging a non-broadcast marker with broadcast marker."""
        from datetime import datetime

        from sosbeacon.event.student_marker import StudentMarker

        broadcasted = datetime.now()

        left = StudentMarker(last_broadcast=broadcasted)
        right = StudentMarker(last_broadcast=None)
        left.merge(right)
        self.assertEqual(broadcasted, left.last_broadcast)

    def test_merge_broadcast(self):
        """Ensure merging broadcast markers."""
        from datetime import datetime

        from sosbeacon.event.student_marker import StudentMarker

        broadcasted = datetime.now()

        left = StudentMarker(last_broadcast=broadcasted)
        right = StudentMarker(last_broadcast=broadcasted)
        left.merge(right)
        self.assertEqual(broadcasted, left.last_broadcast)

    def test_merge_broadcast_with_newer(self):
        """Ensure merging broadcast marker with more recently broadcast."""
        from datetime import datetime, timedelta

        from sosbeacon.event.student_marker import StudentMarker

        broadcasted = datetime.now()
        later_broadcasted = datetime.now() + timedelta(minutes=5)

        left = StudentMarker(last_broadcast=broadcasted)
        right = StudentMarker(last_broadcast=later_broadcasted)
        left.merge(right)
        self.assertEqual(later_broadcasted, left.last_broadcast)

    def test_merge_broadcast_with_older(self):
        """Ensure merging more recently broadcast marker with older marker."""
        from datetime import datetime, timedelta

        from sosbeacon.event.student_marker import StudentMarker

        broadcasted = datetime.now()
        prior_broadcasted = datetime.now() + timedelta(minutes=-5)

        left = StudentMarker(last_broadcast=broadcasted)
        right = StudentMarker(last_broadcast=prior_broadcasted)
        left.merge(right)
        self.assertEqual(broadcasted, left.last_broadcast)

    def test_contacts_with_no_contacts(self):
        """Ensure merging contacts with no contacts."""
        from sosbeacon.event.student_marker import StudentMarker

        contacts = [
            {
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            },
            {
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            },
            {
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }
        ]

        left = StudentMarker(contacts=copy.deepcopy(contacts))
        right = StudentMarker()
        left.merge(right)
        self.assertEqual(contacts, left.contacts)

    def test_merge_no_contacts_with_contacts(self):
        """Ensure merging no contacts with contacts."""
        from datetime import datetime

        from sosbeacon.event.student_marker import StudentMarker

        contacts = [
            {
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com'],
                'acked': True
            },
            {
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com'],
                'acked_at': datetime.now()
            },
            {
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com'],
                'sent': datetime.now()
            }
        ]

        left = StudentMarker()
        right = StudentMarker(contacts=copy.deepcopy(contacts))
        left.merge(right)
        self.assertEqual(contacts, left.contacts)

    @unittest.skip('not there yet')
    def test_merge_overlapping_contacts_incomplete_contacts(self):
        """Ensure merging contacts with overlaps with different contacts."""
        from sosbeacon.event.student_marker import StudentMarker

        contacts_a = [
            {
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            },
            {
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            },
            {
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }
        ]

        contacts_b = [
            {
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            },
            {
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            },
            {
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }
        ]

        left = StudentMarker(contacts=copy.deepcopy(contacts_a))
        right = StudentMarker(contacts=copy.deepcopy(contacts_b))
        left.merge(right)

        for key in contacts_a:
            contacts_a[key].extend(contacts_b[key])
        self.assertEqual(contacts_a, left.contacts)


class TestHashContact(unittest.TestCase):
    """Test that hash_contact functions as expected."""

    def test_no_name_or_methods(self):
        """Ensure hashing with no name or methods works."""
        import hashlib

        from sosbeacon.event.student_marker import _hash_contact

        contact = {}

        hashed = _hash_contact(contact)

        check_hash = hashlib.sha1(unicode(None)).hexdigest()

        self.assertEqual(check_hash, hashed)

    def test_name_with_no_methods(self):
        """Ensure hashing name with no methods works."""
        import hashlib

        from sosbeacon.event.student_marker import _hash_contact

        contact = {'name': 'jimmy'}

        hashed = _hash_contact(contact)

        check_hash = hashlib.sha1(unicode('jimmy')).hexdigest()

        self.assertEqual(check_hash, hashed)

    def test_no_name_with_methods(self):
        """Ensure hashing with no name but with methods works."""
        import hashlib

        from sosbeacon.event.student_marker import _hash_contact

        contact = {'methods': [{'value': 1}, {'value': 2}, {'value': 3}]}

        hashed = _hash_contact(contact)

        check_hash = hashlib.sha1(unicode('1|2|3|None')).hexdigest()

        self.assertEqual(check_hash, hashed)

    def test_name_with_methods(self):
        """Ensure hashing with name and methods works."""
        import hashlib

        from sosbeacon.event.student_marker import _hash_contact

        contact = {'name': 'frank',
                   'methods': [{'value': 1}, {'value': 2}, {'value': 3}]}

        hashed = _hash_contact(contact)

        check_hash = hashlib.sha1(unicode('1|2|3|frank')).hexdigest()

        self.assertEqual(check_hash, hashed)

    def test_email_method(self):
        """Ensure hashing with name and methods works."""
        import hashlib

        from sosbeacon.event.student_marker import _hash_contact

        contact = {'name': 'jim jones',
                   'methods': [{'value': 'jim@jones.com'},
                               {'value': 2},
                               {'value': 3}]}

        hashed = _hash_contact(contact)

        check_hash = hashlib.sha1(
            unicode('2|3|jim jones|jim@jones.com')).hexdigest()

        self.assertEqual(check_hash, hashed)

