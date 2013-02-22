import unittest
import mock
import logging
import webtest
import json
import webapp2

from datetime import datetime

from config import webapp_config
from sosbeacon.user import User
from login import LoginUserHandler

from google.appengine.ext import testbed

class TestGroupService(unittest.TestCase):
    """Test service of group"""
    def setUp(self):
        from sosbeacon.school import School
        from sosbeacon.group import Group
        from sosbeacon.group import ADMIN_GROUPS_ID
        from sosbeacon.group import STAFF_GROUPS_ID

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()

        url_map = [
            webapp2.Route(r'/service/group/<resource_id:.+>',
                handler='sosbeacon.service.GroupHandler'),
            webapp2.Route(r'/service/group<:/?>',
                handler='sosbeacon.service.GroupListHandler'),
            ('/authentication/login', LoginUserHandler)
        ]

        app = webapp2.WSGIApplication(
            url_map,
            config=webapp_config
        )
        self.testapp = webtest.TestApp(app)

        self.user = User(
            id='1',
            name='longly',
            password = 'f14c30f4f19d7810c44801fc0f93ac1d890b1b3a$sha1$QIhZGsYB2JHF',
            email = 'longly@cnc.vn',
            phone = '84973796065'
        )

        self.school1 = School(
            id='100',
            name='School_Test',
        )

        self.school2 = School(
            id='200',
            name='School_Test_2',
        )

        self.school1.put()
        self.user.schools = [self.school1.key]
        self.user.put()

        email = 'longly@cnc.vn'
        password = '123456'

        params1 = {'email': email, 'password': password}
        self.testapp.post('/authentication/login', params1)

        self.group1 = Group(
            id='1',
            name='Group 1',
            school=self.school1.key
        )

        self.group2 = Group(
            id='2',
            name='Group 2',
            school=self.school1.key
        )

        self.group3 = Group(
            id='3',
            name='Group 3',
            school=self.school1.key
        )

        self.group4 = Group(
            id='4',
            name='Group 4',
            school=self.school2.key
        )

        self.group_admin = Group(
            id=ADMIN_GROUPS_ID,
            name='Group Admin',
            school=self.school2.key,
            default = True
        )

    def test_service_url(self):
        """Ensure link to service group exists"""
        response = self.testapp.get('/service/group')
        self.assertEqual(response.status_int, 200)

    def test_service_create_group(self):
        """Ensure create success new event with json object send from client"""
        params = {
            'name': 'Group Test',
            }

        response = self.testapp.post_json('/service/group', params)
        obj = json.loads(response.normal_body)

        self.assertEqual(response.status_int, 200)
        self.assertEqual(obj['name'], params['name'])

    def test_service_create_exists_name_group(self):
        """Ensure can not create duplicate name group"""
        self.group1.put()
        params = {
            'name' : 'Group 1',
        }
        response = self.testapp.post_json('/service/group', params, status=400)

        self.assertEqual(response.status_int, 400)

    def test_service_get_filter_group(self):
        """Ensure server response group which same school"""
        from google.appengine.ext import ndb
        to_put = [self.group1, self.group2, self.group3, self.group4]
        ndb.put_multi(to_put)

        response = self.testapp.get('/service/group')
        obj = json.loads(response.normal_body)

        self.assertEqual(len(obj), 3)

    def test_service_edit_group(self):
        """Ensure group will be update new data"""
        self.group1.put()
        params = {
            'name':'Update Group'
        }

        response = self.testapp.put_json('/service/group/%s' % self.group1.key.urlsafe(), params)
        obj = json.loads(response.normal_body)

        self.assertEqual(response.status_int, 200)
        self.assertEqual(obj['name'], params['name'])

    def test_service_edit_default_group(self):
        """Ensure can not update information of default group"""
        self.group_admin.put()
        params = {
            'name':'Update Group Admin'
        }
        response = self.testapp.put_json('/service/group/%s' % self.group_admin.key.urlsafe(), params, status=400)
        self.assertEqual(response.status_int, 400)

    def test_service_delete_group(self):
        """Ensure this group will be None object"""
        from google.appengine.ext import ndb
        self.group1.put()
        response = self.testapp.delete('/service/group/%s' %self.group1.key.urlsafe())
        query_group = ndb.Key(urlsafe=self.group1.key.urlsafe())
        self.assertIsNone(query_group.get())
        self.assertEqual(response.status_int, 200)

    def test_service_delete_default_group(self):
        """Ensure can not delete default group"""
        self.group_admin.put()
        response = self.testapp.delete('/service/group/%s' % self.group_admin.key.urlsafe(), status=400)
        self.assertEqual(response.status_int, 400)

