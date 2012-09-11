
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


class TestBroadcastToGroups(gaetest.TestCase):
    """Test the broadcast_to_groups method to ensure it inserts a batch of
    tasks per ten groups.
    """

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    def test_one_group(self, insert_tasks_mock):
        """Ensure event key is required to create a message."""
        from sosbeacon.event.message import broadcast_to_groups

        group_keys = []
        for i in range(9):
            group_key = Mock()
            group_key.urlsafe.return_value = i + 100
            group_keys.append(group_key)

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups(group_keys, message_key, '')

        self.assertEqual(insert_tasks_mock.call_count, 1)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    def test_multiple_groups(self, insert_tasks_mock):
        """Ensure event key is required to create a message."""
        from sosbeacon.event.message import broadcast_to_groups

        group_keys = []
        for i in xrange(35):
            group_key = Mock()
            group_key.urlsafe.return_value = i + 100
            group_keys.append(group_key)

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups(group_keys, message_key, '')

        self.assertEqual(4, insert_tasks_mock.call_count)

        call_history = insert_tasks_mock.call_args_list

        for i in range(3):
            self.assertEqual(11, len(call_history[i][0][0]))

        self.assertEqual(2, len(call_history[3][0][0]))

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.group.Group.query')
    def test_all_groups(self, group_query_mock, insert_tasks_mock):
        """Ensure passing in the all groups group, results in a query."""
        from sosbeacon.event.message import broadcast_to_groups

        from sosbeacon.group import ALL_GROUPS_ID
        from sosbeacon.group import Group

        group_order_mock = group_query_mock.return_value.order
        group_iter_mock = group_order_mock.return_value.iter
        group_iter_mock.return_value = []

        group_key = Mock()
        group_key.id = ALL_GROUPS_ID

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups([group_key], message_key, '')

        group_query_mock.assert_called_once_with()
        group_order_mock.assert_called_once_with(Group.key)
        group_iter_mock.assert_called_once_with(keys_only=True)

class TestGetGroupBroadcastTask(gaetest.TestCase):
    """Test the get_group_broadcast_task method to ensure it returns a
    task with the proper settings.
    """

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_name(self, task_mock):
        """Ensure the resultant task name contains enough to be unique."""
        from sosbeacon.event.message import get_group_broadcast_task

        group_key = Mock()
        group_key.urlsafe.return_value = "GROUPKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "MESSAGEKEY"

        batch_id = "BATCHID"
        iteration = 7

        ret_value = get_group_broadcast_task(
            group_key, message_key, batch_id, iteration)

        task_name = task_mock.call_args[1]['name']
        self.assertIn('GROUPKEY', task_name)
        self.assertIn('MESSAGEKEY', task_name)
        self.assertIn('BATCHID', task_name)
        self.assertIn('7', task_name)

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_params(self, task_mock):
        """Ensure the resultant task parms contain all info."""
        from sosbeacon.event.message import get_group_broadcast_task

        group_key = Mock()
        group_key.urlsafe.return_value = "AGROUPKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "SOMEMESSAGEKEY"

        batch_id = "THEBATCHID"
        iteration = 19

        ret_value = get_group_broadcast_task(
            group_key, message_key, batch_id, iteration)

        check_params = {
            'group': 'AGROUPKEY',
            'message': 'SOMEMESSAGEKEY',
            'batch': 'THEBATCHID',
            'cursor': '',
            'iter': 19
        }
        self.assertEqual(check_params, task_mock.call_args[1]['params'])

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_cursor(self, task_mock):
        """Ensure the resultant task parms contain the cursor."""
        from sosbeacon.event.message import get_group_broadcast_task

        group_key = Mock()
        group_key.urlsafe.return_value = "ZGROUPKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "AMESSAGEKEY"

        cursor = Mock()
        cursor.urlsafe.return_value = "CURSOR,THE"

        batch_id = "ABATCHID"
        iteration = 33

        ret_value = get_group_broadcast_task(
            group_key, message_key, batch_id, iteration, cursor)

        check_params = {
            'group': 'ZGROUPKEY',
            'message': 'AMESSAGEKEY',
            'batch': 'ABATCHID',
            'cursor': 'CURSOR,THE',
            'iter': 33
        }
        self.assertEqual(check_params, task_mock.call_args[1]['params'])


class TestBroadcastToGroup(gaetest.TestCase):
    """Test the broadcast_to_group method to ensure it inserts the expected
    tasks.
    """

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.event.message.get_group_broadcast_task', autospec=True)
    @patch('sosbeacon.group.get_students', autospec=True)
    def test_continuation(self, get_students_mock,
                          get_group_broadcast_task_mock, insert_tasks_mock):
        """Verify a continuation task is inserted if there are more students."""
        from sosbeacon.event.message import GROUP_TX_QUEUE
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        message_key = object()
        cursor = object()

        get_students_mock.return_value = ((), cursor, True)

        continuation_marker = object()
        get_group_broadcast_task_mock.return_value = continuation_marker

        broadcast_to_group(group_key=group_key, message_key=message_key,
                           batch_id='alpha', iteration=17, cursor=cursor)

        get_students_mock.assert_called_once_with(group_key, cursor)

        get_group_broadcast_task_mock.assert_called_once_with(
            group_key, message_key, 'alpha', 18, cursor)

        insert_tasks_mock.assert_called_once_with(
            (continuation_marker,), GROUP_TX_QUEUE)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.event.message.get_group_broadcast_task', autospec=True)
    @patch('sosbeacon.group.get_students', autospec=True)
    def test_no_continuation(self, get_students_mock,
                             get_group_broadcast_task_mock, insert_tasks_mock):
        """Verify a continuation task is not inserted if there are not more
        students.
        """
        from sosbeacon.event.message import GROUP_TX_QUEUE
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        message_key = object()
        cursor = object()

        get_students_mock.return_value = ((), cursor, False)

        continuation_marker = object()
        get_group_broadcast_task_mock.return_value = continuation_marker

        broadcast_to_group(group_key=group_key, message_key=message_key,
                           batch_id='alpha', iteration=17, cursor=cursor)

        get_students_mock.assert_called_once_with(group_key, cursor)

        self.assertEqual(get_group_broadcast_task_mock.call_count, 0)
        self.assertEqual(insert_tasks_mock.call_count, 0)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.group.get_students', autospec=True)
    @patch('sosbeacon.event.message.get_student_broadcast_task', autospec=True)
    def test_no_student_task_returned(self, get_student_broadcast_task_mock,
                                      get_students_mock, insert_tasks_mock):
        """Verify a continuation task is not inserted if there are not more
        students.
        """
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        message_key = object()

        get_students_mock.return_value = ((object(),), None, False)

        get_student_broadcast_task_mock.return_value = None

        broadcast_to_group(group_key=group_key, message_key=message_key,
                           batch_id='alpha')

        get_students_mock.assert_called_once_with(group_key, None)

        self.assertEqual(insert_tasks_mock.call_count, 0)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.group.get_students', autospec=True)
    @patch('sosbeacon.event.message.get_student_broadcast_task', autospec=True)
    def test_student_task_returned(self, get_student_broadcast_task_mock,
                                   get_students_mock, insert_tasks_mock):
        """Verify a continuation task is not inserted if there are not more
        students.
        """
        from sosbeacon.event.message import STUDENT_TX_QUEUE
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        message_key = object()

        get_students_mock.return_value = ((object(),), None, False)

        student_task = object()
        get_student_broadcast_task_mock.return_value = student_task

        broadcast_to_group(group_key=group_key, message_key=message_key,
                           batch_id='alpha')

        get_students_mock.assert_called_once_with(group_key, None)

        insert_tasks_mock.assert_called_once_with(
            [student_task,], STUDENT_TX_QUEUE)

