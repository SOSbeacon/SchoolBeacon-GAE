from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

ADMIN_GROUPS_ID = "admin__"
STAFF_GROUPS_ID = "staff__"

group_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
    'notes': basestring,
    'default': voluptuous.boolean(),
}

group_query_schema = {
    'flike_name': basestring,
    'feq_default': voluptuous.boolean(),
    'feq_school': voluptuous.ndbkey()
}


class Group(EntityBase):
    """Represents a group."""

    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower() if x else ''),
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # Useful timestamps.
    added = ndb.DateTimeProperty('a_', auto_now_add=True)
    modified = ndb.DateTimeProperty('m_', auto_now=True)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    school = ndb.KeyProperty('sc', kind='School')

    default = ndb.BooleanProperty('df', default=False)

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Group entity from a dict of values."""
        key = data.get("key")
        group = None
        if key:
            group = key.get()

        if not group:
            group = cls(namespace='_x_')

        group.name = data.get('name')
        group.school = data.get('school')

        return group

    def to_dict(self):
        """Return a Group entity represented as a dict of values
        suitable for Group.from_dict.
        """
        group = self._default_dict()
        group["version"] = self.version_
        group['name'] = self.name
        group['default_group'] = self.default

        number_student, next_curs, more = get_student_keys(self.key)
        group['number_student'] = len(number_student) + 1

        group['added'] = self.added.strftime('%Y-%m-%d %H:%M'),
        group['modified'] = self.modified.strftime('%Y-%m-%d %H:%M'),

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
