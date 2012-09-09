
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import voluptuous

from skel.datastore import EntityBase

GROUP_TX_QUEUE = "group-tx"

message_schema = {
    'key': voluptuous.any(None, voluptuous.ndbkey(), ''),
    'event': voluptuous.ndbkey(),
    'timestamp': basestring,
    'type': basestring,
    'message': {
        'message': basestring,
        'sms': basestring
    }
}

message_query_schema = {
    'feq_event': voluptuous.ndbkey()
}


class Message(EntityBase):
    """Represents a message in an event's message stream."""
    # Store the schema version, to aid in migrations.
    version_ = ndb.IntegerProperty('v_', default=1)

    event = ndb.KeyProperty('e')

    timestamp = ndb.DateTimeProperty('ts', auto_now_add=True)

    message_type = ndb.StringProperty('mt')
    message = ndb.JsonProperty('m')

    @classmethod
    def from_dict(cls, data):
        """Instantiate a Message entity from a dict of values."""
        key = data.get("key")
        message = None
        if key:
            message = key.get()

        if not message:
            from google.appengine.api import namespace_manager

            event_key = data.get('event')
            if not event_key:
                # TODO: Raise some other error type here?
                raise Exception("Event key is required.")

            event = event_key.get()
            if not event:
                # TODO: Raise some other error type here?
                raise Exception("Event not found.")

            if event.school != unicode(namespace_manager.get_namespace()):
                # TODO: Raise some other error type here?
                raise Exception("Security violation!")

            message = cls(event=event.key)

        message_type = data.get('type')
        message.message_type = message_type

        message_data = data.get('message')
        if message_type == 'c':
            assert ['body'] == message_data.keys(), "Invalid comment payload."

        if message_type == 'b':
            assert ['sms', 'email'] == message_data.keys(),\
                   "Invalid broadcast payload."

            # TODO: Ensure user is an admin.
            # TODO: Initiate send.

        message.message = message_data

        return message

    def to_dict(self):
        """Return a Message entity represented as a dict of values
        suitable for Message.from_dict.
        """
        message = self._default_dict()
        message["version"] = self.version_

        message['event'] = self.event
        message['timestamp'] = self.timestamp
        message['type'] = self.message_type
        message['message'] = self.message

        return message


def broadcast_to_groups(group_keys, message_key, batch_id=''):
    """Scan over the given set of groups, sending the broadcast to everyone
    in those groups.
    """
    from sosbeacon.utils import insert_tasks

    from sosbeacon.group import Group
    from sosbeacon.group import ALL_GROUPS_ID

    if len(group_keys) == 1 and group_keys[0].id == ALL_GROUPS_ID:
        group_keys = Group.query().order(Group.key).iter(keys_only=True)

    tasks = []
    for group_key in group_keys:
        # TODO: Batch tasks or start
        tasks.append(get_group_broadcast_task(group_key, message_key, batch_id))

        if len(tasks) > 10:
            insert_tasks(tasks, GROUP_TX_QUEUE)
            tasks = []

    if tasks:
        insert_tasks(tasks, GROUP_TX_QUEUE)


def get_group_broadcast_task(group_key, message_key, batch_id='',
                             iteration=0, cursor=''):
    """Get a task to scan and broadcast messages to all students in group."""
    group_urlsafe = group_key.urlsafe()
    message_urlsafe = message_key.urlsafe()

    name = "tx-%s-%s-%s-%d" % (
        group_urlsafe, message_urlsafe, batch_id, iteration)
    return taskqueue.Task(
        url='/task/event/tx/group',
        name=name,
        params={
            'group': group_urlsafe,
            'message': message_urlsafe,
            'batch': batch_id,
            'cursor': cursor.urlsafe(),
            'iter': iteration
        }
    )

def broadcast_to_group(group, message, iteration=0, cursor=None):
    """Scan over people in the group, starting from cursor if provided,
    sending the broadcast to every contact.
    """

