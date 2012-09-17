
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


class ContactMarker(EntityBase):
    """Used to store Contact-Events tx / view metadata."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    # Used to query for short URLs
    short_id = ndb.StringProperty('i')

    # contact name, for display
    name = ndb.StringProperty('nm')

    acknowledged = ndb.BooleanProperty('a', default=False)
    last_viewed_date = ndb.IntegerProperty('at', indexed=False)

    students = ndb.JsonProperty('s', indexed=False)

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

        marker['students'] = [student for student, name, voice in self.students]

        return marker

