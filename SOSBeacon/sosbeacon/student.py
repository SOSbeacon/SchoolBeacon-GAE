from google.appengine.ext import ndb

import voluptuous

from . import EntityBase


student_schema = {
    'key': basestring,
    'name': basestring,
    'identifier': basestring,
    'groups': [voluptuous.ndbkey()],
    'contacts': [{
        'name': basestring,
        'notes': basestring,
        'methods': [{'type': basestring, 'value': basestring}]
    }]
}

class Student(EntityBase):
    """Represents a student."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    identifier = ndb.StringProperty('i')
    identifier_ = ndb.ComputedProperty(
        lambda self: self.identifier.lower(),
        name='i_')

    groups = ndb.KeyProperty('g', repeated=True)
    contacts = ndb.JsonProperty('c')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Student entity from a dict of values."""
        key = data.get("key")
        student = None
        if key:
            key = ndb.Key(urlsafe=key)
            student = key.get()

        if not student:
            student = cls()

        student.name = data.get('name')
        student.identifier = data.get('identifier')

        student.groups = data.get('groups')
        student.contacts = data.get('contacts')

        return student

    def to_dict(self):
        """Return a Student entity represented as a dict of values
        suitable for Student.from_dict.
        """
        student = self._default_dict()
        student["version"] = self.version_
        student['name'] = self.name
        student['identifier'] = self.identifier

        student['contacts'] = self.contacts if self.contacts else []
        student['groups'] = [key.urlsafe() for key in self.groups]

        return student

