
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

from sosbeacon.event.event import Event

from sosbeacon.utils import get_latest_datetime

marker_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'acknowledged': voluptuous.boolean(),
    'first_name': basestring,
    'last_name': basestring,
    'responded': [basestring],
    'is_direct': voluptuous.boolean(),
}

marker_query_schema = {
    'feq_acknowledged': voluptuous.boolean(),
    'feq_event': voluptuous.ndbkey(),
    'fan_key': voluptuous.ndbkey(),
    'first_name': basestring,
    'first_name': basestring,
    'feq_is_direct': voluptuous.boolean(),
}


class StudentMarker(EntityBase):
    """Used to store Student-Events tx / ack metadata."""
    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower() if x else ''),
    }

   # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    event = ndb.KeyProperty(Event)

    first_name = ndb.StringProperty('fn', indexed=False)
    last_name = ndb.StringProperty('ln', indexed=False)
    contacts = ndb.JsonProperty('c')

    # When did we last try sending a broadcast to this person's contacts?
    last_broadcast = ndb.DateTimeProperty('lb', indexed=False)

    # Has ANYone acknowledged?
    acknowledged = ndb.BooleanProperty('a', default=False)
    acknowledged_at = ndb.IntegerProperty('at', indexed=False)

    # Has EVERYone acknowledged?
    all_acknowledged = ndb.BooleanProperty('aa', default=False)
    all_acknowledged_at = ndb.IntegerProperty('at', indexed=False)

    is_direct = ndb.BooleanProperty('id')

    def merge(self, other):
        """Merge this StudentMarker entity with another StudentMarker."""
        self.first_name = other.first_name or self.first_name
        self.last_name = other.last_name or self.last_name

        self.last_broadcast = get_latest_datetime(self.last_broadcast,
                                                  other.last_broadcast)

        if not other.contacts:
            # All other info comes from contacts, so if there's no change bail.
            return self

        if not self.contacts:
            self.contacts = []

#        for new_hash, new_contact in other.contacts.iteritems():
        for i in range(len(other.contacts)):

            contact = self.contacts[i]
            if not contact:
                # New contact
                self.contacts[i] = other.contacts[i]
                contact = other.contacts[i]
            else:
                # Update existing contact.
                contact['acked'] = max(contact.get('acked'),
                                       other.contacts[i].get('acked'))

                contact['acked_at'] = max(contact.get('acked_at'),
                                          other.contacts[i].get('acked_at'))

                contact['sent'] = max(contact.get('sent'),
                                      other.contacts[i].get('sent'))

            # Update overall information.
            self.acknowledged = max(self.acknowledged,
                                    contact.get('acked'))

            self.acknowledged_at = max(self.acknowledged_at,
                                       contact.get('acked_at'))

            #self.all_acknowledged = min(self.all_acknowledged,
            #                            contact.get('acked'))

            #self.all_acknowledged_at = None if not self.all_acknowledged else max(
            #    self.all_acknowledged_at, contact.get('acked_at'))

            #self.last_broadcast = max(self.last_broadcast,
            #                          contact.get('sent'))
        return self

    def to_dict(self):
        """Return a MethodMarker entity represented as a dict of values."""

        marker = self._default_dict()

        def _handle_date(field, prop):
            marker[field] = None
            if prop:
                marker[field] = prop.strftime('%Y-%m-%d %H:%M')

        marker["version"] = self.version_
        marker['first_name'] = self.first_name
        marker['last_name'] = self.last_name
        marker['contacts'] = self.contacts
        _handle_date('last_broadcast', self.last_broadcast)
        marker['acknowledged'] = self.acknowledged
        _handle_date('acknowledged_at', self.acknowledged_at)
        marker['all_acknowledged'] = self.acknowledged
        _handle_date('all_acknowledged_at', self.all_acknowledged_at)
        marker['is_direct'] = self.is_direct

        return marker


def create_or_update_marker(event_key, student, message_key):
    """Create a StudentMarker if one doesn't exist, otherwise update the
    last_broadcast timestamp if one does.
    """
    from datetime import datetime
    from sosbeacon.event.event import insert_count_update_task

    marker_key = ndb.Key(
        StudentMarker, "%s:%s" % (event_key.id(), student.key.id()))

    if student.is_direct:
        new_marker = StudentMarker(
            key=marker_key,
            event=event_key,
            first_name=student.first_name,
            last_name=student.last_name,
            contacts=_build_contact_map(student.contacts[:]),
            is_direct=True
        )
    else:
        new_marker = StudentMarker(
            key=marker_key,
            event=event_key,
            first_name=student.first_name,
            last_name=student.last_name,
            contacts=_build_contact_map(student.contacts[:]),
            is_direct=False
        )

    @ndb.transactional
    def txn(new_marker):
        marker = new_marker.key.get()

        if marker:
            marker.merge(new_marker)
        else:
            marker = new_marker

        marker.last_broadcast = datetime.now()

        marker.put()

    txn(new_marker)

    insert_count_update_task(event_key, student.key, message_key, 'student')


def _build_contact_map(contacts):
    """Take a list of contacts and convert them to a map, using the hash of
    the contact as the key.
    """
    contact_map = []
    for contact in contacts:
#        contact_hash = _hash_contact(contact)
#        contact_map[contact_hash] = contact
        contact_map.append(contact)

    return contact_map


def _hash_contact(contact):
    """Take a contact dict and return a hash for that contact."""
    import hashlib

    tokens = [unicode(contact.get('first_name'))]
    methods = contact.get('methods')
    if methods:
        tokens.extend(unicode(method.get('value')) for method in methods)

    tokens.sort()

    return hashlib.sha1('|'.join(tokens)).hexdigest()


def mark_as_acknowledged(event_key, student_id):
    """Mark a StudentMarker as acknowledged."""
    import time

    # FIXME: Update contact and check for all.

    marker_key = ndb.Key(
        StudentMarker, "%s:%s" % (event_key.id(), student_id))

    @ndb.transactional
    def txn():
        marker = marker_key.get()
        if not marker:
            return

        marker.acknowledged = True
        marker.acknowledged_at = int(time.time())
        marker.put()
        return marker
    txn()

