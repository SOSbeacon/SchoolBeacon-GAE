
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule


school_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
    #'owner': voluptuous.ndbkey(),
    'invitations': [{
        'key': basestring,
        'name': basestring,
        'email': basestring
        }],
    #'users': [voluptuous.ndbkey()],
}

school_query_schema = {
    'flike_name': basestring,
}


class School(EntityBase):
    """Represents a school."""

    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower() if x else ''),
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # The entity's change revision counter.
    revision = ndb.IntegerProperty('r_', default=0)

    # Useful timestamps.
    added = ndb.DateTimeProperty('a_', auto_now_add=True)
    modified = ndb.DateTimeProperty('m_', auto_now=True)

    # User nick name, key
    name = ndb.StringProperty('n', indexed=False)
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

    # Associated user info.
    owner = ndb.KeyProperty('o', kind='User')
    users = ndb.KeyProperty('ul', kind='User', repeated=True)

    invitations = ndb.JsonProperty('ic')

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
            school = cls(namespace='_x_')

        school.name = data.get('name')

        #owner = data.get('owner')
        #if owner:
        #    school.owner = data.get('owner')

        #school.users = data.get('users')

        # Process invitations.
        raw_invitations = data.get('invitations')

        invitations = {}
        for invitation in raw_invitations:
            invitations[invitation['key']] = {
                'name': invitation.get('name'),
                'email': invitation.get('email'),
                'isnew': False
            }
            if invitation['isnew']:
                # TODO: Send invite email.
                # NOTE: Yes. I am a bad person for putting this here.
                pass

        school.invitations = invitations

        return school

    def to_dict(self):
        """Return a School entity represented as a dict of values
        suitable for School.from_dict.
        """
        invitations = []
        if self.invitations:
            for key, invitation in self.invitations.iteritems():
                invitations.append({
                    'key': key,
                    'name': invitation.get('name'),
                    'email': invitation.get('email'),
                    'isnew': False
                })

        school = {
            'version': self.version_,
            'key': self.key.urlsafe(),
            'revision': self.revision,
            'added': self.added.isoformat(' '),
            'modified': self.modified.isoformat(' '),

            # name
            'name': self.name,

            # user info
            'owner': self.owner.urlsafe() if self.owner else '',
            'users': [key.urlsafe() for key in self.users],

            # Invite tokens
            'invitations': invitations
        }
        return school

