
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase

from sosbeacon.event.event import Event


CONTACT_MERGE_ENDPOINT = '/task/event/update/contact_marker'
CONTACT_MERGE_QUEUE = "contact-marker-update"

MARKER_MERGE_ENDPOINT = '/task/event/merge/contact_marker'
MARKER_MERGE_QUEUE = "contact-marker-merge"


marker_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'acknowledged': voluptuous.boolean(),
    'name': basestring,
    'responded': [basestring],
}

marker_query_schema = {
    'feq_acknowledged': voluptuous.boolean(),
    'fan_key': voluptuous.ndbkey()
}


class ContactMarker(EntityBase):
    """Used to store Contact-Events tx / view metadata.

    Key name is constructed as:
        event.short_id + ':' + ContactMarker.short_id
    """
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # Used to query for short URLs
    short_id = ndb.StringProperty('i')

    event = ndb.KeyProperty(Event)

    # contact name, for display
    name = ndb.StringProperty('nm')

    acknowledged = ndb.BooleanProperty('a', default=False)
    last_viewed_date = ndb.IntegerProperty('at', indexed=False)

    students = ndb.JsonProperty('s', indexed=False)

    methods = ndb.StringProperty('m', indexed=True, repeated=True)

    place_holder = ndb.KeyProperty('p', indexed=False)

    def merge(self, other):
        """Merge this MethodMarker entity with another MethodMarker."""
        other.place_holder = self.key

        self.acknowledged = max(self.acknowledged, other.acknowledged)

        self.last_viewed_date = max(
            self.last_viewed_date if self.last_viewed_date else 0,
            other.last_viewed_date if other.last_viewed_date else 0)

        self.short_id = self.short_id or other.short_id

        self.name = self.name or other.name

        students = set()
        if self.students:
            students |= set(self.students)

        if other.students:
            students |= set(other.students)

        self.students = list(students)

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
        marker['name'] = self.name
        marker['acknowledged'] = self.acknowledged
        marker['last_viewed_date'] = self.last_viewed_date

        marker['students'] = [
            student for student, name, voice in self.students]

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


def create_or_update_marker(event_key, student_key, contact, search_methods):
    """Look for a marker for the requested methods.  If one is found, return
    its short_id, if multiple are found, request a merge, then return one's
    short_id.
    """
    if not search_methods:
        raise ValueError('Non-empty value for search_methods is required.')

    if not contact:
        raise ValueError('Contact is required.')

    if not student_key:
        raise ValueError('student_key is required.')

    if not event_key:
        raise ValueError('event_key is required.')

    marker = get_marker_for_methods(event_key, search_methods)

    if not marker:
        # TODO: What needs set?
        short_id = str(ContactMarker.allocate_ids(size=1, parent=event_key)[0])
        key_id = "%s:%s" % (event_key.id(), short_id)
        marker = ContactMarker(
            id=key_id,
            event=event_key,
            name=contact.get('name'),
            students={str(student_key.id()): [contact]},
            short_id=short_id,
            methods=search_methods)
        marker.put()
        return marker.short_id

    insert_update_marker_task(marker.key, student_key, contact, search_methods)

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
            'contact': contact,
            'methods': search_methods
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
    from google.appengine.api import taskqueue

    event_urlsafe = event_key.urlsafe()

    task = taskqueue.Task(
        url=MARKER_MERGE_ENDPOINT,
        params={
            'event': event_urlsafe,
            'methods': search_methods
        }
    )

    taskqueue.Queue(name=MARKER_MERGE_QUEUE).add(task)


def merge_markers(event_key, search_methods):
    """Combine the contact markers for search_methods, merging as needed."""

    markers = find_markers_for_methods(event_key, search_methods)

    marker_map = {}
    # Organize markers by place holder
    place_holder_map = {}
    acknowledged = set()
    for marker in markers:
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
        base_marker = markers[0]

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

