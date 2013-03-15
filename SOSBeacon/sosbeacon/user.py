
from google.appengine.ext import ndb

import voluptuous
import os
import uuid

from skel.rest_api.rules import RestQueryRule
from webapp2_extras import security

from .school import School

user_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
    # 'default_school': voluptuous.ndbkey(),
    'schools': [voluptuous.ndbkey()],
    # 'contacts': [{'type': basestring, 'value': basestring}],
    'email' : basestring,
    'phone' : basestring,
    'password' : basestring
}

user_query_schema = {
    'flike_name': basestring,
    'flike_phone': basestring,
    'flike_email': basestring,
    'feq_is_admin': voluptuous.boolean(),
    'feq_schools': voluptuous.any('', voluptuous.ndbkey()),
}

class User(ndb.Model):
    """Represents a user."""

    _query_properties = {
        'name': RestQueryRule('n_', lambda x: x.lower() if x else ''),
        'email': RestQueryRule('email', lambda x: x if x else ''),
        'phone': RestQueryRule('phone', lambda x: x if x else ''),
    }

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
#    default_school = ndb.KeyProperty('dc', kind='School')
    schools = ndb.KeyProperty('cl', kind='School', repeated=True)

    # Phone / email / whatever.
    # contacts = ndb.JsonProperty('ci')
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    password = ndb.StringProperty()

    is_admin = ndb.BooleanProperty(default=False)

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
            user = cls(namespace='_x_')

        user.name = data.get('name')

#        user.default_school = data.get('default')
        user.schools = data.get('schools')
        # user.contacts = data.get('contacts')
        user.email = data.get('email')
        user.phone = data.get('phone')

        return user

    def to_dict(self):
        """Return a User entity represented as a dict of values
        suitable for User.from_dict.
        """
        user = {
            'version': self.version_,
            'key': self.key.urlsafe(),
            'revision': self.revision,
            'added': self.added.strftime('%Y-%m-%d %H:%M'),
            'modified': self.modified.strftime('%Y-%m-%d %H:%M'),

            'name': self.name,

            # school info
            'schools': [key.urlsafe() for key in self.schools if key.get() != None],
            # 'default_school': self.default_school.urlsafe() if self.default_school else '',

            # Contact info
            'email' : self.email,
            'phone' : self.phone,
            # 'contacts': self.contacts if self.contacts else []
        }
        return user


    @classmethod
    def get_query_property(cls, prop):
        """Return the property to use in a query"""
        return cls._query_properties.get(prop)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
            The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)

def forgot_password(user):
    """reset password for user"""
    import settings
    import sendgrid

    new_password = uuid.uuid4().hex[:6]

    user.set_password(new_password)
    user.put()

    body = """
    Dear %s, Your login is email address: %s, Your password is: %s . All the best, SOSbeacon
    """ % (user.name, user.email, new_password)

    s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
        settings.SENDGRID_PASSWORD,
        secure=True)

    subject='Sbeacon - Your login details here'

    message = sendgrid.Message(
        settings.SENDGRID_SENDER,
        subject,
        body)
    message.add_to(str(user.email))
    s.web.send(message)


def send_invitation_email(name, email, password):
    """Send user and inviation to join the School Admins."""
    from google.appengine.api import mail
    import settings
    import sendgrid

    try:
        name = name.strip().split()[0]
    except IndexError:
        pass

    host = os.environ['HTTP_HOST']
    url = "http://%s" % (host)

    body = """
    Please DO NOT REPLY to this message - it is an automated email and your reply will not be
    received.
    -----------------------------------------------------------

    Hello %s,
      School Beacon Administrator at %s has created an account for you. You may
      now log in by clicking this link or copying and pasting it to your browser:
          - url: %s
          - Login account: %s
          - Password: %s

    Thanks and welcome to School Beacon,
    The School Beacon Team
    """ % (name, url, url, email, password)

    s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
        settings.SENDGRID_PASSWORD,
        secure=True)

    subject='School Beacon - New user login account'

    message = sendgrid.Message(
        settings.SENDGRID_SENDER,
        subject,
        body)
    message.add_to(str(email))
    s.web.send(message)