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
import urllib
import sys

# Add lib to path.
libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
if libs_dir not in sys.path:
    logging.debug('Adding lib to path.')
    sys.path.insert(0, libs_dir)

import webapp2
from webapp2_extras import sessions

from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers

from mako import exceptions
from mako.lookup import TemplateLookup

from config import webapp_config

from sosbeacon.event import Event
from sosbeacon.event import acknowledge_event
from sosbeacon.event.contact_marker import ContactMarker

from sosbeacon.school import School

EVENT_DOES_NOT_EXIST = "-!It's a Trap!-"

def user_required(handler):
    """
         Decorator for checking if there's a user associated
         with the current session.
         Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        """
            If handler has no login_url specified invoke a 403 error
        """
        session_store = sessions.get_store()
        session = session_store.get_session()
        try:
            if not 'u' in session:
                try:
                    self.redirect('/authentication/login')

                except (AttributeError, KeyError), e:
                    self.abort(403)
            else:
                return handler(self, *args, **kwargs)

        except AttributeError, e:
            # avoid AttributeError when the session was delete from the server
            logging.error(e)
            for key in session.keys():
                del session[key]
            self.redirect('/')

    return check_login


def admin_required(handler):
    """
         Decorator for checking if there's a admin user associated
         with the current session.
         Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        """
            If handler has no admin_login_url specified invoke a 403 error
        """
        session = self.session_store.get_session()
        try:
            if not 'ad' in session:
                try:
                    self.redirect('/admin/authentication/login')
                except (AttributeError, KeyError), e:
                    self.abort(403)
            else:
                return handler(self, *args, **kwargs)

        except AttributeError, e:
            # avoid AttributeError when the session was delete from the server
            logging.error(e)
            for key in session.keys():
                del session[key]
            self.redirect('/admin')

    return check_login

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

class TemplateHandler(BaseHandler):

    def __init__(self, *args, **kwargs):
        super(TemplateHandler, self).__init__(*args, **kwargs)

        self._school_name = None
        self._user_name = None
        self._list_school = None
        self._admin_name = None

    @property
    def school_name(self):
        if not self._school_name:
            self._school_name = 'School'
            school_key = self.session['s']

            if school_key:
                from sosbeacon.school import School  # To get the model in mem.
                school = ndb.Key(urlsafe=school_key).get()
                if school:
                    self._school_name = school.name

        return self._school_name

    @property
    def user_name(self):
        if not self._user_name:
            self._user_name = 'User'
            user_key = self.session['u']

            if user_key:
                from sosbeacon.user import User  # To get the model in mem.
                user = ndb.Key(urlsafe=user_key).get()
                if user:
                    self._user_name = user.name

        return self._user_name

    @property
    def list_school(self):
        if not self._list_school:
            self._list_school = []
            user_key = self.session['u']

            if user_key:
                from sosbeacon.user import User  # To get the model in mem.
                user = ndb.Key(urlsafe=user_key).get()
                if user:
                    self._list_school = [school_key.get() for school_key in user.schools]

        return self._list_school

    @property
    def admin_name(self):
        if not self._admin_name:
            self._admin_name = 'Admin'
            admin_key = self.session['ad']

            if 'ad' in self.session:
                if admin_key:
                    from sosbeacon.user import User  # To get the model in mem.
                    admin = ndb.Key(urlsafe=admin_key).get()
                    if admin:
                        self._admin_name = admin.name
            else:
                self._admin_name = 'Admin'

        return self._admin_name

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
    @user_required
    def get(self):
        if 'tz' in self.session:
            timezone = self.session['tz']
        else:
            timezone = "America/Los_Angeles"

        out = self.render('default.mako', school_name = self.school_name,
                                          user_name = self.user_name,
                                          schools = self.list_school,
                                          timezone = timezone)
        self.response.out.write(out)


class ChooseSchoolHandler(TemplateHandler):
    @user_required
    def get(self, resource_id):
        school_k = ndb.Key(urlsafe=resource_id)

        if school_k:
            self.session['s'] = resource_id
            self.redirect('/')
            return

        self.redirect('/authentication/login')


#TODO: Move to it's own app?
class AdminHandler(TemplateHandler):
    @admin_required
    def get(self):
        out = self.render('admin.mako')
        self.response.out.write(out)


class EventHandler(TemplateHandler):
    def get(self, event_id, method_id):
        from google.appengine.ext import ndb
        from sosbeacon import utils

        event_id = utils.number_decode(event_id)
        method_id = str(utils.number_decode(method_id))

        event_key = ndb.Key(Event, int(event_id), namespace='_x_')

        event_mc_key = 'Event:%s' % (int(event_id),)
        event_html = memcache.get(event_mc_key)
        if not event_html:
            event = event_key.get()
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

        event = event_key.get()
        #Get the school id (ie namespace) and grab the event marker
        marker_key = ndb.Key(
            ContactMarker, "%s:%s" % (event_id, method_id),
            namespace=event.school)

        marker = marker_key.get()
        if not marker:
            # TODO: Can this happen in a legitimate way?
            self.error(404)
            return

        if marker.place_holder:
            marker_key = marker.place_holder

        self.setup_session(marker_key, event)

        self.response.out.write(event_html)

        # Try to mark this event as acknowledged.
        try:
            acknowledge_event(event_key, marker_key)
        except:
            # This is (relatively) non-critical, so log and ignore exceptions.
            logging.exception('Ack failed for marker %s.', marker_key)
            pass

    def setup_session(self, marker_key, event):
        """Setup the session vars."""
        session_store = sessions.get_store()
        session = session_store.get_session()
        session['cm'] = marker_key.id()
        school_id = event.school.strip('_')
        session['n'] = school_id
        session['s'] = ndb.Key(School, int(school_id)).urlsafe()
        session_store.save_sessions(self.response)


class StudentImportHandler(MainHandler):
    @user_required
    def post(self):
        file_ = self.request.get('students_file')
        if not file_:
            #TODO: flag as error and report to user somehow
            return webapp2.redirect("/#/student")

        from sosbeacon.student import import_students
        results = {'success': [], 'failures': []}
        try:
            results = import_students(file_)
        except Exception:
            #TODO: give a nice error page
            logging.exception("Unable to import students")

        out = self.render(
            'import.mako', school_name=self.school_name, **results)
        self.response.out.write(out)


class FileUploadHandler(MainHandler):

    def get(self):
        upload_url = blobstore.create_upload_url('/uploads/post')
        self.response.out.write(upload_url)


class FileUploadPostHandler(blobstore_handlers.BlobstoreUploadHandler):

    def post(self):
        blob_info = self.get_uploads()[0]
        self.response.out.write('/uploads/view/%s' % blob_info.key())


class FileUplaodViewHandler(blobstore_handlers.BlobstoreDownloadHandler):

    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info, content_type="image/png")


url_map = [
    ('/', MainHandler),
    ('/admin/', AdminHandler),
    ('/e/(.*)/(.*)', EventHandler),
    ('/import/student/upload/', StudentImportHandler),
    ('/uploads/new', FileUploadHandler),
    ('/uploads/post', FileUploadPostHandler),
    ('/uploads/view/([^/]+)?', FileUplaodViewHandler),
    webapp2.Route(r'/school/<resource_id:.+>',
        handler='main.ChooseSchoolHandler'),
]
app = webapp2.WSGIApplication(
    url_map,
    config=webapp_config
)
