
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase
from skel.rest_api.rules import RestQueryRule

from sosbeacon.utils import get_latest_datetime

marker_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'acknowledged': voluptuous.boolean(),
    'name': basestring,
    'responded': [basestring],
}

marker_query_schema = {
    'feq_acknowledged': voluptuous.boolean(),
    'fan_key': voluptuous.ndbkey(),
    'name': basestring
}


class StudentMarker(EntityBase):
    """Used to store Student-Events tx / ack metadata."""
    _query_properties = {
        'name': RestQueryRule('name_', lambda x: x.lower() if x else ''),
    }

   # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    name = ndb.StringProperty('n', indexed=False)
    contacts = ndb.JsonProperty('c')

    # When did we last try sending a broadcast to this person's contacts?
    last_broadcast = ndb.DateTimeProperty('lb', indexed=False)

    # Has ANYone acknowledged?
    acknowledged = ndb.BooleanProperty('a', default=False)
    acknowledged_at = ndb.IntegerProperty('at', indexed=False)

    # Has EVERYone acknowledged?
    all_acknowledged = ndb.BooleanProperty('aa', default=False)
    all_acknowledged_at = ndb.IntegerProperty('at', indexed=False)

    def merge(self, other):
        """Merge this StudentMarker entity with another StudentMarker."""
        self.name = self.name or other.name

        self.last_broadcast = get_latest_datetime(self.last_broadcast,
                                                  other.last_broadcast)

        if not other.contacts:
            # All other info comes from contacts, so if there's no change bail.
            return self

        if not self.contacts:
            self.contacts = {}

        for new_hash, new_contact in other.contacts.iteritems():

            contact = self.contacts.get(new_hash)
            if not contact:
                # New contact
                self.contacts[new_hash] = new_contact
                contact = new_contact
            else:
                # Update existing contact.
                contact['acked'] = max(contact.get('acked'),
                                       new_contact.get('acked'))

                contact['acked_at'] = max(contact.get('acked_at'),
                                          new_contact.get('acked_at'))

                contact['sent'] = max(contact.get('sent'),
                                      new_contact.get('sent'))

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
        marker['name'] = self.name
        marker['contacts'] = self.contacts
        _handle_date('last_broadcast', self.last_broadcast)
        marker['acknowledged'] = self.acknowledged
        _handle_date('acknowledged_at', self.acknowledged_at)
        marker['all_acknowledged'] = self.acknowledged
        _handle_date('all_acknowledged_at', self.all_acknowledged_at)

        return marker


def create_or_update_marker(event_key, student):
    """Create a StudentMarker if one doesn't exist, otherwise update the
    last_broadcast timestamp if one does.
    """
    from datetime import datetime

    marker_key = ndb.Key(
        StudentMarker, "%s:%s" % (event_key.id(), student.key.id()))

    new_marker = StudentMarker(
        key=marker_key,
        name=student.name,
        contacts=_build_contact_map(student.contacts[:])
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


def _build_contact_map(contacts):
    """Take a list of contacts and convert them to a map, using the hash of
    the contact as the key.
    """
    contact_map = {}
    for contact in contacts:
        contact_hash = _hash_contact(contact)
        contact_map[contact_hash] = contact

    return contact_map


def _hash_contact(contact):
    """Take a contact dict and return a hash for that contact."""
    import hashlib

    tokens = [unicode(contact.get('name'))]
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

