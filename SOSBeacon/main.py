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
from webapp2_extras.security import check_password_hash

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
from sosbeacon.user import User

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
                    self.redirect('/school')

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
        if not 's' in self.session:
            self.redirect('/')
            return

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
                    self._user_name = user.first_name + " " + user.last_name

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
                        self._admin_name = admin.first_name + " " + admin.last_name
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
#    @admin_required
    def get(self):
        out = self.render('admin.mako')
        self.response.out.write(out)


class EventHandler(TemplateHandler):
    def get(self, event_id, method_id):
        from google.appengine.ext import ndb
        from sosbeacon import utils
        from sosbeacon.event.event import EVENT_STATUS_CLOSED

        event_id = utils.number_decode(event_id)
        method_id = str(utils.number_decode(method_id))
        event_key = ndb.Key(Event, int(event_id), namespace='_x_')

        session_store = sessions.get_store()
        session = session_store.get_session()

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

        if event.status == EVENT_STATUS_CLOSED:
            if 'u' in session:
                self.redirect("/#eventcenter/view/%s" % event_key.get().key.urlsafe())
                return
            else:
                event_html = self.render('event_closed.mako')
                self.response.out.write(event_html)
                return

        marker_key = ndb.Key(
            ContactMarker, "%s:%s" % (event_id, method_id),
            namespace='_x_')

        marker = marker_key.get()
        if not marker:
            if 'u' in session:
                self.redirect("/#eventcenter/view/%s" % event_key.get().key.urlsafe())
                return
            else:
                logging.info("1")
                event_html = self.render('event.mako', event=event, contact_marker = False, contact_name="", timezone = "America/Los_Angeles")
                self.response.out.write(event_html)
                return

        if 'u' in session:
            self.redirect("/#eventcenter/view/%s" % event_key.get().key.urlsafe())
            try:
                acknowledge_event(event_key, marker_key)
            except:
                # This is (relatively) non-critical, so log and ignore exceptions.
                logging.exception('Ack failed for marker %s.', marker_key)
                pass
            return

        if marker.place_holder:
            marker_key = marker.place_holder

        self.setup_session_marker(marker_key, event)

        event_html = self.render('event.mako', event=event, contact_marker = True, contact_name = marker.first_name + " " + marker.last_name, timezone = self.session.get('tz'))
        self.response.out.write(event_html)

        # Try to mark this event as acknowledged.
        try:
            acknowledge_event(event_key, marker_key)
        except:
            # This is (relatively) non-critical, so log and ignore exceptions.
            logging.exception('Ack failed for marker %s.', marker_key)
            pass

    def setup_session_marker(self, marker_key, event):
        """Setup the session vars."""
        session_store = sessions.get_store()
        session = session_store.get_session()
        session['cm'] = marker_key.id()
        session_store.save_sessions(self.response)


class StudentImportHandler(MainHandler):
    @user_required
    def get(self):
        results = {'success': [], 'failures': []}
        results_contact = 'false'
        count = 0
        host = os.environ['HTTP_HOST']
        value = 'student'
        download = "http://%s/static/file/sample_student.csv" % (host)
        out = self.render(
            'import_student.mako', school_name=self.school_name,
            user_name = self.user_name,
            schools = self.list_school, results_contact=results_contact, count=count, download=download, value=value, **results)
        self.response.out.write(out)

    @user_required
    def post(self):
        from sosbeacon.student import preview_import_students
        from sosbeacon.student import import_students

        file_ = self.request.get('students_file')

        import_list = self.request.get('importListString')

        results_contact = 'true'
        host = os.environ['HTTP_HOST']
        download = "http://%s/static/file/sample_student.csv" % (host)

        school_urlsafe = self.session.get('s')
        value = file_

        try:
            is_direct = False
            if import_list == 'student':
                results = preview_import_students(file_, is_direct)
                out = self.render(
                    'import_student.mako', school_name=self.school_name,
                    user_name = self.user_name,
                    schools = self.list_school, results_contact=results_contact, download=download,
                        count='Total records saved: 0', value=value, **results)
                self.response.out.write(out)

            else:
                results = import_students(import_list, school_urlsafe, is_direct)
                out = self.render(
                    'import_student.mako', school_name=self.school_name,
                    user_name = self.user_name,
                    schools = self.list_school, results_contact=results_contact, download=download,
                        count='Import contacts success. Total records saved: %d' % len(results['success']),
                        value='student', **results)
                self.response.out.write(out)

        except Exception:
            #TODO: give a nice error page
            logging.exception("Unable to import students")
            results = {'success': [], 'failures': []}
            out = self.render(
                'import_student.mako', school_name=self.school_name,
                user_name = self.user_name,
                schools = self.list_school, results_contact = results_contact, count='Import contacts success. Total records saved: 0', download=download, value=value, **results)
            self.response.out.write(out)


class ContactImportHandler(MainHandler):

    def get(self):
        results = {'success': [], 'failures': []}
        results_contact = 'false'
        count = 0
        host = os.environ['HTTP_HOST']
        value = 'direct'
        download = "http://%s/static/file/sample_direct.csv" % (host)
        out = self.render(
            'import_direct.mako', school_name=self.school_name,
            user_name = self.user_name,
            schools = self.list_school, results_contact=results_contact, count=count,
                download=download, value=value, **results)
        self.response.out.write(out)

    def post(self):
        from sosbeacon.student import preview_import_students
        from sosbeacon.student import import_students

        file_ = self.request.get('contacts_file')
        import_list = self.request.get('importListString')

        results_contact = 'true'
        host = os.environ['HTTP_HOST']
        download = "http://%s/static/file/sample_direct.csv" % (host)

        school_urlsafe = self.session.get('s')
        value = file_

        try:
            is_direct = True
            if import_list == 'direct':
                results = preview_import_students(file_, is_direct)
                out = self.render(
                    'import_direct.mako', school_name=self.school_name,
                    user_name = self.user_name,
                    schools = self.list_school, results_contact=results_contact, download=download,
                        count='Total records saved: 0', value=value, **results)
                self.response.out.write(out)

            else:
                results = import_students(import_list, school_urlsafe, is_direct)
                out = self.render(
                    'import_direct.mako', school_name=self.school_name,
                    user_name = self.user_name,
                    schools = self.list_school, results_contact=results_contact, download=download,
                        count='Import contacts success. Total records saved: %d' % len(results['success']),
                        value='direct', **results)
                self.response.out.write(out)

        except Exception:
            #TODO: give a nice error page
            logging.exception("Unable to import students")
            results = {'success': [], 'failures': []}
            error = "Unable to import students"
            out = self.render(
                'import_direct.mako', school_name=self.school_name,
                user_name = self.user_name,
                schools = self.list_school, results_contact=results_contact, count='Import contacts success. Total records saved: 0',
                download=download, value=value, **results)
            self.response.out.write(out)


class FileUploadHandler(MainHandler):

    def get(self):
        upload_url = blobstore.create_upload_url('/uploads/post')
        self.response.out.write(upload_url)


class FileUploadPostHandler(blobstore_handlers.BlobstoreUploadHandler):

    def post(self):
        host = os.environ['HTTP_HOST']
        blob_info = self.get_uploads()[0]
        self.response.out.write('//%s/uploads/view/%s' % (host, blob_info.key()))


class FileUplaodViewHandler(blobstore_handlers.BlobstoreDownloadHandler):

    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info, content_type="audio/mp3")


class HomeLoginHandler(TemplateHandler):
    """Home page"""
    def get(self, *args, **kwargs):
        if not 'u' in self.session:
            self.render_user_login(is_loggedin=False, error="")
            return

        urlsafe = self.session.get('u')
        user_key = ndb.Key(urlsafe=urlsafe)

        user = user_key.get()
        school = self.session.get('s')

        if len(user.schools) == 1:
            self.redirect("/")
            return

        if len(user.schools) > 1:
            schools = [school_key.get() for school_key in user.schools]
            self.render_user_login(is_loggedin = True, schools = schools)
            return

        self.render_user_login(is_loggedin = True, schools = None, error="You don't have any schools!.")

    def post(self, *args, **kwargs):
        if not 'u' in self.session:
            email    = self.request.POST['email']
            password = self.request.POST['password']

            user = User.query(ndb.AND(User.email == email),
                namespace = '_x_')

            if user.get() is None:
                self.render_user_login(is_loggedin = False, error='Email or Password is wrong!.')
                return

            if user.get().is_admin:
                self.render_user_login(is_loggedin = False, error='Email or Password is wrong!.')
                return

            else:
                if check_password_hash(password, user.get().password):
                    self.delete_session()
                    self.set_current_user(user)
                else:
                    self.render_user_login(is_loggedin = False, error='Email or Password is wrong!.')
                    return

        user_key = self.session.get('u')
        user = ndb.Key(urlsafe=user_key).get()
        school_length = len(user.schools)

        #check schools that user was asigned
        if school_length == 1:
            school_key = user.schools[0]
            school_key = school_key.get().key.urlsafe()
            self.set_current_school(school_key)
            self.redirect("/")
            return

        if school_length == 0:
            self.render_user_login(is_loggedin = False, error="You don't have any schools!. Please contact with admin for this reason.")
            self.delete_session()
            return

        if school_length > 1 and 'school' not in self.request.POST:
            schools = [school_key.get() for school_key in user.schools]
            self.render_user_login(is_loggedin = True, schools=schools)
            return

        school_key = self.request.POST['school']
        self.set_current_school(school_key)
        self.redirect("/")

    def set_current_user(self, user):
        """set session for current user"""
        self.session['u'] = user.get().key.urlsafe()

    def set_current_school(self, school_key):
        """set session for current school that user choose when login"""
        self.session['s'] = school_key

    def render_user_login(self, **context):
        out = self.render(template_name='home_login.mako', **context)
        self.response.out.write(out)

    def delete_session(self):
        """delete all session"""
        for key in self.session.keys():
            if key != 'tz':
                del self.session[key]


class SelectSchool(TemplateHandler):
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('select_school.mako', is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('select_school.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)

    def post(self, *args, **kwargs):
        if 'school' in self.request.body:
            school_key = self.request.POST['school']
            self.session['s'] = school_key
            self.redirect("/")
            return

        out = self.render('select_school.mako', school_name = self.school_name,
            user_name = self.user_name,
            schools = self.list_school,
            timezone = '',
            is_loggedin = True)
        self.response.out.write(out)



class HomeLogoutHandler(TemplateHandler):
    """Home logout page"""
    def get(self, *args, **kwargs):
        if self.session:
            for key in self.session.keys():
                if key != 'tz':
                    del self.session[key]

        self.redirect("/school/web/users/login/")


class HomeHandler(TemplateHandler):
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('home.mako', is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('home.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)


class AboutHandler(TemplateHandler):
    """render template about sosbeacon"""
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('about.mako',is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('about.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)


class FeaturesHandler(TemplateHandler):
    """render template features sosbeacon"""
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('features.mako',is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('features.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)


class TestimonialsHandler(TemplateHandler):
    """render template testimonials sosbeacon"""
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('testimonials.mako',is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('testimonials.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)


class PrivacyHandler(TemplateHandler):
    """render template testimonials sosbeacon"""
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('privacy.mako',is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('privacy.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)


class TermHandler(TemplateHandler):
    """render template testimonials sosbeacon"""
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('terms.mako',is_loggedin=False)
            self.response.out.write(out)
        else:
            out = self.render('terms.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True)
            self.response.out.write(out)


class SchoolAccountHandler(TemplateHandler):
    """render template testimonials sosbeacon"""
    def get(self):
        self.render_school_account('')

    def post(self):
        """"""
        import sendgrid
        import settings

#        row 1
        schoolName = self.request.POST['schoolName']
        principalName = self.request.POST['principalName']
        adminName = self.request.POST['adminName']
        address = self.request.POST['address']

        schoolPhone = self.request.POST['schoolPhone']
        contactPhone = self.request.POST['contactPhone']
        contactEmail = self.request.POST['contactEmail']
        studentNo = self.request.POST['studentNo']
        classNo = self.request.POST['classNo']

        ageRange = self.request.POST['ageRange']
        gradeRange = self.request.POST['gradeRange']

        profitType = downloadApp = haveEmergency = approval = ''
        if 'profitType' in self.request.body:
            profitType = self.request.POST['profitType']

        foundingDate = self.request.POST['foundingDate']
        website = self.request.POST['website']

#        ROW 2
        if 'downloadApp' in self.request.body:
            downloadApp = self.request.POST['downloadApp']

        sosPhone = self.request.POST['sosPhone']
        sosPhoneCarrier = self.request.POST['sosPhoneCarrier']
        howHear = self.request.POST['howHear']

        if 'haveEmergency' in self.request.body:
            haveEmergency = self.request.POST['haveEmergency']
        whatEmergency = self.request.POST['whatEmergency']
        whenGetSos = self.request.POST['whenGetSos']

        if 'approval' in self.request.body:
            approval = self.request.POST['approval']

        whatApproval = self.request.POST['whatApproval']

        subject = "Email is sent from SOSbeacon School Account Form"

        body = """
            Request form details:
            <h2>School Account Information Form</h2>
            <strong>Name of School:</strong> %s<br />

            <strong>Name of Principal:</strong> %s<br />

            <strong>Name of Contact Admin:</strong> %s<br />

            <strong>Address:</strong> %s<br />

            <strong>School phone:</strong> %s<br />

            <strong>Contact phone :</strong> %s<br />

            <strong>Contact email address:</strong> %s<br />

            <strong>Number of Students:</strong> %s<br />

            <strong>Number of classes:</strong> %s<br />

            <strong>Student Age range:</strong> %s<br />

            <strong>Grade range:</strong> %s<br />

            <strong>Is your school:</strong> %s<br />

            <strong>Date of School Founding (m/d/y):</strong> %s<br />

            <strong>School Website:</strong> %s<br />

            <strong>Have you downloaded the free School Beacon app yet:</strong> %s<br />

            <strong>What mobile phone # will you use for School Beacon service:</strong> %s<br />

            <strong>Type of mobile phone and carrier:</strong> %s<br />

            <strong>How did you hear about School Beacon:</strong> %s<br />

            <strong>Do you have an emergency communications system now:</strong> %s<br />

            <strong>If so, what is it:</strong> %s<br />

            <strong>When would you like to get the School Beacon emergency communications system started at your school:</strong> %s<br />

            <strong>Do you have approval to start this service:</strong> %s<br />

            <strong>If NO, what is required to get approval:</strong> %s<br />

        """ % (schoolName, principalName, adminName, address, schoolPhone, contactPhone, contactEmail, studentNo, classNo,
               ageRange, gradeRange, profitType, foundingDate, website, downloadApp, sosPhone, sosPhoneCarrier, howHear,
               haveEmergency, whatEmergency, whenGetSos, approval, whatApproval)

        s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
            settings.SENDGRID_PASSWORD,
            secure=True)

        email = sendgrid.Message(
            'clifforloff@yahoo.com',
            subject,
            body,
            body)
        email.add_to('clifforloff@yahoo.com')
        s.web.send(email)

        self.render_school_account("Your email sent successfully")

    def render_school_account(self, error):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('school-account.mako',is_loggedin=False, error=error)
            self.response.out.write(out)
        else:
            out = self.render('school-account.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True,
                error = error)
            self.response.out.write(out)


class ContactHandler(TemplateHandler):
    """render template testimonials sosbeacon"""
    def get(self):
        self.render_contact('')

    def post(self):
        """Sent a email to admin of school beacon"""
        import sendgrid
        import settings

        name = self.request.POST['name']
        email = self.request.POST['email']
        subject = self.request.POST['subject']
        message = self.request.POST['message']

        body = """
            Request form details:
            <h2>Contact Information Form</h2>
            <strong>Name:</strong> %s<br />

            <strong>Email:</strong> %s<br />

            <strong>message:</strong> %s<br />
        """ % (name, email, message)

        s = sendgrid.Sendgrid(settings.SENDGRID_ACCOUNT,
            settings.SENDGRID_PASSWORD,
            secure=True)

        email = sendgrid.Message(
            'clifforloff@yahoo.com',
            subject,
            body,
            body)
        email.add_to('clifforloff@yahoo.com')
        s.web.send(email)

        self.render_contact('Your email sent successfully')

    def render_contact(self, error):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('contact.mako',is_loggedin=False, error=error)
            self.response.out.write(out)
        else:
            out = self.render('contact.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True,
                error = error)
            self.response.out.write(out)

class ForgotPasswordHandler(TemplateHandler):
    """render template testimonials sosbeacon"""
    def get(self):
        if not 'u' in self.session or not 's' in self.session:
            out = self.render('forgot_password.mako',is_loggedin=False, message="")
            self.response.out.write(out)
        else:
            out = self.render('forgot_password.mako', school_name = self.school_name,
                user_name = self.user_name,
                schools = self.list_school,
                timezone = '',
                is_loggedin = True,
                message="")
            self.response.out.write(out)

    def post(self):
        """sent email to admin of sosbeacon school"""
        from sosbeacon.user import forgot_password
        email    = self.request.POST['email']

        if not email:
            out = self.render('forgot_password.mako', is_loggedin=False,
                message="Please enter your email address.")
            self.response.out.write(out)
            return

        user_key = User.query(User.email == email)
        user = user_key.get()

        if user:
            forgot_password(user)
            out = self.render('forgot_password.mako', is_loggedin=False,
                message="Your new password has been sent to you by email message. "
                        "You will now be returned to where you were before.")
            self.response.out.write(out)
        else:
            out = self.render('forgot_password.mako', is_loggedin=False,
                message="""
                You have not entered a email address that we recognize, or your account has not been activated or you
                have not set a password in settings in your SOSbeacon app on your mobile phone. Please try again.
                """)
            self.response.out.write(out)


class SMSResponderHandler(TemplateHandler):
    def post(self):
        from sosbeacon.responde_sms import Responder
        from sosbeacon.event.message import Message
        from sosbeacon.event.contact_marker import mark_as_acknowledged

        from_number = self.request.get('From', None)
        from_body = self.request.get('Body', None)

        responder_sms_list = Responder.query(Responder.contact_number == from_number)
        responder_sms_filter = responder_sms_list.order(Responder.added).fetch()
        responder_sms = responder_sms_filter[-1]

        if responder_sms.is_admin == True:
            message = {
                'event': responder_sms.event,
                'type': 'c',
                'is_student': False,
                'user_name': responder_sms.contact_first_name + " " + responder_sms.contact_last_name + " - " + str(from_number),
                'message': {'body': from_body},
                'longitude': '',
                'latitude': '',
            }
            entity = Message.from_dict(message)
            entity.is_admin = True
            entity.user = None
            entity.put()
            return

        mark_as_acknowledged(responder_sms.event, responder_sms.contact_marker)

        message = {
            'event': responder_sms.event,
            'type': 'c',
            'is_student': False,
            'user_name': responder_sms.contact_first_name + " " + responder_sms.contact_last_name + " - " + str(from_number),
            'message': {'body': from_body},
            'longitude': '',
            'latitude': '',
        }
        entity = Message.from_dict(message)
        entity.is_admin = False
        entity.user = None
        entity.put()


class AccountHandler(TemplateHandler):
    """Change info of user"""
    @user_required
    def get(self):
        user_key = self.session.get('u')
        user = ndb.Key(urlsafe = user_key).get()

        self.render_account(error = "",
            user = user,
            school_name = self.school_name,
            schools = self.list_school)

    @user_required
    def post(self):
        """Update user info"""
        first_name = self.request.POST['first_name']
        last_name = self.request.POST['last_name']
        email = self.request.POST['email']
        phone = self.request.POST['phone']

        current_password = self.request.POST['current_password']
        new_password = self.request.POST['new_password']
        confirm_password = self.request.POST['confirm_password']

        errors = {
            'wrong' : 'Current password is wrong.',
            'required' : 'Field current password is required.',
            'not_correct' : 'Confirm password is not correct.',
            'success' : 'Account updated successfully.'
        }

        user_key = self.session.get('u')
        user = ndb.Key(urlsafe = user_key).get()

        if not current_password:
            self.render_account(error = errors['required'],
                user = user,
                school_name = self.school_name,
                schools = self.list_school)

        else:
            if check_password_hash(current_password, user.password):
                if new_password:
                    if new_password != confirm_password:
                        self.render_account(error = errors['not_correct'],
                            user = user,
                            school_name = self.school_name,
                            schools = self.list_school)
                    else:
                        self.update_user(user, first_name, last_name, phone, email, new_password)
                        self.render_account(error = errors['success'],
                            user = user,
                            school_name = self.school_name,
                            schools = self.list_school)
                else:
                    self.update_user(user, first_name, last_name, phone, email, user.password)
                    self.render_account(error = errors['success'],
                        user = user,
                        school_name = self.school_name,
                        schools = self.list_school)
            else:
                self.render_account(error = errors['wrong'],
                    user = user,
                    school_name = self.school_name,
                    schools = self.list_school)

    def update_user(self, user, first_name, last_name, phone, email, password):
        from sosbeacon.student import DEFAULT_STUDENT_ID
        from sosbeacon.student import Student

        student_key = ndb.Key(
            Student, "%s-%s" % (DEFAULT_STUDENT_ID, user.key.id()),
            namespace='_x_')

        student = student_key.get()
        student.first_name = first_name
        student.last_name = last_name
        student.contacts[0]['methods'][1]['value'] = phone
        to_put = [student]

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        if user.password != password:
            user.set_password(password)

        to_put.append(user)
        ndb.put_multi(to_put)

    def render_account(self, **context):
        out = self.render(template_name='account.mako', **context)
        self.response.out.write(out)


class CallBackHandler(TemplateHandler):
    """Record url, create object TwiML"""
    def post(self):
        from twilio import twiml

        answeredBy = self.request.get('AnsweredBy', '')
        textMessage = self.request.get('textMessage', '')
        playUrl = self.request.get('playUrl', '')

        logging.info(playUrl)

        response = twiml.Response()
        response.say('Hello, You have a broadcast from School Of Beacon. ')
        if (answeredBy == 'machine'):
            response.pause(2)
            response.say('We will read you the email broadcast from School Beacon now')
            response.pause(1)

        response.say(textMessage)
        if playUrl:
            response.play(playUrl)

        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(response)

url_map = [
    ('/', MainHandler),
    ('/school/web/users/login/', HomeLoginHandler),
    ('/school/web/users/logout/', HomeLogoutHandler),
    ('/school/web/users/selectschool/', SelectSchool),
    ('/school', HomeHandler),
    ('/school/web/about/index', AboutHandler),
    ('/school/web/about/features', FeaturesHandler),
    ('/school/web/about/testimonials', TestimonialsHandler),
    ('/school/web/about/contact', ContactHandler),
    ('/school/web/about/privacy', PrivacyHandler),
    ('/school/web/about/terms', TermHandler),
    ('/school/web/about/school-account', SchoolAccountHandler),
    ('/school/web/users/forgot', ForgotPasswordHandler),
    ('/school/webapp/account', AccountHandler),
    ('/admin/', AdminHandler),
    ('/e/(.*)/(.*)', EventHandler),
    ('/import/students/upload/', StudentImportHandler),
    ('/import/contacts/upload/', ContactImportHandler),
    ('/uploads/new', FileUploadHandler),
    ('/uploads/post', FileUploadPostHandler),
    ('/uploads/view/([^/]+)?', FileUplaodViewHandler),
    webapp2.Route(r'/school/<resource_id:.+>',
        handler='main.ChooseSchoolHandler'),
    ('/sms-response', SMSResponderHandler),
    ('/broadcast/record', CallBackHandler),
]
app = webapp2.WSGIApplication(
    url_map,
    config=webapp_config
)
