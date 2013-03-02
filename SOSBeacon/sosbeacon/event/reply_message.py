import os
import sys
import voluptuous

from skel.rest_api.rules import RestQueryRule
from skel.datastore import EntityBase

from google.appengine.ext import ndb

reply_message_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'message': voluptuous.ndbkey(),
    'content': basestring,
}

reply_message_query_schema = {
    'feq_message' : voluptuous.ndbkey(),
}

class ReplyMessage(EntityBase):
    """Reply a Message."""

    _query_properties = {
        'name': RestQueryRule('n_', lambda x: x.lower() if x else ''),
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)
    content = ndb.StringProperty('ct')

    message = ndb.KeyProperty('m')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a User entity from a dict of values."""
        key = data.get('key')
        reply_message = None
        if key:
            reply_message = key.get()

        if not reply_message:
            reply_message = cls(namespace='_x_')

        reply_message.content = data.get('content')
        reply_message.message = data.get('message')

        return reply_message

    def to_dict(self):
        """Return a User entity represented as a dict of values
        suitable for Responder.from_dict.
        """
        reply_message = self._default_dict()
        reply_message["version"] = self.version_
        reply_message['content'] = self.content
        reply_message['message'] = self.message.urlsafe()

        return reply_message

    @classmethod
    def get_query_property(cls, prop):
        """Return the property to use in a query"""
        return cls._query_properties.get(prop)
