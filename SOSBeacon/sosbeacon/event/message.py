import logging
from datetime import datetime

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase


GROUPS_TX_ENDPOINT = '/task/event/tx/start'
GROUP_TX_ENDPOINT = '/task/event/tx/group'
GROUP_TX_QUEUE = "group-tx"

STUDENT_TX_ENDPOINT = '/task/event/tx/student'
STUDENT_TX_QUEUE = "student-tx"

CONTACT_TX_ENDPOINT = '/task/event/tx/contact'
CONTACT_TX_QUEUE = "contact-tx"

METHOD_TX_ENDPOINT = '/task/event/tx/method'
METHOD_TX_QUEUE = "method-tx"

message_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'event': voluptuous.ndbkey(),
    'user': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'user_name': basestring,
    'timestamp': voluptuous.any(None, datetime, ''),
    'type': basestring,
    'message': {
        'message': basestring,
        'sms': basestring,
        'title': basestring,
        'email': basestring
    }
}

message_query_schema = {
    'feq_event': voluptuous.ndbkey()
}


class Message(EntityBase):
    """Represents a message in an event's message stream."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    event = ndb.KeyProperty('e')

    timestamp = ndb.DateTimeProperty('ts', auto_now_add=True)

    message_type = ndb.StringProperty('mt')
    message = ndb.JsonProperty('m')

    user = ndb.KeyProperty('u')
    user_name = ndb.StringProperty('un')
    is_admin = ndb.BooleanProperty('ia')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Message entity from a dict of values."""
        key = data.get("key")
        message = None
        if key:
            message = key.get()

        event_key = data.get('event')
        if not event_key:
            # TODO: Raise some other error type here?
            raise Exception("Event key is required.")

        if not message:
            from google.appengine.api import namespace_manager

            event = event_key.get()
            if not event:
                # TODO: Raise some other error type here?
                raise Exception("Event not found.")

            key_id = "%s:%s" % (event_key.id(),
                                cls.allocate_ids(size=1, parent=event_key)[0])
            message = cls(id=key_id, event=event.key)

        message_type = data.get('type')
        message.message_type = message_type

        message_data = data.get('message')
        if message_type == 'c':
            assert ['body'] == message_data.keys(), "Invalid comment payload."

        if message_type == 'b':
            assert ['sms', 'email', 'title'] == message_data.keys(),\
                "Invalid broadcast payload."

            # TODO: Ensure user is an admin.
            broadcast_message(event_key, message.key)

        message.user_name = data.get('user_name')
        message.user = data.get('user')

        message.message = message_data

        return message

    def to_dict(self):
        """Return a Message entity represented as a dict of values
        suitable for Message.from_dict.
        """
        message = self._default_dict()
        message["version"] = self.version_

        message['event'] = self.event.urlsafe()
        message['added'] = self.timestamp.strftime('%Y-%m-%d %H:%M')
        message['type'] = self.message_type
        message['message'] = self.message

        message['user_name'] = self.user_name or ''
        message['user'] = None
        message['is_admin'] = self.is_admin

        if self.user:
            message['user'] = self.user.urlsafe()

        return message


def broadcast_message(event_key, message_key, batch_id=""):
    """Insert a task to initiate the broadcast."""
    from sosbeacon.event.event import EVENT_STATUS_CLOSED
    from sosbeacon.event.event import EVENT_STATUS_SENT

    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    name = "tx-s-%s-%s" % (message_urlsafe, batch_id)
    task = taskqueue.Task(
        url=GROUPS_TX_ENDPOINT,
        name=name,
        params={
            'event': event_urlsafe,
            'message': message_urlsafe,
            'batch': batch_id
        },
        countdown=2  # TODO: Need something better than this for sure.
    )
    taskqueue.Queue(name=GROUP_TX_QUEUE).add(task)

    @ndb.transactional
    def update_event_status():
        event = event_key.get()

        if event.status != EVENT_STATUS_CLOSED:
            # Don't reopen the event if it is closed.
            event.status = EVENT_STATUS_SENT

        event.last_broadcast_date = datetime.now()

        event.put()

    update_event_status()


def broadcast_to_groups(group_keys, event_key, message_key, batch_id):
    """Scan over the given set of groups, sending the broadcast to everyone
    in those groups.
    """
    from sosbeacon.group import ADMIN_GROUPS_ID
    from sosbeacon.group import Group
    from sosbeacon.utils import insert_tasks

    # This is done to dedupe the group list, for better resilience.
    group_keys = list(set(group_keys))

    if len(group_keys) == 1 and group_keys[0].id() == ADMIN_GROUPS_ID:
        group_keys = Group.query().order(Group.key).iter(keys_only=True)

    tasks = []
    for group_key in group_keys:
        # TODO: Batch tasks or start
        tasks.append(
            get_group_broadcast_task(
                group_key, event_key, message_key, batch_id))

        if len(tasks) > 10:
            insert_tasks(tasks, GROUP_TX_QUEUE)
            tasks = []

    if tasks:
        insert_tasks(tasks, GROUP_TX_QUEUE)


def get_group_broadcast_task(group_key, event_key, message_key,
                             batch_id='', iteration=0, cursor=''):
    """Get a task to scan and broadcast messages to all students in group."""
    group_urlsafe = group_key.urlsafe()
    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    name = "tx-%s-%s-%s-%d" % (
        group_urlsafe, message_urlsafe, batch_id, iteration)
    return taskqueue.Task(
        url=GROUP_TX_ENDPOINT,
        name=name,
        params={
            'group': group_urlsafe,
            'event': event_urlsafe,
            'message': message_urlsafe,
            'batch': batch_id,
            'cursor': cursor.urlsafe() if cursor else '',
            'iter': iteration
        }
    )


def broadcast_to_group(group_key, event_key, message_key, batch_id='',
                       iteration=0, cursor=None):
    """Scan over people in the group, starting from cursor if provided,
    sending the broadcast to every contact.
    """
    from sosbeacon.group import get_student_keys
    from sosbeacon.utils import insert_tasks

    students, cursor, more = get_student_keys(group_key, cursor)

    if more:
        continuation = get_group_broadcast_task(
            group_key, event_key, message_key, batch_id, iteration + 1, cursor)

        insert_tasks((continuation,), GROUP_TX_QUEUE)

    tasks = []
    for student_key in students:
        task = get_student_broadcast_task(
            student_key, event_key, message_key, batch_id)
        if not task:
            continue

        tasks.append(task)

        if len(tasks) > 10:
            insert_tasks(tasks, STUDENT_TX_QUEUE)
            tasks = []

    if tasks:
        insert_tasks(tasks, STUDENT_TX_QUEUE)

    #update_event_counts(
    #    event_key, group_urlsafe, iteration,
    #    contact_count=len(self.seen_methods),
    #    student_count=len(students))


def get_student_broadcast_task(student_key, event_key, message_key,
                               batch_id=''):
    """Get a task to broadcast a message to all a student's contacts."""
    student_urlsafe = student_key.urlsafe()
    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    name = "tx-%s-%s-%s" % (
        student_urlsafe, message_urlsafe, batch_id)
    return taskqueue.Task(
        url=STUDENT_TX_ENDPOINT,
        name=name,
        params={
            'student': student_urlsafe,
            'event': event_urlsafe,
            'message': message_urlsafe,
            'batch': batch_id
        }
    )


def broadcast_to_student(student_key, event_key, message_key, batch_id=''):
    """Send broadcast to each of the student's contacts."""
    from sosbeacon.event.student_marker import create_or_update_marker
    from sosbeacon.student import Student  # Needed to load the entity.
    from sosbeacon.utils import insert_tasks

    student = student_key.get()

    if not student:
        # TODO: ?
        logging.info('Tried to broadcast %s to missing student %s.',
                     message_key.urlsafe(), student_key.urlsafe())
        return

    tasks = []

    #contacts = {}
    for contact in student.contacts:
        # TODO: Optimize task building with memcache markers to
        # avoid building tasks that already exist.

        task = get_contact_broadcast_task(
            event_key, message_key, student_key, contact, batch_id)

        if not task:
            continue

        tasks.append(task)

        # TODO: WTF is this?
        #contacts[contact['t']] = contact

    if tasks:
        insert_tasks(tasks, CONTACT_TX_QUEUE)

    create_or_update_marker(event_key, student)


def get_contact_broadcast_task(event_key, message_key, student_key, contact,
                               batch_id=''):
    """Get a task to broadcast a message to a contact."""
    import hashlib
    import json

    student_urlsafe = student_key.urlsafe()
    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    BROADCAST_TYPES = ('e', 't')

    methods = []
    for method in contact.get('methods', ()):
        method_type = method.get('type')
        value = method.get('value')

        if not value or method_type not in BROADCAST_TYPES:
            continue

        methods.append(value)

    if not methods:
        return

    contact_ident = hashlib.sha1('|'.join(sorted(methods))).hexdigest()

    name = "tx-%s-%s-%s-%s" % (
        student_urlsafe, message_urlsafe, batch_id, contact_ident)
    return taskqueue.Task(
        url=CONTACT_TX_ENDPOINT,
        name=name,
        params={
            'student': student_urlsafe,
            'event': event_urlsafe,
            'message': message_urlsafe,
            'batch': batch_id,
            'contact': json.dumps(contact)
        }
    )


def broadcast_to_contact(event_key, message_key, student_key, contact,
                         batch_id=''):
    """Insert tasks to send message to each contact method, and create a
    contact marker.
    """
    from sosbeacon.event.contact_marker import create_or_update_marker
    from sosbeacon.utils import insert_tasks

    SEARCH_TYPES = ('e', 't')

    # Find methods we want to query by.
    methods = set()
    for method in contact.get('methods', ()):
        method_type = method.get('type')
        value = method.get('value')

        if not value or method_type not in SEARCH_TYPES:
            continue

        methods.add(value)

    if not methods:
        return

    short_id = create_or_update_marker(
        event_key, student_key, contact, methods)

    method_tasks = []
    for method in methods:
        method_tasks.append(get_method_broadcast_task(
            event_key, message_key, short_id, method, batch_id))

    insert_tasks(method_tasks, METHOD_TX_QUEUE)


def get_method_broadcast_task(event_key, message_key, short_id, method,
                              batch_id=''):
    """Get a task to broadcast a message to a contact method."""
    import hashlib

    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    method_ident = hashlib.sha1(method).hexdigest()

    name = "tx-%s-%s-%s-%s" % (
        message_urlsafe, short_id, batch_id, method_ident)
    return taskqueue.Task(
        url=METHOD_TX_ENDPOINT,
        name=name,
        params={
            'message': message_urlsafe,
            'event': event_urlsafe,
            'batch': batch_id,
            'short_id': short_id,
            'method': method
        }
    )


def broadcast_to_method(event_key, message_key, short_id, method):
    """Send the message to the given contact method."""
    import os

    from sosbeacon import utils

    message = message_key.get()

    encoded_event = utils.number_encode(event_key.id())
    encoded_method = utils.number_encode(short_id)

    host = os.environ['HTTP_HOST']

    url = "http://%s/e/%s/%s" % (host, encoded_event, encoded_method)

    if '@' not in method:
        broadcast_sms(method, message, url)
        return

    broadcast_email(method, message, url)


def broadcast_sms(number, message, url):
    """Send a message to a given phone number."""
    from twilio.rest import TwilioRestClient

    import settings

    logging.debug('Sending notice to %s via twilio.', number)

    body = message.message['sms']
    body = "%s - %s" % (body, url)

    client = TwilioRestClient(settings.TWILIO_ACCOUNT,
                              settings.TWILIO_TOKEN)

    client.sms.messages.create(
        to="+%s" % (number), from_=settings.TWILIO_FROM, body=body)


def broadcast_email(address, message, url):
    """Send an email to a given email address."""

    logging.info('Sending notice to %s via mail api.', address)

    #sender = "SBeacon <noreply@sosbeacon.org>"
    sender = "noreply@sosbeacon.org"
    subject = message.message['title']

    body = "%s\n\n%s" % (message.message['email'], url)
    # App Engine Built In Email
    #from google.appengine.api import mail
    #email_message = mail.EmailMessage(sender=sender,
    #                                  subject=subject)

    #email_message.to = address

    #email_message.body = body

    #email_message.send()

    #TODO: it might make sense to group emails as we can add more than one to
    # address per email sent
    import sendgrid

    import settings

    s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
                          settings.SENDGRID_PASSWORD,
                          secure=True)

    message = sendgrid.Message(
        settings.SENDGRID_SENDER,
        subject,
        message.message['sms'],
        body)
    message.add_to(address)
    s.web.send(message)

