from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

contact_schema = {
    'key': basestring,
    'name': basestring,
    'students': list,
    'methods': list
}

contact_query_schema = {
    'flike_name': basestring,
    'feq_students': voluptuous.any('', voluptuous.ndbkey())
}

class Contact(EntityBase):
    """Represents a contact."""

    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower()),
        'students': RestQueryRule('students', lambda x: None if x == '' else x)
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    students = ndb.KeyProperty('s', repeated=True)
    methods = ndb.JsonProperty('m')

    def _pre_put_hook(self):
        """Ran before the entity is written to the datastore."""
        self.revision += 1

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Contact entity from a dict of values."""
        key = data.get("key")
        contact = None
        if key:
            key = ndb.Key(urlsafe=key)
            contact = key.get()

        if not contact:
            contact = cls()

        contact.name = data.get('name')
        contact.students = [ndb.Key(urlsafe=key)
            for key in data.get('students', [])]
        contact.methods = data.get('methods')

        return contact

    def to_dict(self):
        """Return a Contact entity represented as a dict of values
        suitable for contact.from_dict.
        """
        contact = self._default_dict()
        contact["version"] = self.version_
        contact['name'] = self.name

        contact['students'] = [key.urlsafe() for key in self.students]
        contact['methods'] = self.methods

        return contact
