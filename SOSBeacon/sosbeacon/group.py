from google.appengine.ext import ndb

import voluptuous

from . import EntityBase


group_schema = {
    'key': basestring,
    'name': basestring,
    'active': voluptuous.boolean(),
    'notes': basestring
}

class Group(EntityBase):
    """Represents a group."""
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
            key = ndb.Key(urlsafe=key)
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
