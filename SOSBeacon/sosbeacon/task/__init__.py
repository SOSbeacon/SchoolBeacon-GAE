import logging

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import webapp2

# NOTE: The Event model is imported here so the schema is loaded.
from sosbeacon.event import EVENT_UPDATE_QUEUE
from sosbeacon.event import Event
from sosbeacon.event import MethodMarker
from sosbeacon.event import get_try_next_method_task
from sosbeacon.event import get_tx_worker_task
from sosbeacon.event import insert_event_updator
from sosbeacon.event import send_notification
from sosbeacon.event import get_student_method_marker
from sosbeacon.event import update_event_contact
from sosbeacon.event import update_event_counts
from sosbeacon.utils import insert_tasks

GROUP_TX_QUEUE = "group-tx"
METHOD_TX_QUEUE = "contact-tx"


class EventStartTxHandler(webapp2.RequestHandler):
    """Start the process of sending messages to every Contact associated
    with an Event.

    For each Group on an Event, insert a task that will sequentially scan the
    group inserting a send-message job for each contact, and an add-to-group
    message for each student.
    """
    def post(self):
        # batch_id is used so that we can force resend of notices for an event.
        batch_id = self.request.get('batch', '')

        event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            logging.error('No event key given.')
            return

        # TODO: Use event id rather than key here for namespacing purposes?
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

        groups = event.groups
        if len(groups) == 1 and groups[0].id() == '__all_groups__':
            from sosbeacon.group import Group
            groups = Group.query().iter(keys_only=True)

        # TODO: Create / handle an "all" group.
        tasks = []
        for group_key in groups:
            group_urlsafe = group_key.urlsafe()
            name = "tx-s-%s-%s-%s" % (event_urlsafe, group_urlsafe, batch_id)
            tasks.append(taskqueue.Task(
                url='/task/event/tx/group',
                name=name,
                params={
                    'event': event_urlsafe,
                    'group': group_urlsafe,
                    'batch': batch_id
                }
            ))
            if len(tasks) > 10:
                insert_tasks(tasks, GROUP_TX_QUEUE)
                tasks = []

        if tasks:
            insert_tasks(tasks, GROUP_TX_QUEUE)


class EventGroupTxHandler(webapp2.RequestHandler):
    """Sequentially scan the given group, insert a task for each Contact
    indicating a message needs sent, insert a task for each student
    indicating their membership in the event (also used to create an index
    mapping students to each contact a message is sent for).
    """
    BATCH_SIZE = 100

    def post(self):
        # Used to force resends of event notices.
        self.batch_id = self.request.get('batch', '')

        self.event_urlsafe = event_urlsafe = self.request.get('event')
        self.group_urlsafe = group_urlsafe = self.request.get('group')
        if not event_urlsafe or not group_urlsafe:
            logging.error('Missing event, %s, or group, %s, key.',
                          event_urlsafe, group_urlsafe)
            return

        # Used in task-names to prevent task-bombs.
        self.iteration = iteration = int(self.request.get('iter', 0))

        logging.debug('Processing Event %s, task %d of batch %s for Group %s.',
                      event_urlsafe, iteration, self.batch_id, group_urlsafe)

        self.event_key = event_key = ndb.Key(urlsafe=event_urlsafe)
        event = event_key.get()
        if not event:
            logging.error('Event %s not found; task %d, Group %s!',
                          event_urlsafe, iteration, group_urlsafe)
            return

        if not event.active:
            logging.error('Event %s not active!', event_urlsafe)
            return

        students = self._get_students()

        self.notify_level = 1 if event.who_to_notify == 'd' else None
        self.notify_parents_only = True if event.who_to_notify == 'p' else False

        # We want to start sending notices ASAP, so insert tx workers for each
        # contact, and a marker for the student-contact index here.  The
        # relationship index can be updated after sending the message.
        self.seen_methods = set()
        self.tx_workers = []
        student_markers = []
        for student in students:
            student_markers.extend(self._process_student(student))

            if len(student_markers) > 20:
                insert_tasks(student_markers, EVENT_UPDATE_QUEUE)
                student_markers = []

        if self.tx_workers:
            insert_tasks(self.tx_workers, METHOD_TX_QUEUE)

        if student_markers:
            insert_tasks(student_markers, EVENT_UPDATE_QUEUE)

        update_event_counts(
            event_key, group_urlsafe, iteration,
            contact_count=len(self.seen_methods),
            student_count=len(students))

    def _get_students(self):
        """Return the next batch of students in this group, insert continuation
        task if there are more to process for this batch.
        """
        from sosbeacon.student import Student

        query = Student.query().order(Student.key)

        group_key = ndb.Key(urlsafe=self.group_urlsafe)
        if group_key.id() != '__all__':
            query = query.filter(Student.groups == group_key)

        start_cursor = ndb.Cursor(urlsafe=self.request.get('cursor'))

        students, cursor, more = query.fetch_page(self.BATCH_SIZE,
                                                  start_cursor=start_cursor)
        if more:
            self._insert_continuation(cursor)

        return students

    def _insert_continuation(self, cursor):
        """Insert a task to continue scanning of students in this group."""
        name = "tx-%s-%s-%s-%d" % (
            self.event_urlsafe, self.group_urlsafe,
            self.batch_id, self.iteration)
        task = taskqueue.Task(
            url='/task/event/tx/group',
            name=name,
            params={
                'event': self.event_urlsafe,
                'group': self.group_urlsafe,
                'batch': self.batch_id,
                'cursor': cursor.urlsafe(),
                'iter': self.iteration + 1
            }
        )
        insert_tasks((task,), GROUP_TX_QUEUE)

    def _process_student(self, student):
        markers = []
        for contact in student.contacts[:self.notify_level]:
            # TODO: Optimize task building with memcache markers to
            # avoid building tasks that already exist.

            #if self.notify_parents_only and contact.type != 'p':
            #    continue
            methods = contact.get('methods')

            if not methods:
                continue

            method = methods.pop(0)['value']
            if not method:
                continue

            methods = [next_method['value'] for next_method in methods]
            markers.append(get_student_method_marker(
                self.event_key, method, methods,
                student.key, name=contact.get('name')))

            if method in self.seen_methods:
                continue

            self.seen_methods.add(method)
            self.tx_workers.append(get_tx_worker_task(
                self.event_key, self.batch_id, method))

        if len(self.tx_workers) > 10:
            insert_tasks(self.tx_workers, METHOD_TX_QUEUE)
            self.tx_workers = []

        return markers


class TryNextMethodTxHandler(webapp2.RequestHandler):
    """For any contacts in this event who use this method, try their next
    contact method.

    Contact(s) with the given method have either failed to respond within
    retry-timeout seconds, or there was some other error sending notification.
    Find any associated students and try sending to the next method for each
    associated contact(s).
    """
    def post(self):
        # Used so we can force resends of the event.
        self.batch_id = self.request.get('batch')

        event_urlsafe = self.event_urlsafe = self.request.get('event')
        if not event_urlsafe:
            return

        event_key = ndb.Key(urlsafe=event_urlsafe)
        event_future = event_key.get_async()

        method_id = self.request.get('method')
        if not method_id:
            return

        method_key = ndb.Key(MethodMarker, method_id, parent=event_key)
        method_future = method_key.get_async()

        logging.debug('Trying next method for contacts with %s, for Event %s.',
                      method_id, event_urlsafe)

        event = event_future.get_result()
        if not event:
            logging.error('Event %s not found trying next for %s!',
                          event_urlsafe, method_id)
            return

        if not event.active:
            logging.warning('Event %s not active!', event_key)
            return

        method = method_future.get_result()
        if not method:
            # NOTE: Should this ever happen?
            logging.debug('MethodMarker %s not found trying next for Event %s!',
                          method_id, event_urlsafe)
            return

        # Start sending notices ASAP, insert tx workers for each contact
        # method.  The relationship can be determined after sending the
        # message.
        self.seen_methods = set()
        self.tx_workers = []
        student_markers = []
        for student in method.students:
            student_markers.extend(self._process_student(student))

            if len(student_markers) > 20:
                insert_tasks(student_markers, EVENT_UPDATE_QUEUE)
                student_markers = []

        if self.tx_workers:
            insert_tasks(self.tx_workers, METHOD_TX_QUEUE)

        if student_markers:
            insert_tasks(student_markers, EVENT_UPDATE_QUEUE)

        update_event_counts(
            event_key, None, None,
            contact_count=len(self.seen_methods),
            student_count=len(method.students))

    def _process_student(self, student_info):
        student_key, contact_name, methods = student_info
        try:
            method = methods.pop(0)
        except IndexError:
            return

        marker = get_student_method_marker(
            self.event_key, method, methods, student_key, name=contact_name)

        if method in self.seen_methods:
            return marker

        self.seen_methods.add(method)
        self.tx_workers.append(get_tx_worker_task(
            self.event_key, self.batch_id, method))

        if len(self.tx_workers) > 10:
            insert_tasks(self.tx_workers, METHOD_TX_QUEUE)
            self.tx_workers = []

        return marker


class MethodTxHandler(webapp2.RequestHandler):
    """Send a message about the Event to the specified Contact Method.

    After sending, a message to write a "message sent" marker for this
    Event-Contact Method combination is inserted.

    If the Contact Method has already been contacted within the specified
    response-wait time, return without another contact attempt.  Otherwise,
    if the last contact attempt was longer than response-wait time, try the
    next contact method.
    """
    def post(self):
        from time import time

        event_urlsafe = self.request.get('event')
        event_key = ndb.Key(urlsafe=event_urlsafe)
        batch_id = self.request.get('batch')
        method = self.request.get('method')

        if not method:
            # TODO: Insert failed attempt marker.
            logging.error(
                'Contact method not provided, trying to notify for Event %s!',
                event_key.urlsafe())
            return

        logging.debug('Notifying Contact Method %s of Event %s.',
                      method, event_key)

        event = event_key.get()
        if not event:
            logging.error('Event %s not found, notifying Contact Method %s!',
                          event_key, method)
            return

        now = int(time())

        marker_key = ndb.Key(MethodMarker, method, parent=event_key)
        marker = marker_key.get()
        if marker:
            if marker.acknowledged:
                return

            if marker.last_try:
                tried_seconds_ago = now - marker.last_try
                if tried_seconds_ago < event.response_wait_seconds:
                    return

                task = get_try_next_method_task(
                    event_key.urlsafe(), batch_id, method)
                insert_tasks((task,), METHOD_TX_QUEUE)
                return

        # TODO: Use memcache check here to help prevent duplicate IDs.
        if marker and marker.short_id:
            short_id = marker.short_id
        else:
            short_id = MethodMarker.allocate_ids(size=1, parent=event.key)[0]

        send_notification(event, method, short_id)

        update_event_contact(event_key.urlsafe(), method, now, short_id)


class EventUpdateHandler(webapp2.RequestHandler):
    """Handle applying changes to the event entity group.

    This includes updating counts, managing acknowledgments, and retries, and
    also applying changes to the student-method entities.
    """
    def post(self):
        # Max number of work-units to process in one go, and how long to lease.
        BATCH_SIZE = 500
        LEASE_SECONDS = 45

        event_urlsafe = self.request.get('event')
        event_key = ndb.Key(urlsafe=event_urlsafe)

        update_queue = taskqueue.Queue(name=EVENT_UPDATE_QUEUE)
        updates = update_queue.lease_tasks_by_tag(LEASE_SECONDS, BATCH_SIZE,
                                                  tag=event_urlsafe)

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
                    short_id=update['short_id'],
                )
            elif update['type'] == 'ntxm':
                marker = MethodMarker(
                    key=marker_key,
                    try_next=True
                )
                workers.append(get_try_next_method_task(
                    event_key.urlsafe, method))
            elif update['type'] == 'idx':
                import json
                student_info = (update['student'],
                                update.get('contact_name', ''),
                                json.loads(update.get('methods', "[]")))
                marker = MethodMarker(
                    key=marker_key,
                    name=update.get('contact_name', ''),
                    students=(student_info,)
                )

            if marker_key in marker_map:
                marker_map[marker_key].merge(marker)
                continue

            marker_map[marker_key] = marker

        event_update(event_key, count_updates, marker_map)

        if workers:
            # Run these *after* the event update txn, since they may depend
            # on data written there.
            insert_tasks(workers, METHOD_TX_QUEUE)

        update_queue.delete_tasks(updates)

        if len(updates) >= BATCH_SIZE:
            insert_event_updator(event_key)


@ndb.transactional
def event_update(event_key, count_updates, marker_map):
    """Apply the given updates to an Event and its associated MethodMarkers
    and StudentMarkers.
    """
    keys = marker_map.keys()
    keys.append(event_key)

    marker_entities = ndb.get_multi(keys)

    event_key = keys.pop() # Discard event key so for loop works...
    event = marker_entities.pop()
    if not event:
        logging.warning('Event not found, %s', event_key)
        return

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

