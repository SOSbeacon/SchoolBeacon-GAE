import logging
import hashlib
import re
import datetime

from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from sosbeacon.utils import insert_tasks
from sosbeacon.error_log import create_error_log

from .student_marker import StudentMarker
from .event import EVENT_STATUS_CLOSED

from settings import TWILIO_ACCOUNT
from settings import TWILIO_TOKEN
from settings import TWILIO_FROM

from twilio.rest import TwilioRestClient

ROBOCALL_START = '/task/event/robo/start'
ROBOCALL_PROCESS = '/task/event/robo/process'
ROBOCALL_SENTEMAIL_PROCESS = '/task/event/robo/sentemail'
ROBOCALL_QUEUE_NAME = "robocall"

def get_robocall_start_task(event_urlsafe, is_direct, batch_id=""):

    name = "rb-%s-%s" % (event_urlsafe,batch_id)

    task = taskqueue.Task(
        name = name,
        url = ROBOCALL_START,
        params={
            'event': event_urlsafe,
            'is_direct': is_direct
        }
    )
    taskqueue.Queue(name=ROBOCALL_QUEUE_NAME).add(task)

def robocall_start(event_key, is_direct, user_urlsafe):

    event_urlsafe = ndb.Key(urlsafe=event_key)
    event = event_urlsafe.get()

    if not event:
        logging.error('Event %s not found!', event_urlsafe)
        return

    if event.status == EVENT_STATUS_CLOSED:
        logging.error('Event %s closed!', event_urlsafe)
        return

    query = StudentMarker.query(StudentMarker.event == event_urlsafe,
                                StudentMarker.acknowledged == False,
                                StudentMarker.is_direct == is_direct)

    student_markers = query.fetch()
    logging.info(student_markers)

    tasks = []
    phones = []

    for student_marker in student_markers:
        for key, value in student_marker.contacts.iteritems():
            if value['methods'][2]['value']:
                phones.append(value['methods'][2]['value'])
            else:
                phones.append(value['methods'][1]['value'])

    phones = list(set(phones))

    for phone in phones:
        tasks.append(
            get_robocall_task(event_urlsafe, phone)
        )

        if len(tasks) > 10:
            insert_tasks(tasks, ROBOCALL_QUEUE_NAME)
            tasks = []

    if tasks:
        tasks.append(get_sent_email_task(event_urlsafe, user_urlsafe))
        insert_tasks(tasks, ROBOCALL_QUEUE_NAME)


def regex_phone(phone):
    p = re.compile(r"\D+")
    phone = p.sub("",phone)
    return phone


def get_robocall_task(event_key, phone):
    phone = regex_phone(phone)

    event_urlsafe = event_key.urlsafe()
    phone_task = hashlib.sha1(phone).hexdigest()
    name = "%s-%s" % (event_urlsafe, phone_task)

    return taskqueue.Task(
#        name = name,
        url = ROBOCALL_PROCESS,
        params={
            'event': event_urlsafe,
            'phone': phone
        }
    )


def get_sent_email_task(event_key, user_urlsafe):
    event_urlsafe = event_key.urlsafe()

    return taskqueue.Task(
        url = ROBOCALL_SENTEMAIL_PROCESS,
        params={
            'event': event_urlsafe,
            'user': user_urlsafe,
        }
    )


def robocall_phone(event_urlsafe, phone_markers):
    from .message import broadcast_call
    from .message import Message

    if not event_urlsafe:
        logging.error('No event key given.')
        return

    # TODO: Use event id rather than key here for namespacing purposes?
    event_key = ndb.Key(urlsafe=event_urlsafe)
    event = event_key.get()

    if not event:
        logging.error('Event %s not found!', event_key)
        error = 'Event %s not found!' % event_key
        create_error_log(error, 'ERR')
        return

    if event.status == EVENT_STATUS_CLOSED:
        logging.error('Event %s closed!', event_key)
        error = 'Event %s not found!' % event_key
        create_error_log(error, 'ERR')
        return

    if not phone_markers:
        logging.error('No phone marker given.')
        error = 'Event %s not found!' % event_key
        create_error_log(error, 'ERR')
        return

    list_broadcast = Message.query(Message.event == event_key,
                                   Message.message_type.IN(['b', 'eo', 'em', 'ec']))\
                            .order(Message.timestamp).fetch()

    last_broadcast = list_broadcast[-1]
    text_message = last_broadcast.user.get().name + " checked in " + last_broadcast.user.get().phone + ". Message " + last_broadcast.message['email']
    broadcast_call(phone_markers, text_message, last_broadcast.link_audio)


def send_email_robocall_to_user(event_urlsafe, user_urlsafe):
    from sosbeacon.event.contact_marker import ContactMarker
    import sendgrid
    import settings

    if not event_urlsafe:
        logging.error('No event key given.')
        return

    # TODO: Use event id rather than key here for namespacing purposes?
    event_key = ndb.Key(urlsafe=event_urlsafe)
    event = event_key.get()
    user_key = ndb.Key(urlsafe = user_urlsafe)
    user = user_key.get()

    if not event:
        logging.error('Event %s not found!', event_key)
        error = 'Event %s not found!' % event_key
        create_error_log(error, 'ERR')
        return

    if event.status == EVENT_STATUS_CLOSED:
        logging.error('Event %s closed!', event_key)
        error = 'Event %s not found!' % event_key
        create_error_log(error, 'ERR')
        return

    if not user:
        logging.error('User %s not found!', user_key)
        error = 'User %s not found!' % user_key
        create_error_log(error, 'ERR')
        return

    logging.info('Sending notice to %s via mail api.', user.email)

    contact_markers = ContactMarker.query(ContactMarker.event == event_key,
                                          ContactMarker.acknowledged == False)

    string_date = "%s %s, %s at %s:%s %s (GMT)" % (event.added.strftime("%B"), event.added.strftime("%d"),
                                                   event.added.strftime("%Y"),event.added.strftime("%I"),
                                                   event.added.strftime("%M"), event.added.strftime("%p"))

    subject = "School Beacon ROBOCALL service for alert %s was requested by you" % event_key.id()
    body = "School Beacon ROBOCALL service for alert <span style='color: red'>%s</span> was requested by you" % event_key.id()
    body = body + " on " + "<br><span style='color:red'>" + string_date + "</span>.<br><br>" + " The following numbers were called: <br>"

    for contact_marker in contact_markers:
        for method in contact_marker.methods:
            if '@' not in method:
                body += str(method) + '<br>'

    body += "<br><br>The following text was delivered:<br> <span style='color:red'>%s</span>" % event.content

    s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
        settings.SENDGRID_PASSWORD,
        secure=True)

    email = sendgrid.Message(
        user.email,
        subject,
        body,
        body)
    email.add_to(user.email)
    s.web.send(email)
