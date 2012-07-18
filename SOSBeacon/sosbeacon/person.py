from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule


person_schema = {
    'key': basestring,
    'name': basestring,
    'groups': list,
    'contacts': list
}

person_query_schema = {
    'flike_name': basestring,
    'feq_contacts': voluptuous.any('', voluptuous.ndbkey())
}

class Person(EntityBase):
    """Represents a person."""
    # Store the schema version, to aid in migrations.

    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower()),
        'contacts': RestQueryRule('contacts', lambda x: None if x == '' else x)
    }
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    groups = ndb.KeyProperty('g', repeated=True)
    contacts = ndb.KeyProperty('c', repeated=True)

    def _pre_put_hook(self):
        """Ran before the entity is written to the datastore."""
        self.revision += 1

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Person entity from a dict of values."""
        key = data.get("key")
        person = None
        if key:
            key = ndb.Key(urlsafe=key)
            person = key.get()

        if not person:
            person = cls()

        person.name = data.get('name')
        person.groups = [ndb.Key(urlsafe=key) for key in data.get('groups', [])]
        person.contacts = [ndb.Key(urlsafe=key)
            for key in data.get('contacts', [])]

        return person

    def to_dict(self):
        """Return a Person entity represented as a dict of values
        suitable for Person.from_dict.
        """
        person = self._default_dict()
        person["version"] = self.version_
        person['name'] = self.name

        person['groups'] = [key.urlsafe() for key in self.groups]
        person['contacts'] = [key.urlsafe() for key in self.contacts]

        return person
