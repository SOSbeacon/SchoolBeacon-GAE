from google.appengine.ext import ndb

from . import EntityBase


contact_schema = {
    'key': basestring,
    'name': basestring,
    'students': list,
    'methods': list
}

class Contact(EntityBase):
    """Represents a contact."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    students = ndb.KeyProperty('s', repeated=True)
    methods = ndb.JsonProperty('m')

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
