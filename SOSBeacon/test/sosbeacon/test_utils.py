
import gaetest
import mock

from datetime import datetime


class TestNumberEncoding(gaetest.TestCase):
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


class TestInsertTasks(gaetest.TestCase):
    def test_insert_batch(self):
        """Ensure taskqueue.Queue.add is called exactly once."""
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        queue = mock.Mock()
        self.patch(taskqueue, 'Queue', queue)

        tasks = []
        for i in xrange(1, 10):
            tasks.append(object())
        added = insert_tasks(tasks, 'default')
        self.assertEqual(added, 9)

    def test_splits_once(self):
        """Ensure task batches are split and insertion is retried on
        TaskAlreadyExistsError.
        """
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        def side_effect(*args):
            if 2 in args[0]:
                raise taskqueue.TombstonedTaskError('uh oh')

        add = mock.Mock()
        add.side_effect = side_effect
        self.patch(taskqueue.Queue, 'add', add)

        tasks = [i for i in xrange(0, 9)]
        added = insert_tasks(tasks, 'default')

        self.assertEqual(added, 8)
        self.assertEqual(add.call_count, 7)

    def test_splits_on_tombstoned(self):
        """Ensure task batches are split and insertion is retried on
        TombstonedTaskError.
        """
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        add = mock.Mock()
        add.side_effect = taskqueue.TombstonedTaskError
        self.patch(taskqueue.Queue, 'add', add)

        tasks = [i for i in xrange(0, 7)]
        added = insert_tasks(tasks, 'default')

        self.assertEqual(added, 0)
        self.assertEqual(add.call_count, 13)

    def test_splits_on_taskexists(self):
        """Ensure task batches are split and insertion is retried on
        TaskAlreadyExistsError.
        """
        from google.appengine.api import taskqueue
        from sosbeacon.utils import insert_tasks

        add = mock.Mock()
        add.side_effect = taskqueue.TaskAlreadyExistsError
        self.patch(taskqueue.Queue, 'add', add)

        tasks = [i for i in xrange(0, 10)]
        added = insert_tasks(tasks, 'default')

        self.assertEqual(added, 0)
        self.assertEqual(add.call_count, 19)


class TestFormatDatetime(gaetest.TestCase):
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

