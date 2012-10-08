
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase


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

        last_broadcast = max(self.last_broadcast, other.last_broadcast)

        for contact_key, new_contact in other.contacts.iteritems():
            contact = self.contacts.get(contact_key)
            if contact:
                contact['acked'] = max(contact['acked'], new_contact['acked'])

                last_sent = max(contact['sent'], new_contact['sent'])
                contact['sent'] = last_sent
                last_broadcast = max(last_sent, last_broadcast)

            self.contacts[contact_key] = contact

        self.last_broadcast = last_broadcast

        self.acknowledged = max(self.acknowledged, other.acknowledged)

        self.acknowledged_at = get_latest_datetime(
            self.acknowledged_at, other.acknowledged_at)

        self.all_acknowledged = max(
            self.all_acknowledged, other.all_acknowledged)

        self.all_acknowledged_at = get_latest_datetime(
            self.all_acknowledged_at, other.acknowledged_at)

        if not self.all_acknowledged:
            self.all_acknowledged = all(
                [contact.get('acked') for contact in self.contacts])

        return self

    def to_dict(self):
        """Return a MethodMarker entity represented as a dict of values."""

        marker = self._default_dict()
        marker["version"] = self.version_
        marker['name'] = self.name
        marker['acknowledged'] = self.acknowledged
        marker['last_viewed_date'] = self.last_viewed_date

        marker['students'] = [student for student, name, voice in self.students]

        return marker

