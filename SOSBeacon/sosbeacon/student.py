import logging

from google.appengine.ext import ndb

import uuid
import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule


student_schema = {
    'key': basestring,
    'name': basestring,
    'identifier': basestring,
    'groups': [voluptuous.ndbkey()],
    'contacts': [{
        'name': basestring,
        'type': voluptuous.any('p', 'o', 'd'),
        'notes': basestring,
        'methods': [{'type': basestring, 'value': basestring}]
    }]
}

student_query_schema = {
    'flike_name': basestring,
    'feq_groups': voluptuous.any('', voluptuous.ndbkey()),
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

    identifier = ndb.StringProperty('i')
    identifier_ = ndb.ComputedProperty(
        lambda self: self.identifier.lower(),
        name='i_')

    groups = ndb.KeyProperty('g', repeated=True)
    contacts = ndb.JsonProperty('c')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Student entity from a dict of values."""
        key = data.get("key")
        student = None
        if key:
            key = ndb.Key(urlsafe=key)
            student = key.get()

        if not student:
            student = cls()

        student.name = data.get('name')
        student.identifier = data.get('identifier')

        student.groups = data.get('groups')
        student.contacts = data.get('contacts')

        return student

    def to_dict(self):
        """Return a Student entity represented as a dict of values
        suitable for Student.from_dict.
        """
        student = self._default_dict()
        student["version"] = self.version_
        student['name'] = self.name
        student['identifier'] = self.identifier

        student['contacts'] = self.contacts if self.contacts else []
        student['groups'] = [key.urlsafe() for key in self.groups]

        return student

def import_students(file_):
    import csv
    import StringIO

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

        student, future = import_student(student_array, groups)
        if not student and future:
            futures.append(future)

    ndb.Future.wait_all(futures)

def import_student(student_array, group_lookup=None):
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

    student = Student.query(Student.name_ == student_name.lower()).get()
    if not student:
        #TODO: generic identifier for now? something better?
        student = Student(identifier=uuid.uuid4().hex, name=student_name)

    student.contacts = _get_contacts(student_array)

    if group_future:
        group_key = group_future.get_result()

    if group_name.lower() not in group_lookup:
        group_lookup[group_name.lower()] = group_key

    if group_key not in student.groups:
        student.groups.append(group_key)

    future = student.put_async()
    return student, future

def _get_contacts(student_array):
    contacts = []
    type_map = {
        1: "email",
        2: "phone",
        3: "text"
    }

    def _get_init_contact(name):
        return {
            "notes": "",
            "type": "p",
            "name": name,
            "methods": []
        }

    def _get_contact(start_index):
        if not len(student_array) > start_index:
            logging.debug("No contacts in array")
            return

        name  = student_array[start_index]
        if not name:
            logging.debug("Contact name not found in array")
            return

        contact = _get_init_contact(name)
        for index, type_ in type_map.iteritems():
            if len(student_array) > start_index + index:
                value = student_array[start_index + index].strip()
                if not value:
                    continue

                #validate and convert phone numbers
                if index in [2, 3]:
                    value = ''.join(filter(lambda x: x.isdigit(), value))
                    if len(value) == 10:
                        value = "1" + value

                    if len(value) != 11:
                        logging.error("Invalid phone number %s", value)
                        continue

                    logging.debug(value)
                    value = "%s (%s) %s-%s" % (
                        value[0], value[1:4], value[4:7], value[7:11])
                    logging.debug(value)

                contact['methods'].append(
                    {
                        "type": type_,
                        "value": value
                    }
                )

        return contact

    for index in [3, 8]:
        contact = _get_contact(index)
        if contact:
            contacts.append(contact)

    return contacts

def _get_group(group_name, group_lookup):
    """ Return a group for the group name passed in. Checks the group cache first
    if not there then queries by the lower case name. If not there then creates
    a new group.
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
    group =  Group(name=group_name, active=True)
    future = group.put_async()
    return group.key, future
