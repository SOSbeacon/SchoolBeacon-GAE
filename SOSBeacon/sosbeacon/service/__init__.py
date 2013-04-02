import datetime
import json
import logging
import re

from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers

import webapp2
from webapp2_extras import sessions

from skel.rest_api import handler as rest_handler

from sosbeacon.event.contact_marker import ContactMarker
from sosbeacon.user import User

from sosbeacon.error_log import create_error_log

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


class TimeZoneHandler(webapp2.RequestHandler):

    def get(self, resource_id, *args, **kwargs):
        session_store = sessions.get_store()
        session = session_store.get_session()

        session['tz'] = resource_id
        session_store.save_sessions(self.response)

        self.response.write(resource_id)


class SchoolRestApiListHandler(rest_handler.RestApiListHandler):
    """Filter student, group end event for current school which user choose"""
    def get(self, *args, **kwargs):
        from google.appengine.api import namespace_manager
        namespace_manager.set_namespace('_x_')

        session_store = sessions.get_store(request=self.request)
        session = session_store.get_session()

        if not 'u' in session:
            self.abort(403)
            return

        self.request.GET['feq_school'] = session.get('s')

        super(SchoolRestApiListHandler, self).get(
            self, *args, **kwargs)

    def process(self, resource_id, *args, **kwargs):
        from voluptuous import Schema
        from google.appengine.api import namespace_manager

        namespace_manager.set_namespace('_x_')

        session_store = sessions.get_store(request=self.request)
        session = session_store.get_session()

        if not 'u' in session:
            self.about(403)
            return

        obj = json.loads(self.request.body)
        schema = Schema(self.schema, extra=True)

        try:
            obj = schema(obj)
        except:
            logging.exception('validation failed')

        session_store = sessions.get_store()
        session = session_store.get_session()

        school_key = ndb.Key(urlsafe = session.get('s'))

        obj['school'] = school_key

        entity = self.entity.from_dict(obj)
        entity.put()

        self.write_json_response(entity.to_dict())


def process_messages(request, schema, entity):
    from voluptuous import Schema
    from sosbeacon.event.message import get_sendemail_user_task
    from sosbeacon.event.contact_marker import update_count_comment

    session_store = sessions.get_store()
    session = session_store.get_session()

    obj = json.loads(request.body)
    schema = Schema(schema, extra=True)

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')

    message = entity.from_dict(obj)
    to_put = [message]

    #get the user and add them to the message
    if obj['is_admin'] is True:
        message.is_admin = True
        user_id = session.get('u')
        if user_id:
            user_key = ndb.Key(urlsafe=user_id)
            user = user_key.get()
            message.user = user.key
            if user:
                if message.message_type == 'c':
                    marker_key = ndb.Key(
                        ContactMarker, "%s:%s" % (message.event.id(), user_key.id()),
                        namespace='_x_')
                    update_count_comment(marker_key)
                message.user_name = user.name
            else:
                message.user_name = "Guest"
        else:
            message.user_name = "Guest"

    else:
        if obj['is_student'] == True:
            cm_id = session["cm"]
            cm_key = ndb.Key( ContactMarker, cm_id, namespace='_x_')
            cm = cm_key.get()
            if cm:
                message.user_name = cm.name
                update_count_comment(cm_key)
            else:
                message.user_name = 'Guest'

        else:
            message.user_name = obj['user_name']

    event_key = message.event
    event = event_key.get()

    if message.message_type == 'em' or message.message_type == 'b':
        event.message_type = 'rc'

    if message.message_type != 'c':
        get_sendemail_user_task(message.event, message.key, session.get('u'), session.get('s'))

    to_put.append(event)
    to_put.append(message)
    ndb.put_multi(to_put)

    return message


class MessageHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema

        super(MessageHandler, self).__init__(
            Message, message_schema, request, response)

    def process(self, resource_id, *args, **kwargs):
        message = process_messages(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())

    def delete(self, resource_id, *args, **kwargs):
        self.update_total_message(resource_id)
        return super(MessageHandler, self).delete(resource_id, *args, **kwargs)

    def update_total_message(self, resource_id):
        message = ndb.Key(urlsafe = resource_id).get()

        event = message.event.get()
        event.total_comment -= 1
        event.put()


class MessageListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema
        from sosbeacon.event.message import message_query_schema

        super(MessageListHandler, self).__init__(
            Message, message_schema, request, response,
            query_schema=message_query_schema)

    def process(self, resource_id, *args, **kwargs):
        message = process_messages(self.request, self.schema, self.entity)

        if message is False:
            self.abort(403)
            return

        message = message.to_dict()

        session_store = sessions.get_store()
        session = session_store.get_session()
        if 'tz' in session:
            message['added'] = self.convertTimeZone(session.get('tz'), message['added'])
        else:
            message['added'] = self.convertTimeZone("America/Los_Angeles", message['added'])
        self.write_json_response(message)


class StudentHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.student import Student
        from sosbeacon.student import student_schema

        super(StudentHandler, self).__init__(
            Student, student_schema, request, response)

    def put(self, resource_id, *args, **kwargs):
        """edit contact student"""
        from voluptuous import Schema
        from sosbeacon.student import Student

        student_key = ndb.Key(urlsafe = resource_id)
        if student_key.get().is_direct:
            super(StudentHandler, self).put(self, *args, **kwargs)
            return

        obj = json.loads(self.request.body)
        schema = Schema(self.schema, extra=True)

        try:
            obj = schema(obj)
        except:
            logging.exception('validation failed')

        student = student_key.get().to_dict()
        if obj['contacts'][1]['name'] == '':
            obj['contacts'][1]['name'] = student['contacts'][1]['name']

        if obj['contacts'][1]['methods'][0]['value'] == obj['contacts'][1]['methods'][1]['value'] \
            == obj['contacts'][1]['methods'][2]['value'] == '':
                obj['contacts'][1]['methods'][0]['value'] = student['contacts'][1]['methods'][0]['value']
                obj['contacts'][1]['methods'][1]['value'] = student['contacts'][1]['methods'][1]['value']
                obj['contacts'][1]['methods'][2]['value'] = student['contacts'][1]['methods'][2]['value']

        student = Student.from_dict(obj)
        to_put = [student]
        ndb.put_multi(to_put)

        self.write_json_response(student.to_dict())


class StudentListHandler(SchoolRestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.student import Student
        from sosbeacon.student import student_schema
        from sosbeacon.student import student_query_schema

        super(StudentListHandler, self).__init__(
            Student, student_schema, request, response,
            query_schema=student_query_schema)

    def get(self, resource_id, *args, **kwargs):
        from sosbeacon.student import Student
        from sosbeacon.student import DEFAULT_STUDENT_ID

        session_store = sessions.get_store()
        session = session_store.get_session()

        if not 'u' in session:
            self.abort(403)
            return

        self.request.GET['feq_school'] = session.get('s')

        resources = self.query.fetch(
            self.entity, self.request.params, self.query_schema)

        response = [entity.to_dict() for entity in resources]

        user_key = ndb.Key(urlsafe = session.get('u'))

        student_key = ndb.Key(
            Student, "%s-%s" % (DEFAULT_STUDENT_ID, user_key.id()),
            namespace='_x_')

        if 'feq_is_direct' not in self.request.GET:
            response.insert(0, student_key.get().to_dict())
            self.changeTimezone(response)
            self.write_json_response(response)
            return

        if self.request.GET['feq_is_direct'] == 'false':
            self.changeTimezone(response)
            self.write_json_response(response)
            return

        response.insert(0, student_key.get().to_dict())

        self.changeTimezone(response)
        self.write_json_response(response)


def process_group(request, schema, entity):
    from voluptuous import Schema
    from sosbeacon.group import Group

    session_store = sessions.get_store()
    session = session_store.get_session()

    if not 'u' in session:
        return False

    if not 's' in session:
        return False

    obj = json.loads(request.body)
    schema = Schema(schema, extra=True)

    if obj['name'] == '':
        return False

    #check group duplicate
    group_name = obj['name'].lower()
    school_key = ndb.Key(urlsafe = session.get('s'))

    check_name = Group.query(Group.name_ == group_name, Group.school == school_key, namespace = '_x_')

    if check_name.get():
        return False

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')
        logging.info(obj)

    obj['school'] = school_key

    group = entity.from_dict(obj)
    to_put = [group]
    ndb.put_multi(to_put)

    return group


class GroupHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema
        from google.appengine.api import namespace_manager
        namespace_manager.set_namespace('_x_')

        super(GroupHandler, self).__init__(
            Group, group_schema, request, response)

    def process(self, resource_id, *args, **kwargs):
        if self.resource_is_all_groups(resource_id):
            self.abort(400)
            return

        group = process_group(self.request, self.schema, self.entity)

        if group is False:
            self.abort(400)
            return

        group = group.to_dict()

        session_store = sessions.get_store()
        session = session_store.get_session()
        if 'tz' in session:
            group['added'] = self.convertTimeZone(session.get('tz'), group['added'])
            group['modified'] = self.convertTimeZone(session.get('tz'), group['modified'])
        else:
            group['added'] = self.convertTimeZone("America/Los_Angeles", group['added'])
            group['modified'] = self.convertTimeZone("America/Los_Angeles", group['modified'])

        self.write_json_response(group)

    def delete(self, resource_id, *args, **kwargs):
        if self.resource_is_all_groups(resource_id):
            self.abort(400)
            return

        return super(GroupHandler, self).delete(resource_id, *args, **kwargs)

    def resource_is_all_groups(self, resource_id):
        """Ensure they don't mess with the 'All Groups' group."""
        from sosbeacon.group import ADMIN_GROUPS_ID
        from sosbeacon.group import STAFF_GROUPS_ID

        key = ndb.Key(urlsafe=resource_id)

        session_store = sessions.get_store()
        session = session_store.get_session()

        school_key = ndb.Key(urlsafe = session.get('s'))

        if key.id() == (ADMIN_GROUPS_ID + "%s" % school_key.id()) \
            or (key.id() == STAFF_GROUPS_ID + "%s" % school_key.id()):
            return True


class GroupListHandler(SchoolRestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema
        from sosbeacon.group import group_query_schema

        from google.appengine.api import namespace_manager
        namespace_manager.set_namespace('_x_')

        super(GroupListHandler, self).__init__(
            Group, group_schema, request, response,
            query_schema=group_query_schema)

    def process(self, resource_id, *args, **kwargs):
        group = process_group(self.request, self.schema, self.entity)

        if group is False:
            self.abort(400)
            return

        group = group.to_dict()

        session_store = sessions.get_store()
        session = session_store.get_session()
        if 'tz' in session:
            group['added'] = self.convertTimeZone(session.get('tz'), group['added'])
            group['modified'] = self.convertTimeZone(session.get('tz'), group['modified'])
        else:
            group['added'] = self.convertTimeZone("America/Los_Angeles", group['added'])
            group['modified'] = self.convertTimeZone("America/Los_Angeles", group['modified'])

        self.write_json_response(group)

    def get(self, resource_id, *args, **kwargs):
        from sosbeacon.group import Group
        from sosbeacon.group import ADMIN_GROUPS_ID
        from sosbeacon.group import STAFF_GROUPS_ID

        session_store = sessions.get_store()
        session = session_store.get_session()

        if not 'u' in session:
            self.abort(403)
            return

        self.request.GET['feq_school'] = session.get('s')
        self.request.GET['feq_default'] = 'false'

        resources = self.query.fetch(
            self.entity, self.request.params, self.query_schema)

        response = [entity.to_dict() for entity in resources]

        school_key = ndb.Key(urlsafe = session.get('s'))

        group_admin_key = ndb.Key(
            Group, ADMIN_GROUPS_ID + "%s" % (school_key.id()),
            namespace='_x_')

        group_staff_key = ndb.Key(
            Group, STAFF_GROUPS_ID + "%s" % (school_key.id()),
            namespace='_x_')

        response.insert(0, group_admin_key.get().to_dict())
        response.insert(1, group_staff_key.get().to_dict())

        self.changeTimezone(response)
        self.write_json_response(response)


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
        from sosbeacon.group import ADMIN_GROUPS_ID
        from sosbeacon.group import STAFF_GROUPS_ID

        group_admin = Group(key=ndb.Key(Group, ADMIN_GROUPS_ID + "%s" % (school.key.id()),
            namespace="_x_"))
        group_admin.name = "Admin"
        group_admin.school = school.key
        group_admin.default = True

        group_staff = Group(key=ndb.Key(Group, STAFF_GROUPS_ID + "%s" % (school.key.id()),
            namespace="_x_"))
        group_staff.name = "Staff"
        group_staff.school = school.key
        group_staff.default = True

        to_put.append(group_admin)
        to_put.append(group_staff)

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
        school = process_school(self.request, self.schema, self.entity)
        self.write_json_response(school.to_dict())


class EventHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema

        # TODO: Lock event (or restrict some fields) if sending is in progress?
        super(EventHandler, self).__init__(
            Event, event_schema, request, response)


class EventListHandler(SchoolRestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema
        from sosbeacon.event import event_query_schema

        # TODO: Lock event (or restrict some fields) if sending is in progress?
        super(EventListHandler, self).__init__(
            Event, event_schema, request, response,
            query_schema=event_query_schema,
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


class UpdateUserVisitsHandler(webapp2.RequestHandler):
    """Update visits count of current user"""
    def post(self, resource_id, *args, **kwargs):
        """"""
        from sosbeacon.event.event import Event
        event_key = ndb.Key(urlsafe = resource_id)
        if not event_key.get():
            return

        session_store = sessions.get_store()
        session = session_store.get_session()

        user_key = ndb.Key(urlsafe = session.get('u'))
        if not user_key.get():
            self.abort(403)
            return

        marker = ndb.Key(
            ContactMarker, "%s:%s" % (event_key.id(), user_key.id()),
            namespace='_x_').get()

        if marker:
            marker.count_visit += 1
            marker.put()


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


class ReplyMessageHandler(rest_handler.RestApiHandler):

    def __init__(self, request, response):
        from sosbeacon.event.reply_message import ReplyMessage
        from sosbeacon.event.reply_message import reply_message_schema

        super(ReplyMessageHandler, self).__init__(
            ReplyMessage, reply_message_schema, request, response)


class ReplyMessageListHandler(rest_handler.RestApiListHandler):

    def __init__(self, request, response):
        from sosbeacon.event.reply_message import ReplyMessage
        from sosbeacon.event.reply_message import reply_message_schema
        from sosbeacon.event.reply_message import reply_message_query_schema

        super(ReplyMessageListHandler, self).__init__(
            ReplyMessage, reply_message_schema, request, response,
            query_schema=reply_message_query_schema)


class StudentRobocallHandler(rest_handler.RestApiListHandler, ProcessMixin):
    """Make a robocall for student contact"""
    def __init__(self, request, response):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema
        from sosbeacon.event import event_query_schema

        super(StudentRobocallHandler, self).__init__(
            Event, event_schema, request, response,
            query_schema=event_query_schema)

    def process(self, resource_id, *args, **kwargs):
        from sosbeacon.event.robocall import robocall_start
        session_store = sessions.get_store()
        session = session_store.get_session()

        user_key = ndb.Key(urlsafe=session.get('u'))
        if not user_key.get():
            return

        is_direct = False
        robocall_start(resource_id, is_direct, user_key.urlsafe())


class DirectRobocallHandler(rest_handler.RestApiListHandler, ProcessMixin):
    """Make a robocall for direct contact"""
    def __init__(self, request, response):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema
        from sosbeacon.event import event_query_schema

        super(DirectRobocallHandler, self).__init__(
            Event, event_schema, request, response,
            query_schema=event_query_schema)

    def process(self, resource_id, *args, **kwargs):
        from sosbeacon.event.robocall import robocall_start

        session_store = sessions.get_store()
        session = session_store.get_session()

        user_key = ndb.Key(urlsafe=session.get('u'))
        if not user_key.get():
            return

        is_direct = True
        robocall_start(resource_id, is_direct, user_key.urlsafe())


class DownloadHandler(webapp2.RequestHandler):
    def get(self, event_id, number, *args, **kwargs):
        import sendgrid
        import settings
        from datetime import datetime
        from sosbeacon.event.message import Message
        from sosbeacon.event.student_marker import StudentMarker

        session_store = sessions.get_store()
        session = session_store.get_session()
        user_urlsafe = session.get('u')

        user_key = ndb.Key(urlsafe = user_urlsafe).get()
        event_key = ndb.Key(urlsafe = event_id)
        query_messages = Message.query(Message.event == event_key).fetch()

        body = ""

        for i in number:
        #           list comment message
            if i == "1":
                list_comment = Message.query(Message.event == event_key,
                    Message.message_type == 'c')
                title       = "Responder messages"
                body += str(self.responder_messages(user_key, title, list_comment))

            #           list student marker Responders
            if i == "2":
                query_response = StudentMarker.query(StudentMarker.event == event_key,
                    StudentMarker.is_direct == True,
                    StudentMarker.acknowledged == True)
                student_markers = query_response.fetch()
                title = "Responder List"
                body += str(self.email_student_marker(student_markers, title))

            #           list student marker Non Responders
            if i == "3":
                query_response = StudentMarker.query(StudentMarker.event == event_key,
                    StudentMarker.acknowledged == False, StudentMarker.is_direct == True)
                student_markers = query_response.fetch()
                title = "No Responder List"
                body += str(self.email_student_marker(student_markers, title))

            #           list message email
            if i == "4":
                title = "Alert Messages"
                body += str(self.email_broadcast_message(user_key, title, query_messages))

        today       = datetime.today()
        today       = today.strftime('%Y-%m-%d %H:%M')
        subject     = "Download data sent from SOSbeacon Message Center %s" % today
        email       = user_key.email

        s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
            settings.SENDGRID_PASSWORD,
            secure=True)

        message = sendgrid.Message(
            settings.SENDGRID_SENDER,
            subject,
            body, body)

        message.add_to(str(email))
        try:
            s.web.send(message)
        except:
            error = "Can not download email."
            create_error_log(error, 'ERR')

    def responder_messages(self, user_key, title, list_comment):
        """List comment messages of current event"""
        body = """
            <table style='border:1px solid #607298;width:540px;max-width:600px'>
                <thead>
                    <tr>
                        <th colspan="2" style="background:#607298;color:#fff;min-height:30px;line-height:30px;text-align:center;font-size:20px">%s</th>
                    </tr>
                </thead>
                <tbody>
        """ % (title)

        try:
            for comment in list_comment:
                message = comment.message['body']
                create_at   = comment.added.strftime('%Y-%m-%d %H:%M')
                body       += self.format_email_comment_message(comment.user_name, create_at, message)
        except:
            error = "Can not query comment message."
            create_error_log(error, 'ERR')

        body += """</tbody></table><br><br><br>"""
        return body

    def format_email_comment_message(self, user_name_comment, create_at, comment):
        """Format email of comment message"""
        body_email = """
            <tr></tr>
            <tr style="font-weight:bold;color:#3c4f7a">
                <td style="padding:3px 6px">%s</td>
                <td style="padding:3px 6px;text-align:right;width:150px;font-weight:normal">%s</td>
            </tr>
            <tr><td colspan="2" style="border:1px solid #f3f3f3;padding:5px 6px">
                %s</td>
            </tr>
        """ % (user_name_comment, create_at, comment)

        return body_email

    def email_broadcast_message(self, user_key, title, query_messages):

        body = """
            <table style='border:1px solid #607298;width:540px;max-width:600px'>
                <thead>
                    <tr>
                        <th colspan="2" style="background:#607298;color:#fff;min-height:30px;line-height:30px;text-align:center;font-size:20px">%s</th>
                    </tr>
                </thead>
                <tbody>
        """ % (title)

        try:
            for query_message in query_messages:
                sms_content = query_message.message['sms']
                email_content = query_message.message['email']
                create_at   = query_message.added.strftime('%Y-%m-%d %H:%M')
                body       += self.format_email_message(user_key.name, user_key.phone, user_key.email, create_at, sms_content, email_content)
        except:
            error = "Can not query message."
            create_error_log(error, 'ERR')

        body += """</tbody></table><br><br><br>"""
        return body

    def format_email_message(self, user_name, user_phone, user_email, create_at, sms_content, email_content):

        body_email = """
            <tr>
                <td colspan="2" style="background:#eceff5;font-weight:bold;color:#3c4f7a;padding:6px">Details</td>
            </tr>
            <tr>
                <td style="border:1px solid #f3f3f3;padding:3px 6px;width:100px">From: </td>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">%s</td>
            </tr>
            <tr>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">Number: </td>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">%s</td>
            </tr>
            <tr>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">Email: </td>
                <td style="border:1px solid #f3f3f3;padding:3px 6px"><a href="mailto:%s" target="_blank">%s</a></td>
            </tr>
            <tr>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">Time: </td>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">%s</td>
            </tr>
            <tr>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">SMS: </td>
                <td style="border:1px solid #f3f3f3;padding:3px 6px">%s</td>
            </tr>
            <tr>
                <td style="border:1px solid #f3f3f3;padding:3px 6px" colspan="2"><hr>Email: %s</td>
            </tr>
        """ % (user_name, user_phone, user_email, user_email, create_at, sms_content, email_content)

        return body_email


    def email_student_marker(self, student_markers, title):

        body = """
            <table style="border:1px solid #607298;width:540px;max-width:600px">
                <thead>
                    <tr>
                        <th style="background:#607298;color:#fff;min-height:30px;line-height:30px;text-align:center;font-size:20px">%s</th>
                    </tr>
                </thead>
                <tbody>
        """ % (title)

        for student_marker in student_markers:
            for contact in student_marker.contacts:
                student_name = contact['name']
                for number in contact['methods']:
                    if number['type'] == 'e':
                        email_student = number['value']
                        body += str(self.format_email_student_marker(student_name, email_student))

        body += """</tbody></table><br><br><br>"""
        return body

    def format_email_student_marker(self, student_name, student_email):

        body_email = """
            <tr>
                <td style="padding:3px 6px;border-bottom:1px solid #f3f3f3">
                    <strong>%s</strong>
                    <br>
                    <a href="mailto:%s" target="_blank">%s</a>
                </td>
            </tr>
        """ % (student_name, student_email, student_email)

        return body_email


class UserHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.user import user_schema

        super(UserHandler, self).__init__(
            User, user_schema, request, response)

    def put(self, resource_id, *args, **kwargs):
        """Update user information"""
        user = process_put_user(self.request, self.schema, self.entity)
        self.write_json_response(user.to_dict())

class UserListHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request=None, response=None):
        from sosbeacon.user import user_schema
        from sosbeacon.user import user_query_schema

        super(UserListHandler, self).__init__(
            User, user_schema, request, response,
            query_schema=user_query_schema,
            query_options={'namespace': '_x_'})

    def post(self, resource_id, *args, **kwargs):
        user = process_post_user(self.request, self.schema, self.entity)
        if user is False:
            self.abort(400)
            return

        self.write_json_response(user.to_dict())

#    def get(self, resource_id, *args, **kwargs):
#        """"""
#        self.request.GET['feq_is_admin'] = False
#
#        resources = self.query.fetch(
#            self.entity, self.request.params, self.query_schema)
#        response = [entity.to_dict() for entity in resources]
#
#        self.write_json_response(response)


def process_post_user(request, schema, entity):
    from voluptuous import Schema
    from sosbeacon.student import create_default_student
    from sosbeacon.user import send_invitation_email

    obj = json.loads(request.body)
    schema = Schema(schema, extra=True)

    if obj['email'] == '' or obj['phone'] == '' or \
            obj['name'] == '':
        return False

    if len(obj['password']) < 6:
        return False

    #check user exits
    check_email = User.query(User.email == obj['email'], namespace = '_x_')
    check_phone = User.query(User.phone == obj['phone'], namespace = '_x_')

    if check_email.get() or check_phone.get():
        return False

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')
        logging.info(obj)

    user = entity.from_dict(obj)
    user.set_password(obj['password'])
    to_put = [user]

    ndb.put_multi(to_put)
    create_default_student(user)
    send_invitation_email(user.name, user.email, obj['password'])

    return user

def process_put_user(request, schema, entity):
    from voluptuous import Schema

    obj = json.loads(request.body)
    schema = Schema(schema, extra=True)

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')
        logging.info(obj)

    user = entity.from_dict(obj)
    if len(obj['password']) > 6:
        user.set_password(obj['password'])

    to_put = [user]

    ndb.put_multi(to_put)

    return user


class ExportStudentHandler(blobstore_handlers.BlobstoreDownloadHandler):

    def get(self):
        """Export all student contact of current school"""
        from sosbeacon.student import Student
        from google.appengine.ext import blobstore
        from google.appengine.api import files

        session_store = sessions.get_store()
        session = session_store.get_session()

        school_urlsafe = session.get('s')
        school_key = ndb.Key(urlsafe = school_urlsafe)

        file_name = files.blobstore.create(mime_type='text/csv',_blobinfo_uploaded_filename='export_student.csv')
        students = Student.query(ndb.AND(Student.school == school_key,
                                         Student.is_direct == False),
                                namespace = '_x_').fetch()

        headers = ['group_name', 'contacts_name','parent1', 'parent1_email', 'parent1_text_phone',
                   'parent1_voice_phone', 'parent2', 'parent2_email', 'parent2_text_phone',
                   'parent2_voice_phone']

        headers = ','.join(headers)

        with files.open(file_name, 'a') as f:
            f.write(headers)
            f.write('\n')

        for student in students:
            with files.open(file_name, 'a') as f:
                info = self.get_info_student(student)
                info = ','.join(info)
                f.write(info)
                f.write('\n')

        files.finalize(file_name)
        blob_key = files.blobstore.get_blob_key(file_name)

        blob_info = blobstore.BlobInfo.get(blob_key)
        if not blobstore.get(blob_key):
            self.error(404)
        else:
            self.send_blob(blob_info, save_as=blob_info.filename)

    def get_info_student(self, student):
        info_student = []
        info_student.append("")
        info_student.append(student.name)

        for contact in student.contacts:
            info_student.append(contact['name'])
            if len(contact['methods'][0]['value']) > 0:
                info_student.append(contact['methods'][0]['value'])
            if len(contact['methods'][0]['value']) == 0:
                info_student.append("")

            if len(contact['methods']) > 1:
                info_student.append(regex_phone(contact['methods'][1]['value']))
            if len(contact['methods']) <= 1:
                info_student.append("")

            if len(contact['methods']) > 2:
                info_student.append(regex_phone(contact['methods'][2]['value']))
            if len(contact['methods']) <= 2:
                info_student.append("")

        return info_student

def regex_phone(phone):
    p = re.compile(r"\D+")
    phones = p.sub("",phone)
    return phones