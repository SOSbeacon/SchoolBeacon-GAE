
import time

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import voluptuous

from sosbeacon.utils import insert_tasks

from . import EntityBase

BATCH_SECONDS = 5
EVENT_UPDATE_QUEUE = "event-up"
EVENT_UPDATE_WORKER_QUEUE = "event-updator"

event_schema = {
    'key': basestring,
    'active': voluptuous.boolean(),
    'title': basestring,
    'summary': basestring,
    'detail': basestring,
    'groups': [voluptuous.ndbkey()],
    'notify_primary_only': voluptuous.boolean(),
    'response_wait_seconds': int,
}

class Event(EntityBase):
    """Represents a event."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    contact_count = ndb.IntegerProperty(default=0, indexed=False)
    acknowledged_count = ndb.IntegerProperty(default=0, indexed=False)
    notify_primary_only = ndb.BooleanProperty('po', indexed=False, default=False)
    response_wait_seconds = ndb.IntegerProperty(default=3600, indexed=False)

    notice_sent_by = ndb.UserProperty('nsb')
    notice_sent_at = ndb.DateTimeProperty('nsa')
    notice_sent = ndb.BooleanProperty('ns')

    active = ndb.BooleanProperty('a')

    title = ndb.StringProperty('t')
    title_ = ndb.ComputedProperty(lambda self: self.title.lower(), name='t_')

    summary = ndb.TextProperty('s')
    detail = ndb.TextProperty('d')

    groups = ndb.KeyProperty('g', repeated=True)

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Event entity from a dict of values."""
        key = data.get("key")
        event = None
        if key:
            key = ndb.Key(urlsafe=key)
            event = key.get()

        if not event:
            event = cls()

        event.notify_primary_only = data.get('notify_primary_only')
        event.response_wait_seconds = data.get('response_wait_seconds')

        event.active = data.get('active')
        event.title = data.get('title')
        event.summary = data.get('summary')
        event.detail = data.get('detail')
        event.groups = data.get('groups')

        return event

    def to_dict(self):
        """Return a Event entity represented as a dict of values
        suitable for Event.from_dict.
        """
        event = self._default_dict()
        event["version"] = self.version_
        event['active'] = 'Yes' if self.active else ''
        event['notice_sent'] = 'Yes' if self.notice_sent else ''
        #event['notice_sent_at'] = self.notice_sent_at
        event['title'] = self.title
        event['summary'] = self.summary
        event['detail'] = self.detail
        event['groups'] = [key.urlsafe() for key in self.groups]

        event['contact_count'] = self.contact_count
        event['acknowledged_count'] = self.acknowledged_count
        event['notify_primary_only'] = self.notify_primary_only
        event['response_wait_seconds'] = self.response_wait_seconds

        return event


class EventMarker(EntityBase):
    """Used to store Contact-Events tx / view metadata."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    acknowledged = ndb.BooleanProperty('a', default=False)
    acknowledged_at = ndb.IntegerProperty('at', indexed=False)

    last_try = ndb.IntegerProperty('t', indexed=False, default=0)
    last_contact_method = ndb.IntegerProperty('m', indexed=False, default=-1)

    def merge(self, other):
        """Merge this EventMarker entity with another EventMarker."""
        self.acknowledged = max(self.acknowledged, other.acknowledged)
        self.acknowledged_at = min(
            self.acknowledged_at or other.acknowledged_at,
            other.acknowledged_at or self.acknowledged_at)

        self.last_try = max(self.last_try, other.last_try)
        self.last_contact_method = max(self.last_contact_method,
                                       other.last_contact_method)
        return self


def update_contact_counts(event_key, contact_count, group_key, group_task_no):
    """Insert a task to apply count updates to the given event."""
    task = taskqueue.Task(
        method="PULL",
        tag=event_key,
        params={
            'type': "cnt",
            'event': event_key,
            'contact_count': contact_count,
            'group': group_key,
            'task_no': group_task_no
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)
    insert_event_updator(ndb.Key(urlsafe=event_key))


def update_event_contact(event_key, contact_key, contact_method, when):
    """Insert a task containing contact method details."""
    task = taskqueue.Task(
        method="PULL",
        tag=event_key,
        params={
            'type': "tx",
            'event': event_key,
            'contact': contact_key,
            'method': contact_method,
            'when': when
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)
    insert_event_updator(ndb.Key(urlsafe=event_key))


def acknowledge_event(event_key, contact_key):
    """Insert a task to acknowledge an event for the given contact."""
    ack_marker_key = "rx:%s:%s" % (event_key.id(), contact_key.id())
    seen = memcache.get(ack_marker_key)
    if seen:
        return

    task = taskqueue.Task(
        method="PULL",
        tag=event_key.urlsafe(),
        params={
            'type': 'ack',
            'event': event_key.urlsafe(),
            'contact': contact_key.urlsafe(),
            'when': int(time.time())
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)

    memcache.set(ack_marker_key, True)
    insert_event_updator(event_key)


def insert_event_updator(event_key):
    """Insert a task to aggregate and apply updates to the given event."""
    from time import time
    time_block = int(time() / BATCH_SECONDS)
    name = "up-%s-%s" % (event_key.id(), time_block)
    exists = memcache.get(name)
    if exists:
        return

    task = taskqueue.Task(
        url='/task/event/update',
        name=name,
        params={'event': event_key.urlsafe()}
    )
    insert_tasks((task,), EVENT_UPDATE_WORKER_QUEUE)

    memcache.set(name, True)

