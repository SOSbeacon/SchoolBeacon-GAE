from datetime import datetime

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule
from sosbeacon.group import Group


EVENT_STATUS_CLOSED = 'cl'
EVENT_STATUS_DRAFT = 'dr'
EVENT_STATUS_SENT = 'se'

EVENT_UPDATE_QUEUE = 'event-update'

EVENT_UPDATOR_ENDPOINT = '/task/event/update/event/counts'
EVENT_UPDATOR_QUEUE = 'event-updator'

COUNT_TYPE_MAP = {
    'student': 'student_count',
    'contact': 'contact_count',
    'ack': 'responded_count'
}


event_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'title': basestring,
    'status': voluptuous.any('', EVENT_STATUS_DRAFT, EVENT_STATUS_CLOSED,
                             EVENT_STATUS_SENT),
    'last_broadcast_date': voluptuous.any(None, basestring,
                                          voluptuous.datetime()),
    'groups': [voluptuous.ndbkey()],
    'school': voluptuous.ndbkey(),
    'type': voluptuous.any('e', 'n'),
    'counts': {
        'contacts': int,
        'students': int,
        'responses': int
    }
}

event_query_schema = {
    'flike_title': basestring,
    'feq_groups': voluptuous.any('', voluptuous.ndbkey()),
    'feq_school': voluptuous.ndbkey()
}


class Event(EntityBase):
    """Represents a event.

    Events store the main "page" content, and connect messages. Events get put
    into a special global namespace, `_x_`.  Their associated markers go into
    the corresponding school's namespace.
    """

    _query_properties = {
        'title': RestQueryRule('title_', lambda x: x.lower() if x else ''),
        'groups': RestQueryRule('groups', lambda x: None if x == '' else x),
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    title = ndb.StringProperty('t')
    title_ = ndb.ComputedProperty(lambda self: self.title.lower(), name='t_')

    event_type = ndb.StringProperty('et')
    message_type = ndb.StringProperty('mt')

    date = ndb.DateTimeProperty('d')
    status = ndb.StringProperty('st', default='dr')

    content = ndb.TextProperty('c')

    groups = ndb.KeyProperty('g', repeated=True)
    school = ndb.KeyProperty('sch', kind='School')

    student_count = ndb.IntegerProperty('sc', default=0, indexed=False)
    contact_count = ndb.IntegerProperty('cc', default=0, indexed=False)
    responded_count = ndb.IntegerProperty('rc', default=1, indexed=False)
    total_comment = ndb.IntegerProperty('tc', default=0)

    last_broadcast_date = ndb.DateTimeProperty('lb')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Event entity from a dict of values."""
        key = data.get("key")
        event = None
        if key:
            event = key.get()

        if not event:
            event = cls(namespace='_x_')

        event.title = data.get('title')
        event.event_type = data.get('event_type')

        if not event.date:
            event.date = datetime.utcnow()
        else:
            event.date = datetime.strptime(data.get('date'), "%Y-%m-%d %H:%M")

        status = data.get('status', EVENT_STATUS_DRAFT)
        if status == EVENT_STATUS_CLOSED:
            event.status = EVENT_STATUS_CLOSED

        if status == EVENT_STATUS_SENT:
            event.status = EVENT_STATUS_SENT

        event.content = data.get('content')
        if data.get('school'):
            event.school = data.get('school')

        groups = []
        for key in data.get('groups'):
            if isinstance(key, basestring):
                groups.append(ndb.Key(urlsafe=key))
                event.groups = list(set(groups))
            else:
                groups.append(key)
                event.groups = list(set(groups))

        if event.key and event.key.id():
            # This needs done in the handler.  We ca not do it in a hook, since
            # that would fire everytime we update stats.
            event_mc_key = 'Event:%s' % (int(event.key.id()),)
            memcache.delete(event_mc_key)

        return event

    def to_dict(self):
        """Return a Event entity represented as a dict of values
        suitable for Event.from_dict.
        """
        event = self._default_dict()
        event["version"] = self.version_

        event['title'] = self.title
        event['type'] = self.event_type
        event['message_type'] = self.message_type

        event['date'] = None
        if self.date:
            event['date'] = self.date.strftime('%Y-%m-%d %H:%M')

        event['status'] = self.status

        event['content'] = self.content

        event['groups'] = [key.urlsafe() for key in self.groups if key.get()]

        event['student_count'] = self.student_count
        event['contact_count'] = self.contact_count
        event['responded_count'] = self.responded_count

#        number_student, next_curs, more = total_comment(self.key)
#        event['total_comment'] = len(number_student)
        event['total_comment'] = self.total_comment

        event['last_broadcast_date'] = None
        if self.date:
            event['last_broadcast_date'] = self.date.strftime('%Y-%m-%d %H:%M')

        event['id'] = self.key.id()

        return event


def insert_count_update_task(event_key, source_key, message_key, count_type):
    """Inserts a marker in the event's queue and attempts to insert
    a worker to apply the update.
    """
    import time
    from .message import broadcast_email_robocall_task

    if count_type not in COUNT_TYPE_MAP:
        return

    event_key = event_key.urlsafe()
    source_key = source_key.urlsafe()

    try:
        taskqueue.add(
            queue_name=EVENT_UPDATE_QUEUE,
            method='PULL',
            tag=event_key,
            name="%s-%s-%s" % (count_type, event_key, source_key),
            params={'type': count_type, 'source': source_key}
        )
    except (taskqueue.TombstonedTaskError,
            taskqueue.TaskAlreadyExistsError):
        pass

    base_task_name = "counts-%s" % (event_key,)

    batch = memcache.get(base_task_name)
    if not batch:
        batch = 0

    task_name = "%s-%d-%s" % (base_task_name, int(time.time() / 20), batch)

    try:
        taskqueue.add(
            queue_name=EVENT_UPDATOR_QUEUE,
            url=EVENT_UPDATOR_ENDPOINT,
            name=task_name,
            countdown=20,
            params={
                'type': count_type,
                'source': source_key,
                'event': event_key
            }
        )
    except (taskqueue.TombstonedTaskError,
            taskqueue.TaskAlreadyExistsError):
        pass

    try:
        if message_key:
            if message_key.get():
                if message_key.get().message_type == 'ec':
                    event = ndb.Key(urlsafe = event_key)
                    broadcast_email_robocall_task(message_key, event)

    except (taskqueue.TombstonedTaskError,
            taskqueue.TaskAlreadyExistsError):
        pass


def update_event_counts(event_key):
    """Fetch work for this event and update the event counts."""

    event_key = event_key.urlsafe()

    base_task_name = "counts-%s" % (event_key,)
    memcache.incr(base_task_name, initial_value=0)

    queue = taskqueue.Queue(name=EVENT_UPDATE_QUEUE)

    work = queue.lease_tasks_by_tag(
        lease_seconds=20,
        max_tasks=250,
        tag=event_key,
        deadline=3
    )

    counts = _get_counts_from_work(work)

    _apply_count_updates(event_key, counts)

    queue.delete_tasks(work)


def _get_counts_from_work(work):
    """Parse the payloads from the tasks and return a count map."""
    counts = {
        'student_count': 0,
        'contact_count': 0,
        'responded_count': 0
    }
    for task in work:
        params = task.extract_params()

        count_type = COUNT_TYPE_MAP.get(params.get('type'))
        if not count_type:
            continue

        counts[count_type] += 1

    return counts


@ndb.transactional
def _apply_count_updates(event_key, counts):
    """Transactionally apply the count updates to the event entity."""
    event = ndb.Key(urlsafe=event_key).get()
    if not event:
        return

    event.student_count += counts['student_count']
    event.contact_count += counts['contact_count']
    event.responded_count += counts['responded_count']

    event.put()


def total_comment(event_key, cursor=None, batch_size=50):
    """count message of this event"""
    from .message import Message

    query = Message.query().order(Message.key)

    query = query.filter(Message.event == event_key, Message.message_type == 'c')

    start_cursor = ndb.Cursor(urlsafe=cursor)

    return query.fetch_page(
        batch_size, start_cursor=start_cursor, keys_only=True)