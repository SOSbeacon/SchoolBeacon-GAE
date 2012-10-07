"""Assorted utility functions that are generally useful."""

import string


#  Functions used to encode numeric entity IDs with a url friendly alphabet.

ALPHABET = string.ascii_letters + string.digits + '-_$'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)


def number_encode(number):
    s = []
    while True:
        number, r = divmod(number, BASE)
        s.append(ALPHABET[r])
        if not number:
            break
    return ''.join(reversed(s))


def number_decode(encoded):
    number = 0
    for c in encoded:
        number = number * BASE + ALPHABET_REVERSE[c]
    return number


# Make a nice looking date.

def format_datetime(datetime):
    """If a datetime is really just a date, return a string representation
    of the date.
    """
    if not datetime:
        return ''

    if datetime.hour == 0 and datetime.minute == 0:
        return datetime.strftime('%m/%d/%y')

    return datetime.strftime('%m/%d/%y %H:%M')


# Compare two datetimes.

def get_latest_datetime(lhs, rhs):
    """Compare to datetimes, right-hand-side and left-hand-side, and return
    the most-recent (the greatest).
    """
    if not lhs:
        return rhs

    if not rhs:
        return lhs

    return max(lhs, rhs)


# Helper to auto-retry inserting tasks, should one fail.

def insert_tasks(tasks, queue_name=None):
    """Try inserting the given batch of tasks.

    If a Task Exists or Tombstoned Task error are raised, split the group
    in two and retry each half.  The exceptions that trigger the split
    are ignored.

    Returns the number of tasks successfully inserted.
    """
    from google.appengine.api import taskqueue

    batch_count = len(tasks)
    try:
        taskqueue.Queue(name=queue_name).add(tasks)
        return batch_count
    except (taskqueue.TombstonedTaskError,
            taskqueue.TaskAlreadyExistsError,
            taskqueue.BadTaskStateError):
        if batch_count <= 1:
            return 0

    midpoint = batch_count / 2
    actual_count = insert_tasks(tasks[:midpoint], queue_name)
    actual_count += insert_tasks(tasks[midpoint:], queue_name)
    return actual_count

