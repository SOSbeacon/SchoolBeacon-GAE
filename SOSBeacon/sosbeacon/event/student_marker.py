
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
            self.contacts = []

        for contact in other.contacts:
            new_acked = contact.pop('acked', None)
            new_acked_at = contact.pop('acked_at', None)
            new_sent = contact.pop('sent', None)

            try:
                original_index = self.contacts.index(contact)
            except ValueError:
                original_index = 0

            if not original_index:
                # New contact
                self.contacts.append(contact)

            else:
                # Existing contact
                original = self.contacts[original_index]
                original['acked'] = max(original.get('acked'), new_acked)
                original['acked_at'] = max(original.get('acked_at'),
                                           new_acked_at)
                original['sent'] = max(original.get('sent'), new_sent)
                contact = original

            # Update overall information.
            self.acknowledged = max(self.acknowledged,
                                    contact.get('acked'))
            self.acknowledged_at = max(self.acknowledged_at,
                                       contact.get('acked_at'))

            self.all_acknowledged = min(self.all_acknowledged,
                                        contact.get('acked'))

            self.all_acknowledged_at = None if not self.all_acknowledged else max(
                self.all_acknowledged_at, contact.get('acked_at'))

            self.last_broadcast = max(self.last_broadcast,
                                      contact.get('sent'))

        return self

    def to_dict(self):
        """Return a MethodMarker entity represented as a dict of values."""

        marker = self._default_dict()
        marker["version"] = self.version_
        marker['name'] = self.name
        marker['acknowledged'] = self.acknowledged
        marker['last_viewed_date'] = self.last_viewed_date


        return marker
