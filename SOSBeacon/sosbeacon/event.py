from google.appengine.ext import ndb

import voluptuous

from . import EntityBase


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

