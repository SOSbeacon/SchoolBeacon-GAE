import logging

from google.appengine.ext import ndb

import webapp2

# NOTE: The Event model is imported here so the schema is loaded.



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

        if event.closed:
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

        if message.message_type != 'b':
            logging.error('Message %s is not a broadcast!', message_key)
            return




    """

    def post(self):


            return


























    """
    def post(self):

        if not event_urlsafe:
            return

        event_key = ndb.Key(urlsafe=event_urlsafe)

            return




            return

            return

            return






            return






            return

        event = event_key.get()
        if not event:
            return
































