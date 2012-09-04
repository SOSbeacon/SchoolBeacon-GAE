
import time

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from sosbeacon.utils import insert_tasks


BATCH_SECONDS = 5
EVENT_UPDATE_QUEUE = "event-up"
EVENT_UPDATE_WORKER_QUEUE = "event-updator"

EVENT_OPEN_STATUS = 'op'











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


def get_student_method_marker(event_key, method, methods, student, name=None):
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
            'contact_name': name if name else '',
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

def update_event_contact(event_key, method, when, short_id):
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
            'short_id': short_id,
            'when': when
        }
    )
    insert_tasks((task,), EVENT_UPDATE_QUEUE)
    insert_event_updator(ndb.Key(urlsafe=event_key))


def acknowledge_event(event_key, method_id):
    """Insert a task to acknowledge an event for the given contact."""
    ack_marker_key = "rx:%s:%s" % (event_key.id(), method_id)
    seen = memcache.get(ack_marker_key)
    if seen:
        return

    method_marker = MethodMarker.query(MethodMarker.short_id == method_id,
                                       namespace='_x_').get()
    if not method_marker:
        # TODO: Somehow retry this...
        return

    task = taskqueue.Task(
        method="PULL",
        tag=event_key.urlsafe(),
        params={
            'type': 'ack',
            'event': event_key.urlsafe(),
            'method': method_marker.key.id(),
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


def send_notification(event, method, short_id):
    """Notify a contact of event information"""
    import logging
    import os

    import settings

    from sosbeacon import utils

    host = os.environ['HTTP_HOST']
    encoded_event = utils.number_encode(event.key.id())
    encoded_method = utils.number_encode(short_id)

    url = "http://%s/e/%s/%s" % (host, encoded_event, encoded_method)

    if '@' not in method:
        logging.info('Sending notice to %s via twilio.', method)
        from twilio.rest import TwilioRestClient

        body = event.summary
        body = "%s - %s" % (body, url)

        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        message = client.sms.messages.create(
            to="+%s" % (method), from_="+14155992671", body=body)
        return


    logging.info('Sending notice to %s via mail api.', method)
    from google.appengine.api import mail

    message = mail.EmailMessage(sender="SBeacon <clifforloff@gmail.com>",
                                subject=event.title)

    message.to = method

    body = "%s\n\n%s" % (event.detail, url)
    message.body = body

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

