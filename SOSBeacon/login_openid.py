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
import urllib

# Add lib to path.
libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
if libs_dir not in sys.path:
    logging.debug('Adding lib to path.')
    sys.path.insert(0, libs_dir)


from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
from webapp2_extras import sessions

from config import webapp_config

from sosbeacon.school import School
from sosbeacon.user import User


class LoginHandler(webapp2.RequestHandler):
    """Construct the login url and redirect the user to it."""
    def get(self, *args, **kwargs):
        session_store = sessions.get_store()
        session = session_store.get_session()
        if session:
            # TODO: Is there a better way to do this?
            for key in session.keys():
                del session[key]

        federated_identity = 'google.com/accounts/o8/id'

        token = self.request.get('tk')
        if token:
            session['tk'] = token
            session_store.save_sessions(self.response)

        school = self.request.get('sc')
        params = {}
        if school:
            params['sc'] = school

        dest_url = '/_userconfig?' + urllib.urlencode(params)

        login_url = users.create_login_url(
            dest_url=dest_url,
            federated_identity=federated_identity)

        self.redirect(login_url)

    def post(self, *args, **kwargs):
        self.get(*args, **kwargs)


class UserConfigHandler(webapp2.RequestHandler):
    """The user is authenticated, auth them into the proper namespace."""
    def get(self):
        self.user = users.get_current_user()
        self.user_key = ndb.Key(User, str(self.user.user_id()), namespace='')
        self.user_future = self.user_key.get_async()

        school_urlsafe = self.request.get('sc')
        if not school_urlsafe:
            school_key = self.handle_existing_user()
        else:
            school_key = self.handle_new_user(school_urlsafe)

        if not school_key:
            # TODO: Somewhere better here?
            logging.debug("Couldn't find school %s.", school_urlsafe)
            self.redirect(users.create_logout_url('http://google.com'))
            return

        self.setup_session(school_key)

        continue_to = self.request.get('continue', '/')
        if self.needs_tos_accept:
            params = {'continue_to': continue_to}
            continue_to = '/_userconfig/tosaccept?' + urllib.urlencode(params)

        self.redirect(continue_to)

    def setup_session(self, school_key):
        """Setup the session vars."""
        session_store = sessions.get_store()
        session = session_store.get_session()
        session['u'] = self.user.user_id()
        session['n'] = str(school_key.id())
        session['s'] = school_key.urlsafe()
        session_store.save_sessions(self.response)

    def handle_existing_user(self):
        """Return the default school from this user."""
        user = self.user_future.get_result()
        if not user:
            # TODO: Redirect to some help page or something?
            logging.debug("Couldn't find user: %s.", self.user_key)
            self.redirect(users.create_logout_url('http://google.com'))
            return

        self.needs_tos_accept = True if not user.tos_accepted else False

        # TODO: Provide some mechansim to set default_school.
        # TODO: Check that the user is still allowed to access school?
        return user.default_school

    def handle_new_user(self, school_urlsafe):
        """Add the user to the school user list, and remove the reg token."""
        school_key = ndb.Key(urlsafe=school_urlsafe)
        school_entity = school_key.get()
        if not school_entity:
            # School doesn't exist... log them out and redirect them away.
            logging.warning('Missing school: %s.', school_urlsafe)
            self.redirect(users.create_logout_url('http://google.com'))
            return

        if self.user_key not in school_entity.users:
            session_store = sessions.get_store()
            session = session_store.get_session()
            reg_token = session.get('tk')
            if 'tk' in session:
                del session['tk']
            if not reg_token or reg_token not in school_entity.invited:
                logging.warning("Invalid token '%s'", reg_token)
                # User isn't allowed or bad invite token.
                self.redirect(users.create_logout_url('http://google.com'))
                return

            @ndb.transactional
            def update_school_txn(user_key, reg_token):
                school_entity = school_key.get()
                if user_key in school_entity.users:
                    return

                school_entity.invited.remove(reg_token)
                school_entity.users.append(user_key)
                return school_entity.put()
            update_school_txn(self.user_key, reg_token)

        user_entity = self.user_future.get_result()
        if not user_entity or school_key not in user_entity.schools:
            @ndb.transactional
            def update_user_txn(user_key, school_key):
                user_entity = user_key.get()
                if user_entity and school_key in user_entity.schools:
                    return

                if not user_entity:
                    user_entity = User(
                        key=user_key,
                        user=self.user,
                        name=self.user.nickname(),
                        default_school=school_key,
                        schools=[])

                user_entity.schools.append(school_key)
                user_entity.put()

            update_user_txn(self.user_key, school_key)

        self.needs_tos_accept = True
        return school_key


class ToSAcceptHandler(webapp2.RequestHandler):
    """The user is authenticated, ask them to accept the ToS."""
    def get(self):
        """Display the ToS."""
        from mako import exceptions
        from mako.lookup import TemplateLookup

        continue_to = self.request.get('continue_to')
        try:
            lookup = TemplateLookup(directories=['templates'])
            template = lookup.get_template('tosaccept.mako')
            out = template.render(continue_to=continue_to)
        except:
            out = exceptions.html_error_template().render()
            logging.exception('Oh NO!')

        self.response.out.write(out)

    def post(self):
        user = users.get_current_user()
        user_key = ndb.Key(User, str(user.user_id()), namespace='')
        user_future = user_key.get_async()

        accept = self.request.get('accept')
        if accept != "I Accept the Terms":
            logging.info("Didn't accept the terms")
            self.redirect(users.create_logout_url('http://google.com'))
            return

        user = user_future.get_result()
        if not user:
            logging.info("User not found.")
            logging.info(user_key)
            self.redirect(users.create_logout_url('http://google.com'))
            return

        if not user.tos_accepted:
            from datetime import datetime
            @ndb.transactional
            def update_user_txn(user_key):
                user_entity = user_key.get()
                user_entity.tos_accepted = datetime.now()
                user_entity.put()

            update_user_txn(user_key)

        continue_to = self.request.get('continue_to')
        if not continue_to:
            continue_to = '/'
        self.redirect(continue_to)


url_map = [
    ('/_ah/login_required', LoginHandler),
    ('/_userconfig', UserConfigHandler),
    ('/_userconfig/tosaccept', ToSAcceptHandler)
]
app = webapp2.WSGIApplication(
    url_map,
    config=webapp_config)

