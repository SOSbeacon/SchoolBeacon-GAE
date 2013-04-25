import logging
import re
import uuid

from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

from sosbeacon.error_log import create_error_log
from sosbeacon.group import Group

DEFAULT_STUDENT_ID = "student__"
EMAIL_REGEX = re.compile("^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")

student_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'first_name': basestring,
    'last_name': basestring,
#    'identifier': basestring,
    'groups': [voluptuous.ndbkey()],
    'contacts': [{
        'name': basestring,
        'type': voluptuous.any('p', 'o', 'd'),
        'notes': basestring,
        'methods': [{'type': voluptuous.any('e', 't', 'p'),
                     'value': basestring}]
    }]
}

student_query_schema = {
    'flike_first_name': basestring,
    'feq_groups': voluptuous.any('', voluptuous.ndbkey()),
    'feq_school': voluptuous.ndbkey(),
    'feq_is_direct': voluptuous.boolean()
}

class Student(EntityBase):
    """Represents a student."""

    _query_properties = {
        'last_name': RestQueryRule('last_name_', lambda x: x.lower() if x else ''),
        'groups': RestQueryRule('groups', lambda x: None if x == '' else x)
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    first_name = ndb.StringProperty('fn')

    last_name = ndb.StringProperty('ln')
    last_name_ = ndb.StringProperty('ln_')
#    last_name_ = ndb.ComputedProperty(lambda self: self.last_name.lower(), last_name='ln_')

#    identifier = ndb.StringProperty('i')
#    identifier_ = ndb.ComputedProperty(
#        lambda self: self.identifier.lower(),
#        name='i_')

    groups = ndb.KeyProperty('g', repeated=True)
    school = ndb.KeyProperty('sc', kind='School')
    contacts = ndb.JsonProperty('c')

    notes = ndb.TextProperty()

#   filter default student
    default_student = ndb.BooleanProperty('ids', default=False)
    is_direct = ndb.BooleanProperty('id')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Student entity from a dict of values."""
        key = data.get("key")
        student = None
        if key:
            student = key.get()

        if not student:
            student = cls(namespace='_x_')

        student.first_name = data.get('first_name')
        student.last_name_ = data.get('last_name').lower()
        student.last_name = data.get('last_name')
#        student.identifier = data.get('identifier')
#       check student is direct contact or student contact
        student.is_direct = data.get('is_direct')
        student.notes = data.get('notes')

        student.groups = data.get('groups')
        student.school = data.get('school') if data.get('school') else student.school
        student.contacts = data.get('contacts')

        return student

    def to_dict(self):
        """Return a Student entity represented as a dict of values
        suitable for Student.from_dict.
        """
        student = self._default_dict()
        student["version"] = self.version_
        student['first_name'] = self.first_name
        student['last_name'] = self.last_name
#        student['identifier'] = self.identifier

        student['contacts'] = self.contacts if self.contacts else []
        student['groups'] = [key.urlsafe() for key in self.groups if key.get() != None]
        student['notes'] = self.notes or ''

        student['is_direct'] = self.is_direct
        student['default_student'] = self.default_student

        return student


#TODO: keep list of exceptions to display
#TODO: Display "results" of import
def preview_import_students(file_, is_direct):
    import csv
    import StringIO
    from collections import namedtuple

    results = {'success': [], 'failures': []}
    ResultItemDirect = namedtuple('ResultItemDirect', ['first_name', 'last_name', 'group', 'email', 'text_phone', 'voice_phone','messages'])
    ResultItemStudent = namedtuple('ResultItemStudent', ['first_name', 'last_name','group', 'parent_first_name_1', 'parent_last_name_1','parent_email_1', 'parent_text_phone_1', 'parent_voice_phone_1',
                                                         'parent_first_name_2', 'parent_last_name_2','parent_email_2', 'parent_text_phone_2', 'parent_voice_phone_2','messages'])

    students = csv.reader(StringIO.StringIO(file_), delimiter=',')
    #TODO: check size and move to tasks

    #expected CSV format
    #Group, Student name, contact name parent 1, contact email,
    #voice phone, text phone, space, contact name parent 2
    #contact email, voice phone, text phone
    for student_array in students:
        if student_array[0] and student_array[0].lower() == 'group':
            #assume it has a header
            continue

        logging.info(student_array)
        first_name = unicode(student_array[1], 'utf8').strip()
        last_name = unicode(student_array[2], 'utf8').strip()
        group = unicode(student_array[0], 'utf8').strip()

        if is_direct:
            if not '@' in unicode(student_array[3], 'utf8').strip():
                break

            email = unicode(student_array[3], 'utf8').strip()
            text_phone = unicode(student_array[4], 'utf8').strip()
            voice_phone = unicode(student_array[5], 'utf8').strip()
            try:
                result = ResultItemDirect(first_name=first_name, last_name=last_name, group=group, email=email, text_phone=text_phone, voice_phone=voice_phone, messages='')
                results['success'].append(result)
            except Exception, e:
                logging.exception("Unable to import direct contact")
                result = ResultItemDirect(first_name=first_name, last_name=last_name, group=group, email=email, text_phone=text_phone, voice_phone=voice_phone, messages=[e.message])
                results['failures'].append(result)
                error = "Unable to import direct contact"
                create_error_log(error, 'ERR')

        else:
            if '@' in unicode(student_array[3], 'utf8').strip():
                break

            parent_first_name_1 = unicode(student_array[3], 'utf8').strip()
            parent_last_name_1 = unicode(student_array[4], 'utf8').strip()
            parent_email_1 = unicode(student_array[5], 'utf8').strip()
            parent_text_phone_1 = unicode(student_array[5], 'utf8').strip()
            parent_voice_phone_1 = unicode(student_array[6], 'utf8').strip()

            if len(student_array) > 7:
                parent_first_name_2 = unicode(student_array[7], 'utf8').strip()
                parent_last_name_2 = unicode(student_array[8], 'utf8').strip()
                parent_email_2 = unicode(student_array[9], 'utf8').strip()
                parent_text_phone_2 = unicode(student_array[10], 'utf8').strip()
                parent_voice_phone_2 = unicode(student_array[11], 'utf8').strip()
            else:
                parent_first_name_2 = parent_last_name_2 = parent_text_phone_2 = parent_voice_phone_2 = ''

            try:
                result = ResultItemStudent(first_name=first_name, last_name=last_name,
                    group=group,
                    parent_first_name_1 = parent_first_name_1,
                    parent_last_name_1 = parent_last_name_1,
                    parent_email_1 = parent_email_1,
                    parent_text_phone_1 = parent_text_phone_1,
                    parent_voice_phone_1 = parent_voice_phone_1,
                    parent_first_name_2 = parent_first_name_2,
                    parent_last_name_2 = parent_last_name_2,
                    parent_email_2 = parent_email_2,
                    parent_text_phone_2 = parent_text_phone_2,
                    parent_voice_phone_2 = parent_voice_phone_2, messages='')

                results['success'].append(result)
            except Exception, e:
                logging.exception("Unable to import direct contact")
                result = ResultItemStudent(first_name=first_name, last_name=last_name,
                    group=group,
                    parent_first_name_1 = parent_first_name_1,
                    parent_last_name_1 = parent_last_name_1,
                    parent_email_1 = parent_email_1,
                    parent_text_phone_1 = parent_text_phone_1,
                    parent_voice_phone_1 = parent_voice_phone_1,
                    parent_first_name_2 = parent_first_name_2,
                    parent_last_name_2 = parent_last_name_2,
                    parent_email_2 = parent_email_2,
                    parent_text_phone_2 = parent_text_phone_2,
                    parent_voice_phone_2 = parent_voice_phone_2, messages=[e.message])

                results['failures'].append(result)
                error = "Unable to import direct contact"
                create_error_log(error, 'ERR')

    return results


def import_students(file_, school_urlsafe, is_direct):
    import csv
    import StringIO
    from collections import namedtuple

    results = {'success': [], 'failures': []}
    ResultItemDirect = namedtuple('ResultItemDirect', ['first_name', 'last_name', 'group', 'email', 'text_phone', 'voice_phone','messages'])
    ResultItemStudent = namedtuple('ResultItemStudent', ['first_name', 'last_name','group', 'parent_first_name_1', 'parent_last_name_1','parent_email_1', 'parent_text_phone_1', 'parent_voice_phone_1',
                                                         'parent_first_name_2', 'parent_last_name_2','parent_email_2', 'parent_text_phone_2', 'parent_voice_phone_2','messages'])

    students = csv.reader(StringIO.StringIO(file_), delimiter=',')
    #TODO: check size and move to tasks

    #expected CSV format
    #Group, Student name, contact name parent 1, contact email,
    #voice phone, text phone, space, contact name parent 2
    #contact email, voice phone, text phone
    groups = {}
    futures = []
    for student_array in students:
        if student_array[0] and student_array[0].lower() == 'group':
            #assume it has a header
            continue

        first_name = unicode(student_array[1], 'utf8').strip()
        last_name = unicode(student_array[2], 'utf8').strip()
        group = unicode(student_array[0], 'utf8').strip()

        if is_direct:
            email = unicode(student_array[3], 'utf8').strip()
            text_phone = unicode(student_array[4], 'utf8').strip()
            voice_phone = unicode(student_array[5], 'utf8').strip()
            try:
                student, future, messages = import_student(school_urlsafe, is_direct, student_array, groups)
                result = ResultItemDirect(first_name=first_name, last_name=last_name, group=group, email=email, text_phone=text_phone, voice_phone=voice_phone, messages=messages)
                results['success'].append(result)
            except Exception, e:
                logging.exception("Unable to import direct contact")
                result = ResultItemDirect(first_name=first_name, last_name=last_name, group=group, email=email, text_phone=text_phone, voice_phone=voice_phone, messages=[e.message])
                results['failures'].append(result)
                error = "Unable to import direct contact"
                create_error_log(error, 'ERR')

#            if not student and future:
#                futures.append(future)

        else:
            parent_first_name_1 = unicode(student_array[3], 'utf8').strip()
            parent_last_name_1 = unicode(student_array[4], 'utf8').strip()
            parent_email_1 = unicode(student_array[5], 'utf8').strip()
            parent_text_phone_1 = unicode(student_array[5], 'utf8').strip()
            parent_voice_phone_1 = unicode(student_array[6], 'utf8').strip()


            if len(student_array) > 7:
                parent_first_name_2 = unicode(student_array[7], 'utf8').strip()
                parent_last_name_2 = unicode(student_array[8], 'utf8').strip()
                parent_email_2 = unicode(student_array[9], 'utf8').strip()
                parent_text_phone_2 = unicode(student_array[10], 'utf8').strip()
                parent_voice_phone_2 = unicode(student_array[11], 'utf8').strip()
            else:
                parent_first_name_2 = parent_last_name_2 = parent_text_phone_2 = parent_voice_phone_2 = ''

            try:
                student, future, messages = import_student(school_urlsafe, is_direct, student_array, groups)
                result = ResultItemStudent(first_name=first_name, last_name=last_name,
                    group=group,
                    parent_first_name_1 = parent_first_name_1,
                    parent_last_name_1 = parent_last_name_1,
                    parent_email_1 = parent_email_1,
                    parent_text_phone_1 = parent_text_phone_1,
                    parent_voice_phone_1 = parent_voice_phone_1,
                    parent_first_name_2 = parent_first_name_2,
                    parent_last_name_2 = parent_last_name_2,
                    parent_email_2 = parent_email_2,
                    parent_text_phone_2 = parent_text_phone_2,
                    parent_voice_phone_2 = parent_voice_phone_2, messages='')

                results['success'].append(result)
            except Exception, e:
                logging.exception("Unable to import direct contact")
                result = ResultItemStudent(first_name=first_name, last_name=last_name,
                    group=group,
                    parent_first_name_1 = parent_first_name_1,
                    parent_last_name_1 = parent_last_name_1,
                    parent_email_1 = parent_email_1,
                    parent_text_phone_1 = parent_text_phone_1,
                    parent_voice_phone_1 = parent_voice_phone_1,
                    parent_first_name_2 = parent_first_name_2,
                    parent_last_name_2 = parent_last_name_2,
                    parent_email_2 = parent_email_2,
                    parent_text_phone_2 = parent_text_phone_2,
                    parent_voice_phone_2 = parent_voice_phone_2, messages=[e.message])

                results['failures'].append(result)
                error = "Unable to import direct contact"
                create_error_log(error, 'ERR')

#                if not student and future:
#                    futures.append(future)

    ndb.Future.wait_all(futures)
    return results


def import_student(school_urlsafe, is_direct, student_array, group_lookup=None):
    messages = []

    if group_lookup is None:
        group_lookup = {}

    #expected CSV format
    #Group, Student name, contact name parent 1, contact email,
    #voice phone, text phone, space, contact name parent 2
    #contact email, voice phone, text phone
    group_name = unicode(student_array[0], 'utf8').strip()
    if not group_name:
        #TODO: add bad message
        logging.error("Invalid group name %s", group_name)
        error = "Invalid group name %s", group_name
        create_error_log(error, 'ERR')
        return None, None, messages

    group_key, group_future = _get_group(group_name, group_lookup, school_urlsafe)

    #TODO: look for existing student by name?
    student_first_name = unicode(student_array[1], 'utf8')
    student_last_name = unicode(student_array[2], 'utf8')
    if not student_first_name:
        #TODO: add bad message
        logging.error("Invalid student name %s", student_first_name)
        error = "Invalid student name %s", student_first_name
        create_error_log(error, 'ERR')
        return None, None, messages

        #Ideally they have an ID in the sheet to import in
    #    student = Student(identifier=uuid.uuid4().hex[:6], name=student_name, is_direct=is_direct)
    student = Student(first_name=student_first_name, last_name=student_last_name, last_name_=student_last_name.lower(), is_direct=is_direct)

    if is_direct:
        student.contacts = _build_direct_contacts(student_array)
    else:
        student.contacts = _build_student_contacts(student_array)

    if group_future:
        group_key = group_future.get_result()

    if group_name.lower() not in group_lookup:
        group_lookup[group_name.lower()] = group_key

    if group_key not in student.groups:
        school_key = ndb.Key(urlsafe = school_urlsafe)
        student.groups.append(group_key)
        student.school = school_key

    logging.info("Saving student %s", student)
    future = student.put_async()
    return student, future, messages


def _build_direct_contacts(student_array):
    contacts = []
    contact_info = student_array[1:]
    while contact_info:
        contact, messages = _contact_from_args(*contact_info[0:5])
        logging.info("Adding contact %s", contact)
        contacts.append(contact)
        contact_info = contact_info[5:]

    return contacts


def _build_student_contacts(student_array):
    contacts = []
    contact_info = student_array[3:]
    while contact_info:
        contact, messages = _contact_from_args(*contact_info[0:5])
        logging.info("Adding contact %s", contact)
        contacts.append(contact)
        contact_info = contact_info[5:]

    return contacts


def _contact_from_args(first_name, last_name, email, text, voice):
    messages = []
    info = {'first_name': first_name, 'last_name': last_name, 'methods': [], "type": "p", "notes": ""}

    def _add_phone_number(number, type_):
        phone, messages = validate_and_standardize_phone(number)
        if phone:
            info['methods'].append({'type': type_, 'value': phone})
        else:
            messages.extend(messages)
            info['methods'].append({'type': type_, 'value': ''})

    if email and valid_email(email):
        info['methods'].append({'type': 'e', 'value': email})
    else:
        messages.append("Invalid email address %s" % (email,))
        error = "Invalid email address %s" % (email)
        create_error_log(error, 'ERR')
        info['methods'].append({'type': 'e', 'value': ''})

    if voice:
        _add_phone_number(voice, 'p')
    if text:
        _add_phone_number(text, 't')

    return info, messages


def valid_email(email):
    if EMAIL_REGEX.match(email):
        return True

    return False


def validate_and_standardize_phone(number):
    import string
    messages = []

    logging.info(number)
    try:
        stuff = string.maketrans('', '')
        non_digits = stuff.translate(None, string.digits)
        number = number.translate(None, non_digits)
        logging.info(number)
    except Exception, e:
        logging.exception("Invalid phone number %s", number)
        messages.append("Invalid phone number %s, %s", number, e.message)
        error = "Invalid phone number %s", number
        create_error_log(error, 'ERR')
        return None, messages

    logging.info(number)
    if not number.startswith('1'):
        number = '1' + number

    if not len(number) == 11:
        logging.error("Invalid phone number %s", number)
        messages.append("Invalide number %s, not 11 characters" % (number,))
        error = "Invalid phone number %s", number
        create_error_log(error, 'ERR')
        return None, messages

    number = "%s (%s) %s-%s" % (
        number[0], number[1:4], number[4:7], number[7:11])

    return number, messages


def _get_group(group_name, group_lookup, school_urlsafe):
    """Return a group for the group name passed in. Checks the group cache
    first if not there then queries by the lower case name. If not there then
    creates a new group.
    """
    #check for existing group by name
    if group_name.lower() in group_lookup:
        logging.debug("group found in cache")
        error = "group found in cache"
        create_error_log(error, 'ERR')
        return group_lookup[group_name.lower()], None

    from .group import Group
    school_key = ndb.Key(urlsafe = school_urlsafe)
    group = Group.query(Group.name_ == group_name, Group.school == school_key, namespace = '_x_').get()

    if group:
        logging.debug("group found in datastore")
        error = "group found in datastore"
        create_error_log(error, 'ERR')
        group_lookup[group_name.lower()] = group.key
        return group.key, None

    logging.debug("No group found for %s, creating a new one", group_name)
    group = Group(name=group_name)
    school_key = ndb.Key(urlsafe = school_urlsafe)
    group.school = school_key
    future = group.put_async()
    return group.key, future


def create_default_student(user):
    """Create a default student when user is created"""
    contacts = [
        {'notes': '', 'type': 'd', 'first_name': user.first_name, 'last_name': user.last_name, 'methods': [
            {'type': 'e', 'value': user.email},
            {'type': 't', 'value': user.phone},
            {'type': 'p', 'value': ''}]}]

    default_student = Student(key=ndb.Key(Student, DEFAULT_STUDENT_ID + "-%s" % (user.key.id()),
        namespace="_x_"),
        first_name = user.first_name,
        last_name = user.last_name,
        contacts = contacts,
        default_student=True,
        is_direct = True,
        groups = [],
        school = None)

    default_student.put()