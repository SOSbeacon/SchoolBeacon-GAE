
import json
import unittest

from mock import Mock
from mock import patch

from google.appengine.ext import testbed


class TestMessageModel(unittest.TestCase):
    """Test that Message to / from dict methods work as expected."""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

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

    @patch('sosbeacon.event.message.Message.allocate_ids')
    def test_from_dict_comment_payload(self, message_alloc_ids_mock):
        """Ensure message with comment payload and type works OK."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event()
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

    @patch('sosbeacon.event.message.Message.allocate_ids')
    def test_from_dict_bad_comment_payload(self, message_alloc_ids_mock):
        """Ensure broadcast message payload with comment type raises an
        exception.
        """
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event()
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

    @patch('sosbeacon.event.message.Message.allocate_ids')
    @patch('google.appengine.api.taskqueue.Queue.add')
    def test_from_dict_broadcast_payload(self, message_alloc_ids_mock,
                                         queue_add_mock):
        """Ensure broadcast message with correct payload and type works."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event(title='test')
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

    @patch('sosbeacon.event.message.Message.allocate_ids')
    def test_from_dict_bad_broadcast_payload(self, message_alloc_ids_mock):
        """Ensure comment message payload matches expected type."""
        from google.appengine.api import namespace_manager

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event()
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

    @patch('sosbeacon.event.message.Message.allocate_ids')
    @patch('google.appengine.api.taskqueue.Queue.add')
    def test_from_dict_emergency_payload(self, message_alloc_ids_mock,
                                         queue_add_mock):
        """Ensure emergency message with correct payload and type works."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event(title='test')
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'em',
            'message': {
                'sms': 'Your SMS emergency here.',
                'email': 'The emergency email message here.'
            }
        }

        message = Message.from_dict(message_dict)

        self.assertEqual('em', message.message_type)
        self.assertEqual(
            message_dict['message']['sms'], message.message['sms'])
        self.assertEqual(
            message_dict['message']['email'], message.message['email'])

    @patch('sosbeacon.event.message.Message.allocate_ids')
    def test_from_dict_bad_emergency_payload(self, message_alloc_ids_mock):
        """Ensure emergency message payload matches expected type."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event()
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'em',
            'message': {
                'email': 'A write emergency here.',
                'body': 'A write emergency here.'
            }
        }

        self.assertRaisesRegexp(
            AssertionError, "Invalid broadcast payload",
            Message.from_dict, message_dict)

    @patch('sosbeacon.event.message.Message.allocate_ids')
    @patch('google.appengine.api.taskqueue.Queue.add')
    def test_from_dict_email_only_payload(self, message_alloc_ids_mock,
                                         queue_add_mock):
        """Ensure email only message with correct payload and type works."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event(title='test')
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'eo',
            'message': {
                'sms': '',
                'email': 'The email message here.'
            }
        }

        message = Message.from_dict(message_dict)

        self.assertEqual('eo', message.message_type)
        self.assertEqual(
            message_dict['message']['email'], message.message['email'])

    @patch('sosbeacon.event.message.Message.allocate_ids')
    def test_from_dict_bad_email_only_payload(self, message_alloc_ids_mock):
        """Ensure email only message payload matches expected type."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event()
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'eo',
            'message': {
                'body': 'A write emergency here.',
            }
        }

        self.assertRaisesRegexp(
            AssertionError, "Invalid broadcast payload",
            Message.from_dict, message_dict)

    @patch('sosbeacon.event.message.Message.allocate_ids')
    @patch('google.appengine.api.taskqueue.Queue.add')
    def test_from_dict_email_call_payload(self, message_alloc_ids_mock,
                                          queue_add_mock):
        """Ensure email call message with correct payload and type works."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event(title='test')
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'ec',
            'message': {
                'sms': '',
                'email': 'The email message here.'
            }
        }

        message = Message.from_dict(message_dict)

        self.assertEqual('ec', message.message_type)
        self.assertEqual(
            message_dict['message']['email'], message.message['email'])

    @patch('sosbeacon.event.message.Message.allocate_ids')
    def test_from_dict_bad_email_call_payload(self, message_alloc_ids_mock):
        """Ensure email call message payload matches expected type."""
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message

        message_alloc_ids_mock.return_value = 1, 1

        event = Event()
        event_key = Mock()
        event_key.get.return_value = event

        message_dict = {
            'event': event_key,
            'type': 'ec',
            'message': {
                'body': 'A write emergency here.',
                }
        }

        self.assertRaisesRegexp(
            AssertionError, "Invalid broadcast payload",
            Message.from_dict, message_dict)


class TestBroadcastToGroups(unittest.TestCase):
    """Test the broadcast_to_groups method to ensure it inserts a batch of
    tasks per ten groups.
    """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    def test_one_group(self, insert_tasks_mock):
        """Ensure event key is required to create a message."""
        from sosbeacon.event.message import broadcast_to_groups

        group_keys = []
        for i in range(9):
            group_key = Mock()
            group_key.urlsafe.return_value = i + 100
            group_keys.append(group_key)

        event_key = Mock()

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups(group_keys, event_key, message_key, '')

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

        event_key = Mock()

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups(group_keys, event_key, message_key, '')

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

        from sosbeacon.group import ADMIN_GROUPS_ID
        from sosbeacon.group import Group

        group_order_mock = group_query_mock.return_value.order
        group_iter_mock = group_order_mock.return_value.iter
        group_iter_mock.return_value = []

        group_key = Mock()
        group_key.id.return_value = ADMIN_GROUPS_ID

        event_key = Mock()

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups([group_key], event_key, message_key, '')

        group_query_mock.assert_called_once_with()
        group_order_mock.assert_called_once_with(Group.key)
        group_iter_mock.assert_called_once_with(keys_only=True)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.event.message.get_group_broadcast_task', autospec=True)
    def test_batch_passed_through(self, get_task_mock, insert_tasks_mock):
        """Ensure batch is passed to task generation function."""
        from sosbeacon.event.message import broadcast_to_groups

        group_key = Mock()
        group_key.id.return_value = 'SomeGroup'

        event_key = Mock()

        message_key = Mock()
        message_key.urlsafe.return_value = 'abc'

        broadcast_to_groups([group_key], event_key, message_key, '')

        self.assertEqual(insert_tasks_mock.call_count, 1)

        get_task_mock.assert_called_once_with(
            group_key, event_key, message_key, '')


class TestGetGroupBroadcastTask(unittest.TestCase):
    """Test the get_group_broadcast_task method to ensure it returns a
    task with the proper settings.
    """

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_name(self, task_mock):
        """Ensure the resultant task name contains enough to be unique."""
        from sosbeacon.event.message import get_group_broadcast_task

        group_key = Mock()
        group_key.urlsafe.return_value = "GROUPKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "EVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "MESSAGEKEY"

        batch_id = "BATCHID"
        iteration = 7

        get_group_broadcast_task(
            group_key, event_key, message_key, batch_id, iteration)

        task_name = task_mock.call_args[1]['name']
        self.assertIn('GROUPKEY', task_name)
        self.assertNotIn('EVENTKEY', task_name)
        self.assertIn('MESSAGEKEY', task_name)
        self.assertIn('BATCHID', task_name)
        self.assertIn('7', task_name)

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_params(self, task_mock):
        """Ensure the resultant task parms contain all info."""
        from sosbeacon.event.message import get_group_broadcast_task

        group_key = Mock()
        group_key.urlsafe.return_value = "AGROUPKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "SOMEEVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "SOMEMESSAGEKEY"

        batch_id = "THEBATCHID"
        iteration = 19

        get_group_broadcast_task(
            group_key, event_key, message_key, batch_id, iteration)

        check_params = {
            'group': 'AGROUPKEY',
            'event': 'SOMEEVENTKEY',
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

        event_key = Mock()
        event_key.urlsafe.return_value = "ANEVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "AMESSAGEKEY"

        cursor = Mock()
        cursor.urlsafe.return_value = "CURSOR,THE"

        batch_id = "ABATCHID"
        iteration = 33

        get_group_broadcast_task(
            group_key, event_key, message_key, batch_id, iteration, cursor)

        check_params = {
            'group': 'ZGROUPKEY',
            'event': 'ANEVENTKEY',
            'message': 'AMESSAGEKEY',
            'batch': 'ABATCHID',
            'cursor': 'CURSOR,THE',
            'iter': 33
        }
        self.assertEqual(check_params, task_mock.call_args[1]['params'])


class TestBroadcastToGroup(unittest.TestCase):
    """Test the broadcast_to_group method to ensure it inserts the expected
    tasks.
    """

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.event.message.get_group_broadcast_task', autospec=True)
    @patch('sosbeacon.group.get_student_keys', autospec=True)
    def test_continuation(self, get_student_keys_mock,
                          get_group_broadcast_task_mock, insert_tasks_mock):
        """Verify a continuation task is inserted if there are more
        students.
        """
        from sosbeacon.event.message import GROUP_TX_QUEUE
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        event_key = object()
        message_key = object()
        cursor = object()

        get_student_keys_mock.return_value = ((), cursor, True)

        continuation_marker = object()
        get_group_broadcast_task_mock.return_value = continuation_marker

        broadcast_to_group(group_key=group_key, event_key=event_key,
                           message_key=message_key,
                           batch_id='alpha', iteration=17, cursor=cursor)

        get_student_keys_mock.assert_called_once_with(group_key, cursor)

        get_group_broadcast_task_mock.assert_called_once_with(
            group_key, event_key, message_key, 'alpha', 18, cursor)

        insert_tasks_mock.assert_called_once_with(
            (continuation_marker,), GROUP_TX_QUEUE)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.event.message.get_group_broadcast_task', autospec=True)
    @patch('sosbeacon.group.get_student_keys', autospec=True)
    def test_no_continuation(self, get_student_keys_mock,
                             get_group_broadcast_task_mock, insert_tasks_mock):
        """Verify a continuation task is not inserted if there are not more
        students.
        """
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        event_key = object()
        message_key = object()
        cursor = object()

        get_student_keys_mock.return_value = ((), cursor, False)

        continuation_marker = object()
        get_group_broadcast_task_mock.return_value = continuation_marker

        broadcast_to_group(group_key=group_key, event_key=event_key,
                           message_key=message_key,
                           batch_id='alpha', iteration=17, cursor=cursor)

        get_student_keys_mock.assert_called_once_with(group_key, cursor)

        self.assertEqual(get_group_broadcast_task_mock.call_count, 0)
        self.assertEqual(insert_tasks_mock.call_count, 0)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.group.get_student_keys', autospec=True)
    @patch('sosbeacon.event.message.get_student_broadcast_task', autospec=True)
    def test_no_student_task_returned(self, get_student_broadcast_task_mock,
                                      get_student_keys_mock,
                                      insert_tasks_mock):
        """Verify a continuation task is not inserted if there are not more
        students.
        """
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        event_key = object()
        message_key = object()

        get_student_keys_mock.return_value = ((object(),), None, False)

        get_student_broadcast_task_mock.return_value = None

        broadcast_to_group(group_key=group_key, event_key=event_key,
                           message_key=message_key,
                           batch_id='alpha')

        get_student_keys_mock.assert_called_once_with(group_key, None)

        self.assertEqual(insert_tasks_mock.call_count, 0)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.group.get_student_keys', autospec=True)
    @patch('sosbeacon.event.message.get_student_broadcast_task', autospec=True)
    def test_student_task_returned(self, get_student_broadcast_task_mock,
                                   get_student_keys_mock, insert_tasks_mock):
        """Verify a continuation task is not inserted if there are not more
        students.
        """
        from sosbeacon.event.message import STUDENT_TX_QUEUE
        from sosbeacon.event.message import broadcast_to_group

        group_key = object()
        event_key = object()
        message_key = object()

        get_student_keys_mock.return_value = ((object(),), None, False)

        student_task = object()
        get_student_broadcast_task_mock.return_value = student_task

        broadcast_to_group(group_key=group_key, event_key=event_key,
                           message_key=message_key,
                           batch_id='alpha')

        get_student_keys_mock.assert_called_once_with(group_key, None)

        insert_tasks_mock.assert_called_once_with(
            [student_task], STUDENT_TX_QUEUE)


class TestGetStudentBroadcastTask(unittest.TestCase):
    """Test the get_student_broadcast_task method to ensure it generates the
    expected task.
    """

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_name(self, task_mock):
        """Ensure the resultant task name contains enough to be unique."""
        from sosbeacon.event.message import get_student_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "STUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "EVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "MESSAGEKEY"

        batch_id = "BATCHID"

        get_student_broadcast_task(
            student_key, event_key, message_key, batch_id)

        task_name = task_mock.call_args[1]['name']
        self.assertIn('STUDENTKEY', task_name)
        self.assertNotIn('EVENTKEY', task_name)
        self.assertIn('MESSAGEKEY', task_name)
        self.assertIn('BATCHID', task_name)

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_params(self, task_mock):
        """Ensure the resultant task parms contain all info."""
        from sosbeacon.event.message import get_student_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "ASTUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "ANEVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "SOMEMESSAGEKEY"

        batch_id = "THEBATCHID"

        get_student_broadcast_task(
            student_key, event_key, message_key, batch_id)

        check_params = {
            'student': 'ASTUDENTKEY',
            'event': 'ANEVENTKEY',
            'message': 'SOMEMESSAGEKEY',
            'batch': 'THEBATCHID',
        }
        self.assertEqual(check_params, task_mock.call_args[1]['params'])


class TestBroadcastToStudent(unittest.TestCase):
    """Test the broadcast_to_student method to ensure it sends the
    expected task.
    """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_taskqueue_stub(root_path='')

    def test_no_student(self):
        """Ensure the method does not error if the student is not found."""
        from sosbeacon.event.message import broadcast_to_student

        student_key = Mock()
        student_key.get.return_value = None

        event_key = Mock()
        message_key = Mock()

        broadcast_to_student(student_key, event_key, message_key)

    @patch('sosbeacon.event.message.get_contact_broadcast_task', autospec=True)
    def test_no_contacts(self, get_contact_broadcast_task_mock):
        """Ensure the method does not error if no contacts are found."""
        from google.appengine.ext import ndb

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import broadcast_to_student

        student_key = Mock()
        student_key.get.return_value.name = "Joe Blow"
        student_key.get.return_value.contacts = ()
        student_key.get.return_value.key.urlsafe.return_value = "STUDENTKEY"

        event_key = ndb.Key(Event, "EVENTKEY")

        message_key = Mock()

        broadcast_to_student(student_key, event_key, message_key)

        self.assertFalse(get_contact_broadcast_task_mock.called)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('sosbeacon.event.message.get_contact_broadcast_task', autospec=True)
    def test_broadcast_to_contacts(self, get_contact_broadcast_task_mock,
                                   insert_tasks_mock):
        """Ensure the method does not error if no contacts are found."""
        from google.appengine.ext import ndb

        from sosbeacon.event.event import Event
        from sosbeacon.event.message import broadcast_to_student

        contacts = ({'t': 'test', 'name': 'me'},)

        student_key = Mock()
        student_key.get.return_value.name = "Joe Blow"
        student_key.get.return_value.contacts = contacts
        student_key.get.return_value.key.urlsafe.return_value = "STUDENTKEY"

        event_key = ndb.Key(Event, "EVENTKEY")

        message_key = Mock()

        broadcast_to_student(student_key, event_key, message_key)

        get_contact_broadcast_task_mock.assert_called_once_with(
            event_key, message_key, student_key, contacts[0], '')

        self.assertEqual(1, insert_tasks_mock.call_count)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('google.appengine.ext.ndb.Model.put', autospec=True)
    def test_student_marker_inserted(self, put_mock, insert_tasks_mock):
        """Ensure the method creates the student marker."""
        from google.appengine.ext import ndb

        from sosbeacon.event.message import broadcast_to_student

        student_key = Mock()
        student_key.get.return_value.name = "Joe Blow"
        student_key.get.return_value.contacts = ()
        student_key.id.return_value = 211
        student_key.get.return_value.event.id.return_value = 919
        student_key.get.return_value.key.urlsafe.return_value = "STUDENTKEY"

        event_key = Mock(spec=ndb.Key)
        event_key.kind.return_value = "Event"
        event_key.urlsafe.return_value = "EVENTKEY"

        message_key = Mock()

        broadcast_to_student(student_key, event_key, message_key)

        self.assertEqual(1, put_mock.call_count)


class TestGetContactBroadcastTask(unittest.TestCase):
    """Test the get_contact_broadcast_task function to ensure it generates the
    expected task.
    """

    def test_task_name(self):
        """Ensure the resultant task name contains enough to be unique."""
        from sosbeacon.event.message import get_contact_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "STUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "EVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "MESSAGEKEY"

        batch_id = "BATCHID"

        contact = {
            'name': 'Johny Jones',
            'methods': (
                {'type': 't', 'value': '1234567890'},
                {'type': 'e', 'value': 'johny@jones.com'},
            )
        }

        task = get_contact_broadcast_task(
            event_key, message_key, student_key, contact, batch_id)

        self.assertIn('STUDENTKEY', task.name)
        self.assertNotIn('EVENTKEY', task.name)
        self.assertIn('MESSAGEKEY', task.name)
        self.assertIn('BATCHID', task.name)
        self.assertNotIn('johny@jones.com', task.name)

    def test_methods_in_task_name(self):
        """Ensure the resultant task name contains an encoded form of the
        methods, so that the name is unique.
        """
        from sosbeacon.event.message import get_contact_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "STUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "EVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "MESSAGEKEY"

        batch_id = "BATCHID"

        contact_one = {
            'name': 'Johny Jones',
            'methods': (
                {'type': 't', 'value': '1234567890'},
                {'type': 'e', 'value': 'johny@jones.com'},
            )
        }

        contact_two = {
            'name': 'Johny Jones',
            'methods': (
                {'type': 't', 'value': '1234567890'},
                {'type': 'e', 'value': 'jonny@jones.com'},
            )
        }

        task_one = get_contact_broadcast_task(
            event_key, message_key, student_key, contact_one, batch_id)

        task_two = get_contact_broadcast_task(
            event_key, message_key, student_key, contact_two, batch_id)

        self.assertNotEqual(task_one.name, task_two.name)

    def test_task_params(self):
        """Ensure the resultant task parms contain all info."""
        from sosbeacon.event.message import get_contact_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "ASTUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "ANEVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "SOMEMESSAGEKEY"

        batch_id = "THEBATCHID"

        contact = {
            'name': 'Johny Jones',
            'methods': (
                {'type': 't', 'value': '1234567890'},
                {'type': 'e', 'value': 'johny@jones.com'},
            )
        }

        task = get_contact_broadcast_task(
            event_key, message_key, student_key, contact, batch_id)

        check_params = {
            'student': 'ASTUDENTKEY',
            'event': 'ANEVENTKEY',
            'message': 'SOMEMESSAGEKEY',
            'batch': 'THEBATCHID',
            'contact': json.dumps(contact),
        }
        self.assertEqual(check_params, task.extract_params())

    def test_no_methods(self):
        """Ensure no task is returned when there are no contact methods."""
        #raise Exception("Make sure it doesn't send a task if no methods.")
        from sosbeacon.event.message import get_contact_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "ASTUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "SOMEEVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "SOMEMESSAGEKEY"

        batch_id = "THEBATCHID"

        contact = {
            'name': 'Johny Jones',
            'methods': ()
        }

        task = get_contact_broadcast_task(
            event_key, message_key, student_key, contact, batch_id)

        self.assertIsNone(task)

    def test_missing_methods(self):
        """Ensure there is no exception raised and no task is return when the
        methods key is missing.
        """
        #raise Exception("Make sure it doesn't send a task if no methods.")
        from sosbeacon.event.message import get_contact_broadcast_task

        student_key = Mock()
        student_key.urlsafe.return_value = "ASTUDENTKEY"

        event_key = Mock()
        event_key.urlsafe.return_value = "ANEVENTKEY"

        message_key = Mock()
        message_key.urlsafe.return_value = "SOMEMESSAGEKEY"

        batch_id = "THEBATCHID"

        contact = {
            'name': 'Johny Jones'
        }

        ret_value = get_contact_broadcast_task(
            event_key, message_key, student_key, contact, batch_id)

        self.assertIsNone(ret_value)


class TestBroadcastToContact(unittest.TestCase):
    """Test the broadcast_to_contact method to ensure it inserts the
    expected tasks.
    """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    def test_no_methods(self, insert_tasks_mock):
        """Ensure the method does not error if no contact is passed."""
        from sosbeacon.event.message import broadcast_to_contact

        event_key = Mock()
        event_key.get.return_value = None

        message_key = Mock()
        message_key.get.return_value = None

        student_key = Mock()
        student_key.get.return_value = None

        contact = {}

        ret_value = broadcast_to_contact(
            event_key, message_key, student_key, contact)

        self.assertFalse(insert_tasks_mock.called)
        self.assertIsNone(ret_value)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    def test_no_searchable_methods(self, insert_tasks_mock):
        """Ensure the method does not error if no contact is passed."""
        from sosbeacon.event.message import broadcast_to_contact

        event_key = Mock()
        event_key.get.return_value = None

        message_key = Mock()
        message_key.get.return_value = None

        student_key = Mock()
        student_key.get.return_value = None

        contact = {
            'methods': [
                {'type': 'p', 'value': '1233211234'}
            ]
        }

        ret_value = broadcast_to_contact(
            event_key, message_key, student_key, contact)

        self.assertFalse(insert_tasks_mock.called)
        self.assertIsNone(ret_value)


@patch('sosbeacon.event.message.broadcast_call', autospec=True)
@patch('sosbeacon.event.message.broadcast_sms', autospec=True)
@patch('sosbeacon.event.message.broadcast_email', autospec=True)
class TestBroadcastToMethod(unittest.TestCase):
    """Test broadcast_to_method Send the message to the given contact method."""
    def setUp(self):
        from google.appengine.ext import ndb
        from sosbeacon.event.event import Event
        from sosbeacon.event.message import Message
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.user import User
        from sosbeacon.school import School
        from sosbeacon.event.message import broadcast_to_method

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.school = School(
            id='100',
            name='School_Test',
        )

        self.user = User(
            id='300',
            name='longly',
            email = 'longly@cnc.vn',
            phone = '84973796065'
        )

        self.event = Event(
            id=200,
            school= self.school.key,
            title='test event',
            content= 'This is some test content',
            groups= []
        )

        self.contact_marker = ContactMarker(key=ndb.Key(ContactMarker, "%s:%s" % (self.event.key.id(), 900),
            namespace="_x_"))
        self.contact_marker.short_id = '900'
        self.contact_marker.event = self.event.key

        self.message_broadcast = Message(
            id = '400',
            user = self.user.key,
            event = self.event.key,
            message_type = 'b',
            message = {
                'email': 'broadcast email.',
                'sms': 'broadcast sms.'
            },
        )

        self.message_email_only = Message(
            id = '500',
            user = self.user.key,
            event = self.event.key,
            message_type = 'eo',
            message = {
                'email':  'email only.',
                'sms': ''
            },
        )

        self.message_emergency = Message(
            id = '600',
            user = self.user.key,
            message_type = 'em',
            event = self.event.key,
            message = {
                'email':  'emergency email.',
                'sms': 'emergency sms'
            },
        )

        self.message_call = Message(
            id = '700',
            user = self.user.key,
            message_type = 'ec',
            event = self.event.key,
            message = {
                'email':  'email call.',
                'sms': ''
            },
        )
        to_put = [self.user, self.school, self.event, self.message_broadcast, self.message_call,
                  self.message_email_only, self.message_emergency,
                  self.contact_marker]
        ndb.put_multi(to_put)


    def test_message_type_is_b_sent_email(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: broadcast. Ensure server will sent email with method is email"""
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_broadcast.key, 900, 'longly@cnc.vn')
        self.assertEqual(1, broadcast_email_mock.call_count)
        self.assertEqual(0, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_b_sent_sms(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'b' - broadcast. Ensure server will sent sms with method is phone"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_broadcast.key, 900, '84973796065')
        self.assertEqual(0, broadcast_email_mock.call_count)
        self.assertEqual(1, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_eo_sent_email(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'eo' - email only. Ensure server will sent email with method is email"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_email_only.key, 900, 'longly@cnc.vn')
        self.assertEqual(1, broadcast_email_mock.call_count)
        self.assertEqual(0, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_eo_sent_sms(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'eo' - email only. Ensure server do not sent email with method is phone"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_email_only.key, 900, '84973796065')
        self.assertEqual(0, broadcast_email_mock.call_count)
        self.assertEqual(0, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_em_sent_email(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'em' - emergency. Ensure server will sent email with method is email"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_emergency.key, 900, 'longly@cnc.vn')
        self.assertEqual(1, broadcast_email_mock.call_count)
        self.assertEqual(0, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_em_sent_sms(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'em' - emergency. Ensure server will sent sms with method is phone"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_emergency.key, 900, '84973796065')
        self.assertEqual(0, broadcast_email_mock.call_count)
        self.assertEqual(1, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_ec_sent_sms(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'ec' - email call. Ensure server will sent sms with method is email"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_call.key, 900, 'longly@cnc.vn')
        self.assertEqual(1, broadcast_email_mock.call_count)
        self.assertEqual(0, broadcast_sms_mock.call_count)
        self.assertEqual(0, broadcast_call_mock.call_count)

    def test_message_type_is_ec_sent_sms(self, broadcast_email_mock, broadcast_sms_mock, broadcast_call_mock):
        """Message type: 'ec' - email call. Ensure server will make a call with method is phone"""
        from sosbeacon.event.contact_marker import ContactMarker
        from sosbeacon.event.message import broadcast_to_method

        broadcast_to_method(self.event.key, self.message_call.key, 900, '84973796065')
        self.assertEqual(0, broadcast_email_mock.call_count)
        self.assertEqual(0, broadcast_sms_mock.call_count)
        self.assertEqual(1, broadcast_call_mock.call_count)


class TestFunctionBroadcast(unittest.TestCase):
    """Test functions broadcast"""
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    @patch('twilio.rest.TwilioRestClient', autospec=True)
    def test_broadcast_sms(self, TwilioRestClient_mock):
        """Ensure sent a sms to method is number, message type is emergency"""
        from google.appengine.ext import ndb
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import broadcast_sms

        message_key = Mock(spec=ndb.Key)
        message_key.kind.return_value = "Message"
        message = Message(key=message_key, message_type='em', message={'email': '', 'sms': 'Test sms'})
        message_key.get.return_value = message

        broadcast_sms('84973796065', message, 'http://google.com', 'longly', 'longly')
        self.assertEqual(1, TwilioRestClient_mock.call_count)

    def test_boadcast_email(self):
        """Ensure sent a email to method is email"""
        from google.appengine.ext import ndb
        from sosbeacon.user import User
        from sosbeacon.school import School
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import broadcast_email

        user_key = Mock()
        user_key.get.return_value.name = 'longly'
        user_key.get.return_value.email= 'longly@cnc.vn'
        user_key.get.return_value.phone = '84973796065'

        school_key = Mock()
        school_key.get.return_value.name = 'Test School'

        message_key = Mock(spec=ndb.Key)
        message_key.kind.return_value = "Message"
        message = Message(key=message_key, message_type='em', message={'email': 'Test email', 'sms': 'Test sms'})
        message_key.get.return_value = message

        broadcast_email('lyhoanglong90@gmail.com', message, 'http://google.com', user_key, school_key)

    @patch('twilio.rest.TwilioRestClient', autospec=True)
    def test_broadcast_call(self, TwilioRestClient_mock):
        """Ensure robocall is active"""
        from sosbeacon.event.message import broadcast_call
        broadcast_call('84973796065')
        self.assertEqual(1, TwilioRestClient_mock.call_count)


class TestBroadcastToUser(unittest.TestCase):
    """Test the create_marker_user method to ensure it inserts a tasks for user method.
    """

    def setUp(self):
        from google.appengine.datastore.datastore_stub_util import\
            TimeBasedHRConsistencyPolicy

        from sosbeacon.event.event import Event
        from sosbeacon.user import User

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub(
            consistency_policy=TimeBasedHRConsistencyPolicy())
        self.testbed.init_memcache_stub()

        self.event = Event(
            id='100',
            title='test event 1',
            status='send'
        )

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('google.appengine.ext.ndb.Model.put', autospec=True)
    def test_message_type_email_only(self, put_mock, insert_tasks_mock):
        """Ensure the method creates the contact marker default with message type is email only."""
        from sosbeacon.event.message import create_marker_user

        event_key = self.event.key

        message_key = Mock()
        message_key.urlsafe.return_value = 'MESSAGE'
        message_key.get.return_value.message_type = 'eo'

        user_key = Mock()
        user_key.urlsafe.return_value = 'USER'
        user_key.get.return_value.name = 'longly'
        user_key.get.return_value.email= 'longly@cnc.vn'
        user_key.get.return_value.phone = '84973796065'

        create_marker_user(event_key, message_key, user_key)

        self.assertEqual(1, put_mock.call_count)
        self.assertEqual(1, insert_tasks_mock.call_count)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('google.appengine.ext.ndb.Model.put', autospec=True)
    def test_message_type_is_broadcast(self, put_mock, insert_tasks_mock):
        """Ensure the method create the contact marker default with message type is broadcast"""
        from sosbeacon.event.message import create_marker_user

        event_key = self.event.key

        message_key = Mock()
        message_key.urlsafe.return_value = 'MESSAGE'
        message_key.get.return_value.message_type = 'b'

        user_key = Mock()
        user_key.urlsafe.return_value = 'USER'
        user_key.get.return_value.name = 'longly'
        user_key.get.return_value.email= 'longly@cnc.vn'
        user_key.get.return_value.phone = '84973796065'

        create_marker_user(event_key, message_key, user_key)

        self.assertEqual(1, put_mock.call_count)
        self.assertEqual(1, insert_tasks_mock.call_count)
    #
    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('google.appengine.ext.ndb.Model.put', autospec=True)
    def test_message_type_is_emergency(self, put_mock, insert_tasks_mock):
        """Ensure the method create the contact marker default with message type is emergency"""
        from sosbeacon.event.message import create_marker_user

        event_key = self.event.key

        message_key = Mock()
        message_key.urlsafe.return_value = 'MESSAGE'
        message_key.get.return_value.message_type = 'em'

        user_key = Mock()
        user_key.urlsafe.return_value = 'USER'
        user_key.get.return_value.name = 'longly'
        user_key.get.return_value.email= 'longly@cnc.vn'
        user_key.get.return_value.phone = '84973796065'

        create_marker_user(event_key, message_key, user_key)

        self.assertEqual(1, put_mock.call_count)
        self.assertEqual(1, insert_tasks_mock.call_count)

    @patch('sosbeacon.utils.insert_tasks', autospec=True)
    @patch('google.appengine.ext.ndb.Model.put', autospec=True)
    def test_message_type_is_call(self, put_mock, insert_tasks_mock):
        """Ensure the method create the contact marker default with message type is email call"""
        from sosbeacon.event.message import create_marker_user

        event_key = self.event.key

        message_key = Mock()
        message_key.urlsafe.return_value = 'MESSAGE'
        message_key.get.return_value.message_type = 'ec'

        user_key = Mock()
        user_key.urlsafe.return_value = 'USER'
        user_key.get.return_value.name = 'longly'
        user_key.get.return_value.email= 'longly@cnc.vn'
        user_key.get.return_value.phone = '84973796065'

        create_marker_user(event_key, message_key, user_key)

        self.assertEqual(1, put_mock.call_count)
        self.assertEqual(1, insert_tasks_mock.call_count)


class TestGetGroupBroadcastTask(unittest.TestCase):
    """Test the get_broadcast_method_to_user_task method to ensure it returns a
    task with the proper settings.
    """
    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_name(self, task_mock):
        from sosbeacon.event.message import get_broadcast_method_to_user_task

        event_key = Mock()
        event_key.urlsafe.return_value = 'EVENT'

        message_key = Mock()
        message_key.urlsafe.return_value = 'MESSAGE'

        user_key = Mock()
        user_key.urlsafe.return_value = 'USER'

        method = 'longly@cnc.vn'

        get_broadcast_method_to_user_task(event_key, message_key, user_key, method)

        task_name = task_mock.call_args[1]['name']
        self.assertIn('USER', task_name)
        self.assertIn('MESSAGE', task_name)
        self.assertIn('EVENT', task_name)

    @patch('google.appengine.api.taskqueue.Task', autospec=True)
    def test_task_params(self, task_mock):
        from sosbeacon.event.message import get_broadcast_method_to_user_task

        event_key = Mock()
        event_key.urlsafe.return_value = 'EVENT'

        message_key = Mock()
        message_key.urlsafe.return_value = 'MESSAGE'

        user_key = Mock()
        user_key.urlsafe.return_value = 'USER'

        method = 'longly@cnc.vn'

        get_broadcast_method_to_user_task(event_key, message_key, user_key, method)

        check_params = {
            'user': 'USER',
            'event': 'EVENT',
            'message': 'MESSAGE',
            'method': 'longly@cnc.vn'
        }

        self.assertEqual(check_params, task_mock.call_args[1]['params'])