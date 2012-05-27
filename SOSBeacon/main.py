#!/usr/bin/env python
#
# Copyright 2012 Ezox Systems LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Map user-facing handlers here.  This is meant to map actual HTML pages."""

import logging
import os
import sys

# Add lib to path.
libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
if libs_dir not in sys.path:
    logging.debug('Adding lib to path.')
    sys.path.insert(0, libs_dir)

import webapp2

from google.appengine.api import memcache

from mako import exceptions
from mako.lookup import TemplateLookup

from sosbeacon.contact import Contact
from sosbeacon.event import Event
from sosbeacon.event import acknowledge_event


EVENT_DOES_NOT_EXIST = "-!It's a Trap!-"


class TemplateHandler(webapp2.RequestHandler):
    def render(self, template_name, **context):
        try:
            lookup = TemplateLookup(directories=["templates"])
            template = lookup.get_template(template_name)
            out = template.render(**context)
        except:
            out = exceptions.html_error_template().render()
            logging.exception('Oh NO! Rendering error.')

        return out

class MainHandler(TemplateHandler):
    def get(self):
        out = self.render('default.mako')
        self.response.out.write(out)


class EventHandler(TemplateHandler):
    def get(self, event_id, contact_id):
        from google.appengine.ext import ndb
        event_key = ndb.Key(Event, int(event_id))
        contact_key = ndb.Key(Contact, int(contact_id))

        event_mc_key = 'Event:%s' % (int(event_id),)
        event_html = memcache.get(event_mc_key)
        if not event_html:
            event = Event.get_by_id(int(event_id))
            if not event:
                memcache.set(event_mc_key, EVENT_DOES_NOT_EXIST)
                self.error(404)
                return

            event_html = self.render('event.mako', event=event)
            memcache.set(event_mc_key, event_html)

        if event_html == EVENT_DOES_NOT_EXIST:
            # Some one might be exploring.  Lets not give them anything.
            self.error(404)
            return

        event = Event.get_by_id(int(event_id))
        #contact = Contact.get_by_id(int(contact_id))
        #contact_groups = set(contact.groups)
        #event_groups = set(event.groups)
        #if event_groups.isdisjoint(contact_groups):
        #    # This contact isn't in the groups allowed to see this event.
        #    self.error(404)
        #    return

        self.response.out.write(event_html)

        # Try to mark this event as acknowledged.
        try:
            acknowledge_event(event_key, contact_key)
        except:
            # This is (relatively) non-critical, so ignore all exceptions.
            pass

url_map = [
    ('/', MainHandler),
    ('/e/(.*)/(.*)', EventHandler),
]
app = webapp2.WSGIApplication(url_map)

