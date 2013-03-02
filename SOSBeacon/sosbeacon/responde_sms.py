import os
import sys

from skel.rest_api.rules import RestQueryRule
from skel.datastore import EntityBase

from google.appengine.ext import ndb

class Responder(EntityBase):
    """Represents a user."""

    _query_properties = {
        'name': RestQueryRule('n_', lambda x: x.lower() if x else ''),
        }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    contact_name = ndb.StringProperty('cn')
    contact_number = ndb.StringProperty('pn')
    url = ndb.StringProperty('ur')

    is_admin = ndb.BooleanProperty('ia')

    event = ndb.KeyProperty('e')
    contact_marker = ndb.KeyProperty('cm')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a User entity from a dict of values."""
        key = data.get('key')
        responder = None
        if key:
            responder = key.get()

        if not responder:
            responder = cls(namespace='_x_')

        responder.contact_name = data.get('contact_name')
        responder.contact_number = data.get('contact_number')
        responder.url = data.get('url')

        return responder

    def to_dict(self):
        """Return a User entity represented as a dict of values
        suitable for Responder.from_dict.
        """
        responder = self._default_dict()
        responder["version"] = self.version_
        responder['contact_name'] = self.contact_name
        responder['contact_number'] = self.contact_number
        responder['url'] = self.url
        responder['is_admin'] = self.is_admin
        responder['event'] = self.event.urlsafe()
        responder['contact_marker'] = self.contact_marker.urlsafe()

        return responder

    @classmethod
    def get_query_property(cls, prop):
        """Return the property to use in a query"""
        return cls._query_properties.get(prop)

def create_responder_student_sms(contact_number, short_id, url, event_key):
    from sosbeacon.event.contact_marker import ContactMarker

    marker_key = ndb.Key(
        ContactMarker, "%s:%s" % (event_key.id(), short_id),
        namespace='_x_')

    if not marker_key.get():
        raise Exception("ContactMarker key is required.")

    contact_name = marker_key.get().name
    contact_number = regex_phone(contact_number)

    responder = {
        'contact_name': contact_name,
        'contact_number': "+" + contact_number,
        'url': url,
        }
    entity = Responder.from_dict(responder)
    entity.event = event_key.get().key
    entity.contact_marker = marker_key
    entity.is_admin = False
    entity.put()

def create_responder_user_sms(user_number, user_name, url, event_key):

    user_number = regex_phone(user_number)

    responder = {
        'contact_name': user_name,
        'contact_number': "+" + user_number,
        'url': url,
        }
    entity = Responder.from_dict(responder)
    entity.event = event_key.get().key
    entity.contact_marker = None
    entity.is_admin = True
    entity.put()

def regex_phone(phone):
    import re
    p = re.compile(r"\D+")
    phone = p.sub("",phone)
    return phone

