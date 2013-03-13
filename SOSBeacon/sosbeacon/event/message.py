import logging
import os
import sys

from datetime import datetime

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from sosbeacon.error_log import create_error_log


USER_TX_ENDPOINT = '/task/event/tx/user'
USER_SEND_METHOD = '/task/event/tx/user/method'
USER_TX_QUEUE = "user-tx"

USER_ROBOCALL_EMAIL_ENDPOINT = '/task/event/tx/robocall'
USER_ROBOCALL_EMAIL_QUEUE = 'user-robocall'

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
    'feq_event': voluptuous.ndbkey(),
    'feq_user' : voluptuous.any(None, voluptuous.ndbkey(), '')
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

    # longitude and latitude of geo
    longitude = ndb.StringProperty()
    latitude = ndb.StringProperty()

#    audio path for each message
    link_audio = ndb.StringProperty(default='')

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
            event = event_key.get()
            event.total_comment += 1
            assert ['body'] == message_data.keys(), "Invalid comment payload."

        if message_type == 'b' or message_type == 'em' or\
           message_type == 'eo' or message_type == 'ec':
            assert ['sms', 'email'] == message_data.keys(),\
            "Invalid broadcast payload."

            # TODO: Ensure user is an admin.
            broadcast_message(event_key, message.key)

        message.user_name = data.get('user_name')
        message.user = data.get('user')

        message.longitude = data.get('longitude')
        message.latitude = data.get('latitude')

        message.message = message_data
        message.link_audio = data.get('link_audio')

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

        message['longitude'] = self.longitude
        message['latitude'] = self.latitude

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

    create_or_update_marker(event_key, student, message_key)


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
        event_key, student_key, message_key, contact, methods)

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
    from sosbeacon.event.contact_marker import ContactMarker
    from sosbeacon.event.student_marker import StudentMarker
    from sosbeacon.responde_sms import create_responder_student_sms
    from sosbeacon.responde_sms import create_responder_user_sms
    from sosbeacon.log import create_log

    message = message_key.get()
    event = event_key.get()

    encoded_event = utils.number_encode(event_key.id())
    encoded_method = utils.number_encode(short_id)

    host = os.environ['HTTP_HOST']

    url = "http://%s/e/%s/%s" % (host, encoded_event, encoded_method)

    message_log = message.to_dict()
    log_sms = message_log['message']['sms']
    log_email = message_log['message']['email']

    froms = message.user.get().email
    phones = message.user.get().phone
    user = message.user
    school = event.school

    if '@' not in method:
        if message.message_type == 'ec':
            text_message = "Message " + message.message['email']
            broadcast_call(method, text_message, message.link_audio)
            return

        if message.message_type == 'eo':
            return

        broadcast_sms(method, message, url, user.get().name, school.get().name)
        create_log(phones, method, 's', log_sms, user.get().name, school.get().name, url)

        if short_id == user.id():
            create_responder_user_sms(user.get().phone, user.get().name, url, event_key)
        else:
            create_responder_student_sms(method, short_id, url, event_key)

        return

    broadcast_email(method, message, url, user, school)
    create_log(froms, method, 'e', log_email, user.get().name, school.get().name, url)


def broadcast_sms(number, message, url, user_name, school_name):
    """Send a message to a given phone number."""
    from twilio.rest import TwilioRestClient
    import settings

    logging.debug('Sending notice to %s via twilio.', number)
    logging.info('Sending notice to %s via twilio.', number)

    body = message.message['sms']
    body = "Broadcast from %s (School %s). Link %s. Message: %s" % (user_name, school_name, url, body)

    client = TwilioRestClient(settings.TWILIO_ACCOUNT,
        settings.TWILIO_TOKEN)

    try:
        client.sms.messages.create(
            to="+%s" % (number), from_=settings.TWILIO_FROM, body=body)
    except:
        error = "The 'To' number %s is not a valid phone number" % number
        create_error_log(error, 'ERR')


def broadcast_email(address, message, url, user, school):
    """Send an email to a given email address."""

    logging.info('Sending notice to %s via mail api.', address)

    #    if message.message['title']:
    #        subject = message.message['title']
    #    else:
    if message.message_type == 'em':
        subject = "Emergency Alert from %s (%s)" % (user.get().name, school.get().name)
    else:
        subject = "School Notice message from %s (%s)" % (user.get().name, school.get().name)

    if message.message['email']:
        body = "%s (%s) sent a Event Broadcast. Detail here: %s. \nMessage: %s" %\
               (user.get().name, school.get().name, url, message.message['email'])
    else:
        body = "%s (%s) sent a Event Broadcast. Detail here: %s. \nMessage: %s" %\
               (user.get().name, school.get().name, url, message.message['sms'])

    #TODO: it might make sense to group emails as we can add more than one to
    # address per email sent
    import sendgrid
    import settings

    s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
        settings.SENDGRID_PASSWORD,
        secure=True)

    try:
        message = sendgrid.Message(
            user.get().email,
            subject,
            body,
            body)
        message.add_to(address)
        s.web.send(message)

    except:
        error = "The 'To' email %s is not a valid email" % address
        create_error_log(error, 'ERR')


def broadcast_call(number, text_message, play_audio):
    """Send a message to a given phone number."""
    from twilio.rest import TwilioRestClient
    import settings
    import urllib
    import re

    logging.debug('Call notice to %s via twilio.', number)

    client = TwilioRestClient(settings.TWILIO_ACCOUNT,
        settings.TWILIO_TOKEN)

    try:
        message = re.sub('<[^<]+?>', '', text_message)
        params = {'textMessage' : str(message)}
        broadcast_url = "http://4.sos-beacon-dev.appspot.com/broadcast/record?" + urllib.urlencode(params) + "&playUrl=" + play_audio
        client.calls.create(to = number,
            from_ = settings.TWILIO_FROM,
            url = broadcast_url,
            if_machine = 'Continue',
        )
    except:
        logging.info("call error")
        error = 'Can not make a call to phone number: %s' % number
        create_error_log(error, 'ERR')


def get_sendemail_user_task(event_key, message_key, user_urlsafe, school_urlsafe):
    """Insert a task to initiate the broadcast."""

    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    name = "u-%s-%s-%s" % (message_urlsafe, user_urlsafe, school_urlsafe)
    task = taskqueue.Task(
        url=USER_TX_ENDPOINT,
        name=name,
        params={
            'event': event_urlsafe,
            'message': message_urlsafe,
            'user': user_urlsafe,
            },
        countdown=2  # TODO: Need something better than this for sure.
    )
    taskqueue.Queue(name=USER_TX_QUEUE).add(task)


def create_marker_user(event_key, message_key, user_key):
    """Scan over the given set of groups, sending the broadcast to everyone
    in those groups.
    """
    from sosbeacon.utils import insert_tasks
    from sosbeacon.event.contact_marker import ContactMarker
    from sosbeacon.event.contact_marker import get_marker_for_methods
    from sosbeacon.student import Student
    from sosbeacon.student import DEFAULT_STUDENT_ID

    methods = set()
    if message_key.get().message_type == 'eo':
        methods.add(user_key.get().email)
    else:
        methods.add(user_key.get().phone)
        methods.add(user_key.get().email)

    marker = get_marker_for_methods(event_key, methods)

    student_key = ndb.Key(
        Student, "%s-%s" % (DEFAULT_STUDENT_ID, user_key.id()),
        namespace='_x_')

    if not marker:
        # TODO: What needs set?
        short_id = str(ContactMarker.allocate_ids(size=1, parent=event_key)[0])
        key_id = "%s:%s" % (event_key.id(), user_key.id())
        marker = ContactMarker(
            id=key_id,
            event=event_key,
            name=user_key.get().name,
            students={str(student_key.id()): []},
            short_id=short_id,
            methods=[user_key.get().email,user_key.get().phone],
            count_comment = 0,
            count_visit = 0,
            is_user = True
        )
        marker.acknowledged = True
        marker.put()

    tasks = []
    for method in methods:
        # TODO: Batch tasks or start
        tasks.append(
            get_broadcast_method_to_user_task(
                event_key, message_key, user_key, method))

        if len(tasks) > 10:
            insert_tasks(tasks, USER_TX_QUEUE)
            tasks = []

    if tasks:
        insert_tasks(tasks, USER_TX_QUEUE)


def get_broadcast_method_to_user_task(event_key, message_key, user_key, method):
    """Get a task to scan and broadcast messages to all students in group."""
    import hashlib

    user_urlsafe = user_key.urlsafe()
    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    method_ident = hashlib.sha1(method).hexdigest()

    name = "user-%s-%s-%s-%s" % (
        user_urlsafe, event_urlsafe, message_urlsafe, method_ident)
    return taskqueue.Task(
        url=USER_SEND_METHOD,
        name=name,
        params={
            'user': user_urlsafe,
            'event': event_urlsafe,
            'message': message_urlsafe,
            'method': method
        }
    )


def broadcast_email_robocall_task(message_key, event_key, batch_id=""):
    from sosbeacon.event.event import EVENT_STATUS_CLOSED
    from sosbeacon.event.event import EVENT_STATUS_SENT

    event_urlsafe = event_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    name = "tx-s-%s-%s" % (message_urlsafe, batch_id)
    task = taskqueue.Task(
        url=USER_ROBOCALL_EMAIL_ENDPOINT,
        name=name,
        params={
            'event': event_urlsafe,
            'message': message_urlsafe,
            'batch': batch_id
        },
        countdown=2  # TODO: Need something better than this for sure.
    )
    taskqueue.Queue(name=USER_ROBOCALL_EMAIL_QUEUE).add(task)


def send_email_robocall_to_user(message_key, event_key):
    from sosbeacon.event.contact_marker import ContactMarker
    import sendgrid
    import settings

    user_key = message_key.get().user
    message = message_key.get()

    logging.info('Sending notice to %s via mail api.', user_key.get().email)

    contact_markers = ContactMarker.query(ContactMarker.event == event_key)
    string_date = "%s %s, %s at %s:%s %s (GMT)" % (message.added.strftime("%B"), message.added.strftime("%d"),
                                                   message.added.strftime("%Y"),message.added.strftime("%I"),
                                                   message.added.strftime("%M"), message.added.strftime("%p"))

    subject = "School Beacon ROBOCALL service for alert %s was requested by you" % event_key.id()
    body = "School Beacon ROBOCALL service for alert <span style='color: red'>%s</span> was requested by you" % event_key.id()
    body = body + " on " + "<br><span style='color:red'>" + string_date + "</span>.<br><br>" + " The following numbers were called: <br>"

    for contact_marker in contact_markers:
        for method in contact_marker.methods:
            if '@' not in method:
                body += str(method) + '<br>'

    body += "<br><br>The following text was delivered:<br> <span style='color:red'>%s</span>" % message.message['email']

    s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
        settings.SENDGRID_PASSWORD,
        secure=True)

    email = sendgrid.Message(
        user_key.get().email,
        subject,
        body,
        body)
    email.add_to(user_key.get().email)
    s.web.send(email)
