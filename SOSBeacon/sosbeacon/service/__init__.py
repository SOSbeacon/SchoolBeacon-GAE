import datetime
import json
import logging

import webapp2

from skel.rest_api import handler as rest_handler


def request_query(entity, **kwargs):
    #TODO: had in other collection handling
    user_query = kwargs.get('query')
    query_filter = kwargs.get('filter', "name_")
    limit = int(kwargs.get('limit', 10))

    query = entity.query()

    if user_query:
        filter_property = getattr(entity, query_filter)
        search = user_query.strip().lower()
        query = query.filter(filter_property >= search)
        query = query.filter(filter_property < search + u"\uFFFD")

    if limit > 0:
        query = query.fetch(limit)

    return [entity.to_dict() for entity in query]


class JSONCRUDHandler(webapp2.RequestHandler):

    def __init__(self, entity, schema, *args, **kwargs):
        super(JSONCRUDHandler, self).__init__(*args, **kwargs)

        self.entity = entity
        self.schema = schema

    def get(self, args):
        if not args:
            entities = list(request_query(self.entity, **self.request.params))
        else:
            from google.appengine.ext import ndb
            keys = [ndb.Key(urlsafe=key) for key in args.split(',')]
            entities = [entity.to_dict() if entity else None
                        for entity in ndb.get_multi(keys)]

        self.response.out.write(json.dumps(entities))

    def delete(self, args):
        from google.appengine.ext import ndb

        urlsafe = self.request.path.rsplit('/', 1)[-1]
        if not urlsafe:
            return

        ndb.Key(urlsafe=urlsafe).delete()
        logging.info("Deleted %s with key: %s", self.entity, urlsafe)

    def post(self, args):
        self.process(args)

    def put(self, args):
        self.process(args)

    def process(self, args):
        from voluptuous import Schema

        obj = json.loads(self.request.body)
        schema = Schema(self.schema, extra=True)

        try:
            obj = schema(obj)
        except:
            logging.exception('validation failed')
            logging.info(obj)

        entity = self.entity.from_dict(obj)
        entity.put()

        out = entity.to_dict()
        self.response.out.write(json.dumps(out))


class PersonHandler(JSONCRUDHandler):

    def __init__(self, *args, **kwargs):
        from sosbeacon.person import Person
        from sosbeacon.person import person_schema

        super(PersonHandler, self).__init__(Person, person_schema, *args, **kwargs)


class ContactHandler(JSONCRUDHandler):

    def __init__(self, *args, **kwargs):
        from sosbeacon.contact import Contact
        from sosbeacon.contact import contact_schema

        super(ContactHandler, self).__init__(Contact, contact_schema, *args, **kwargs)

class StudentHandler(JSONCRUDHandler):

    def __init__(self, *args, **kwargs):
        from sosbeacon.student import Student
        from sosbeacon.student import student_schema

        super(StudentHandler, self).__init__(Student, student_schema, *args, **kwargs)

class GroupHandler(rest_handler.RestApiHandler):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema

        super(GroupHandler, self).__init__(
            Group, group_schema, request, response)

class GroupListHandler(rest_handler.RestApiListHandler):

    def __init__(self, request=None, response=None):
        from sosbeacon.group import Group
        from sosbeacon.group import group_schema
        from sosbeacon.group import group_query_schema

        super(GroupListHandler, self).__init__(
            Group, group_schema, request, response,
            query_schema=group_query_schema)

class EventHandler(JSONCRUDHandler):

    def __init__(self, *args, **kwargs):
        from sosbeacon.event import Event
        from sosbeacon.event import event_schema

        super(EventHandler, self).__init__(Event, event_schema, *args, **kwargs)

    def get(self, args):
        if not args:
            context = {}
            context.update(self.request.params)
            context['filter'] = "title_"

            entities = list(request_query(self.entity, **context))
        else:
            from google.appengine.ext import ndb
            keys = [ndb.Key(urlsafe=key) for key in args.split(',')]
            entities = [entity.to_dict() if entity else None
                        for entity in ndb.get_multi(keys)]

        self.response.out.write(json.dumps(entities))

class SendEventHandler(webapp2.RequestHandler):
    def post(self):
        from google.appengine.api import taskqueue
        from google.appengine.ext import ndb

        event_key = ndb.Key(urlsafe=self.request.get('event'))
        if not event_key:
            return

        taskqueue.add(
            url='/task/event/tx/start',
            name='send-%s' % (event_key.urlsafe(),),
            params={'event': event_key.urlsafe()}
        )

        @ndb.transactional
        def add_event_sent_props():
            event = event_key.get()
            event.notice_sent = True
            event.notice_sent_at = datetime.datetime.utcnow()
            #TODO: save the user that sent the event
            event.put()

        add_event_sent_props()

