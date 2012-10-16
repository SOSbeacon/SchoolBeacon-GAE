
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
        from sosbeacon.event.student_marker import build_contact_map

        contacts = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}]
            },
            {
                'name': 'Josh Jones',
                'methods': [{'value': '443241'}, {'value': 'josh@jones.com'}]
            },
            {
                'name': 'Betty Boop',
                'methods': [{'value': '321133'}, {'value': 'betty@earth.com'}]
            }
        ])

        left = StudentMarker(contacts=copy.deepcopy(contacts))
        right = StudentMarker()
        left.merge(right)
        self.assertEqual(contacts, left.contacts)

    def test_merge_no_contacts_with_contacts(self):
        """Ensure merging no contacts with contacts."""
        from sosbeacon.event.student_marker import StudentMarker
        from sosbeacon.event.student_marker import build_contact_map

        contacts = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}],
                'acked': True
            },
            {
                'name': 'Josh Jones',
                'methods': [{'value': '443241'}, {'value': 'josh@jones.com'}],
                'acked_at': 123432
            },
            {
                'name': 'Betty Boop',
                'methods': [{'value': '321133'}, {'value': 'betty@earth.com'}],
                'sent': 23423
            }
        ])

        left = StudentMarker()
        right = StudentMarker(contacts=copy.deepcopy(contacts))
        left.merge(right)
        self.assertEqual(contacts, left.contacts)

    def test_merge_overlapping_contacts(self):
        """Ensure merging overlapping contacts."""
        from sosbeacon.event.student_marker import StudentMarker
        from sosbeacon.event.student_marker import build_contact_map

        contacts = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}]
            },
            {
                'name': 'Josh Jones',
                'methods': [{'value': '443241'}, {'value': 'josh@jones.com'}]
            },
            {
                'name': 'Betty Boop',
                'methods': [{'value': '321133'}, {'value': 'betty@earth.com'}]
            }
        ])

        left = StudentMarker(contacts=copy.deepcopy(contacts))
        right = StudentMarker(contacts=copy.deepcopy(contacts))
        left.merge(right)

        for contact in contacts.values():
            contact['acked'] = None
            contact['acked_at'] = None
            contact['sent'] = None

        self.assertEqual(contacts, left.contacts)

    def test_merge_new_ack_info(self):
        """Ensure merging ack info into contacts works."""
        from sosbeacon.event.student_marker import StudentMarker
        from sosbeacon.event.student_marker import build_contact_map

        contacts = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}]
            },
            {
                'name': 'Josh Jones',
                'methods': [{'value': '443241'}, {'value': 'josh@jones.com'}]
            },
            {
                'name': 'Betty Boop',
                'methods': [{'value': '321133'}, {'value': 'betty@earth.com'}]
            }
        ])

        new_acked_contact = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}],
                'acked': True,
                'acked_at': 1234231,
                'sent': 232311,
            }
        ])

        left = StudentMarker(contacts=copy.deepcopy(contacts))
        right = StudentMarker(contacts=copy.deepcopy(new_acked_contact))
        left.merge(right)

        contacts.update(new_acked_contact)

        self.assertEqual(contacts, left.contacts)
        self.assertEqual(True, left.acknowledged)
        self.assertEqual(1234231, left.acknowledged_at)

    def test_merge_contacts_into_ack_info(self):
        """Ensure merging contact list into ack info works."""
        from sosbeacon.event.student_marker import StudentMarker
        from sosbeacon.event.student_marker import build_contact_map

        contacts = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}]
            },
            {
                'name': 'Josh Jones',
                'methods': [{'value': '443241'}, {'value': 'josh@jones.com'}]
            },
            {
                'name': 'Betty Boop',
                'methods': [{'value': '321133'}, {'value': 'betty@earth.com'}]
            }
        ])

        acked_contact = build_contact_map([
            {
                'name': 'Sam Smith',
                'methods': [{'value': '123432'}, {'value': 'me@earth.com'}],
                'acked': True,
                'acked_at': 1234231,
                'sent': 232311,
            }
        ])

        left = StudentMarker(contacts=copy.deepcopy(acked_contact))
        right = StudentMarker(contacts=copy.deepcopy(contacts))
        left.merge(right)

        contacts.update(acked_contact)

        self.assertEqual(contacts, left.contacts)
        self.assertEqual(True, left.acknowledged)
        self.assertEqual(1234231, left.acknowledged_at)


class TestBuildContactMap(unittest.TestCase):
    """Test that build_contact_map functions as expected."""

    def test_no_contacts(self):
        """Ensure building map of no contacts doesn't blow up."""
        from sosbeacon.event.student_marker import build_contact_map

        contacts = []

        contact_map = build_contact_map(contacts[:])

        self.assertEqual({}, contact_map)

    def test_one_contact(self):
        """Ensure building map of one contact works."""
        import copy

        from sosbeacon.event.student_marker import _hash_contact
        from sosbeacon.event.student_marker import build_contact_map

        contacts = [{'name': 'joe', 'methods': [{'value': 123}]}]

        contact_map = build_contact_map(copy.deepcopy(contacts))

        contact_hash = _hash_contact(contacts[0])

        self.assertEqual({contact_hash: contacts[0]}, contact_map)

    def test_two_contacts(self):
        """Ensure building map of two contacts works."""
        import copy

        from sosbeacon.event.student_marker import _hash_contact
        from sosbeacon.event.student_marker import build_contact_map

        contacts = [{'name': 'joe', 'methods': [{'value': 123}]},
                    {'name': 'jim', 'methods': [{'value': 'asd'}]}]

        contact_map = build_contact_map(copy.deepcopy(contacts))

        good_map = {
            _hash_contact(contacts[0]): contacts[0],
            _hash_contact(contacts[1]): contacts[1],
        }

        self.assertEqual(good_map, contact_map)

    def test_duplicate_contacts(self):
        """Ensure building map from list with duplicate contacts works."""
        import copy

        from sosbeacon.event.student_marker import _hash_contact
        from sosbeacon.event.student_marker import build_contact_map

        contacts = [{'name': 'joe', 'methods': [{'value': 123}]},
                    {'name': 'joe', 'methods': [{'value': 123}]}]

        contact_map = build_contact_map(copy.deepcopy(contacts))

        good_map = {
            _hash_contact(contacts[0]): contacts[0],
        }

        self.assertEqual(good_map, contact_map)


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

