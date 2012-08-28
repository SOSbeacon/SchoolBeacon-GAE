
from google.appengine.ext import ndb

import voluptuous

school_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
    'owner': voluptuous.ndbkey(),
    'invited': [basestring],
    'users': [voluptuous.ndbkey()],
}

class School(ndb.Model):
    """Represents a school."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # The entity's change revision counter.
    revision = ndb.IntegerProperty('r_', default=0)

    # Useful timestamps.
    added = ndb.DateTimeProperty('a_', auto_now_add=True)
    modified = ndb.DateTimeProperty('m_', auto_now=True)

    # User nick name, key
    name = ndb.StringProperty('n', indexed=False)
    n_ = ndb.ComputedProperty(lambda self: self.name.lower())

    # Associated user info.
    owner = ndb.KeyProperty('o', kind='User')
    users = ndb.KeyProperty('ul', kind='User', repeated=True)

    invited = ndb.StringProperty('rtl', repeated=True)

    def _pre_put_hook(self):
        """Ran before the entity is written to the datastore."""
        self.revision += 1

    @classmethod
    def from_dict(cls, data):
        """Instantiate a School entity from a dict of values."""
        key = data.get('key')
        school = None
        if key:
            school = key.get()

        if not school:
            school = cls()

        school.name = data.get('name')

        school.owner = data.get('owner')
        school.users = data.get('users')

        school.invited = data.get('invited')

        return school

    def to_dict(self):
        """Return a School entity represented as a dict of values
        suitable for School.from_dict.
        """
        school = {
            'version': self.version_,
            'key': self.key.urlsafe(),
            'revision': self.revision,
            'added': self.added.isoformat(' '),
            'modified': self.modified.isoformat(' '),

            # name
            'name': self.name,

            # user info
            'owner': self.owner.urlsafe(),
            'users': [key.urlsafe() for key in self.users],

            # Invite tokens
            'invited': self.invited,
        }
        return school

