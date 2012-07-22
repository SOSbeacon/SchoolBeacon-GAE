
import time

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import voluptuous

from sosbeacon.utils import insert_tasks

from . import EntityBase

BATCH_SECONDS = 5
EVENT_UPDATE_QUEUE = "event-up"
EVENT_UPDATE_WORKER_QUEUE = "event-updator"


def format_datetime(datetime):
    if not datetime:
        return ''

    if datetime.hour == 0 and datetime.minute == 0:
        return datetime.strftime('%m/%d/%y')

    return datetime.strftime('%m/%d/%y %H:%M')


event_schema = {
    'key': basestring,
    'active': voluptuous.boolean(),
    'title': basestring,
    'summary': basestring,
    'detail': basestring,
    'groups': [voluptuous.ndbkey()],
    'who_to_notify': voluptuous.any('a', 'd', 'p'),
    'response_wait_seconds': int,
}

class Event(EntityBase):
    """Represents a event."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    student_count = ndb.IntegerProperty('sc', default=0, indexed=False)
    contact_count = ndb.IntegerProperty('cc', default=0, indexed=False)
    acknowledged_count = ndb.IntegerProperty('ac', default=0, indexed=False)

    who_to_notify = ndb.StringProperty('who', indexed=False, default='')

    response_wait_seconds = ndb.IntegerProperty(default=3600, indexed=False)

    notice_sent_by = ndb.UserProperty('nsb')
    notice_sent_at = ndb.DateTimeProperty('nsa')
    notice_sent = ndb.BooleanProperty('ns')

    active = ndb.BooleanProperty('a')

    title = ndb.StringProperty('t')
    title_ = ndb.ComputedProperty(lambda self: self.title.lower(), name='t_')

    summary = ndb.TextProperty('s')
    detail = ndb.TextProperty('d')

    groups = ndb.KeyProperty('g', repeated=True)

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Event entity from a dict of values."""
        key = data.get("key")
        event = None
        if key:
            key = ndb.Key(urlsafe=key)
            event = key.get()

        if not event:
            event = cls()

        event.who_to_notify = data.get('who_to_notify')
        event.response_wait_seconds = data.get('response_wait_seconds')

        event.active = data.get('active')
        event.title = data.get('title')
        event.summary = data.get('summary')
        event.detail = data.get('detail')
        event.groups = data.get('groups')

        return event

    def to_dict(self):
        """Return a Event entity represented as a dict of values
        suitable for Event.from_dict.
        """
        event = self._default_dict()
        event["version"] = self.version_
        event['active'] = 'Yes' if self.active else ''
        event['notice_sent'] = 'Yes' if self.notice_sent else ''
        event['notice_sent_at'] = format_datetime(self.notice_sent_at)
        #TODO: set notice sent by to user
        #event['notice_sent_by'] = self.notice_sent_by
        event['title'] = self.title
        event['summary'] = self.summary
        event['detail'] = self.detail
        event['groups'] = [key.urlsafe() for key in self.groups]

        event['who_to_notify'] = self.who_to_notify
        event['response_wait_seconds'] = self.response_wait_seconds

        event['student_count'] = self.student_count
        event['contact_count'] = self.contact_count
        event['acknowledged_count'] = self.acknowledged_count

        return event


class MethodMarker(EntityBase):
    """Used to store Contact-Events tx / view metadata."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    acknowledged = ndb.BooleanProperty('a', default=False)
    acknowledged_at = ndb.IntegerProperty('at', indexed=False)

    last_try = ndb.IntegerProperty('t', indexed=False, default=0)
    students = ndb.JsonProperty('s', indexed=False)

    # This method is considered failed, suggest trying next method.
    try_next = ndb.BooleanProperty('n', default=False)

    def merge(self, other):
        """Merge this MethodMarker entity with another MethodMarker."""
        self.acknowledged = max(self.acknowledged, other.acknowledged)
        self.acknowledged_at = min(
            self.acknowledged_at or other.acknowledged_at,
            other.acknowledged_at or self.acknowledged_at)

        self.last_try = max(self.last_try, other.last_try)

        students = set()
        if self.students:
            for student, methods in self.students:
                students.add((student, tuple(methods)))
        if other.students:
            for student, methods in other.students:
                students.add((student, tuple(methods)))
        self.students = list(students)
        return self


class StudentMarker(EntityBase):
    """Used to store Student-Events tx / ack metadata."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n', indexed=False)
    contacts = ndb.JsonProperty('c')

    all_acknowledged = ndb.BooleanProperty('a', default=False)
    all_acknowledged_at = ndb.IntegerProperty('at', indexed=False)


def update_event_counts(event_key, group_key, group_iter,
                        contact_count, student_count):
    """Insert a task to apply count updates to the given event."""
    if isinstance(event_key, ndb.Key):
        event_key = event_key.urlsafe()

    task = taskqueue.Task(
        method="PULL",
        tag=event_key,
        params={
            'type': "cnt",
            'event': event_key,
            'contact_count': contact_count,
            'student_count': student_count,
            'group': group_key,
            'iter': group_iter
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)
    insert_event_updator(ndb.Key(urlsafe=event_key))


def try_next_contact_method(event_key, method, when):
    """Insert a task indicating the next contact method for contacts with
    method should be tried.
    """
    if isinstance(event_key, ndb.Key):
        event_key = event_key.urlsafe()

    task = taskqueue.Task(
        method="PULL",
        tag=event_key,
        params={
            'type': "ntxm",
            'event': event_key,
            'method': method,
            'when': when
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)
    insert_event_updator(ndb.Key(urlsafe=event_key))


def set_student_method_marker(event_key, method, student, methods):
    """Insert a task indicating the next contact method that should be tried
    for each student-contact.
    """
    import json
    if isinstance(event_key, ndb.Key):
        event_key = event_key.urlsafe()

    if isinstance(student, ndb.Key):
        student = student.urlsafe()

    task = taskqueue.Task(
        method="PULL",
        tag=event_key,
        params={
            'type': "idx",
            'event': event_key,
            'method': method,
            'student': student,
            'methods': json.dumps(methods)
        }
    )
    return task


def get_tx_worker_task(event_key, batch_id, method):
    """Get a task to send the notification to method."""
    import hashlib
    task = taskqueue.Task(
        method="POST",
        url='/task/event/tx/method',
        name="tx-%s-%s-%s" % (event_key.id(), batch_id, hashlib.sha1(method).hexdigest()),
        params={
            'event': event_key.urlsafe(),
            'method': method,
        }
    )
    return task


def get_try_next_method_task(event_urlsafe, batch_id, method):
    """Get a task to try sending notifications to the next contact method."""
    import hashlib
    task = taskqueue.Task(
        method="POST",
        url='/task/event/method/next',
        name="ntx-%s-%s-%s" % (event_urlsafe, batch_id, hashlib.sha1(method).hexdigest()),
        params={
            'event': event_urlsafe,
            'batch': batch_id,
            'method': method,
        }
    )
    return task

def update_event_contact(event_key, method, when):
    """Insert a task containing contact method details."""
    if isinstance(event_key, ndb.Key):
        event_key = event_key.urlsafe()

    task = taskqueue.Task(
        method="PULL",
        tag=event_key,
        params={
            'type': "tx",
            'event': event_key,
            'method': method,
            'when': when
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)
    insert_event_updator(ndb.Key(urlsafe=event_key))


def acknowledge_event(event_key, method):
    """Insert a task to acknowledge an event for the given contact."""
    ack_marker_key = "rx:%s:%s" % (event_key.id(), method)
    seen = memcache.get(ack_marker_key)
    if seen:
        return

    task = taskqueue.Task(
        method="PULL",
        tag=event_key.urlsafe(),
        params={
            'type': 'ack',
            'event': event_key.urlsafe(),
            'method': method,
            'when': int(time.time())
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)

    memcache.set(ack_marker_key, True)
    insert_event_updator(event_key)


def insert_event_updator(event_key):
    """Insert a task to aggregate and apply updates to the given event."""
    from time import time
    time_block = int(time() / BATCH_SECONDS)
    name = "up-%s-%s" % (event_key.id(), time_block)
    exists = memcache.get(name)
    if exists:
        return

    task = taskqueue.Task(
        url='/task/event/update',
        name=name,
        params={'event': event_key.urlsafe()}
    )
    insert_tasks((task,), EVENT_UPDATE_WORKER_QUEUE)

    memcache.set(name, True)


def send_notification(event, method):
    """Notify a contact of event information"""
    import logging
    #return

    import settings

    #TODO: enable twilio integration.
    if '@' not in method:
        logging.info('Sending notice to %s via twilio.', method)
        from twilio.rest import TwilioRestClient

        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        message = client.sms.messages.create(
            to="+%s" % (method), from_="+14155992671", body=event.summary)
        return


    logging.info('Sending notice to %s via mail api.', method)
    from google.appengine.api import mail

    message = mail.EmailMessage(sender="SOS Beacon <robert.kluin@ezoxsystems.com>",
                                        subject=event.title)

    message.to = method
    message.body = event.detail

    message.send()

    #TODO: enable sendgrid integration
    #TODO: it might make sense to group emails as we can add more than one to
    #address per email sent
    #import sendgrid
    #s = sendgrid.Sendgrid(
        #settings.SENDGRID_ACCOUNT, settings.SENDGRID_PASSWORD, secure=True)
    #message = sendgrid.Message(
        #'robert.kluin@ezoxsystems.com', event.summary, "plain body",
        #event.detail)
    #message.add_to("lyddonb@gmail.com", "Beau Lyddon")

    #s.web.send(message)

