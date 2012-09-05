
import gaetest

from mock import Mock
from mock import patch


class TestMessageModel(gaetest.TestCase):
    """Test that Message to / from dict methods work as expected."""

    def test_from_empty_dict(self):
        """Ensure event key is required to create a message."""
        from sosbeacon.event.message import Message

        self.assertRaisesRegexp(
            Exception, 'key is required', Message.from_dict, {})

    def test_from_dict_bad_event_key(self):
        """Ensure valid event key is required to create message."""
        from google.appengine.ext import ndb

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        event_key = ndb.Key(Event, 1)

        self.assertRaisesRegexp(
            Exception, "Event not found",
            Message.from_dict, {'event': event_key})

    def test_from_dict_namespace_mismatch(self):
        """Ensure event school matches current namespace."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        event = Event(school='12345')
        event_key = Mock()
        event_key.get.return_value = event

        self.assertRaisesRegexp(
            Exception, "Security violation",
            Message.from_dict, {'event': event_key})

    def test_from_dict_comment_payload(self):
        """Ensure comment message payload matches expected type."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        event = Event(school=unicode(namespace_manager.get_namespace()))
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'c',
            'message': {
                'body': 'A Comment here.'
            }
        }

        message = Message.from_dict(message_dict)

        self.assertEqual('c', message.message_type)
        self.assertEqual(
            message_dict['message']['body'], message.message['body'])

    def test_from_dict_bad_comment_payload(self):
        """Ensure comment message payload matches expected type."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        event = Event(school=unicode(namespace_manager.get_namespace()))
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'c',
            'message': {
                'email': 'A Comment here.',
                'body': 'A Comment here.'
            }
        }

        self.assertRaisesRegexp(
            AssertionError, "Invalid comment payload",
            Message.from_dict, message_dict)

    def test_from_dict_broadcast_payload(self):
        """Ensure comment message payload matches expected type."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        event = Event(school=unicode(namespace_manager.get_namespace()))
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'b',
            'message': {
                'sms': 'Your SMS message here.',
                'email': 'The email message here.'
            }
        }

        message = Message.from_dict(message_dict)

        self.assertEqual('b', message.message_type)
        self.assertEqual(
            message_dict['message']['sms'], message.message['sms'])
        self.assertEqual(
            message_dict['message']['email'], message.message['email'])

    def test_from_dict_bad_broadcast_payload(self):
        """Ensure comment message payload matches expected type."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        event = Event(school=unicode(namespace_manager.get_namespace()))
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'b',
            'message': {
                'email': 'A Comment here.',
                'body': 'A Comment here.'
            }
        }

        self.assertRaisesRegexp(
            AssertionError, "Invalid broadcast payload",
            Message.from_dict, message_dict)


class TestScanGroups(gaetest.TestCase):
    """Test the broadcast_to_groups method to ensure it inserts a batch of
    tasks per ten groups.
    """

    def test_one_group(self):
        """Ensure event key is required to create a message."""
        from sosbeacon import utils

        from sosbeacon.event.message import broadcast_to_groups

        insert_tasks_mock = Mock()

        self.patch(utils, 'insert_tasks', insert_tasks_mock)

        group_keys = []
        for i in range(9):
            group_key = Mock()
            group_key.urlsafe.return_value = i + 100
            group_keys.append(group_key)

        message = Mock()
        message.key.urlsafe.return_value = 'abc'

        broadcast_to_groups(group_keys, message)

        self.assertEqual(insert_tasks_mock.call_count, 1)

    def test_multiple_groups(self):
        """Ensure event key is required to create a message."""
        from sosbeacon import utils

        from sosbeacon.event.message import broadcast_to_groups

        insert_tasks_mock = Mock()

        self.patch(utils, 'insert_tasks', insert_tasks_mock)

        group_keys = []
        for i in xrange(35):
            group_key = Mock()
            group_key.urlsafe.return_value = i + 100
            group_keys.append(group_key)

        message = Mock()
        message.key.urlsafe.return_value = 'abc'

        broadcast_to_groups(group_keys, message)

        self.assertEqual(4, insert_tasks_mock.call_count)

        call_history = insert_tasks_mock.call_args_list

        for i in range(3):
            self.assertEqual(11, len(call_history[i][0][0]))

        self.assertEqual(2, len(call_history[3][0][0]))

    def test_all_groups(self):
        from sosbeacon.event.message import broadcast_to_groups
        """Ensure passing in the all groups group, results in a query."""

        from sosbeacon.group import Group
        from sosbeacon.group import ALL_GROUPS_ID

        group_iter_mock = Mock(return_value=[])
        group_order_mock = Mock(return_value=group_iter_mock)
        group_query_mock = Mock(return_value=group_order_mock)
        group_query = Mock(return_value=group_query_mock)

        self.patch(Group, 'query', group_query)

        print ''
        print group_iter_mock
        print Group.query().order()

        group_key = Mock()
        group_key.id = ALL_GROUPS_ID

        message = Mock()
        message.key.urlsafe.return_value = 'abc'

        broadcast_to_groups([group_key], message)

        self.assertEqual(1, group_query_mock.call_count)

