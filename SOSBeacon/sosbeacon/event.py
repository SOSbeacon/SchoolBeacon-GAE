from google.appengine.ext import ndb

import voluptuous

from . import EntityBase


event_schema = {
    'key': basestring,
    'active': voluptuous.boolean(),
    'title': basestring,
    'summary': basestring,
    'detail': basestring,
    'groups': [voluptuous.ndbkey()]
}

class Event(EntityBase):
    """Represents a event."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

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

        return event

