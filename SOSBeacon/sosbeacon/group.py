from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

ALL_GROUPS_ID = "__all__"

group_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
    'active': voluptuous.boolean(),
    'notes': basestring
}

group_query_schema = {
    'flike_name': basestring,
    'feq_active': voluptuous.boolean()
}


class Group(EntityBase):
    """Represents a group."""

    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower() if x else ''),
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    active = ndb.BooleanProperty('a')

    notes = ndb.TextProperty('nt')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Group entity from a dict of values."""
        key = data.get("key")
        group = None
        if key:
            group = key.get()

        if not group:
            group = cls()

        group.name = data.get('name')
        group.active = data.get('active')
        group.notes = data.get('notes')

        return group

    def to_dict(self):
        """Return a Group entity represented as a dict of values
        suitable for Group.from_dict.
        """
        group = self._default_dict()
        group["version"] = self.version_
        group['name'] = self.name
        group['active'] = 'Yes' if self.active else ''
        group['notes'] = self.notes

        return group


def get_student_keys(group_key, cursor=None, batch_size=50):
    """Return the next batch of students in this group, insert continuation
    task if there are more to process for this batch.

    Returns a tuple of students, new cursor, more.
    """
    from sosbeacon.student import Student

    query = Student.query().order(Student.key)

    query = query.filter(Student.groups == group_key)

    start_cursor = ndb.Cursor(urlsafe=cursor)

    return query.fetch_page(
        batch_size, start_cursor=start_cursor, keys_only=True)

