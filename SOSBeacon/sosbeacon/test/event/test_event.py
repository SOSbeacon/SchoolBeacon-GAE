
import unittest

import mock


class TestEventModel(unittest.TestCase):
    """Test that Event to / from dict methods work as expected."""

    def test_from_empty_dict(self):
        """Ensure merging two non-acked doesn't ack."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.event import EVENT_DRAFT_STATUS

        event = Event.from_dict({'groups': []})
        self.assertEqual('_x_', event.key.namespace())
        self.assertEqual(EVENT_DRAFT_STATUS, event.status)

    def test_from_dict(self):
        """Ensure merging two non-acked doesn't ack."""
        from datetime import datetime
        from sosbeacon.event.event import Event
        from sosbeacon.event.event import EVENT_DRAFT_STATUS

        event_dict = {
            'title': 'Test Title',
            'type': 'e',
            'date': datetime(2012, 8, 30, 7, 37),
            'status': EVENT_DRAFT_STATUS,
            'content': 'This is some test content',
            'groups': []
        }

        event = Event.from_dict(event_dict)

        self.assertEqual('_x_', event.key.namespace())

        self.assertEqual(event_dict['title'], event.title)
        self.assertEqual(event_dict['type'], event.event_type)
        self.assertEqual(event_dict['date'], event.date)
        self.assertEqual(event_dict['status'], event.status)
        self.assertEqual(event_dict['content'], event.content)
        self.assertEqual(event_dict['groups'], event.groups)

    @unittest.skip('Figure out if this test has any value.')
    def test_to_from_composition(self):
        """Ensure to_dict(from_dict(x)) returns a correctly setup object."""
        from datetime import datetime
        from sosbeacon.event.event import Event
        from sosbeacon.event.event import EVENT_DRAFT_STATUS

        event_dict = {
            'title': 'Test Title',
            'type': 'e',
            'date': datetime(2012, 8, 30, 7, 37),
            'status': EVENT_DRAFT_STATUS,
            'content': 'This is some test content',
            'groups': []
        }

        event = Event.from_dict(event_dict)
        event._prepare_for_put()  # Needed to trip auto-now datetimes.

        new_dict = event.to_dict()

        # TODO: Figure out if this test has any value.
        self.assertEqual(event_dict, new_dict)

    def test_status_change_to_sent(self):
        """Ensure status can not be set to sent."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.event import EVENT_DRAFT_STATUS
        from sosbeacon.event.event import EVENT_SENT_STATUS

        event_dict = {
            'title': 'Test Title',
            'type': 'e',
            'status': EVENT_SENT_STATUS,
            'content': 'This is some test content',
            'groups': []
        }

        event = Event.from_dict(event_dict)

        # TODO: Figure out if this test has any value.
        self.assertEqual(EVENT_DRAFT_STATUS, event.status)

    @mock.patch('google.appengine.ext.ndb.Key.get')
    def test_status_change_to_draft_from_sent(self, key_get_mock):
        """Ensure status can not be changed from sent to draft."""
        from google.appengine.ext import ndb

        from sosbeacon.event.event import Event
        from sosbeacon.event.event import EVENT_DRAFT_STATUS
        from sosbeacon.event.event import EVENT_SENT_STATUS

        event = Event(status=EVENT_SENT_STATUS)
        key_get_mock.return_value = event

        event_dict = {
            'key': ndb.Key(Event, 1),
            'title': 'Test Title',
            'type': 'e',
            'status': EVENT_DRAFT_STATUS,
            'content': 'This is some test content',
            'groups': []
        }

        new_event = Event.from_dict(event_dict)

        # TODO: Figure out if this test has any value.
        self.assertEqual(EVENT_SENT_STATUS, new_event.status)

