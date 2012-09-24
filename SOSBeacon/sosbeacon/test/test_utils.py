
import unittest

import mock

from datetime import datetime


class TestNumberEncoding(unittest.TestCase):
    def test_encoder(self):
        """Ensure encoder produces expected encoded output."""
        from sosbeacon.utils import number_encode

        number = 123
        encoded = number_encode(number)
        self.assertEqual(encoded, 'b6')

    def test_decoder(self):
        """Ensure decoded correctly decodes a known encoded number."""
        from sosbeacon.utils import number_decode

        encoded = 'b6'
        number = number_decode(encoded)
        self.assertEqual(number, 123)

    def test_inverse(self):
        """Ensure decode(encode(number)) == number over a range of numbers."""
        from sosbeacon.utils import number_decode
        from sosbeacon.utils import number_encode

        for number in range(0, 500000, 339):
            encoded = number_encode(number)
            decoded = number_decode(encoded)
            self.assertEqual(number, decoded)


class TestInsertTasks(unittest.TestCase):

    @mock.patch('google.appengine.api.taskqueue.Queue')
    def test_insert_batch(self, queue_mock):
        """Ensure taskqueue.Queue.add is called exactly once."""
        from sosbeacon.utils import insert_tasks

        tasks = []
        for i in xrange(1, 10):
            tasks.append(object())
        added = insert_tasks(tasks, 'default')
        self.assertEqual(added, 9)

    @mock.patch('google.appengine.api.taskqueue.Queue.add')
    def test_splits_once(self, queue_add_mock):
        """Ensure task batches are split and insertion is retried on
        TaskAlreadyExistsError.
        """
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        def side_effect(*args):
            if 2 in args[0]:
                raise taskqueue.TombstonedTaskError('uh oh')

        queue_add_mock.side_effect = side_effect

        tasks = [i for i in xrange(0, 9)]
        added = insert_tasks(tasks, 'default')

        self.assertEqual(added, 8)
        self.assertEqual(queue_add_mock.call_count, 7)

    @mock.patch('google.appengine.api.taskqueue.Queue.add')
    def test_splits_on_tombstoned(self, queue_add_mock):
        """Ensure task batches are split and insertion is retried on
        TombstonedTaskError.
        """
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        queue_add_mock.side_effect = taskqueue.TombstonedTaskError

        tasks = [i for i in xrange(0, 7)]
        added = insert_tasks(tasks, 'default')

        self.assertEqual(added, 0)
        self.assertEqual(queue_add_mock.call_count, 13)

    @mock.patch('google.appengine.api.taskqueue.Queue.add')
    def test_splits_on_taskexists(self, queue_add_mock):
        """Ensure task batches are split and insertion is retried on
        TaskAlreadyExistsError.
        """
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        queue_add_mock.side_effect = taskqueue.TaskAlreadyExistsError

        tasks = [i for i in xrange(0, 10)]
        added = insert_tasks(tasks, 'default')

        self.assertEqual(added, 0)
        self.assertEqual(queue_add_mock.call_count, 19)


class TestFormatDatetime(unittest.TestCase):
    def test_date(self):
        """Ensure a date with no hours / minutes is retuned as a date."""
        from sosbeacon.utils import format_datetime

        date = datetime(year=2012, month=8, day=30)
        encoded = format_datetime(date)
        self.assertEqual('08/30/12', encoded)

    def test_date_with_time(self):
        """Ensure a date with hours and minutes is retuned as a datetime."""
        from sosbeacon.utils import format_datetime

        date = datetime(year=2012, month=8, day=30, hour=7, minute=13)
        encoded = format_datetime(date)
        self.assertEqual('08/30/12 07:13', encoded)

    def test_date_with_zero_hours(self):
        """Ensure a date with minutes but no hours is retuned as a datetime."""
        from sosbeacon.utils import format_datetime

        date = datetime(year=2012, month=8, day=30, hour=0, minute=13)
        encoded = format_datetime(date)
        self.assertEqual('08/30/12 00:13', encoded)

    def test_date_with_zero_minutes(self):
        """Ensure a date with hours but no minutes is retuned as a datetime."""
        from sosbeacon.utils import format_datetime

        date = datetime(year=2012, month=8, day=30, hour=19, minute=0)
        encoded = format_datetime(date)
        self.assertEqual('08/30/12 19:00', encoded)

    def test_non_input(self):
        """Ensure a missing date returns the empty string."""
        from sosbeacon.utils import format_datetime

        encoded = format_datetime(None)
        self.assertEqual('', encoded)


class TestGetLatestDatetime(unittest.TestCase):
    def test_no_lhs(self):
        """Ensure a missing lhs returns rhs."""
        from sosbeacon.utils import get_latest_datetime

        lhs = None
        rhs = object()

        result = get_latest_datetime(lhs, rhs)

        self.assertIs(rhs, result)

    def test_no_rhs(self):
        """Ensure a missing lhs returns rhs."""
        from sosbeacon.utils import get_latest_datetime

        lhs = object()
        rhs = None

        result = get_latest_datetime(lhs, rhs)

        self.assertIs(lhs, result)

    def test_larger_lhs(self):
        """Ensure a missing lhs returns rhs."""
        from sosbeacon.utils import get_latest_datetime

        lhs = datetime(2012, 9, 20, 3, 45)
        rhs = datetime(2012, 9, 20, 2, 45)

        result = get_latest_datetime(lhs, rhs)

        self.assertIs(lhs, result)

    def test_larger_rhs(self):
        """Ensure a missing lhs returns rhs."""
        from sosbeacon.utils import get_latest_datetime

        lhs = datetime(2012, 9, 20, 2, 59)
        rhs = datetime(2012, 9, 20, 3, 00)

        result = get_latest_datetime(lhs, rhs)

        self.assertIs(rhs, result)

    def test_equal_inputs(self):
        """Ensure a missing lhs returns rhs."""
        from sosbeacon.utils import get_latest_datetime

        lhs = rhs = datetime(2012, 9, 20, 2, 59)

        result = get_latest_datetime(lhs, rhs)

        self.assertIs(rhs, result)
        self.assertIs(lhs, result)

