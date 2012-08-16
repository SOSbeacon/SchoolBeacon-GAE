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
from webapp2_extras import sessions

from google.appengine.api import memcache
from google.appengine.ext import ndb

from mako import exceptions
from mako.lookup import TemplateLookup

from config import webapp_config

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
        from google.appengine.ext import ndb
        from sosbeacon.school import School

        school_name = 'Account'

        session_store = sessions.get_store()
        session = session_store.get_session()
        school_key = session.get('s')
        if school_key:
            school = ndb.Key(urlsafe=school_key).get()
            school_name = school.name

        out = self.render('default.mako', school_name=school_name)
        self.response.out.write(out)


#TODO: Move to it's own app?
class AdminHandler(TemplateHandler):
    def get(self):
        out = self.render('admin.mako')
        self.response.out.write(out)


class EventHandler(TemplateHandler):
    def get(self, event_id, method_id):
        from google.appengine.ext import ndb
        from sosbeacon import utils

        event_id = utils.number_decode(event_id)
        method_id = str(utils.number_decode(method_id))

        event_key = ndb.Key(Event, event_id)

        event_mc_key = 'Event:%s' % (int(event_id),)
        event_html = memcache.get(event_mc_key)
        if not event_html:
            event = Event.get_by_id(int(event_id), namespace='_x_')
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
            acknowledge_event(event_key, method_id)
        except:
            # This is (relatively) non-critical, so log and ignore exceptions.
            logging.exception('Ack failed')
            pass

class StudentImportHandler(TemplateHandler):

    def post(self):
        file_ = self.request.get('students_file')
        if not file_:
            #TODO: flag as error and report to user somehow
            return webapp2.redirect("/#/student")

        from sosbeacon.student import import_students
        try:
            import_students(file_)
        except:
            #TODO: give a nice error page
            logging.exception("Unable to import students")

        #TODO: do we want a results page?
        return webapp2.redirect("/#/student")

url_map = [
    ('/', MainHandler),
    ('/admin/', AdminHandler),
    ('/e/(.*)/(.*)', EventHandler),
    ('/student/import/upload/', StudentImportHandler),
]
app = webapp2.WSGIApplication(
    url_map,
    config=webapp_config
)

