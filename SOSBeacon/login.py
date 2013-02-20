#!/usr/bin/python
#
# Copyright 2012 Ezox Systems, LLC
#
# This software is licensed. If a license was not provided with
# these files please contact Ezox Systems, LLC.
#
# Unless required by applicable law or agreed to in writing, this
# software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under
# the License.
"""OpenID login and user setup handlers."""

import logging
import os
import sys
import webapp2

from google.appengine.ext import ndb
from webapp2_extras.security import check_password_hash

from config import webapp_config
from main import TemplateHandler

from sosbeacon.user import User

# Add lib to path.
libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
if libs_dir not in sys.path:
    logging.debug('Adding lib to path.')
    sys.path.insert(0, libs_dir)

class LoginUserHandler(TemplateHandler):
    """Construct the login url and redirect home."""
    def get(self, *args, **kwargs):
        if not 'u' in self.session:
            self.render_user_login(is_loggedin=False, error="")
            return

        urlsafe = self.session.get('u')
        user_key = ndb.Key(urlsafe=urlsafe)

        user = user_key.get()
        school = self.session.get('s')

        if len(user.schools) == 1 or school:
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
        out = self.render(template_name='login.mako', **context)
        self.response.out.write(out)

    def delete_session(self):
        """delete all session"""
        for key in self.session.keys():
            if key != 'tz':
                del self.session[key]


class LogoutUserHandler(TemplateHandler):
    """Log out and delete all session except session timezone."""
    def get(self, *args, **kwargs):
        if self.session:
            for key in self.session.keys():
                if key != 'tz':
                    del self.session[key]

        self.redirect("/authentication/login")


class LoginAdminHandler(TemplateHandler):
    def get(self):
        if not 'ad' in self.session:
            self.render_admin_login(error="")
        else:
            self.redirect("/admin")

    def post(self, *args, **kwargs):
        if not 'ad' in self.session:
            email    = self.request.POST['email']
            password = self.request.POST['password']

            user = User.query(ndb.AND(User.email == email,
                User.is_admin == True),
                namespace = '_x_')

            if user.get() is None:
                self.render_admin_login(error='Email or Password is wrong!.')
                return
            else:
                if check_password_hash(password, user.get().password):
                    self.setup_admin_session(user)
                else:
                    self.render_admin_login(error='Email or Password is wrong!.')
                    return

        self.redirect("/admin")

    def setup_admin_session(self, user):
        """set session for current admin"""
        self.session['ad'] = user.get().key.urlsafe()

    def render_admin_login(self, **context):
        out = self.render(template_name='admin_login.mako', **context)
        self.response.out.write(out)


class LogoutAdminHandler(TemplateHandler):
    def get(self, *args, **kwargs):
        """Logout and delete all session"""
        for key in self.session.keys():
            del self.session[key]
        self.redirect("/admin/authentication/login")

url_map = [
    #    ('/_ah/login_required', LoginHandler),
    ('/authentication/login', LoginUserHandler),
    ('/authentication/logout', LogoutUserHandler),
    ('/admin/authentication/login', LoginAdminHandler),
    ('/admin/authentication/logout', LogoutAdminHandler),
]
app = webapp2.WSGIApplication(
    url_map,
    config=webapp_config)
