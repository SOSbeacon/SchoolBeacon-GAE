import unittest
import mock
import webapp2
import webtest
import logging
import json

from SOSBeacon.login import LoginUserHandler
from SOSBeacon.login import LoginAdminHandler
from sosbeacon.user import User
from sosbeacon.school import School

from config import webapp_config

from google.appengine.ext import testbed

@mock.patch('main.TemplateHandler', autospec=True)
@mock.patch('webapp2_extras.sessions', autospec=True)
class TestLogInSystem(unittest.TestCase):
    """Test login"""
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        app = webapp2.WSGIApplication([
            ('/authentication/login', LoginUserHandler),
        ], config=webapp_config)
        self.testapp = webtest.TestApp(app)

        self.user = User(
            id='1',
            name='longly',
            password = 'f14c30f4f19d7810c44801fc0f93ac1d890b1b3a$sha1$QIhZGsYB2JHF',
            email = 'longly@cnc.vn',
            phone = '84973796065'
        )

        self.supper_user = User(
            id='2',
            name='supper user',
            password = 'f14c30f4f19d7810c44801fc0f93ac1d890b1b3a$sha1$QIhZGsYB2JHF',
            email = 'admin@cnc.vn',
            phone = '84973796061',
            is_admin = True
        )

        self.school1 = School(
            id='100',
            name='School_Test',
        )

        self.school2 = School(
            id='200',
            name='School_Test_2',
        )

    def test_get_url_login(self, sessions_mock, template_mock):
        """Test the app, passing parameters to build a request."""
        response = self.testapp.get('/authentication/login')
        self.assertEqual(response.status_int, 200)

    def test_login_wrong_password(self, sessions_mock, template_mock):
        """Test post wrong email and password to url login"""
        email = 'longly@cnc.vn'
        password = 'abc123'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/authentication/login', params)
        self.assertEqual(response.status_int, 200)
        self.assertIn('Email or Password is wrong!.', response.normal_body)

    def test_login_wrong_email(self, sessions_mock, template_mock):
        """Test post wrong email and password to url login"""
        email = 'longly1@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/authentication/login', params)
        self.assertEqual(response.status_int, 200)
        self.assertIn('Email or Password is wrong!.', response.normal_body)

    def test_login_user_no_assign_school(self, sessions_mock, template_mock):
        """Test post correct email and password to url login but do not assign to school"""
        self.user.put()
        email = 'longly@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/authentication/login', params)

        self.assertEqual(response.status_int, 200)
        self.assertIn("You don't have any schools!. Please contact with admin for this reason.",
            response.normal_body)

    def test_login_user_assigned_one_school(self, sessions_mock, template_mock):
        """Test post correct email and password to url login and assigned to one school"""
        self.school1.put()
        self.user.schools = [self.school1.key]
        self.user.put()

        email = 'longly@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/authentication/login', params)

        self.assertEqual(response.location, 'http://localhost/')

    def test_login_assigned_multi_school(self, sessions_mock, template_mock):
        """Test post correct email and password to url login and assigned to multi school"""
        self.school1.put()
        self.school2.put()
        self.user.schools = [self.school1.key, self.school2.key]
        self.user.put()

        email = 'longly@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/authentication/login', params)

        self.assertEqual(response.status_int, 200)
        self.assertIn("Please choose school",response.normal_body)
        self.assertIn(self.school1.name, response.normal_body)
        self.assertIn(self.school2.name, response.normal_body)

    def test_user_login_is_admin(self, sessions_mock, template_mock):
        """Ensure superuser can not logged to system"""
        self.supper_user.put()

        email = 'admin@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/authentication/login', params)

        self.assertEqual(response.status_int, 200)
        self.assertIn('Email or Password is wrong!.', response.normal_body)


class TestAdminLogin(unittest.TestCase):
    """Test admin login"""
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        app = webapp2.WSGIApplication([
            ('/admin/authentication/login', LoginAdminHandler),
        ], config=webapp_config)
        self.testapp = webtest.TestApp(app)

        self.supper_user = User(
            id='2',
            name='supper user',
            password = 'f14c30f4f19d7810c44801fc0f93ac1d890b1b3a$sha1$QIhZGsYB2JHF',
            email = 'admin@cnc.vn',
            phone = '84973796061',
            is_admin = True
        )

        self.normal_user = User(
            id='1',
            name = 'normal user',
            password = 'f14c30f4f19d7810c44801fc0f93ac1d890b1b3a$sha1$QIhZGsYB2JHF',
            email = 'longly@cnc.vn',
            phone = '84973796065',
        )

    def test_normal_user_can_not_login_admin(self):
        """Ensure normal user can not login to admin area"""
        self.normal_user.put()

        email = 'longly@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/admin/authentication/login', params)

        self.assertEqual(response.status_int, 200)
        self.assertIn('Email or Password is wrong!.', response.normal_body)

    def test_supper_user_login_admin(self):
        """Ensure supper can be login to admin area"""
        self.supper_user.put()

        email = 'admin@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/admin/authentication/login', params)

        self.assertEqual(response.location, 'http://localhost/admin')

    def test_supper_user_wrong_password(self):
        """Ensure supper user can not login with wrong password"""
        self.supper_user.put()

        email = 'admin@cnc.vn'
        password = '1234567'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/admin/authentication/login', params)

        self.assertIn('Email or Password is wrong!.', response.normal_body)

    def test_supper_user_wrong_email(self):
        """Ensure supper user can not login with wrong password"""
        self.supper_user.put()

        email = 'admin1@cnc.vn'
        password = '123456'

        params = {'email': email, 'password': password}
        response = self.testapp.post('/admin/authentication/login', params)

        self.assertIn('Email or Password is wrong!.', response.normal_body)

@mock.patch('main.TemplateHandler', autospec=True)
@mock.patch('webapp2_extras.sessions', autospec=True)
class TestLogOutSystem(unittest.TestCase):
    """Test logout system"""
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        app = webapp2.WSGIApplication([('/authentication/logout', LoginUserHandler)], config=webapp_config)
        self.testapp = webtest.TestApp(app)

    def test_get_url_logout(self, sessions_mock, template_mock):
        """Ensure when logout, auto redirect /authentication/logout"""
        response = self.testapp.get('/authentication/logout')
        self.assertIn('School Beacon Login', response.normal_body)
        self.assertEqual(response.status_int, 200)


