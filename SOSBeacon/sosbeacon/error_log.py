from google.appengine.ext import ndb
from skel.datastore import EntityBase

import voluptuous
import logging

from datetime import datetime

log_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'date': voluptuous.any(None, datetime, ''),
    'message': basestring,
    'event' : basestring
}

log_query_schema = {
    'feq_type': basestring
}

class ErrorLog(EntityBase):
    #date occurs log
    added = ndb.DateTimeProperty('d', auto_now_add=True)
    #error to be logged
    message = ndb.StringProperty('ms')

    event = ndb.StringProperty()

    @classmethod
    def from_dict(cls, data):
        key = data.get("key")
        error_log = None

        if key:
            error_log = key.get()
        if not error_log:
            error_log = cls(namespace='_x_')

        error_log.message = data.get('message')
        error_log.event = data.get('event')

        to_put = [error_log]
        ndb.put_multi(to_put)

        return error_log

    def to_dict(self):

        error_log = {
            'key': self.key.urlsafe(),
            'added': self.added.strftime("%Y-%m-%d %H:%M"),

            'message': self.message,
            'event' : self.event
        }
        return error_log


def create_error_log(message, event):
    error_log = {
        'message' : message,
        'event' : event
    }
    ErrorLog.from_dict(error_log)