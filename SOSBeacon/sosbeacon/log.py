from google.appengine.ext import ndb
from skel.datastore import EntityBase

import voluptuous
import logging

from datetime import datetime

log_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'froms': basestring,
    'tos': basestring,
    'added': voluptuous.any(None, datetime, ''),
    'type': basestring,
    'message': basestring
}

log_query_schema = {
    'flike_froms': basestring,
    'flike_tos': basestring,
    'feq_type': basestring
}

class Log(EntityBase):
    #date occurs log
    added = ndb.DateTimeProperty('d', auto_now_add=True)
    #from email or phone
    froms = ndb.StringProperty('fr')
    #to email or phone
    tos = ndb.StringProperty('to')
    #message to be logged
    message = ndb.StringProperty(indexed=False)

    type = ndb.StringProperty('tp')

    school_name = ndb.StringProperty('sc')

    user_name = ndb.StringProperty('us')

    url = ndb.StringProperty('url')

    @classmethod
    def from_dict(cls, data):
        key = data.get("key")
        log = None

        if key:
            log = key.get()
        if not log:
            log = cls(namespace='_x_')

        log.froms = data.get('from')
        log.tos = data.get('to')

        log.message = data.get('message')
        log.type = data.get('type')

        log.user_name = data.get('user')
        log.school_name = data.get('school')

        log.url = data.get('url')

        to_put = [log]
        ndb.put_multi(to_put)

        return log

    def to_dict(self):
        if self.school_name:
            log = {
                'key': self.key.urlsafe(),
                'added': self.added.strftime("%Y-%m-%d %H:%M"),

                'from': self.froms,
                'to': self.tos,

                'message': self.user_name + " (" + self.school_name + ") " + " sent a broadcast." +
                           " </br>Message: " + self.message + " Detail here: " + "<a href=" + self.url + ">" + self.url + "</a>",
                'type': self.type,
                'url' : self.url
            }
        else:
            log = {
                'key': self.key.urlsafe(),
                'added': self.added.strftime("%Y-%m-%d %H:%M"),

                'from': self.froms,
                'to': self.tos,

                'message': "Admin School Beacon sent a email to: " + str(self.tos) +
                                                 " </br>Message: " + str(self.message),
                'type': self.type,
                'url' : self.url
            }

        return log


def log_send_email_admin(to, log_message, user_name):
    froms = 'sender@sosbeacon.org'
    type = 'e'
    create_log(froms, to, type, log_message, user_name, school=None, url=None)


def create_log(froms, tos, type, message, user, school, url):
    log = {
        'from' : froms,
        'to' : tos,
        'type' : type,
        'message' : message,
        'user' : user,
        'school' : school,
        'url' : url
    }
    Log.from_dict(log)
