
import json

from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

from sosbeacon.event.event import Event


CONTACT_MERGE_ENDPOINT = '/task/event/update/contact_marker'
CONTACT_MERGE_QUEUE = "contact-marker-update"

MARKER_MERGE_ENDPOINT = '/task/event/merge/contact_marker'
MARKER_MERGE_QUEUE = "contact-marker-merge"


marker_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'acknowledged': voluptuous.boolean(),
    'first_name': basestring,
    'last_name': basestring,
    'responded': [basestring],
}

marker_query_schema = {
    'feq_acknowledged': voluptuous.boolean(),
    'feq_event': voluptuous.ndbkey(),
    'fan_key': voluptuous.ndbkey(),
    'first_name': basestring,
    'last_name': basestring
}


class ContactMarker(EntityBase):
    """Used to store Contact-Events tx / view metadata.

    Key name is constructed as:
        event.short_id + ':' + ContactMarker.short_id
    """
    _query_properties = {
        'first_name': RestQueryRule('first_name_', lambda x: x.lower() if x else ''),
    }

    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # Used to query for short URLs
    short_id = ndb.StringProperty('i')

    event = ndb.KeyProperty(Event)

    # contact name, for display
    first_name = ndb.StringProperty('fnm')
    last_name = ndb.StringProperty('lnm')

    acknowledged = ndb.BooleanProperty('a', default=False)
    last_viewed_date = ndb.IntegerProperty('at', indexed=False)

    students = ndb.JsonProperty('s', indexed=False)

    methods = ndb.StringProperty('m', indexed=True, repeated=True)

    place_holder = ndb.KeyProperty('p', indexed=False)

#    count user visit link
    count_visit = ndb.IntegerProperty('vn', default=0)
#    count user comment
    count_comment = ndb.IntegerProperty('cc', default=0)
#    marker of user for sort response list
    is_user = ndb.BooleanProperty(default=False)

    def merge(self, other):
        """Merge this MethodMarker entity with another MethodMarker."""
        other.place_holder = self.key

        self.acknowledged = max(self.acknowledged, other.acknowledged)

        self.last_viewed_date = max(
            self.last_viewed_date if self.last_viewed_date else 0,
            other.last_viewed_date if other.last_viewed_date else 0)

        self.short_id = self.short_id or other.short_id

        self.first_name = self.first_name or other.first_name
        self.last_name = self.last_name or other.last_name

        if not self.students:
            self.students = other.students
        elif other.students:
            for student, contacts in other.students.iteritems():
                if student not in self.students:
                    self.students[student] = contacts
                    continue

                base_contacts = self.students[student]
                for contact in contacts:
                    if contact not in base_contacts:
                        base_contacts.append(contact)
                        continue

        methods = set()
        if self.methods:
            methods |= set(self.methods)

        if other.methods:
            methods |= set(other.methods)

        self.methods = list(methods)

        return self

    def to_dict(self):
        """Return a MethodMarker entity represented as a dict of values."""

        marker = self._default_dict()
        marker["version"] = self.version_
        marker['first_name'] = self.first_name
        marker['last_name'] = self.last_name
        marker['acknowledged'] = self.acknowledged
        marker['last_viewed_date'] = self.last_viewed_date
        marker['students'] = self.students.keys()
        marker['count_visit'] = self.count_visit
        marker['count_comment'] = self.count_comment
        marker['methods'] = self.methods

        return marker


def find_markers_for_methods(event_key, methods):
    """Helper method to return a ContactMarker query for the given event and
    methods.

    This method exists primarily to make unit testing easier.
    """
    if not event_key:
        raise ValueError('event_key is required.')

    if not methods:
        raise ValueError('Non-empty value for methods is required.')

    return ContactMarker.query(
        ContactMarker.event == event_key, ContactMarker.methods.IN(methods))


def get_marker_for_methods(event_key, search_methods):
    # Setup query to search for matching markers.
    query = find_markers_for_methods(event_key, search_methods)

    # Assess results to see if there is any overlap.
    place_holder_counts = {}
    markers = []
    for marker in query:
        if not marker.place_holder:
            markers.append(marker)
            continue

        count = place_holder_counts.get(marker.place_holder, 0)
        place_holder_counts[marker.place_holder] = count + 1

    if not place_holder_counts and not markers:
        return None

    if place_holder_counts:
        place_holder_key = sorted(
            place_holder_counts, key=lambda x: place_holder_counts[x])[-1]
        place_holder = place_holder_key.get()
    else:
        place_holder = markers.pop()

    return place_holder


def create_or_update_marker(event_key, student_key, message_key, contact, search_methods):
    """Look for a marker for the requested methods.  If one is found, return
    its short_id, if multiple are found, request a merge, then return one's
    short_id.
    """
    from .event import insert_count_update_task

    if not search_methods:
        raise ValueError('Non-empty value for search_methods is required.')

    if not contact:
        raise ValueError('Contact is required.')

    if not student_key:
        raise ValueError('student_key is required.')

    if not event_key:
        raise ValueError('event_key is required.')

    if not message_key:
        raise ValueError('message_key is required.')

    marker = get_marker_for_methods(event_key, search_methods)

    if marker:
        insert_update_marker_task(
            marker.key, student_key, contact, search_methods)
    else:
        import logging
        # TODO: What needs set?
        short_id = str(ContactMarker.allocate_ids(size=1, parent=event_key)[0])
        key_id = "%s:%s" % (event_key.id(), short_id)
        marker = ContactMarker(
            id=key_id,
            event=event_key,
            first_name=contact.get('first_name'),
            last_name=contact.get('last_name'),
            students={str(student_key.id()): [contact]},
            short_id=short_id,
            methods=search_methods)
        marker.put()

    insert_count_update_task(event_key, marker.key, message_key, 'contact')

    return marker.short_id


def insert_update_marker_task(marker_key, student_key,
                              contact, search_methods):
    """Insert a task to merge a contact's info into a marker."""
    from google.appengine.api import taskqueue

    marker_urlsafe = marker_key.urlsafe()
    student_urlsafe = student_key.urlsafe()

    task = taskqueue.Task(
        url=CONTACT_MERGE_ENDPOINT,
        params={
            'marker': marker_urlsafe,
            'student': student_urlsafe,
            'contact': json.dumps(contact),
            'methods': json.dumps(list(search_methods))
        }
    )

    taskqueue.Queue(name=CONTACT_MERGE_QUEUE).add(task)


@ndb.transactional
def update_marker(marker_key, student_key, contact, methods):
    """Look for a marker for the requested methods.  If one is found, return
    its short_id, if multiple are found, merge them, then return the short_id.
    """
    marker = marker_key.get()

    marker.methods = list(set(marker.methods) | set(methods))

    student_contacts = marker.students.setdefault(str(student_key.id()), [])

    # TODO: Fix this.
    if contact not in student_contacts:
        student_contacts.append(contact)

    marker.put()

    insert_merge_task(marker.event, methods)


def insert_merge_task(event_key, search_methods):
    """Insert a task to merge contact markers for the given search_methods."""
    import random

    from google.appengine.api import taskqueue

    event_urlsafe = event_key.urlsafe()

    task = taskqueue.Task(
        url=MARKER_MERGE_ENDPOINT,
        countdown=random.randint(5, 190),
        params={
            'event': event_urlsafe,
            'methods': json.dumps(list(search_methods))
        }
    )

    taskqueue.Queue(name=MARKER_MERGE_QUEUE).add(task)


def merge_markers(event_key, search_methods):
    """Combine the contact markers for search_methods, merging as needed."""

    markers = find_markers_for_methods(event_key, search_methods)

    first_marker = None
    marker_map = {}
    # Organize markers by place holder
    place_holder_map = {}
    acknowledged = set()
    for marker in markers:
        first_marker = first_marker or marker  # TODO: Find a better way.
        marker_map[marker.key] = marker
        place_holder_map.setdefault(marker.place_holder, []).append(marker)
        if marker.acknowledged:
            acknowledged.add(marker.key)

    # Redirect dupes to the most-referenced marker to minimize RPCs needed.
    place_holders = sorted(
        place_holder_map, key=lambda x: len(place_holder_map[x]),
        reverse=True)

    base_marker_key = None
    if place_holders:
        base_marker_key = place_holders[0]
        if not base_marker_key and len(place_holder_map) > 1:
            base_marker_key = place_holders[1]

    if base_marker_key:
        base_marker = marker_map[base_marker_key]
    elif acknowledged:
        base_marker = marker_map[acknowledged.pop()]
    else:
        base_marker = first_marker

    for marker in markers:
        if marker == base_marker:
            continue

        # TODO: actually put the merged stuff.
        newly_acked_students = base_marker.merge(marker)

        update_marker_pair(base_marker, marker)

    # do_stuff_with_new_acks(newly_acked_students)


def update_marker_pair(marker1, marker2):
    @ndb.transactional(xg=True)
    def update_marker_pair(marker1, revision1, marker2, revision2):
        check_entity1 = marker1.key.get()
        if check_entity1.revision != revision1:
            raise Exception("Marker1 revision out of date.")

        check_entity2 = marker2.key.get()
        if check_entity2.revision != revision2:
            raise Exception("Marker2 revision out of date.")

        ndb.put_multi([marker1, marker2])

    update_marker_pair(marker1, marker1.revision, marker2, marker2.revision)


def mark_as_acknowledged(event_key, marker_key):
    """Mark a ContactMarker as acknowledged, and insert tasks to mark
    StudentMarker as acknowledged.
    """
    import time

    from .event import insert_count_update_task
    from .student_marker import mark_as_acknowledged as acknowledge_student

    @ndb.transactional
    def txn():
        marker = marker_key.get()
        if not marker:
            return

        marker.acknowledged = True
        marker.last_viewed_date = int(time.time())
        marker.count_visit += 1
        marker.put()
        return marker
    marker = txn()

    if not marker:
        return

    for student_id in marker.students:
        acknowledge_student(event_key, student_id)

    insert_count_update_task(event_key, marker.key, None, 'ack')


def update_count_comment(marker_key):
    """Update count comment each times student add new comment"""
    marker = marker_key.get()

    if not marker:
        return

    marker.count_comment += 1
    marker.put()
