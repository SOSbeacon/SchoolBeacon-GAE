import logging
import re
import uuid

from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

DEFAULT_STUDENT_ID = "student__"
EMAIL_REGEX = re.compile("^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")

student_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'name': basestring,
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
    'flike_name': basestring,
    'feq_groups': voluptuous.any('', voluptuous.ndbkey()),
    'feq_school': voluptuous.ndbkey(),
    'feq_is_direct': voluptuous.boolean()
}

class Student(EntityBase):
    """Represents a student."""

    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower() if x else ''),
        'groups': RestQueryRule('groups', lambda x: None if x == '' else x)
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n')
    name_ = ndb.ComputedProperty(lambda self: self.name.lower(), name='n_')

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

        student.name = data.get('name')
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
        student['name'] = self.name
#        student['identifier'] = self.identifier

        student['contacts'] = self.contacts if self.contacts else []
        student['groups'] = [key.urlsafe() for key in self.groups]
        student['notes'] = self.notes or ''

        student['is_direct'] = self.is_direct
        student['default_student'] = self.default_student

        return student


#TODO: keep list of exceptions to display
#TODO: Display "results" of import
def import_students(file_):
    import csv
    import StringIO
    from collections import namedtuple

    results = {'success': [], 'failures': []}
    ResultItem = namedtuple('ResultItem', ['name', 'messages'])

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

        name = unicode(student_array[1], 'utf8').strip()
        try:
            student, future, messages = import_student(student_array, groups)
            result = ResultItem(name=name, messages=messages)
            results['success'].append(result)
        except Exception, e:
            logging.exception("Unable to import student")
            result = ResultItem(name=name, messages=[e.message])
            results['failures'].append(result)

        if not student and future:
            futures.append(future)

    ndb.Future.wait_all(futures)

    return results


def import_student(student_array, group_lookup=None):
    messages = []

    if group_lookup is None:
        group_lookup = {}

    #expected CSV format
    #Group, Student name, contact name parent 1, contact email,
    #voice phone, text phone, space, contact name parent 2
    #contact email, voice phone, text phone
    group_name = unicode(student_array[0], 'utf8').strip()
    group_key, group_future = _get_group(group_name, group_lookup)

    #TODO: look for existing student by name?
    student_name = unicode(student_array[1], 'utf8')
    if not student_name:
        #TODO: add bad message
        logging.error("Invalid student name %s", student_name)
        return None, None, messages

    #Ideally they have an ID in the sheet to import in
    student = Student(identifier=uuid.uuid4().hex[:6], name=student_name)

    student.contacts = _build_contacts(student_array)

    if group_future:
        group_key = group_future.get_result()

    if group_name.lower() not in group_lookup:
        group_lookup[group_name.lower()] = group_key

    if group_key not in student.groups:
        student.groups.append(group_key)

    logging.info("Saving student %s", student)
    future = student.put_async()
    return student, future, messages


def _build_contacts(student_array):
    contacts = []
    contact_info = student_array[3:]
    while contact_info:
        contact, messages = _contact_from_args(*contact_info[0:4])
        logging.info("Adding contact %s", contact)
        contacts.append(contact)
        contact_info = contact_info[5:]

    return contacts


def _contact_from_args(name, email, voice=None, text=None):
    messages = []
    info = {'name': name, 'methods': [], "type": "p", "notes": ""}

    def _add_phone_number(number, type_):
        phone, messages = validate_and_standardize_phone(number)
        if phone:
            info['methods'].append({'type': type_, 'value': phone})
        else:
            messages.extend(messages)

    if email and valid_email(email):
        info['methods'].append({'type': 'e', 'value': email})
    else:
        messages.append("Invalid email address %s" % (email,))

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

    try:
        stuff = string.maketrans('', '')
        non_digits = stuff.translate(None, string.digits)
        number = number.translate(None, non_digits)
    except Exception, e:
        logging.exception("Invalid phone number %s", number)
        messages.append("Invalid phone number %s, %s", number, e.message)
        return None, messages

    if not number.startswith('1'):
        number = '1' + number

    if not len(number) == 11:
        logging.error("Invalid phone number %s", number)
        messages.append("Invalide number %s, not 11 characters" % (number,))
        return None, messages

    number = "%s (%s) %s-%s" % (
        number[0], number[1:4], number[4:7], number[7:11])

    return number, messages


def _get_group(group_name, group_lookup):
    """Return a group for the group name passed in. Checks the group cache
    first if not there then queries by the lower case name. If not there then
    creates a new group.
    """
    #check for existing group by name
    if group_name.lower() in group_lookup:
        logging.debug("group found in cache")
        return group_lookup[group_name.lower()], None

    from .group import Group
    group = Group.query(Group.name_ == group_name.lower()).get()
    if group:
        logging.debug("group found in datastore")
        group_lookup[group_name.lower()] = group.key
        return group.key, None

    logging.debug("No group found for %s, creating a new one", group_name)
    group = Group(name=group_name, active=True)
    future = group.put_async()
    return group.key, future


def create_default_student(user):
    """Create a default student when user is created"""
    contacts = [
        {'notes': '', 'type': 'd', 'name': user.name, 'methods': [
            {'type': 'e', 'value': user.email},
            {'type': 't', 'value': user.phone},
            {'type': 'p', 'value': ''}]}]

    default_student = Student(key=ndb.Key(Student, DEFAULT_STUDENT_ID + "-%s" % (user.key.id()),
        namespace="_x_"),
        name = user.name,
        contacts = contacts,
        default_student=True,
        groups = [],
        school = None)

    default_student.put()