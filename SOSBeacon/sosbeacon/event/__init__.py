"""This is the event "public" API."""

from .event import Event
from .event import event_query_schema
from .event import event_schema

from .message import Message
from .message import broadcast_to_groups
from .message import message_query_schema
from .message import message_schema


MARKER_ACK_QUEUE = 'contact-marker-ack'
MARKER_ACK_ENDPOINT = '/task/event/ack/contact_marker'


def acknowledge_event(event_key, marker_key):
    """Insert a task to mark the marker as acked."""
    from google.appengine.api import taskqueue

    event_urlsafe = event_key.urlsafe()
    marker_urlsafe = marker_key.urlsafe()

    #name = "ack-%s-%s-%d" % (
    #    event_urlsafe, marker_urlsafe, rounded_time_factor)
    taskqueue.add(
        queue_name=MARKER_ACK_QUEUE,
        url=MARKER_ACK_ENDPOINT,
        #name=name,
        params={
            'event': event_urlsafe,
            'marker': marker_urlsafe
        }
    )

