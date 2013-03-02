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
from google.appengine.ext import ndb

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

            webapp2.Route(r'/service/admin/user<:/?>',
                          handler='sosbeacon.service.UserListHandler'),

            ('/authentication/login', LoginUserHandler)
        ]

        app = webapp2.WSGIApplication(
            url_map,
            config=webapp_config
        )
        self.testapp = webtest.TestApp(app)

        self.school1 = School(
            id='100',
            name='School_Test',
        )

        self.school2 = School(
            id='200',
            name='School_Test_2',
        )

        self.school1.put()

        params = {
            'name': 'longly',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'password': '123456',
            'schools': [self.school1.key.urlsafe()]
        }
        self.testapp.post_json('/service/admin/user/', params)

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
            id=ADMIN_GROUPS_ID + "%s" % (self.school1.key.id()),
            name='Group Admin',
            school=self.school1.key,
            default = True
        )

        self.group_staff = Group(
            id=STAFF_GROUPS_ID + "%s" % (self.school1.key.id()),
            name='Group Staff',
            school=self.school1.key,
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
        to_put = [self.group1, self.group2, self.group3, self.group4, self.group_admin, self.group_staff]
        ndb.put_multi(to_put)

        response = self.testapp.get('/service/group')
        obj = json.loads(response.normal_body)

        self.assertEqual(len(obj), 5)

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

#    def test_service_edit_duplicate_group(self):
#        """Ensure user can not edit duplication group name"""
#        self.group1.put()
#        params = {
#            'name':'Group 1'
#        }
#        response = self.testapp.put_json('/service/group/%s' % self.group1.key.urlsafe(), params)
#        logging.info(response)
#        self.assertEqual(response.status_int, 400)

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

    def test_number_student_of_group(self):
        """Ensure number student of group always > 1"""
        to_put = [self.group1, self.group2, self.group3, self.group4, self.group_admin, self.group_staff]
        ndb.put_multi(to_put)

        response = self.testapp.get('/service/group')
        obj = json.loads(response.normal_body)

        for i in obj:
            self.assertGreaterEqual(1, i['number_student'])

    def test_sort_admin_staff_group(self):
        """Ensure admin and staff always at position 1 and 2"""
        to_put = [self.group1, self.group2, self.group3, self.group4, self.group_admin, self.group_staff]
        ndb.put_multi(to_put)

        response = self.testapp.get('/service/group')
        obj = json.loads(response.normal_body)

        self.assertEqual(obj[0]['name'], self.group_admin.name)
        self.assertEqual(obj[1]['name'], self.group_staff.name)


class TestServiceContact(unittest.TestCase):
    """Test service contact"""
    def setUp(self):
        from sosbeacon.school import School
        from sosbeacon.student import Student
        from sosbeacon.student import DEFAULT_STUDENT_ID

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='testapp')
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        url_map = [
            webapp2.Route(r'/service/student/<resource_id:.+>',
                          handler='sosbeacon.service.StudentHandler'),
            webapp2.Route(r'/service/student<:/?>',
                          handler='sosbeacon.service.StudentListHandler'),

            webapp2.Route(r'/service/admin/user<:/?>',
                          handler='sosbeacon.service.UserListHandler'),

            ('/authentication/login', LoginUserHandler)
        ]

        app = webapp2.WSGIApplication(
            url_map,
            config=webapp_config
        )
        self.testapp = webtest.TestApp(app)

        self.school1 = School(
            id='100',
            name='School_Test',
        )

        self.school2 = School(
            id='200',
            name='School_Test_2',
        )

        self.school1.put()
        self.school2.put()

        params = {
            'name': 'longly',
            'email': 'longly@cnc.vn',
            'phone': '84973796065',
            'password': '123456',
            'schools': [self.school1.key.urlsafe()]
        }
        self.testapp.post_json('/service/admin/user/', params)

        email = 'longly@cnc.vn'
        password = '123456'

        params1 = {'email': email, 'password': password}
        self.testapp.post('/authentication/login', params1)


        self.student1 = Student(
            id = '1',
            name = 'Student 1',
            contacts = [{
                            'name': 'contact 1',
                            'methods': ['123432', 'me@earth.com']
                        },
                        {
                            'name': 'contact 2',
                            'methods': ['123432', 'me@earth.com']
                        }
            ],
            school = self.school1.key,
            is_direct = False
        )

        self.student2 = Student(
            id = '2',
            name = 'Student 2',
            contacts = [{
                            'name': 'contact 1',
                            'methods': ['123432', 'me@earth.com']
                        },
                        {
                            'name': 'contact 2',
                            'methods': ['123432', 'me@earth.com']
                        }
            ],
            school = self.school1.key,
            is_direct = False
        )

        self.student3 = Student(
            id = '3',
            name = 'Student 3',
            contacts = [{
                            'name': 'contact 1',
                            'methods': ['123432', 'me@earth.com']
                        },
                        {
                            'name': 'contact 2',
                            'methods': ['123432', 'me@earth.com']
                        }
            ],
            school = self.school1.key,
            is_direct = True
        )

        self.student4 = Student(
            id = '4',
            name = 'Student 4',
            contacts = [{
                            'name': 'contact 1',
                            'methods': ['123432', 'me@earth.com']
                        },
                        {
                            'name': 'contact 2',
                            'methods': ['123432', 'me@earth.com']
                        }
            ],
            school = self.school2.key,
            is_direct = True
        )

        self.student5 = Student(
            id = '5',
            name = 'Student 5',
            contacts = [{
                            'name': 'contact 1',
                            'methods': ['123432', 'me@earth.com']
                        },
                        {
                            'name': 'contact 2',
                            'methods': ['123432', 'me@earth.com']
                        }
            ],
            school = self.school2.key,
            is_direct = False
        )

    def test_service_create_student(self):
        """Ensure create success new student with json object send from client"""
        params = {
            'name': 'Student Test',
            'groups': [],
            'contacts': [{
                             'name': 'contact 1',
                             'methods': ['123432', 'me@earth.com']
                         },
                         {
                             'name': 'contact 2',
                             'methods': ['123432', 'me@earth.com']
                         }
            ]
        }

        response = self.testapp.post_json('/service/student', params)
        obj = json.loads(response.normal_body)

        self.assertEqual(response.status_int, 200)
        self.assertEqual(obj['name'], params['name'])
        self.assertEqual(obj['groups'], params['groups'])
        self.assertFalse(obj['is_direct'])

    def test_service_get_filter_student_contact(self):
        """Ensure server response student contact which same school"""
        from google.appengine.ext import ndb
        to_put = [self.student1, self.student2, self.student3, self.student4, self.student5]
        ndb.put_multi(to_put)

        response = self.testapp.get('/service/student?feq_is_direct=false')
        obj = json.loads(response.normal_body)

        self.assertEqual(len(obj), 2)

    def test_service_get_filter_direct_contact(self):
        """Ensure server response student contact which same school and default student"""
        from google.appengine.ext import ndb
        to_put = [self.student1, self.student2, self.student3, self.student4, self.student5]
        ndb.put_multi(to_put)

        response = self.testapp.get('/service/student?feq_is_direct=true')
        obj = json.loads(response.normal_body)

        self.assertEqual(len(obj), 2)
        self.assertTrue(obj[0]['default_student'])


    def test_service_edit_student(self):
        """Ensure student will be update new data"""
        self.student1.put()
        params = {
            'name': 'Update Student',
            'groups': [],
            'contacts': [{
                             'name': 'contact 1',
                             'methods': ['123432', 'me@earth.com']
                         },
                         {
                             'name': 'contact 2',
                             'methods': ['123432', 'me@earth.com']
                         }
            ]
        }

        response = self.testapp.put_json('/service/student/%s' % self.student1.key.urlsafe(), params)
        obj = json.loads(response.normal_body)

        self.assertEqual(response.status_int, 200)
        self.assertEqual(obj['name'], params['name'])
        self.assertEqual(obj['groups'], params['groups'])

    def test_service_delete_student(self):
        """Ensure this student will be None object"""
        from google.appengine.ext import ndb
        self.student1.put()
        response = self.testapp.delete('/service/student/%s' %self.student1.key.urlsafe())
        query_event = ndb.Key(urlsafe=self.student1.key.urlsafe())
        self.assertIsNone(query_event.get())
        self.assertEqual(response.status_int, 200)

