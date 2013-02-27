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


class MessageHandler(rest_handler.RestApiListHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.event.message import Message
        from sosbeacon.event.message import message_schema

        super(MessageHandler, self).__init__(
            Message, message_schema, request, response)

    def process(self, resource_id, *args, **kwargs):
        message = process_messages(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())


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
        self.write_json_response(message.to_dict())


class StudentHandler(rest_handler.RestApiHandler, ProcessMixin):

    def __init__(self, request, response):
        from sosbeacon.student import Student
        from sosbeacon.student import student_schema

        super(StudentHandler, self).__init__(
            Student, student_schema, request, response)


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

        if self.request.GET['feq_is_direct'] == 'false':
            self.write_json_response(response)
            return

        user_key = ndb.Key(urlsafe = session.get('u'))

        student_key = ndb.Key(
            Student, "%s-%s" % (DEFAULT_STUDENT_ID, user_key.id()),
            namespace='_x_')

        response.insert(0, student_key.get().to_dict())

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
    check_name = Group.query(Group.name == obj['name'], namespace = '_x_')

    if check_name.get():
        return False

    try:
        obj = schema(obj)
    except:
        logging.exception('validation failed')
        logging.info(obj)

    school_key = ndb.Key(urlsafe = session.get('s'))
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

        self.write_json_response(group.to_dict())

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

        if key.id() == (ADMIN_GROUPS_ID) \
            or (key.id() == STAFF_GROUPS_ID):
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

        self.write_json_response(group.to_dict())


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
        message = process_school(self.request, self.schema, self.entity)
        self.write_json_response(message.to_dict())


class EventHandler(rest_handler.RestApiHandler):

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
        logging.info(school_key)

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