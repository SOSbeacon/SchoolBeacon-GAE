
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
        raise ValueError('Non-empty value for search_methods is required.')

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

    insert_merge_task(event_key, search_methods)

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
        key_id = "%s:%s" % (event_key.id, short_id)
        marker = ContactMarker(
            id=key_id,
            event=event_key,
            name=contact.get('name'),
            students={student_key.id(): contact},
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
def update_marker(marker_key, student_key, contact, search_methods):
    """Look for a marker for the requested methods.  If one is found, return
    its short_id, if multiple are found, merge them, then return the short_id.
    """
    marker = marker_key.get()

    marker.search_methods = list(
        set(marker.search_methods) | set(search_methods))

    student_contacts = marker.students.setdefault(student_key, {})
    if contact['id'] not in student_contacts:
        student_contacts[contact['id']] = contact

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

