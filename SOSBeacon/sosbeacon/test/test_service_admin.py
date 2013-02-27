import mock
import unittest
import json
import webtest
import logging
import webapp2

from google.appengine.ext import testbed
from google.appengine.ext import ndb
from webapp2_extras import security

from config import webapp_config
from sosbeacon.user import User

class TestServiceUser(unittest.TestCase):
    """Test service GET PUT POST user"""
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id = 'testapp')
        self.testbed.init_datastore_v3_stub()

        url_map = [
            webapp2.Route(r'/service/admin/user/<resource_id>',
                      handler='sosbeacon.service.UserHandler'),
            webapp2.Route(r'/service/admin/user<:/?>',
                      handler='sosbeacon.service.UserListHandler'),
        ]
        app = webapp2.WSGIApplication(
            url_map,
            config = webapp_config
        )
        self.testapp = webtest.TestApp(app)

        self.user1 = User(
            id = '100',
            name = 'longly1',
            email = 'longly1@cnc.vn',
            phone = '84973796061',
            password = 'asdfasdfasdfasdf',
        )

        self.user2 = User(
            id = '200',
            name = 'longly2',
            email = 'longly2@cnc.vn',
            phone = '84973796062',
            password = 'qwefasdfqwer',
        )
#       create a new test super user
        self.user3 = User(
            id = '300',
            name = 'longly3',
            email = 'longly3@cnc.vn',
            phone = '84973796063',
            password = 'qwefasdfqwerasdfasdf',
            is_admin = True
        )

    @mock.patch('sosbeacon.user.User.set_password', autospec=True)
    def test_post_user_encrypt_password(self, set_password_mock):
        """Ensure when create new user, password have to encrypt and do not response password to client"""
        params = {
            'name': 'longly',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'password': '123456',
            'schools': []
        }

        response = self.testapp.post_json('/service/admin/user/', params)
        obj = json.loads(response.normal_body)

        self.assertEqual(1, set_password_mock.call_count)
        self.assertEqual(params['name'], obj['name'])
        self.assertEqual(params['phone'], obj['phone'])
        self.assertEqual(params['email'], obj['email'])
        self.assertNotIn('password', obj)

    def test_post_user_empty_email(self):
        """Ensure can not create new user if params email is empty"""
        params = {
            'name': 'longly',
            'email': '',
            'phone': '84973796065',
            'password': '123456',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params, status=400)
        self.assertEqual(response.status_int, 400)

    def test_post_user_empty_phone(self):
        """Ensure can not create new user if params phone is empty"""
        params = {
            'name': 'longly',
            'email': 'longly@cnc.vn',
            'phone': '',
            'password': '123456',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params, status=400)
        self.assertEqual(response.status_int, 400)

    def test_post_user_empty_name(self):
        """Ensure can not create new user if params name is empty"""
        params = {
            'name': '',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'password': '123456',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params, status=400)
        self.assertEqual(response.status_int, 400)

    def test_post_user_password_too_short(self):
        """Ensure can not create new user if password less than 6 character"""
        params = {
            'name': 'longly',
            'email': 'longly@cnc.nv',
            'phone': '84973796065',
            'password': '1',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params, status=400)
        self.assertEqual(response.status_int, 400)

    @mock.patch('sosbeacon.student.create_default_student', autospec=True)
    def test_post_user_create_student_default(self, create_default_student_mock):
        """Ensure when user is created, a student default of this user would be created too"""
        params = {
            'name': 'longly',
            'email': 'longly@cnc.nv',
            'phone': '84973796065',
            'password': '123456',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(1, create_default_student_mock.call_count)

    def test_unique_email_user(self):
        """Ensure can not create two user with same email"""
        ndb.put_multi([self.user1, self.user2])

        params = {
            'name': 'longly1',
            'email': 'longly1@cnc.vn',
            'phone': '84973796065',
            'password': '123456',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params, status=400)
        self.assertEqual(response.status_int, 400)

    def test_unique_phone_user(self):
        """Ensure can not create two user with same phone"""
        ndb.put_multi([self.user1, self.user2])

        params = {
            'name': 'longly1',
            'email': 'longly3@cnc.vn',
            'phone': '84973796061',
            'password': '123456',
            'schools': []
        }
        response = self.testapp.post_json('/service/admin/user/', params, status=400)
        self.assertEqual(response.status_int, 400)

    def test_service_get_user(self):
        """Ensure server response a list json user"""
        ndb.put_multi([self.user1, self.user2])

        response = self.testapp.get('/service/admin/user/')
        obj = json.loads(response.normal_body)

        self.assertEqual(response.status_int, 200)
        self.assertEqual(len(obj), 2)

    def test_update_empty_password(self):
        """Ensure user password do not change if params password less than 6 character"""
        ndb.put_multi([self.user1])
        params = {
            'name': 'longly1',
            'email': 'longly1@cnc.vn',
            'phone': '84973796065',
            'password': '',
            'schools': []
        }
        response = self.testapp.put_json('/service/admin/user/%s' % self.user1.key.urlsafe(), params)
        obj = json.loads(response.normal_body)

        self.assertNotEqual(self.user1.password, params['password'])
        self.assertEqual(obj['phone'], params['phone'])

    @mock.patch('sosbeacon.user.send_invitation_email', autospec=True)
    def test_send_invitation_email(self, send_invitation_email_mock):
        """Ensure server auto sent a email to user when create new user"""
        params = {
            'name': 'longly',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'password': '123456',
            'schools': []
        }
        self.testapp.post_json('/service/admin/user/', params)
        self.assertEqual(1, send_invitation_email_mock.call_count)

    def test_service_delete_user(self):
        """Ensure user will be delete"""
        ndb.put_multi([self.user1])
        self.testapp.delete('/service/admin/user/%s' % self.user1.key.urlsafe())
        query_user = ndb.Key(urlsafe=self.user1.key.urlsafe())
        self.assertIsNone(query_user.get())
