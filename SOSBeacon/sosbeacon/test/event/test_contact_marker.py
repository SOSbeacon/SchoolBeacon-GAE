
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
        self.assertEqual([], left.students)

    def test_merge_students_with_no_students(self):
        """Ensure merging students with no students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students = [
            ('123312', 'Sam Smith', 123432),
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        left = ContactMarker(students=students)
        right = ContactMarker()
        left.merge(right)
        self.assertEqual(sorted(students), sorted(left.students))

    def test_merge_no_students_with_students(self):
        """Ensure merging no students with students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students = [
            ('123312', 'Sam Smith', 123432),
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        left = ContactMarker()
        right = ContactMarker(students=students)
        left.merge(right)
        self.assertEqual(sorted(students), sorted(left.students))

    def test_merge_students(self):
        """Ensure merging students."""
        from sosbeacon.event.contact_marker import ContactMarker

        students_1 = [
            ('123312', 'Sam Smith', 123432),
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        students_2 = [
            ('848423', 'Frank Frankton', 953342),
        ]

        left = ContactMarker(students=students_1)
        right = ContactMarker(students=students_2)
        left.merge(right)
        self.assertEqual(sorted(students_1 + students_2),
                         sorted(left.students))

    def test_merge_overlapping_students(self):
        """Ensure merging students with overlaps."""
        from sosbeacon.event.contact_marker import ContactMarker

        base_students = [
            ('312130', 'John Jones', 312123),
            ('544312', 'Billy Bob', 348223)
        ]

        students_1 = base_students + [('123312', 'Sam Smith', 123432)]
        students_2 = base_students + [('848423', 'Frank Frankton', 953342)]

        left = ContactMarker(students=students_1)
        right = ContactMarker(students=students_2)
        left.merge(right)
        self.assertEqual(sorted(set(students_1 + students_2)),
                         sorted(left.students))


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
        """Ensure error is raised if no contact is provided."""
        from sosbeacon.event.contact_marker import create_or_update_marker

        self.assertRaisesRegexp(
            ValueError, "student_key is required.",
            create_or_update_marker, object(), None, {'a': True}, ['a'])

    def test_no_event_key(self):
        """Ensure error is raised if no contact is provided."""
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
    @mock.patch('sosbeacon.event.contact_marker.insert_merge_task',
                autospec=True)
    @mock.patch('sosbeacon.event.contact_marker.find_markers_for_methods',
                autospec=True)
    def test_sort_place_holders(self, find_markers_for_methods_mock,
                                insert_merge_task_mock,
                                insert_update_marker_task_mock):
        """Ensure an exsting short_id is returned, and contact merged, if
        there is a matching marker.
        """
        from google.appengine.ext import ndb

        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.contact_marker import create_or_update_marker
        from sosbeacon.event.event import Event

        marker1_key = mock.Mock(spec=ndb.Key)
        marker1_key.kind.return_value = "ContactMarker"
        marker1 = ContactMarker(key=marker1_key, short_id='A')
        marker1_key.get.return_value = marker1

        find_markers_for_methods_mock.return_value = (marker1,)

        event_key = ndb.Key(Event, 'EVENTKEY')

        student_key = mock.Mock()
        student_key.id.return_value = "STUDENTKEY"

        ret_value = create_or_update_marker(
            event_key, student_key, {'a': True}, ['123'])

        self.assertEqual('A', ret_value)

        self.assertEqual(1, insert_update_marker_task_mock.call_count)
        self.assertEqual(1, insert_merge_task_mock.call_count)

