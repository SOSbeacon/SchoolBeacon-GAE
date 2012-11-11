
import copy
import unittest

import mock

from google.appengine.ext import testbed


class TestContactMarkerMerge(unittest.TestCase):
    """Test that ContactMarker merge logic functions as expected."""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def test_merge_non_ack(self):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=False)
        right = ContactMarker(acknowledged=False)
        left.merge(right)
        self.assertFalse(left.acknowledged)

    def test_merge_ack_to_non_ack(self):
        """Ensure merging acked to non-acked acks."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=False)
        right = ContactMarker(acknowledged=True)
        left.merge(right)
        self.assertTrue(left.acknowledged)

    def test_merge_non_ack_to_ack(self):
        """Ensure merging non-acked to acked stays acked."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=True)
        right = ContactMarker(acknowledged=False)
        left.merge(right)
        self.assertTrue(left.acknowledged)

    def test_merge_acks(self):
        """Ensure merging two acked stays acked."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(acknowledged=True)
        right = ContactMarker(acknowledged=True)
        left.merge(right)
        self.assertTrue(left.acknowledged)

    def test_merge_unviewed(self):
        """Ensure merging two non-acked doesn't set view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(0, left.last_viewed_date)

    def test_merge_last_viewed_date(self):
        """Ensure merging acked to non-acked sets view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=0)
        right = ContactMarker(last_viewed_date=12345)
        left.merge(right)
        self.assertEqual(12345, left.last_viewed_date)

    def test_merge_last_viewed_date_with_non_acked(self):
        """Ensure merging non-acked with acked preserves view date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=321123)
        right = ContactMarker(last_viewed_date=0)
        left.merge(right)
        self.assertEqual(321123, left.last_viewed_date)

    def test_merge_last_viewed_date_with_smaller(self):
        """Ensure merging earlier acked with later acked keeps most recent
        ack date.
        """
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=100)
        right = ContactMarker(last_viewed_date=10)
        left.merge(right)
        self.assertEqual(100, left.last_viewed_date)

    def test_merge_last_viewed_date_with_larger(self):
        """Ensure merging more recently acked with earlier acked keeps most
        recent ack date.
        """
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=20)
        right = ContactMarker(last_viewed_date=200)
        left.merge(right)
        self.assertEqual(200, left.last_viewed_date)

    def test_merge_last_viewed_date_with_same(self):
        """Ensure merging acked with acked preserves ack date."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(last_viewed_date=334)
        right = ContactMarker(last_viewed_date=334)
        left.merge(right)
        self.assertEqual(334, left.last_viewed_date)

    def test_merge_no_short_ids(self):
        """Ensure merging with no short ids."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(None, left.short_id)

    def test_merge_new_short_id(self):
        """Ensure merging with no short id with new short id."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker(short_id='N123')
        left.merge(right)
        self.assertEqual('N123', left.short_id)

    def test_merge_missing_short_id(self):
        """Ensure merging short id with no short id."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(short_id='N213')
        right = ContactMarker()
        left.merge(right)
        self.assertEqual('N213', left.short_id)

    def test_merge_different_short_id(self):
        """Ensure merging with different short ids."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(short_id='N123')
        right = ContactMarker(short_id='Z312')
        left.merge(right)
        self.assertEqual('N123', left.short_id)

    def test_merge_no_names(self):
        """Ensure merging with no names."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(None, left.name)

    def test_merge_new_name(self):
        """Ensure merging no name with new name."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker(name='Name 1')
        left.merge(right)
        self.assertEqual('Name 1', left.name)

    def test_merge_missing_name(self):
        """Ensure merging missing name with name."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(name='Name 2')
        right = ContactMarker()
        left.merge(right)
        self.assertEqual('Name 2', left.name)

    def test_merge_different_name(self):
        """Ensure merging with two different names."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker(name='Name 3')
        right = ContactMarker(name='Name 4')
        left.merge(right)
        self.assertEqual('Name 3', left.name)

    def test_merge_no_students(self):
        """Ensure merging with no students."""
        from sosbeacon.event.contact_marker import ContactMarker

        left = ContactMarker()
        right = ContactMarker()
        left.merge(right)
        self.assertIsNone(left.students)

    def test_merge_students_with_no_students(self):
        """Ensure merging students with no students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students = {
            '123': [{
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            }],
            '345': [{
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            }],
            '231': [{
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }],
        }

        left = ContactMarker(students=copy.deepcopy(students))
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(students, left.students)

    def test_merge_no_students_with_students(self):
        """Ensure merging no students with students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students = {
            '123': [{
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            }],
            '345': [{
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            }],
            '231': [{
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }],
        }

        left = ContactMarker()
        right = ContactMarker(students=copy.deepcopy(students))
        left.merge(right)
        self.assertEqual(students, left.students)

    def test_merge_students(self):
        """Ensure merging students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students_1 = {
            '123': [{
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            }],
            '345': [{
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            }],
            '231': [{
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }],
        }

        students_2 = {
            'ABC': [{
                'name': 'Julie James',
                'methods': ['5433423', 'julie@some.com']
            }],
        }

        left = ContactMarker(students=copy.deepcopy(students_1))
        right = ContactMarker(students=copy.deepcopy(students_2))
        left.merge(right)

        students_1.update(students_2)

        self.assertEqual(students_1, left.students)

    def test_merge_overlapping_students(self):
        """Ensure merging students with overlaps."""
        from sosbeacon.event.contact_marker import ContactMarker

        base_students = {
            '123': [{
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            }],
            '345': [{
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            }]
        }

        students_1 = {
            '231': [{
                'name': 'Betty Boop',
                'methods': ['321133', 'betty@earth.com']
            }],
        }
        students_1.update(base_students)

        students_2 = {
            'ABC': [{
                'name': 'Julie James',
                'methods': ['5433423', 'julie@some.com']
            }],
        }
        students_2.update(base_students)

        left = ContactMarker(students=copy.deepcopy(students_1))
        right = ContactMarker(students=copy.deepcopy(students_2))
        left.merge(right)

        students_1.update(students_2)
        self.assertEqual(students_1, left.students)

    def test_merge_overlapping_students_incomplete_contacts(self):
        """Ensure merging students with overlaps with different contacts."""
        from sosbeacon.event.contact_marker import ContactMarker

        students_1 = {
            '123': [{
                'name': 'Billy Bob',
                'methods': ['324321', 'billy@bob.com']
            }],
            '345': [{
                'name': 'Josh Jones',
                'methods': ['443241', 'josh@jones.com']
            }]
        }

        students_2 = {
            '123': [{
                'name': 'Sam Smith',
                'methods': ['123432', 'me@earth.com']
            }],
            '345': [{
                'name': 'Jenny Benny',
                'methods': ['234232', 'jenny@jones.com']
            }]
        }

        left = ContactMarker(students=copy.deepcopy(students_1))
        right = ContactMarker(students=copy.deepcopy(students_2))
        left.merge(right)

        for key in students_1:
            students_1[key].extend(students_2[key])
        self.assertEqual(students_1, left.students)

    def test_merge_methods_with_no_methods(self):
        """Ensure merging methods with no methods preserves methods."""
        from sosbeacon.event.contact_marker import ContactMarker

        methods = ['123312', 'samsmith@me.com']

        left = ContactMarker(methods=methods[:])
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(sorted(methods), sorted(left.methods))

    def test_merge_no_methods_with_methods(self):
        """Ensure merging no methods with methods preserves methods."""
        from sosbeacon.event.contact_marker import ContactMarker

        methods = ['123312', 'samsmith@me.com']

        left = ContactMarker()
        right = ContactMarker(methods=methods[:])
        left.merge(right)
        self.assertEqual(sorted(methods), sorted(left.methods))

    def test_merge_same_methods(self):
        """Ensure merging same methods doesn't dupe."""
        from sosbeacon.event.contact_marker import ContactMarker

        methods = [
            '1234567890', 'johnjones@earth.com',
            '2098765432', 'billybob@somewhere.com'
        ]

        left = ContactMarker(methods=methods[:])
        right = ContactMarker(methods=methods[:])
        left.merge(right)
        self.assertEqual(sorted(set(methods[:])), sorted(left.methods))

    def test_merge_methods_with_overlapping_methods(self):
        """Ensure merging new methods with overlapping methods doesn't dupe."""
        from sosbeacon.event.contact_marker import ContactMarker

        base_methods = [
            '1234567890', 'johnjones@earth.com',
            '2098765432', 'billybob@somewhere.com'
        ]

        methods_1 = base_methods + ['123312', 'samsmith@me.com']
        methods_2 = base_methods + ['848423', 'frank.frankton@me.com']

        left = ContactMarker(methods=methods_1[:])
        right = ContactMarker(methods=methods_2[:])
        left.merge(right)
        self.assertEqual(sorted(set(methods_1 + methods_2)),
                         sorted(left.methods))


class TestGetMarkerForMethods(unittest.TestCase):
    """Test get_marker_for_methods correctly gets existing ContactMarkers."""

    def test_no_search_methods(self):
        """Ensure error is raised if there are no methods."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import get_marker_for_methods
        from sosbeacon.event.event import Event

        event_key = ndb.Key(Event, 'EVENTKEY')

        self.assertRaisesRegexp(
            ValueError, "value for methods is required.",
            get_marker_for_methods, event_key, [])

    def test_no_event_key(self):
        """Ensure error is raised if no event_key is given."""
        from sosbeacon.event.contact_marker import get_marker_for_methods

        self.assertRaisesRegexp(
            ValueError, "event_key is required.",
            get_marker_for_methods, None, [])

    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_no_matches(self, find_markers_for_methods_mock):
        """Ensure a new short id is returned if there are non existing."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import get_marker_for_methods
        from sosbeacon.event.event import Event

        find_markers_for_methods_mock.return_value = ()

        event_key = ndb.Key(Event, 'EVENTKEY')

        ret_value = get_marker_for_methods(event_key, ['123'])

        self.assertIsNone(ret_value)

    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_matching_marker(self, find_markers_for_methods_mock):
        """Ensure a single existing placeholder is returned."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import get_marker_for_methods
        from sosbeacon.event.event import Event

        marker1_key = mock.Mock(spec=ndb.Key)
        marker1_key.kind.return_value = "ContactMarker"
        marker1 = ContactMarker(key=marker1_key, short_id='A')

        find_markers_for_methods_mock.return_value = (marker1,)

        event_key = ndb.Key(Event, 'EVENTKEY')

        ret_value = get_marker_for_methods(event_key, ['123'])

        self.assertIs(marker1, ret_value)

    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_matching_markers(self, find_markers_for_methods_mock):
        """Ensure a marker is returned when there are multiple existing
        markers.
        """
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import get_marker_for_methods
        from sosbeacon.event.event import Event

        marker1_key = mock.Mock(spec=ndb.Key)
        marker1_key.kind.return_value = "ContactMarker"
        marker1 = ContactMarker(key=marker1_key, short_id='A')

        marker2_key = mock.Mock(spec=ndb.Key)
        marker2_key.kind.return_value = "ContactMarker"
        marker2 = ContactMarker(key=marker2_key, short_id='Z')

        find_markers_for_methods_mock.return_value = (marker1, marker2)

        event_key = ndb.Key(Event, 'EVENTKEY')

        ret_value = get_marker_for_methods(event_key, ['123'])

        self.assertIn(ret_value, (marker1, marker2))

    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_one_place_holder(self, find_markers_for_methods_mock):
        """Ensure one place holder is returned."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import get_marker_for_methods
        from sosbeacon.event.event import Event

        marker1_key = mock.Mock(spec=ndb.Key)
        marker1_key.kind.return_value = "ContactMarker"
        marker1 = ContactMarker(key=marker1_key, short_id='A')
        marker1_key.get.return_value = marker1

        find_markers_for_methods_mock.return_value = (
            ContactMarker(place_holder=marker1_key),
            ContactMarker(place_holder=marker1_key),
            ContactMarker(place_holder=marker1_key),
        )

        event_key = ndb.Key(Event, 'EVENTKEY')

        ret_value = get_marker_for_methods(event_key, ['123'])

        self.assertIs(marker1, ret_value)

    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_sort_place_holders(self, find_markers_for_methods_mock):
        """Ensure multiple place holders are sorted correctly."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import get_marker_for_methods
        from sosbeacon.event.event import Event

        marker1_key = mock.Mock(spec=ndb.Key)
        marker1_key.kind.return_value = "ContactMarker"
        marker1 = ContactMarker(key=marker1_key, short_id='A')
        marker1_key.get.return_value = marker1

        marker2_key = mock.Mock(spec=ndb.Key)
        marker2_key.kind.return_value = "ContactMarker"
        marker2 = ContactMarker(key=marker2_key, short_id='Z')
        marker2_key.get.return_value = marker2

        find_markers_for_methods_mock.return_value = (
            ContactMarker(place_holder=marker1_key),
            ContactMarker(place_holder=marker2_key),
            ContactMarker(place_holder=marker1_key),
            ContactMarker(place_holder=marker2_key),
            ContactMarker(place_holder=marker1_key),
        )

        event_key = ndb.Key(Event, 'EVENTKEY')

        ret_value = get_marker_for_methods(event_key, ['123'])

        self.assertIs(marker1, ret_value)


class TestCreateOrUpdateMarker(unittest.TestCase):
    """Test create_or_update_marker creates or updates a ContactMarker."""

    def test_no_search_methods(self):
        """Ensure error is raised if there are no methods."""
        from sosbeacon.event.contact_marker import create_or_update_marker

        self.assertRaisesRegexp(
            ValueError, "value for search_methods is required.",
            create_or_update_marker, object(), object(), {'a': True}, [])

    def test_no_contact(self):
        """Ensure error is raised if no contact is provided."""
        from sosbeacon.event.contact_marker import create_or_update_marker

        self.assertRaisesRegexp(
            ValueError, "Contact is required.",
            create_or_update_marker, object(), object(), {}, ['a'])

    def test_no_student_key(self):
        """Ensure error is raised if no student is provided."""
        from sosbeacon.event.contact_marker import create_or_update_marker

        self.assertRaisesRegexp(
            ValueError, "student_key is required.",
            create_or_update_marker, object(), None, {'a': True}, ['a'])

    def test_no_event_key(self):
        """Ensure error is raised if no event is provided."""
        from sosbeacon.event.contact_marker import create_or_update_marker

        self.assertRaisesRegexp(
            ValueError, "event_key is required.",
            create_or_update_marker, None, object(), {'a': True}, ['a'])

    @mock.patch('sosbeacon.event.contact_marker.insert_update_marker_task',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_no_matches(self, find_markers_for_methods_mock,
                        insert_update_marker_task_mock):
        """Ensure a new short id is returned if there are non existing."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import create_or_update_marker
        from sosbeacon.event.event import Event

        find_markers_for_methods_mock.return_value = ()

        event_key = ndb.Key(Event, 'EVENTKEY')

        student_key = mock.Mock()
        student_key.id.return_value = "STUDENTKEY"

        ret_value = create_or_update_marker(
            event_key, student_key, {'a': True}, ['123'])

        self.assertIsNotNone(ret_value)

        self.assertFalse(insert_update_marker_task_mock.called)

    @mock.patch('sosbeacon.event.contact_marker.insert_update_marker_task',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_sort_place_holders(self, find_markers_for_methods_mock,
                                insert_update_marker_task_mock):
        """Ensure an exsting short_id is returned, and contact merged, if
        there is a matching marker.
        """
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import create_or_update_marker
        from sosbeacon.event.event import Event
        from sosbeacon.student import Student

        marker1_key = mock.Mock(spec=ndb.Key)
        marker1_key.kind.return_value = "ContactMarker"
        marker1_key.urlsafe.return_value = "CONTACTMARKER"

        marker1 = ContactMarker(key=marker1_key, short_id='A')
        marker1_key.get.return_value = marker1

        find_markers_for_methods_mock.return_value = (marker1,)

        event_key = ndb.Key(Event, 'EVENTKEY')

        student_key = ndb.Key(Student, 'STUDENTKEY')

        ret_value = create_or_update_marker(
            event_key, student_key, {'a': True}, ['123'])

        self.assertEqual('A', ret_value)

        self.assertEqual(1, insert_update_marker_task_mock.call_count)


class TestInsertUpdateMarkerTask(unittest.TestCase):
    """Ensure the insert_update_marker_task creates and inserts a task to
    update a contact marker.
    """

    @mock.patch('google.appengine.api.taskqueue.Task', autospec=True)
    @mock.patch('google.appengine.api.taskqueue.Queue.add', autospec=True)
    def test_task_params(self, queue_add_mock, task_mock):
        """Ensure the update marker task name contains enough to be unique."""
        import json

        from sosbeacon.event.contact_marker import insert_update_marker_task

        marker_key = mock.Mock()
        marker_key.urlsafe.return_value = "MARKERKEY"

        student_key = mock.Mock()
        student_key.urlsafe.return_value = "STUDENTKEY"

        contact = {'name': 'joe'}
        search_methods = ['a', 123]

        insert_update_marker_task(
            marker_key, student_key, contact.copy(), search_methods[:])

        check_params = {
            'marker': 'MARKERKEY',
            'student': 'STUDENTKEY',
            'contact': json.dumps(contact.copy()),
            'methods': json.dumps(search_methods[:])
        }

        self.assertEqual(check_params, task_mock.call_args[1]['params'])

        self.assertTrue(queue_add_mock.called)


class TestUpdateMarker(unittest.TestCase):
    """Ensure update_marker correctly merges the new student and contact
    information, then inserts a marker merge task.
    """

    @mock.patch('sosbeacon.event.contact_marker.ContactMarker.put',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.insert_merge_task',
                autospec=True)
    def test_methods_get_merged(self, insert_merge_task_mock, marker_put_mock):
        """Test that existing methods don't get duplicated and new methods get
        added.
        """
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import update_marker

        methods = ['abc']

        marker_key = mock.Mock(spec=ndb.Key)
        marker_key.kind.return_value = "ContactMarker"

        marker = ContactMarker(key=marker_key, students={}, methods=methods[:])
        marker_key.get.return_value = marker

        student_key = mock.Mock(spec=ndb.Key)
        student_key.id.return_value = "STUDENTKEY"

        contact = {'id': 1}

        new_methods = ['abc', '123', '456']

        update_marker(marker_key, student_key, contact, new_methods[:])

        all_methods = sorted(set(new_methods) | set(methods))

        self.assertEqual(all_methods, sorted(marker.methods))

        self.assertTrue(marker_put_mock.called)

        self.assertEqual(1, insert_merge_task_mock.call_count)

    @mock.patch('sosbeacon.event.contact_marker.ContactMarker.put',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.insert_merge_task',
                autospec=True)
    def test_student_gets_added(self, insert_merge_task_mock, marker_put_mock):
        """Test a new student is added to the marker."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import update_marker

        methods = ['abc']

        marker_key = mock.Mock(spec=ndb.Key)
        marker_key.kind.return_value = "ContactMarker"

        marker = ContactMarker(key=marker_key, students={}, methods=methods[:])
        marker_key.get.return_value = marker

        student_key = mock.Mock(spec=ndb.Key)
        student_key.id.return_value = "STUDENTKEY"

        contact = {'name': 'jimmy'}

        update_marker(marker_key, student_key, contact.copy(), methods)

        self.assertIn(student_key.id(), marker.students)

        self.assertEqual([contact.copy()], marker.students[student_key.id()])

        self.assertTrue(marker_put_mock.called)

        self.assertEqual(1, insert_merge_task_mock.call_count)

    @mock.patch('sosbeacon.event.contact_marker.ContactMarker.put',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.insert_merge_task',
                autospec=True)
    def test_contact_gets_added_to_student(self, insert_merge_task_mock,
                                           marker_put_mock):
        """Test that new contact is added to the existing student."""
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import update_marker

        methods = ['abc']

        student_key = mock.Mock(spec=ndb.Key)
        student_key.id.return_value = "STUDENTKEY"

        student_contacts = {
            'name': 'Joe Blow'
        }

        marker_key = mock.Mock(spec=ndb.Key)
        marker_key.kind.return_value = "ContactMarker"

        marker = ContactMarker(
            key=marker_key,
            students={
                student_key.id(): [student_contacts.copy()]
            },
            methods=methods[:])
        marker_key.get.return_value = marker

        contact = {'name': 'Some Dude'}

        update_marker(marker_key, student_key, contact.copy(), methods)

        self.assertIn(student_key.id(), marker.students)

        self.assertIn(contact.copy(), marker.students[student_key.id()])

        self.assertTrue(marker_put_mock.called)

        self.assertEqual(1, insert_merge_task_mock.call_count)


class TestInsertMergeTask(unittest.TestCase):
    """Ensure the insert_update_marker_task creates and inserts a task to
    update a contact marker.
    """

    @mock.patch('google.appengine.api.taskqueue.Task', autospec=True)
    @mock.patch('google.appengine.api.taskqueue.Queue.add', autospec=True)
    def test_task_params(self, queue_add_mock, task_mock):
        """Ensure the marker merge task name contains enough to be unique."""
        import json

        from sosbeacon.event.contact_marker import insert_merge_task

        event_key = mock.Mock()
        event_key.urlsafe.return_value = "EVENTKEY"

        search_methods = ['a', 123]

        insert_merge_task(event_key, search_methods[:])

        check_params = {
            'event': 'EVENTKEY',
            'methods': json.dumps(search_methods[:])
        }

        self.assertEqual(check_params, task_mock.call_args[1]['params'])

        self.assertTrue(queue_add_mock.called)


class TestMergeMarkers(unittest.TestCase):
    """Ensure merge_markers correctly combines markers and fires ack signals
    when one of the markers has been aacked.
    """

    def setUp(self):
        from google.appengine.datastore.datastore_stub_util import \
            TimeBasedHRConsistencyPolicy

        from sosbeacon.event.contact_marker import ContactMarker

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub(
            consistency_policy=TimeBasedHRConsistencyPolicy())
        self.testbed.init_memcache_stub()

        self.marker1 = ContactMarker(
            id='a',
            students={'a': 'student_a'},
            methods=['method_a']
        )
        self.marker2 = ContactMarker(
            id='b',
            students={'b': 'student_b'},
            methods=['method_b'],
        )
        self.marker3 = ContactMarker(
            id='c',
            students={'c': 'student_c'},
            methods=['method_c'],
        )
        self.marker4 = ContactMarker(
            id='d',
            students={'d': 'student_d'},
            methods=['method_d'],
        )

    @mock.patch('google.appengine.ext.ndb.put_multi', autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.update_marker_pair',
                autospec=True)
    def test_all_new(self, update_marker_pair_mock,
                     find_markers_for_methods_mock, put_multi_mock):
        """Ensure all of the new markers are merged."""
        from sosbeacon.event.contact_marker import merge_markers

        all_students = self.marker1.students.keys()
        all_students.extend(self.marker2.students.keys())
        all_students.extend(self.marker3.students.keys())

        all_methods = self.marker1.methods[:]
        all_methods.extend(self.marker2.methods[:])
        all_methods.extend(self.marker3.methods[:])

        find_markers_for_methods_mock.return_value = (
            self.marker1, self.marker2, self.marker3)

        merge_markers(object(), object())

        self.assertEqual(sorted(all_students), sorted(self.marker1.students))
        self.assertEqual(sorted(all_methods), sorted(self.marker1.methods))

        self.assertEqual(self.marker1.key, self.marker2.place_holder)
        self.assertEqual(self.marker1.key, self.marker3.place_holder)

        self.assertEqual(2, update_marker_pair_mock.call_count)

    @mock.patch('google.appengine.ext.ndb.put_multi', autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.update_marker_pair',
                autospec=True)
    def test_new_with_one_acked(self, update_marker_pair_mock,
                                find_markers_for_methods_mock,
                                put_multi_mock):
        """Ensure the new markers are merged, and the acked marker is used
        as the base.
        """
        from sosbeacon.event.contact_marker import merge_markers

        self.marker2.acknowledged = True
        self.marker2.last_viewed_date = 12345

        all_students = self.marker1.students.keys()
        all_students.extend(self.marker2.students.keys())
        all_students.extend(self.marker3.students.keys())

        all_methods = self.marker1.methods[:]
        all_methods.extend(self.marker2.methods[:])
        all_methods.extend(self.marker3.methods[:])

        find_markers_for_methods_mock.return_value = (
            self.marker1, self.marker2, self.marker3)

        merge_markers(object(), object())

        self.assertEqual(sorted(all_students), sorted(self.marker2.students))
        self.assertEqual(sorted(all_methods), sorted(self.marker2.methods))

        self.assertEqual(self.marker2.key, self.marker1.place_holder)
        self.assertEqual(self.marker2.key, self.marker3.place_holder)

        self.assertEqual(2, update_marker_pair_mock.call_count)

    @mock.patch('google.appengine.ext.ndb.put_multi', autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.update_marker_pair',
                autospec=True)
    def test_with_place_holder(self, update_marker_pair_mock,
                               find_markers_for_methods_mock,
                               put_multi_mock):
        """Ensure the marker already pointed at is used as the base."""
        from sosbeacon.event.contact_marker import merge_markers

        self.marker3.place_holder = self.marker1.key

        all_students = self.marker1.students.keys()
        all_students.extend(self.marker2.students.keys())
        all_students.extend(self.marker3.students.keys())

        all_methods = self.marker1.methods[:]
        all_methods.extend(self.marker2.methods[:])
        all_methods.extend(self.marker3.methods[:])

        find_markers_for_methods_mock.return_value = (
            self.marker1, self.marker2, self.marker3)

        merge_markers(object(), object())

        self.assertEqual(sorted(all_students), sorted(self.marker1.students))
        self.assertEqual(sorted(all_methods), sorted(self.marker1.methods))

        self.assertEqual(self.marker1.key, self.marker2.place_holder)
        self.assertEqual(self.marker1.key, self.marker3.place_holder)

        self.assertEqual(2, update_marker_pair_mock.call_count)

    @mock.patch('google.appengine.ext.ndb.put_multi', autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.update_marker_pair',
                autospec=True)
    def test_with_multiple_place_holders(self, update_marker_pair_mock,
                                         find_markers_for_methods_mock,
                                         put_multi_mock):
        """Ensure marker pointed at the most is used as the base."""
        from sosbeacon.event.contact_marker import merge_markers

        self.marker3.place_holder = self.marker1.key
        self.marker4.place_holder = self.marker1.key
        self.marker2.place_holder = self.marker3.key

        all_students = self.marker1.students.keys()
        all_students.extend(self.marker2.students.keys())
        all_students.extend(self.marker3.students.keys())
        all_students.extend(self.marker4.students.keys())

        all_methods = self.marker1.methods[:]
        all_methods.extend(self.marker2.methods[:])
        all_methods.extend(self.marker3.methods[:])
        all_methods.extend(self.marker4.methods[:])

        find_markers_for_methods_mock.return_value = (
            self.marker1, self.marker2, self.marker3, self.marker4)

        merge_markers(object(), object())

        self.assertEqual(sorted(all_students), sorted(self.marker1.students))
        self.assertEqual(sorted(all_methods), sorted(self.marker1.methods))

        self.assertEqual(self.marker1.key, self.marker2.place_holder)
        self.assertEqual(self.marker1.key, self.marker3.place_holder)

        self.assertEqual(3, update_marker_pair_mock.call_count)


class TestUpdateMarkerPair(unittest.TestCase):
    """Ensure update_marker_pair updates the two markers, and remerges if a
    marker is out of date.
    """

    def setUp(self):
        from google.appengine.datastore.datastore_stub_util import \
            TimeBasedHRConsistencyPolicy

        from sosbeacon.event.contact_marker import ContactMarker

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub(
            consistency_policy=TimeBasedHRConsistencyPolicy())
        self.testbed.init_memcache_stub()

        self.marker1 = ContactMarker(
            id='a',
            students={'a': 'student_a'},
            methods=['method_a']
        )
        self.marker2 = ContactMarker(
            id='b',
            students={'b': 'student_b'},
            methods=['method_b'],
        )

    def test_both_valid(self):
        """Test that the two markers are put if both are valid."""
        from sosbeacon.event.contact_marker import update_marker_pair

        self.marker1.put()
        self.marker2.put()

        update_marker_pair(self.marker1, self.marker2)

    def test_exception_raised_if_one_ood(self):
        """Test that the an exception is raised is a marker is stale."""
        from sosbeacon.event.contact_marker import update_marker_pair

        self.marker1.put()
        self.marker2.put()

        evil_marker1 = self.marker1.key.get(use_cache=False)
        evil_marker1.put(use_cache=False)

        self.assertRaisesRegexp(
            Exception, "revision out of date.",
            update_marker_pair, self.marker1, self.marker2)

