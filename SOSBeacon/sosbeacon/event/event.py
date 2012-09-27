
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule


EVENT_CLOSED_STATUS = 'cl'
EVENT_DRAFT_STATUS = 'dr'
EVENT_SENT_STATUS = 'se'


event_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'closed': voluptuous.boolean(),
    'title': basestring,
    'status': basestring,
    'date': basestring,
    'last_broadcast_date': basestring,
    'groups': [voluptuous.ndbkey()],
    'type': voluptuous.any('e', 'n'),
    'counts': {
        'contacts': int,
        'students': int,
        'responses': int
    }
}

event_query_schema = {
    'flike_title': basestring,
    'feq_closed': voluptuous.boolean(),
    'feq_groups': voluptuous.any('', voluptuous.ndbkey())
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
        'closed': RestQueryRule('closed')
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    school = ndb.StringProperty('sch')

    title = ndb.StringProperty('t')
    title_ = ndb.ComputedProperty(lambda self: self.title.lower(), name='t_')

    event_type = ndb.StringProperty('et')
    date = ndb.DateTimeProperty('d')
    status = ndb.StringProperty('st', default='dr')

    content = ndb.TextProperty('c')

    groups = ndb.KeyProperty('g', repeated=True)

    student_count = ndb.IntegerProperty('sc', default=0, indexed=False)
    contact_count = ndb.IntegerProperty('cc', default=0, indexed=False)
    responded_count = ndb.IntegerProperty('rc', default=0, indexed=False)

    last_broadcast_date = ndb.DateTimeProperty('lb')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Event entity from a dict of values."""
        key = data.get("key")
        event = None
        if key:
            event = key.get()

        if not event:
            from google.appengine.api import namespace_manager
            school = namespace_manager.get_namespace()
            event = cls(namespace='_x_', school=unicode(school))

        event.title = data.get('title')
        event.event_type = data.get('type')
        event.date = data.get('date')

        status = data.get('status', EVENT_DRAFT_STATUS)
        if status == EVENT_CLOSED_STATUS:
            event.status = EVENT_CLOSED_STATUS

        event.content = data.get('content')
        event.groups = data.get('groups')

        return event

    def to_dict(self):
        """Return a Event entity represented as a dict of values
        suitable for Event.from_dict.
        """
        event = self._default_dict()
        event["version"] = self.version_

        event['title'] = self.title
        event['type'] = self.event_type
        event['date'] = self.date
        event['status'] = self.status

        event['content'] = self.content

        event['groups'] = [key.urlsafe() for key in self.groups]

        event['student_count'] = self.student_count
        event['contact_count'] = self.contact_count
        event['responded_count'] = self.responded_count

        event['last_broadcast_date'] = self.last_broadcast_date

        return event
