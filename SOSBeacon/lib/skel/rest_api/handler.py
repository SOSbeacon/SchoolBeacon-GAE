import json
import logging

import webapp2

from skel.datastore import EntityBase
from .rules import RestQueryRule


class JsonHandler(webapp2.RequestHandler):

    def __init__(self, request=None, response=None):
        super(JsonHandler, self).__init__(request, response)

        self.json_response = {}

    def write_json_response(self, json_response):
        self.response.headers['Content-type'] = 'application/json'

        if not self.json_response:
            self.json_response = json_response
        else:
            self.json_response.update(json_response)

        self.response.write(json.dumps(self.json_response))

    def convertTimeZone(self, tz, created_at):
        from datetime import datetime
        from pytz import timezone

        fmt = "%Y-%m-%d %H:%M"
        fmt_utc = "%Y-%m-%d %H:%M %Z%z"

        create_at_obj = datetime.strptime(created_at, fmt)
        create_at_obj_utc = create_at_obj.replace(tzinfo=timezone('UTC'))

        now_pacific = create_at_obj_utc.astimezone(timezone(tz))

        return now_pacific.strftime(fmt)

class RestApiSaveHandler(JsonHandler):

    def post(self, resource_id, *args, **kwargs):
        self.process(resource_id, *args, **kwargs)

    def put(self, resource_id, *args, **kwargs):
        self.process(resource_id, *args, **kwargs)

    def process(self, resource_id, *args, **kwargs):
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

        self.write_json_response(entity.to_dict())

    def delete(self, resource_id, *args, **kwargs):
        from google.appengine.ext import ndb

        if not resource_id:
            return

        key = ndb.Key(urlsafe=resource_id)
        if self.entity._get_kind() != key.kind():
            return

        key.delete()

        logging.info("Deleted %s with key: %s", self.entity, resource_id)


class RestApiHandler(RestApiSaveHandler):

    def __init__(self, entity, schema, request=None, response=None):
        super(RestApiHandler, self).__init__(request, response)

        self.entity = entity
        self.schema = schema

    def get(self, resource_id, *args, **kwargs):
        from google.appengine.ext import ndb

        if ',' in resource_id:
            #assume this is a list of keys
            keys = [ndb.Key(urlsafe=keystr) for keystr in resource_id.split(',')]
            response = [entity.to_dict() for entity in ndb.get_multi(keys)]
        else:
            key = ndb.Key(urlsafe=resource_id)
            resource = key.get()

            if not resource:
                self.error(404)
                response = {}
            else:
                response = resource.to_dict()

        if type(response) != type(list()):
            self.changeTimezone(response)

        self.write_json_response(response)

    def changeTimezone(self, response):
        from webapp2_extras import sessions

        session_store = sessions.get_store()
        session = session_store.get_session()

        if 'tz' in session:
            tz = session.get('tz')
            response['added'] = self.convertTimeZone(tz, response['added'])
            response['modified'] = self.convertTimeZone(tz, response['modified'])
            if 'date' in response:
                response['date'] = self.convertTimeZone(tz, response['date'])
                response['last_broadcast_date'] = self.convertTimeZone(tz, response['last_broadcast_date'])

        else :
            tz = "America/Los_Angeles"
            session['tz'] = tz
            response['added'] = self.convertTimeZone(tz, response['added'])
            response['modified'] = self.convertTimeZone(tz, response['modified'])
            if 'date' in response:
                response['date'] = self.convertTimeZone(tz, response['date'])
                response['last_broadcast_date'] = self.convertTimeZone(tz, response['last_broadcast_date'])



class RestApiListHandler(RestApiSaveHandler):

    def __init__(self, entity, schema, request=None, response=None,
                 default_filters=None, query_schema=None, query_options=None):
        super(RestApiListHandler, self).__init__(request, response)

        self.entity = entity
        self.schema = schema
        self.query_schema = query_schema
        self.query = RestQuery(default_filters=default_filters,
                               query_options=query_options)

    def get(self, *args, **kwargs):
        resources = self.query.fetch(
            self.entity, self.request.params, self.query_schema)

        response = [entity.to_dict() for entity in resources]
        self.changeTimezone(response)

        self.write_json_response(response)

    def changeTimezone(self, response):
        from webapp2_extras import sessions

        session_store = sessions.get_store()
        session = session_store.get_session()

        if 'tz' in session:
            tz = session.get('tz')
            for value in response:
                value['added'] = self.convertTimeZone(tz, value['added'])
                value['modified'] = self.convertTimeZone(tz, value['modified'])
                if 'date' in value:
                    value['date'] = self.convertTimeZone(tz, value['date'])
                    value['last_broadcast_date'] = self.convertTimeZone(tz, value['last_broadcast_date'])

        else :
            tz = "America/Los_Angeles"
            session['tz'] = tz
            for value in response:
                value['added'] = self.convertTimeZone(tz, value['added'])
                value['modified'] = self.convertTimeZone(tz, value['modified'])
                if 'date' in value:
                    value['date'] = self.convertTimeZone(tz, value['date'])
                    value['last_broadcast_date'] = self.convertTimeZone(tz, value['last_broadcast_date'])


class RestQuery(object):

    def __init__(self, default_filters=None, **kwargs):
        self.default_filters = default_filters if default_filters else []
        self.sort_orders = []

        query_options = kwargs.get('query_options')
        self.query_options = query_options or {}

    def fetch(self, entity, params, query_schema=None):
        if query_schema:
            from voluptuous import Schema
            #convert params for validation
            #TODO: need to handle complex values. this is a quick fix to get it in
            query_params = {}
            query_params.update(params)

            schema = Schema(query_schema, extra=True)
            params = schema(query_params)

        self.query_filters = RestQueryFilters()
        limit = int(params.get('limit', 200))

        query = entity.query(**self.query_options)

        for default_filters in self.default_filters:
            query = query.filter(default_filters)

        query = self._parse(entity, query, params)
        query = self._add_ordering(entity, query, params)

        return query.fetch(limit)

    def _add_ordering(self, entity, query, params):
        if 'orderBy' not in params:
            if self.sort_orders:
                query.order(*self.sort_orders)
            return query

        order_asc = True
        if 'orderDirection' in params and params['orderDirection'] == 'desc':
            order_asc = False

        prop_string = params.pop('orderBy')

        query_rule = self._get_query_rule(entity, prop_string)
        if query_rule and isinstance(query_rule, RestQueryRule):
            prop_string = query_rule.prop

        prop = getattr(entity, prop_string, None)
        if prop:
            if order_asc:
                self.sort_orders.append(prop)
            else:
                self.sort_orders.append(-prop)

        return query.order(*self.sort_orders)

    def _get_query_rule(self, entity, prop_string):
        if hasattr(entity, '_query_properties'):
            return entity.get_query_property(prop_string)

    def _parse(self, entity, query, params):
        filters = ["f%s" % (f) for f in self.query_filters.filters.iterkeys()]

        sort_matches = False
        for prop, value in params.iteritems():

            psplit = prop.split('_')
            if len(psplit) < 2:
                continue

            f = psplit[0].lower()
            if f not in filters:
                continue

            prop_string = query_prop_string  = '_'.join(psplit[1:])

            query_rule = self._get_query_rule(entity, prop_string)
            if query_rule and isinstance(query_rule, RestQueryRule):
                prop_string = query_rule.prop
                if query_rule.empty_as_none and not value:
                    value = None

                value = query_rule.parse_value(value)

            entity_prop = getattr(entity, prop_string)

            if isinstance(value, basestring):
                value = value.strip()

            query, sort = self.query_filters.get(
                query, f, entity_prop, value)

            if self._check_is_order(sort, query_prop_string, params):
                sort_matches = True

        if sort_matches:
            if 'orderBy' in params:
                params.pop('orderBy')
            if 'orderDirection' in params:
                params.pop('orderDirection')

        return query

    def _check_is_order(self, sort, prop_string, params):
        if not sort:
            return False

        #we need to check if the orderBy is the same property as this
        #if it is we should remove as we don't need it in the query
        if not 'orderBy' in params:
            return False

        if params['orderBy'] != prop_string:
            self.sort_orders.append(sort)
            return False

        if ('orderDirection' in params and
            params['orderDirection'] == 'desc'):
            self.sort_orders.append(-sort)
            return True

        self.sort_orders.append(sort)
        return True


class RestQueryFilters(object):

    def __init__(self):
        self.filters = {
            'eq': self._add_equality_filter,
            'neq': self._add_inequality_filter,
            'like': self._add_like_filter,
            'gt': self._add_greater_than_filter,
            'an': self._add_ancestor_filter
        }

    def get(self, query, query_filter, prop, val):
        f = self.filters.get(query_filter[1:])
        if not f:
            return query

        return f(query, prop, val)

    def _add_ancestor_filter(self, query, filter_property, val):
        # TODO:  This needs done at query instantiation.
        from google.appengine.ext import ndb
        key = val
        if not isinstance(val, ndb.Key):
            key = ndb.Key(urlsafe=val)
        query._Query__ancestor = key
        return query, None

    def _add_equality_filter(self, query, filter_property, val):
        return query.filter(filter_property == val), None

    def _add_inequality_filter(self, query, filter_property, val):
        return query.filter(filter_property != val), filter_property

    def _add_like_filter(self, query, filter_property, val):
        query = query.filter(filter_property >= val)
        return query.filter(filter_property < val + u"\uFFFD"), filter_property

    def _add_greater_than_filter(self, query, filter_property, val):
        return query.filter(filter_property >= val), filter_property
