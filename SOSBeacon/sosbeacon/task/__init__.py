import logging
import unicodedata

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import webapp2

# NOTE: Contact and Event models are imported here so the schemas are loaded.
from sosbeacon.contact import Contact
from sosbeacon.event import  update_event_counts
from sosbeacon.event import  update_event_contact
from sosbeacon.event import EVENT_UPDATE_QUEUE
from sosbeacon.event import Event
from sosbeacon.event import MethodMarker
from sosbeacon.utils import insert_tasks

GROUP_TX_QUEUE = "group-tx"
CONTACT_TX_QUEUE = "contact-tx"


# TODO: Replace with real api method...
def send_notification(*args, **kwargs):
    logging.info('send_notification(%s)', args)


class EventStartTxHandler(webapp2.RequestHandler):
    """Start the process of sending messages to every Contact associated
    with an Event.

    For each Group on an Event, insert a task that will start linearly
    scanning the group inserting a send-message job for each contact, and
    an add-to-group message for each student.
    """
    def post(self):
        # batch_id is used so that we can force a resend on an event.
        batch_id = self.request.get('batch', '')

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here, for namespacing purposes?
        event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found!', event_key)
            return

        if not event.active:
            logging.error('Event %s not active!', event_key)
            return

        if not event.notice_sent:
            logging.error('Event %s not ready to send!', event_key)
            return

        # TODO: Create / Handle some special "all" group.
        tasks = []
        for group_key in event.groups:
            group = group_key.urlsafe()
            name = "tx-s-%s-%s-%s" % (event_urlsafe, group, batch_id)
            tasks.append(taskqueue.Task(
                url='/task/event/tx/group',
                name=name,
                params={
                    'event': event_urlsafe,
                    'group': group,
                    'batch': batch_id
                }
            ))
            if len(tasks) > 10:
                insert_tasks(tasks, GROUP_TX_QUEUE)
                tasks = []

        if tasks:
            insert_tasks(tasks, GROUP_TX_QUEUE)


class EventGroupTxHandler(webapp2.RequestHandler):
    """Scan over the given group sequentially and insert a task for each
    Contact indicating that a message needs sent.
    """
    def post(self):
        from sosbeacon.student import Student

        BATCH_SIZE = 100

        # Used so we can force resends of the event.
        batch_id = self.batch_id = self.request.get('batch')

        event_urlsafe = self.request.get('event')
        event_key = ndb.Key(urlsafe=event_urlsafe)
        group_key = ndb.Key(urlsafe=self.request.get('group'))
        if not event_key or not group_key:
            return

        # Used in task-names to prevent fork-bombs.
        iteration = int(self.request.get('iter', 0))

        logging.debug('Processing Event %s, task %d of batch %s for Group %s.',
                      event_key, iteration, batch_id, group_key)

        event = event_key.get()
        event_key = self.event_key = event_key.urlsafe()
        if not event:
            logging.error('Event %s not found processing task %d for Group %s!',
                          event_key, iteration, group_key)
            return

        if not event.active:
            logging.error('Event %s not active!', event_key)
            return

        cursor = ndb.Cursor(urlsafe=self.request.get('cursor'))
        query = Student.query(Student.groups == group_key).order(Student.key)

        students, cursor, more = query.fetch_page(BATCH_SIZE,
                                                  start_cursor=cursor)
        if more:
            name = "tx-%s-%s-%s-%d" % (
                event_key, group_key.urlsafe(), batch_id, iteration)
            task = taskqueue.Task(
                url='/task/event/tx/group',
                name=name,
                params={
                    'event': event_key,
                    'group': group_key.urlsafe(),
                    'batch': batch_id,
                    'cursor': cursor.urlsafe(),
                    'iter': iteration + 1
                }
            )
            insert_tasks((task,), GROUP_TX_QUEUE)

        notify_level = 1 if event.who_to_notify == 'd' else None
        notify_parents_only = True if event.who_to_notify == 'p' else False

        # We want to start sending notices ASAP, so insert tx workers for each
        # contact, and a marker for the student here.  The relationship can be
        # determined after sending the message.
        self.seen_contacts = set()
        self.tx_workers = []
        student_markers = []
        for student in students:
            self._process_student(student)

            student_markers.append(get_student_marker_task(
                event_key.urlsafe(), student.key.urlsafe()))

            if len(student_markers) > 20:
                insert_tasks(student_markers)
                student_markers = []

        if self.tx_workers:
            insert_tasks(self.tx_workers)

        if student_markers:
            insert_tasks(student_markers)

        update_event_counts(
            event_key, group_key.urlsafe(), iteration,
            contact_count=len(self.seen_contacts),
            student_count=len(students))

    def _process_student(self, student):
        for contact in student.contacts[:self.notify_level]:
            # TODO: Optimize task building with memcache markers to
            # avoid building tasks that already exist.
            if not len(contact.methods) > 0:
                continue
            method = contact.methods[0]['value']
            if not method:
                continue

            name = "tx-%s-%s-%s" % (self.event_key, self.batch_id, method)
            if name in self.seen_contacts:
                continue
            self.seen_contacts.add(name)
            self.tx_workers.append(get_tx_worker_task(
                self.event_key, self.batch_id, method))

        if len(self.tx_workers) > 10:
            insert_tasks(self.tx_workers)
            self.tx_workers = []


class TryNextMethodTxHandler(webapp2.RequestHandler):
    """For any contacts in this group, try thier next contact method.

    Contact(s) with the given method have either failed to respond within
    retry-timeout seconds, or there was some other error sending notification.
    Find any associated students and try sending to the next method for each
    associated contact(s).
    """
    def post(self):
        from sosbeacon.student import Student

        # Used so we can force resends of the event.
        batch_id = self.batch_id = self.request.get('batch')

        event_key = ndb.Key(urlsafe=self.request.get('event'))
        if not event_key:
            return
        event_future = event_key.get_async()
        event_key = self.event_key = event_key.urlsafe()

        method_id = self.request.get('method')
        method_key = ndb.Key(MethodMarker, method_id, parent=event_key)
        if not method_id:
            return
        method_future = method_key.get_async()

        logging.debug('Trying next method for contacts with %s, for Event %s.',
                      method_id, event_key)

        event = event_future.get_result()
        if not event:
            logging.error('Event %s not found trying next for %s!',
                          event_key, method_id)
            return

        student_futures = ndb.get_multi_async(event.students)

        if not event.active:
            logging.error('Event %s not active!', event_key)
            return

        self.notify_level = 1 if event.notify_primary_only else None

        method = method_future.get_result()
        if not method:
            logging.debug('Method %s not found trying next for Event %s!',
                          method_id, event_key)
            return

        # Start sending notices ASAP, insert tx workers for each contact
        # method.  The relationship can be determined after sending the
        # message.
        self.seen_contacts = set()
        self.tx_workers = []
        for future in student_futures:
            # TODO: Use tasklets instead of loop here?
            student = future.get_result()

            # TODO: What marker do we insert here?  We just want the
            # relationship.  The student should already exist at this point.
            # Maybe we should use the same approach above too.  Insert a
            # relationship marker, and if the student marker doesn't exist,
            # we can create the student marker?
            # OR, maybe the approach is wrong.  Maybe this should just be done
            # via an indexed list of methods on the student marker?  This is
            # safe here, since it is all in the same entity group.
            # But, what happens when an as-of-yet unseen student is using this
            # method?  With the query approach, do we ever know that we should
            # go on to thier next contact?
            # This is where the first method helps, we can simply use
            # task-names to handle our deduplification and basically retry
            # for all students here.
            self._process_student(student)

            student_markers.append(get_student_marker_task(
                event_key.urlsafe(), student.key.urlsafe()))

            if len(student_markers) > 20:
                insert_tasks(student_markers)
                student_markers = []

        if self.tx_workers:
            insert_tasks(self.tx_workers)

        if student_markers:
            insert_tasks(student_markers)

        update_event_counts(
            event_key, group_key.urlsafe(), iteration,
            contact_count=len(self.seen_contacts),
            student_count=len(students))

    def _process_student(self, student):
        for contact in student.contacts[:self.notify_level]:
            # TODO: Optimize task building with memcache markers to
            # avoid building tasks that already exist.
            if not len(contact.methods) > 0:
                continue
            method = contact.methods[0]['value']
            if not method:
                continue

            name = "tx-%s-%s-%s" % (self.event_key, self.batch_id, method)
            if name in self.seen_contacts:
                continue
            self.seen_contacts.add(name)
            self.tx_workers.append(get_tx_worker_task(
                self.event_key, self.batch_id, method))

        if len(self.tx_workers) > 10:
            insert_tasks(self.tx_workers)
            self.tx_workers = []

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
        method_type = self.request.get('type')
        method = self.request.get('method')

        if not method:
            # TODO: Insert failed attempt marker.
            logging.error(
                'Contact method not provided, trying to notify for Event %s!',
                event_key.urlsafe())
            return

        if not method_type:
            # TODO: Insert failed attempt marker.
            logging.error(
                'Contact method type not provided, trying to notify %s for '
                'Event %s!', method, event_key.urlsafe())
            return

        logging.debug('Notifying Contact %s of Event %s.',
                      method, event_key)

        event = event_key.get()
        if not event:
            logging.error('Event %s not found, notifying Contact %s!',
                          event_key, method)
            return

        now = int(time())

        marker_key = ndb.Key(MethodMarker, method, parent=event_key)
        marker = marker_key.get()
        if marker:
            if marker.acknowledged:
                return

            tried_seconds_ago = now - marker.last_try
            if tried_seconds_ago < event.response_wait_seconds:
                return

            try_next_contact_method(event_key.urlsafe(), method, now)
            return

        # TODO: Send message about the event
        send_notification(event, method_type, method)

        update_event_contact(event_key.urlsafe(), method, now)


class EventUpdateHandler(webapp2.RequestHandler):
    """Handle operations on the event entity group.

    This includes updating counts, managing acknowledgments, and retries.
    """
    def post(self):
        # Max number of work-units to process in one go, and how long to lease.
        BATCH_SIZE = 500
        LEASE_SECONDS = 45

        event_key = ndb.Key(urlsafe=self.request.get('event'))

        update_queue = taskqueue.Queue(name=EVENT_UPDATE_QUEUE)
        updates = update_queue.lease_tasks_by_tag(LEASE_SECONDS, BATCH_SIZE,
                                                  tag=event_key.urlsafe())

        count_updates = {
            'contacts': 0,
            'students': 0,
            'ack': 0
        }

        marker_map = {}
        workers = []

        for update_task in updates:
            update = update_task.extract_params()
            if update['type'] == 'cnt':
                count_updates['contacts'] += int(update['contact_count'])
                count_updates['students'] += int(update['student_count'])
                continue

            method = update['method']
            marker_key = ndb.Key(MethodMarker, method, parent=event_key)

            if update['type'] == 'ack':
                count_updates['ack'] += 1
                marker = MethodMarker(
                    key=marker_key,
                    acknowledged=True,
                    acknowledged_at=int(update['when'])
                )
            elif update['type'] == 'tx':
                marker = MethodMarker(
                    key=marker_key,
                    last_try=int(update['when']),
                )
            elif update['type'] == 'ntxm':
                marker = MethodMarker(
                    key=marker_key,
                    try_next=True
                )
                workers.append(get_try_next_contact_task(
                    event_key.urlsafe, method))

            if marker_key in marker_map:
                marker_map[marker_key].merge(marker)
                continue

            marker_map[marker_key] = marker

        event_update(event_key, count_updates, marker_map)

        if workers:
            # Run these *after* the event update txn, since they may depend
            # on data written there.
            insert_tasks(workers)

        update_queue.delete_tasks(updates)

        if len(updates) >= BATCH_SIZE:
            insert_event_updator(event_key)


@ndb.transactional
def event_update(event_key, count_updates, marker_map):
    """Apply the given updates to an Event and its associated ContactMarkers
    and StudentMarkers.
    """
    keys = marker_map.keys()
    keys.append(event_key)

    marker_entities = ndb.get_multi(keys)
    event = marker_entities.pop()
    keys.pop() # Discard event key for loop...

    event.student_count += count_updates['students']
    event.contact_count += count_updates['contacts']
    event.acknowledged_count += count_updates['ack']

    to_put = [event]
    for key, marker in zip(keys, marker_entities):
        if not marker:
            to_put.append(marker_map[key])
            continue

        to_put.append(marker.merge(marker_map[key]))

    ndb.put_multi(to_put)

