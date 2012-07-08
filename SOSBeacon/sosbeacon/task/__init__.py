import logging

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import webapp2

from sosbeacon.contact import Contact
from sosbeacon.event import  notify_contact
from sosbeacon.event import  update_contact_counts
from sosbeacon.event import  update_event_contact
from sosbeacon.event import EVENT_UPDATE_QUEUE
from sosbeacon.event import Event
from sosbeacon.event import EventMarker
from sosbeacon.utils import insert_tasks

GROUP_TX_QUEUE = "group-tx"
CONTACT_TX_QUEUE = "contact-tx"


class EventStartTxHandler(webapp2.RequestHandler):
    """Start the process of sending messages to every Contact associated
    with an Event.

    For each Group on an Event, insert a task that will start linearly
    scanning the group inserting a job for each contact.
    """
    def post(self):
        event_key = ndb.Key(urlsafe=self.request.get('event'))
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        tasks = []
        for group_key in event.groups:
            event = event_key.urlsafe()
            group = group_key.urlsafe()
            name = "tx-s-%s-%s" % (event, group)
            tasks.append(taskqueue.Task(
                url='/task/event/tx/group',
                name=name,
                params={
                    'event': event,
                    'group': group
                }
            ))

        if not tasks:
            return

        # TODO: Switch over to using a divide and retry here.
        insert_tasks(tasks, GROUP_TX_QUEUE)

        # TODO: Insert task to mark Event as notice sent


class EventGroupTxHandler(webapp2.RequestHandler):
    """Linearly scan the given group and insert a task for each Contact
    indicating that a message needs sent.
    """
    def post(self):
        from sosbeacon.student import Student

        event_key = ndb.Key(urlsafe=self.request.get('event'))
        group_key = ndb.Key(urlsafe=self.request.get('group'))
        task_no = int(self.request.get('task_no', 0))

        logging.debug('Processing Event %s, batch %d for Group %s.',
                      event_key, task_no, group_key)

        event = event_key.get()
        if not event:
            logging.error('Event %s not found, batch %d for Group %s!',
                          event_key, task_no, group_key)
            return

        cursor = ndb.Cursor(urlsafe=self.request.get('cursor'))
        query = Student.query(Student.groups == group_key).order(Student.key)

        students, cursor, more = query.fetch_page(100, start_cursor=cursor)
        if more:
            name = "tx-%d-%s-%s" % (
                task_no, event_key.urlsafe(), group_key.urlsafe())
            task = taskqueue.Task(
                url='/task/event/tx/group',
                name=name,
                params={
                    'event': event_key.urlsafe(),
                    'group': group_key.urlsafe(),
                    'cursor': cursor.urlsafe(),
                    'task_no': task_no + 1
                }
            )
            insert_tasks((task,), GROUP_TX_QUEUE)

        event_key = event_key.urlsafe()
        notify_level = 1 if event.notify_primary_only else None

        # We want to start sending notices ASAP, so just insert a marker
        # for each contact here.  The rest can be determined after sending
        # the message.
        work = {}
        for student in students:
            for contact in student.contacts[:notify_level]:
                # TODO: Optimize task building with memcache markers to
                # avoid building tasks that already exist.
                contact_key = contact.urlsafe()
                name = "tx-%s-%s" % (event_key, contact_key)
                work[name] = taskqueue.Task(
                    url='/task/event/tx/contact',
                    name=name,
                    params={'event': event_key,
                            'contact': contact_key}
                )

        if not work:
            return

        # TODO: Need batch split / retry logic here too.
        contact_work = work.values()
        insert_tasks(contact_work, CONTACT_TX_QUEUE)

        update_contact_counts(
            event_key, len(contact_work), group_key.urlsafe(), task_no)


class EventContactTxHandler(webapp2.RequestHandler):
    """Send a message about the specified Event to the specified Contact.

    Inserts a task to write a "message sent" marker for this Event-Contact
    combination.

    If the Contact has already been contacted within the specified
    response-wait time, return without contact attempt.  Otherwise, if the
    last contact attempt was longer than response-wait time, try the next
    contact method.
    """
    def post(self):
        from time import time

        event_key = ndb.Key(urlsafe=self.request.get('event'))
        contact_key = ndb.Key(urlsafe=self.request.get('contact'))

        logging.debug('Notifying Contact %s of Event %s.',
                      contact_key, event_key)

        event, contact = ndb.get_multi((event_key, contact_key))
        if not event:
            logging.error('Event %s not found, notifying Contact %s!',
                          event_key, contact_key)
            return

        if not contact:
            logging.error('Contact %s not found, notifying for Event %s!',
                          contact_key, event_key)
            return

        now = int(time())
        next_contact_method = -1

        marker_key = ndb.Key(EventMarker, contact_key.id(), parent=event_key)
        marker = marker_key.get()
        if marker:
            if marker.acknowledged:
                return

            tried_seconds_ago = now - marker.last_try
            if tried_seconds_ago < event.response_wait_seconds:
                return

            next_contact_method = marker.last_contact_method

        next_contact_method = min(next_contact_method + 1,
                                  len(contact.methods))

        # TODO: Send message about the event
        notify_contact(event, contact, next_contact_method)

        update_event_contact(event_key.urlsafe(), contact_key.urlsafe(),
                             next_contact_method, now)


class EventUpdateHandler(webapp2.RequestHandler):
    def post(self):
        BATCH_SIZE = 500

        event_key = ndb.Key(urlsafe=self.request.get('event'))
        update_queue = taskqueue.Queue(name=EVENT_UPDATE_QUEUE)

        updates = update_queue.lease_tasks_by_tag(45, BATCH_SIZE,
                                                  tag=event_key.urlsafe())

        count_updates = {
            'total': 0,
            'ack': 0
        }
        marker_map = {}

        for update_task in updates:
            update = update_task.extract_params()
            if update['type'] == 'cnt':
                count_updates['total'] += int(update['contact_count'])
                continue

            contact_id = ndb.Key(urlsafe=update['contact']).id()
            marker_key = ndb.Key(EventMarker, contact_id, parent=event_key)

            if update['type'] == 'ack':
                count_updates['ack'] += 1
                marker = EventMarker(
                    key=marker_key,
                    acknowledged=True,
                    acknowledged_at=int(update['when'])
                )
            elif update['type'] == 'tx':
                marker = EventMarker(
                    key=marker_key,
                    last_try=int(update['when']),
                    last_contact_method=int(update['method'])
                )

            if marker_key in marker_map:
                marker_map[marker_key].merge(marker)
                continue

            marker_map[marker_key] = marker

        event_update(event_key, count_updates, marker_map)
        update_queue.delete_tasks(updates)
        if len(updates) >= BATCH_SIZE:
            insert_event_updator(event_key)


@ndb.transactional
def event_update(event_key, count_updates, marker_map):
    """Apply the given updates to an Event and its EventMarkers."""
    keys = marker_map.keys()
    keys.append(event_key)

    marker_entities = ndb.get_multi(keys)
    event = marker_entities.pop()
    keys.pop()

    event.contact_count += count_updates['total']
    event.acknowledged_count += count_updates['ack']

    to_put = [event]
    for key, marker in zip(keys, marker_entities):
        if not marker:
            to_put.append(marker_map[key])
            continue

        to_put.append(marker.merge(marker_map[key]))

    ndb.put_multi(to_put)

