import json
import logging

import webapp2


def request_query(entity, **kwargs):
    #TODO: had in other collection handling
    query = kwargs.get('query')
    query_filter = kwargs.get('filter')
    limit = int(kwargs.get('limit', 10))

    q = entity.query()

    if query:
        search = query.strip().lower()
        q = q.filter(query_filter >= search)
        q = q.filter(query_filter < search + u"\uFFFD")

    if limit > 0:
        q = q.fetch(limit)

    return q


class JSONCRUDHandler(webapp2.RequestHandler):

    def __init__(self, entity, schema, **kwargs):
        super(JSONCRUDHandler, self).__init__(**kwargs)

        self.entity = entity
        self.schema = schema

    def get(self):
        objs = request_query(self.entity, **self.request)
        self.response.out.write(json.dumps(objs))

    def delete(self):
        from google.appengine.ext import ndb

        urlsafe = self.request.path.rsplit('/', 1)[-1]
        if not urlsafe:
            return

        ndb.Key(urlsafe=urlsafe).delete()
        logging.info("Deleted %s with key: %s", (self.entity, urlsafe))

    def post(self):
        self.process()

    def put(self):
        self.process()

    def process(self):
        from voluptuous import Schema

        obj = json.loads(self.request.body)
        schema = Schema(self.schema, extra=True)

        try:
            schema(obj)
            #TODO: this may need to be obj = schema(obj) or something similar
        except:
            logging.exception('validation failed')
            logging.info(obj)

        entity = self.entity.from_dict(obj)
        entity.put()

        out = entity.to_dict()
        self.response.out.write(json.dumps(out))


class PersonHandler(JSONCRUDHandler):

    def __init__(self, **kwargs):
        from sosbeacon.person import Person
        from sosbeacon.person import person_schema

        super(PersonHandler, self).__init__(Person, person_schema, **kwargs)


class ContactHandler(JSONCRUDHandler):

    def __init__(self, **kwargs):
        from sosbeacon.contact import Contact
        from sosbeacon.contact import contact_schema

        super(ContactHandler, self).__init__(Contact, contact_schema, **kwargs)
