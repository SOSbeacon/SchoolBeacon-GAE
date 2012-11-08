import datetime
import json
import logging


from google.appengine.ext import ndb

import webapp2
from webapp2_extras import sessions

from skel.rest_api import handler as rest_handler

from sosbeacon.event.contact_marker import ContactMarker
from sosbeacon.user import User


class ProcessMixin(object):

    def process(self, resource_id=None, *args, **kwargs):
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


def process_messages(request, schema, entity):
    from voluptuous import Schema

    obj = json.loads(request.body)
    schema = Schema(schema, extra=True)

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')
        logging.info(obj)

    message = entity.from_dict(obj)

    session_store = sessions.get_store()
    session = session_store.get_session()

    #get the user and add them to the message
    if "cm" in session:
        cm_id = session["cm"]
        cm_key = ndb.Key(
            ContactMarker, cm_id, namespace="_%s" % (session.get('n')))
        cm = cm_key.get()
        if cm:
            message.user_name = cm.name
    else:
        message.is_admin = True
        user_id = session.get('u')
        if user_id:
            message.user = ndb.Key(User, user_id, namespace='')
            user = message.user.get()
            if user:
                message.user_name = user.name

    message.put()
    return message


class MessageHandler(rest_handler.RestApiHandler):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema

        super(MessageHandler, self).__init__(
            Message, message_schema, request, response)

    def process(self, resource_id, *args, **kwargs):
        message = process_messages(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())


class MessageListHandler(rest_handler.RestApiListHandler):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema
        from sosbeacon.event.message import message_query_schema

        super(MessageListHandler, self).__init__(
            Message, message_schema, request, response,
            query_schema=message_query_schema)

    def process(self, resource_id, *args, **kwargs):
        message = process_messages(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())


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

    def process(self, resource_id, *args, **kwargs):
        if self.resource_is_all_groups(resource_id):
            return

        return super(GroupHandler, self).process(resource_id, *args, **kwargs)

    def delete(self, resource_id, *args, **kwargs):
        if self.resource_is_all_groups(resource_id):
            return

        return super(GroupHandler, self).delete(resource_id, *args, **kwargs)

    def resource_is_all_groups(self, resource_id):
        """Ensure they don't mess with the 'All Groups' group."""
        from sosbeacon.group import ALL_GROUPS_ID

        key = ndb.Key(urlsafe=resource_id)

        if key.id() == ALL_GROUPS_ID:
            return True


class GroupListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema
        from sosbeacon.group import group_query_schema

        super(GroupListHandler, self).__init__(
            Group, group_schema, request, response,
            query_schema=group_query_schema)


def process_school(request, schema, entity):
    from voluptuous import Schema

    obj = json.loads(request.body)
    schema = Schema(schema, extra=True)

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')
        logging.info(obj)

    school = entity.from_dict(obj)
    to_put = [school]

    if not obj.get('key'):
        # this is a new school. add the all groups group
        from sosbeacon.group import Group
        from sosbeacon.group import ALL_GROUPS_ID
        group = Group(key=ndb.Key(Group, ALL_GROUPS_ID,
                      namespace="_%s" % (school.key.id())),
                      active=True,
                      notes='This is a special group, it may not be removed.')
        group.name = "All Groups"
        group.active = True
        to_put.append(group)

    ndb.put_multi(to_put)

    return school


class SchoolHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.school import School
        from sosbeacon.school import school_schema

        super(SchoolHandler, self).__init__(
            School, school_schema, request, response)

    def process(self, resource_id, *args, **kwargs):
        message = process_school(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())


class SchoolListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.school import School
        from sosbeacon.school import school_schema
        from sosbeacon.school import school_query_schema

        super(SchoolListHandler, self).__init__(
            School, school_schema, request, response,
            query_schema=school_query_schema,
            query_options={'namespace': '_x_'})

    def process(self, resource_id, *args, **kwargs):
        message = process_school(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())


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


class ContactMarkerListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.event.contact_marker import marker_schema
        from sosbeacon.event.contact_marker import marker_query_schema

        super(ContactMarkerListHandler, self).__init__(
            ContactMarker, marker_schema, request, response,
            query_schema=marker_query_schema)


class StudentMarkerListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.event.student_marker import StudentMarker
        from sosbeacon.event.student_marker import marker_schema
        from sosbeacon.event.student_marker import marker_query_schema

        super(StudentMarkerListHandler, self).__init__(
            StudentMarker, marker_schema, request, response,
            query_schema=marker_query_schema)
