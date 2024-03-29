import logging

from google.appengine.ext import ndb

import webapp2

# NOTE: The Event model is imported here so the schema is loaded.
from sosbeacon.event.contact_marker import mark_as_acknowledged
from sosbeacon.event.contact_marker import merge_markers
from sosbeacon.event.contact_marker import update_marker

from sosbeacon.event.event import EVENT_STATUS_CLOSED
from sosbeacon.event.event import update_event_counts

from sosbeacon.event.message import broadcast_to_contact
from sosbeacon.event.message import broadcast_to_group
from sosbeacon.event.message import broadcast_to_groups
from sosbeacon.event.message import broadcast_to_method
from sosbeacon.event.message import broadcast_to_student

from sosbeacon.error_log import create_error_log

from sosbeacon.event.robocall import robocall_phone
from sosbeacon.event.robocall import robocall_start

class GroupsTxHandler(webapp2.RequestHandler):
    """Start the process of sending a message to every Contact associated
    with an Event.

    For each Group on an Event, insert a task that will sequentially scan the
    group inserting a send-message job for each contact, and an add-to-group
    message for each student.
    """
    def post(self):
        from google.appengine.api import namespace_manager

        # batch_id is used so that we can force resend of notices for an event.
        batch_id = self.request.get('batch', '')

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        message_urlsafe = self.request.get('message')
        if not message_urlsafe:
            logging.error('No message key given.')
            return

        # TODO: Use message id rather than key here for namespacing purposes?
        message_key = ndb.Key(urlsafe=message_urlsafe)

        # TODO: Check namespace here.
        current_namespae = unicode(namespace_manager.get_namespace())
        if message_key.namespace() != current_namespae:
            logging.error('Message %s not in namespace %s!',
                          message_key, current_namespae)
            return

        message = message_key.get()
        if not message:
            logging.error('Message %s not found!', message_key)
            return

        # We don't want to send the wrong message to the wrong groups.
        if message.event != event.key:
            logging.error('Message %s not belong to Event %s!',
                          message_key, event_key)
            return

        if message.message_type == 'c' :
            logging.error('Message %s is not a broadcast!', message_key)
            return

        broadcast_to_groups(event.groups, event_key, message_key, batch_id)


class GroupTxHandler(webapp2.RequestHandler):
    """Iterate over every Contact in a group, sending them the message.

    For each Student in the Group, insert a task to load the student, parse
    the Contacts, and send a message to every contact.
    """
    def post(self):
        from google.appengine.api import namespace_manager

        # batch_id is used so that we can force resend of notices for an event.
        batch_id = self.request.get('batch', '')

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        message_urlsafe = self.request.get('message')
        if not message_urlsafe:
            logging.error('No message key given.')
            return

        # TODO: Use message id rather than key here for namespacing purposes?
        message_key = ndb.Key(urlsafe=message_urlsafe)

        # TODO: Check namespace here.
        current_namespae = unicode(namespace_manager.get_namespace())
        if message_key.namespace() != current_namespae:
            logging.error('Message %s not in namespace %s!',
                          message_key, current_namespae)
            return

        message = message_key.get()
        if not message:
            logging.error('Message %s not found!', message_key)
            return

        # We don't want to send the wrong message to the wrong groups.
        if message.event != event.key:
            logging.error('Message %s not belong to Event %s!',
                          message_key, event_key)
            return

        if message.message_type == 'c' :
            logging.error('Message %s is not a broadcast!', message_key)
            return

        group_urlsafe = self.request.get('group')
        if not group_urlsafe:
            logging.error('No group key given.')
            return

        # TODO: Use group id rather than key here for namespacing purposes?
        group_key = ndb.Key(urlsafe=group_urlsafe)

        broadcast_to_group(group_key, event_key, message_key, batch_id)


class StudentTxHandler(webapp2.RequestHandler):
    """Iterate over every Contact on the Student, sending them the message.

    For each Contact on the Student, insert a task to send them a message, and
    create a method marker for each method.
    """
    def post(self):
        from google.appengine.api import namespace_manager

        # batch_id is used so that we can force resend of notices for an event.
        batch_id = self.request.get('batch', '')

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        message_urlsafe = self.request.get('message')
        if not message_urlsafe:
            logging.error('No message key given.')
            return

        # TODO: Use message id rather than key here for namespacing purposes?
        message_key = ndb.Key(urlsafe=message_urlsafe)

        # TODO: Check namespace here.
        current_namespae = unicode(namespace_manager.get_namespace())
        if message_key.namespace() != current_namespae:
            logging.error('Message %s not in namespace %s!',
                          message_key, current_namespae)
            return

        message = message_key.get()
        if not message:
            logging.error('Message %s not found!', message_key)
            return

        # We don't want to send the wrong message to the wrong groups.
        if message.event != event.key:
            logging.error('Message %s not belong to Event %s!',
                          message_key, event_key)
            return

        if message.message_type == 'c' :
            logging.error('Message %s is not a broadcast!', message_key)
            return

        student_urlsafe = self.request.get('student')
        if not student_urlsafe:
            logging.error('No student key given.')
            return

        # TODO: Use group id rather than key here for namespacing purposes?
        student_key = ndb.Key(urlsafe=student_urlsafe)

        broadcast_to_student(student_key, event_key, message_key, batch_id)


class ContactTxHandler(webapp2.RequestHandler):
    """Iterate over every method on the Contact, sending them the message.

    For each Method on the Contact, insert a task to send them a message, and
    create a method marker for each method.
    """
    def post(self):
        import json

        from google.appengine.api import namespace_manager

        # batch_id is used so that we can force resend of notices for an event.
        batch_id = self.request.get('batch', '')

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        message_urlsafe = self.request.get('message')
        if not message_urlsafe:
            logging.error('No message key given.')
            return

        # TODO: Use message id rather than key here for namespacing purposes?
        message_key = ndb.Key(urlsafe=message_urlsafe)

        # TODO: Check namespace here.
        current_namespae = unicode(namespace_manager.get_namespace())
        if message_key.namespace() != current_namespae:
            logging.error('Message %s not in namespace %s!',
                          message_key, current_namespae)
            return

        message = message_key.get()
        if not message:
            logging.error('Message %s not found!', message_key)
            return

        # We don't want to send the wrong message to the wrong groups.
        if message.event != event.key:
            logging.error('Message %s not belong to Event %s!',
                          message_key, event_key)
            return

        if message.message_type == 'c' :
            logging.error('Message %s is not a broadcast!', message_key)
            return

        student_urlsafe = self.request.get('student')
        if not student_urlsafe:
            logging.error('No student key given.')
            return

        # TODO: Use group id rather than key here for namespacing purposes?
        student_key = ndb.Key(urlsafe=student_urlsafe)

        contact = self.request.get('contact')
        if not contact:
            logging.error('No contact given.')
            return
        contact = json.loads(contact)

        broadcast_to_contact(event_key, message_key, student_key, contact,
                             batch_id)


class MethodTxHandler(webapp2.RequestHandler):
    """Sending the message to method."""
    def post(self):
        from google.appengine.api import namespace_manager

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        message_urlsafe = self.request.get('message')
        if not message_urlsafe:
            logging.error('No message key given.')
            return

        # TODO: Use message id rather than key here for namespacing purposes?
        message_key = ndb.Key(urlsafe=message_urlsafe)

        # TODO: Check namespace here.
        current_namespae = unicode(namespace_manager.get_namespace())
        if message_key.namespace() != current_namespae:
            logging.error('Message %s not in namespace %s!',
                          message_key, current_namespae)
            return

        message = message_key.get()
        if not message:
            logging.error('Message %s not found!', message_key)
            return

        # We don't want to send the wrong message to the wrong groups.
        if message.event != event.key:
            logging.error('Message %s not belong to Event %s!',
                          message_key, event_key)
            return

        if message.message_type == 'c' :
            logging.error('Message %s is not a broadcast!', message_key)
            return

        short_id = self.request.get('short_id')
        if not short_id:
            logging.error('No short_id given.')
            return
        short_id = int(short_id)

        method = self.request.get('method')
        if not method:
            logging.error('No method given.')
            return

        retry_count = int(
            self.request.headers.get('X-AppEngine-TaskRetryCount', 0))
        exec_count = int(
            self.request.headers.get('X-AppEngine-ExecutionCount', 0))

        if exec_count > 5 or retry_count > 10:
            logging.error('Too many failures sending to %s, aborting.', method)
            return

        broadcast_to_method(event_key, message_key, short_id, method)


class UpdateContactMarkerHandler(webapp2.RequestHandler):
    """Merge a contact's info into the contact marker."""
    def post(self):
        import json

        from google.appengine.api import namespace_manager

        marker_urlsafe = self.request.get('marker')
        if not marker_urlsafe:
            logging.error('No marker key given.')
            return

        # TODO: Use message id rather than key here for namespacing purposes?
        marker_key = ndb.Key(urlsafe=marker_urlsafe)

        # TODO: Check namespace here.
        current_namespae = unicode(namespace_manager.get_namespace())
        if marker_key.namespace() != current_namespae:
            logging.error('Marker %s not in namespace %s!',
                          marker_key, current_namespae)
            return

        marker = marker_key.get()
        if not marker:
            logging.error('Marker %s not found!', marker_key)
            return

        student_urlsafe = self.request.get('student')
        if not student_urlsafe:
            logging.error('No student key given.')
            return

        # TODO: Use student id rather than key here for namespacing purposes?
        student_key = ndb.Key(urlsafe=student_urlsafe)

        contact = self.request.get('contact')
        if not contact:
            logging.error('No contact given.')
            return
        contact = json.loads(contact)

        methods = self.request.get('methods')
        if not methods:
            logging.error('No methods given.')
            return
        methods = json.loads(methods)

        update_marker(marker_key, student_key, contact, methods)


class MergeContactMarkerHandler(webapp2.RequestHandler):
    """Merge a contact's info into the contact marker."""
    def post(self):
        import json

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        methods = self.request.get('methods')
        if not methods:
            logging.error('No methods given.')
            return
        methods = json.loads(methods)

        merge_markers(event_key, methods)


class AckContactMarkerHandler(webapp2.RequestHandler):
    """Ack contact marker."""
    def post(self):
        event_urlsafe = self.request.get('event')


        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if event.status == EVENT_STATUS_CLOSED:
            logging.error('Event %s closed!', event_key)
            return

        marker_urlsafe = self.request.get('marker')

        if not marker_urlsafe:
            logging.error('No marker key given.')
            return

        marker_key = ndb.Key(urlsafe=marker_urlsafe)

        mark_as_acknowledged(event_key, marker_key)


class UpdateEventCountsHandler(webapp2.RequestHandler):
    """Update the event's count totals."""
    def post(self):
        event_urlsafe = self.request.get('event')

        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        update_event_counts(event_key)


class UserTxHandler(webapp2.RequestHandler):
#    broadcast email to user
    def post(self):
        from sosbeacon.event.message import create_marker_user
        from sosbeacon.event.event import EVENT_STATUS_CLOSED

        event_urlsafe = self.request.get('event')
        user_urlsafe = self.request.get('user')
        message_urlsafe = self.request.get('message')

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

        user_key = ndb.Key(urlsafe = user_urlsafe)
        user = user_key.get()

        if not user:
            logging.error('User %s not found!', user_key)
            error = 'User %s not found!' % user_key
            create_error_log(error, 'ERR')
            return

        message_key = ndb.Key(urlsafe = message_urlsafe)
        message = message_key.get()

        if not message:
            logging.error('Message %s not found!', message_key)
            error = 'Message %s not found!' % message_key
            create_error_log(error, 'ERR')
            return

        create_marker_user(event_key, message_key, user_key)


class UserMethodTxHandler(webapp2.RequestHandler):
    def post(self):
        from sosbeacon.event.event import EVENT_STATUS_CLOSED

        event_urlsafe = self.request.get('event')
        user_urlsafe = self.request.get('user')
        message_urlsafe = self.request.get('message')
        method = self.request.get('method')

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

        user_key = ndb.Key(urlsafe = user_urlsafe)
        user = user_key.get()

        if not user:
            logging.error('User %s not found!', user_key)
            error = 'User %s not found!' % user_key
            create_error_log(error, 'ERR')
            return

        message_key = ndb.Key(urlsafe = message_urlsafe)
        message = message_key.get()

        if not message:
            logging.error('Message %s not found!', message_key)
            error = 'Message %s not found!' % message_key
            create_error_log(error, 'ERR')
            return

        broadcast_to_method(event_key, message_key, user_key.id(), method)


class EmailRobocallHander(webapp2.RequestHandler):
#    broadcast email to user
    def post(self):
        from sosbeacon.event.message import send_email_robocall_to_user
        from sosbeacon.event.event import EVENT_STATUS_CLOSED

        event_urlsafe = self.request.get('event')
        message_urlsafe = self.request.get('message')

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

        message_key = ndb.Key(urlsafe = message_urlsafe)
        message = message_key.get()

        if not message:
            logging.error('Message %s not found!', message_key)
            error = 'Message %s not found!' % message_key
            create_error_log(error, 'ERR')
            return

        send_email_robocall_to_user(message_key, event_key)


class RobocallStartHandler(webapp2.RequestHandler):
#    Robocall TWILIO
    def post(self):
        event_urlsafe = self.request.get('event')
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()

        if not event:
            logging.error('Event %s not found!', event_key)
            error = 'Event %s not found!' % event_key
            create_error_log(error, 'ERR')
            return

        is_direct = self.request.get('is_direct')
        robocall_start(event_urlsafe, is_direct)


class RobocallProcessHandler(webapp2.RequestHandler):

    def post(self):
        event_urlsafe = self.request.get('event')
        phone_markers = self.request.get('phone')
        message_urlsafe = self.request.get('message')
        timezone = self.request.get('timezone')

        robocall_phone(event_urlsafe, phone_markers, message_urlsafe, timezone)


class RobocallSentEmailHandler(webapp2.RequestHandler):
    def post(self):
        from sosbeacon.event.robocall import send_email_robocall_to_user

        event_urlsafe = self.request.get('event')
        user_urlsafe = self.request.get('user')
        message_urlsafe = self.request.get('message')
        phones = self.request.get_all('phones')

        send_email_robocall_to_user(event_urlsafe, user_urlsafe, message_urlsafe, phones)