import datetime
import json
import logging

import webapp2

from skel.rest_api import handler as rest_handler


class ProcessMixin(object):

    def process(self, resource_id=None, *arg, **kwrgs):
        from voluptuous import Schema

        obj = json.loads(self.request.body)
        schema = Schema(self.schema, extra=True)
        try:
            obj = schema(obj)
        except:
            logging.exception('validation failed')
            logging.info(obj)

        entity = self.entity.from_dict(obj)
        entity.put()

        out = entity.to_dict()
        self.response.out.write(json.dumps(out))


class PersonHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.person import Person
        from sosbeacon.person import person_schema

        super(PersonHandler, self).__init__(
            Person, person_schema, request, response)


class PersonListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.person import Person
        from sosbeacon.person import person_schema
        from sosbeacon.person import person_query_schema

        super(PersonListHandler, self).__init__(
            Person, person_schema, request, response,
            query_schema=person_query_schema)


class ContactHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.contact import Contact
        from sosbeacon.contact import contact_schema

        super(ContactHandler, self).__init__(
            Contact, contact_schema, request, response)


class ContactListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.contact import Contact
        from sosbeacon.contact import contact_schema
        from sosbeacon.contact import contact_query_schema

        super(ContactListHandler, self).__init__(
            Contact, contact_schema, request, response,
            query_schema=contact_query_schema)


class StudentHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.student import Student
        from sosbeacon.student import student_schema

        super(StudentHandler, self).__init__(
            Student, student_schema, request, response)


class StudentListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.student import Student
        from sosbeacon.student import student_schema
        from sosbeacon.student import student_query_schema

        super(StudentListHandler, self).__init__(
            Student, student_schema, request, response,
            query_schema=student_query_schema)


class GroupHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema

        super(GroupHandler, self).__init__(
            Group, group_schema, request, response)


class GroupListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema
        from sosbeacon.group import group_query_schema

        super(GroupListHandler, self).__init__(
            Group, group_schema, request, response,
            query_schema=group_query_schema)


class EventHandler(rest_handler.RestApiHandler):

    def __init__(self, request, response):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema

        # TODO: Lock event (or restrict some fields) if sending is in progress?
        super(EventHandler, self).__init__(
            Event, event_schema, request, response)


class EventListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema
        from sosbeacon.event import event_query_schema

        # TODO: Lock event (or restrict some fields) if sending is in progress?
        super(EventListHandler, self).__init__(
            Event, event_schema, request, response,
            query_schema=event_query_schema)


    #def get(self, args):
        #if not args:
            #context = {}
            #context.update(self.request.params)
            #context['filter'] = "title_"

            #entities = list(request_query(self.entity, **context))
        #else:
            #from google.appengine.ext import ndb
            #keys = [ndb.Key(urlsafe=key) for key in args.split(',')]
            #entities = [entity.to_dict() if entity else None
                        #for entity in ndb.get_multi(keys)]

        #self.response.out.write(json.dumps(entities))

class SendEventHandler(webapp2.RequestHandler):
    def post(self):
        from google.appengine.api import taskqueue
        from google.appengine.ext import ndb

        from sosbeacon.event import Event

        event_key = self.request.get('event')
        if not event_key:
            self.error(404)
            return

        event_key = ndb.Key(urlsafe=event_key)

        @ndb.transactional
        def mark_as_sent():
            """Update the event to mark it as sent and track who sent it."""
            event = event_key.get()
            if not event or event.notice_sent:
                return

            #event.notice_sent_by = current user here.
            event.notice_sent_at = datetime.datetime.now()
            event.notice_sent = True

            event.put()

            taskqueue.add(
                url='/task/event/tx/start',
                params={'event': event_key.urlsafe()},
                transactional=True
            )

        mark_as_sent()

