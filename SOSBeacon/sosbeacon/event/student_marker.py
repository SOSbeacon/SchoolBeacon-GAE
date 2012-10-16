
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase

from sosbeacon.utils import get_latest_datetime

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


class StudentMarker(EntityBase):
    """Used to store Student-Events tx / ack metadata."""
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
        marker["version"] = self.version_
        marker['name'] = self.name
        marker['acknowledged'] = self.acknowledged
        marker['all_acknowledged'] = self.acknowledged
        marker['last_viewed_date'] = self.last_viewed_date

        return marker


def build_contact_map(contacts):
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

