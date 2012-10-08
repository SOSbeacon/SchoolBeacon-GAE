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


class MessageHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema

        super(MessageHandler, self).__init__(
            Message, message_schema, request, response)


class MessageListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema
        from sosbeacon.event.message import message_query_schema

        super(MessageListHandler, self).__init__(
            Message, message_schema, request, response,
            query_schema=message_query_schema)


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


class SchoolHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.school import School
        from sosbeacon.school import school_schema

        super(SchoolHandler, self).__init__(
            School, school_schema, request, response)


class SchoolListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.school import School
        from sosbeacon.school import school_schema
        from sosbeacon.school import school_query_schema

        super(SchoolListHandler, self).__init__(
              School, school_schema, request, response,
              query_schema=school_query_schema,
              query_options={'namespace': '_x_'})


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

        from google.appengine.api import namespace_manager
        school = namespace_manager.get_namespace()
        school_filter = Event.school == unicode(school)

        # TODO: Lock event (or restrict some fields) if sending is in progress?
        super(EventListHandler, self).__init__(
            Event, event_schema, request, response,
            query_schema=event_query_schema,
            default_filters=(school_filter,),
            query_options={'namespace': '_x_'})


class EventStudentListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event import MethodMarker
        from sosbeacon.event import marker_schema
        from sosbeacon.event import marker_query_schema

        super(EventStudentListHandler, self).__init__(
            MethodMarker, marker_schema, request, response,
            query_schema=marker_query_schema)

    def post(self):
        self.error(405)
        return

    def put(self):
        self.error(405)
        return

    def delete(self):
        self.error(405)
        return


class EventStudentHandler(rest_handler.RestApiHandler):

    def __init__(self, request, response):
        from sosbeacon.event import MethodMarker
        from sosbeacon.event import marker_schema
        from sosbeacon.event import marker_query_schema

        # TODO: Lock event (or restrict some fields) if sending is in progress?
        super(EventListHandler, self).__init__(
            MethodMarker, marker_schema, request, response,
            query_schema=marker_query_schema)

    def post(self):
        self.error(405)
        return

    def put(self):
        self.error(405)
        return

    def delete(self):
        self.error(405)
        return

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

