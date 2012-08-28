
from google.appengine.ext import ndb

import voluptuous

user_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
    'default': voluptuous.ndbkey(),
    'schools': [voluptuous.ndbkey()],
    'contact_info': [{'type': basestring, 'value': basestring}],
}

class User(ndb.Model):
    """Represents a user."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # The entity's change revision counter.
    revision = ndb.IntegerProperty('r_', default=0)

    # Useful timestamps.
    added = ndb.DateTimeProperty('a_', auto_now_add=True)
    modified = ndb.DateTimeProperty('m_', auto_now=True)

    # User
    user = ndb.UserProperty('u', indexed=False)

    # ToS Accepted
    tos_accepted = ndb.DateTimeProperty('tos', indexed=True)

    # User nick name, key
    name = ndb.StringProperty('n', indexed=False)
    n_ = ndb.ComputedProperty(lambda self: self.name.lower())

    # Associated school info.
    default_school = ndb.KeyProperty('dc', kind='School')
    schools = ndb.KeyProperty('cl', kind='School', repeated=True)

    # Phone / email / whatever.
    contact_info = ndb.JsonProperty('ci')

    def _pre_put_hook(self):
        """Ran before the entity is written to the datastore."""
        self.revision += 1

    @classmethod
    def from_dict(cls, data):
        """Instantiate a User entity from a dict of values."""
        key = data.get('key')
        user = None
        if key:
            user = key.get()

        if not user:
            user = cls()

        user.name = data.get('name')

        user.default_school = data.get('default')
        user.schools = data.get('schools')

        user.contact_info = data.get('contact_info')

        return user

    def to_dict(self):
        """Return a User entity represented as a dict of values
        suitable for User.from_dict.
        """
        user = {
            'version': self.version_,
            'key': self.key.urlsafe(),
            'revision': self.revision,
            'added': self.added.isoformat(' '),
            'modified': self.modified.isoformat(' '),

            # name
            'name': self.name,

            # school info
            'default': self.default_school.urlsafe(),
            'schools': [key.urlsafe() for key in self.schools],

            # Contact info
            'contact_info': self.contact_info,
        }
        return user


