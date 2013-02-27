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

"""Map service handlers here.  These might be exposed JSON endpoints."""

import logging
import os
import sys

# Add lib to path.
libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
if libs_dir not in sys.path:
    logging.debug('Adding lib to path.')
    sys.path.insert(0, libs_dir)

import webapp2

from config import webapp_config

url_map = [
    # Contact
    webapp2.Route(r'/service/contact/<resource_id:.+>',
                  handler='sosbeacon.service.ContactHandler'),
    webapp2.Route(r'/service/contact<:/?>',
                  handler='sosbeacon.service.ContactListHandler'),
    # Student
    webapp2.Route(r'/service/student/<resource_id:.+>',
                  handler='sosbeacon.service.StudentHandler'),
    webapp2.Route(r'/service/student<:/?>',
                  handler='sosbeacon.service.StudentListHandler'),

    ## Event - Student Marker
    #webapp2.Route(r'/service/event/student',
    #              handler='sosbeacon.service.EventStudentListHandler'),
    #webapp2.Route(r'/service/event/student/<resource_id>',
    #              handler='sosbeacon.service.EventStudentHandler'),
    ## Event
    webapp2.Route(r'/service/event/<resource_id>',
                  handler='sosbeacon.service.EventHandler'),
    webapp2.Route(r'/service/event<:/?>',
                  handler='sosbeacon.service.EventListHandler'),
    #Message
    webapp2.Route(r'/service/message/<resource_id>',
                  handler='sosbeacon.service.MessageHandler'),
    webapp2.Route(r'/service/message<:/?>',
                  handler='sosbeacon.service.MessageListHandler'),

    # Group
    webapp2.Route(r'/service/group/<resource_id:.+>',
                  handler='sosbeacon.service.GroupHandler'),
    webapp2.Route(r'/service/group<:/?>',
                  handler='sosbeacon.service.GroupListHandler'),

    # School
    webapp2.Route(r'/service/admin/school/<resource_id:.+>',
                  handler='sosbeacon.service.SchoolHandler'),
    webapp2.Route(r'/service/admin/school<:/?>',
                  handler='sosbeacon.service.SchoolListHandler'),

    # Contact marker
    webapp2.Route(r'/service/contact_marker<:/?>',
                  handler='sosbeacon.service.ContactMarkerListHandler'),

    # Student marker
    webapp2.Route(r'/service/student_marker<:/?>',
                  handler='sosbeacon.service.StudentMarkerListHandler'),

    # User
    webapp2.Route(r'/service/admin/user/<resource_id:.+>',
                  handler='sosbeacon.service.UserHandler'),
    webapp2.Route(r'/service/admin/user<:/?>',
                  handler='sosbeacon.service.UserListHandler'),

    # Export Student contact to csv file
    webapp2.Route(r'/service/export/student',
                  handler='sosbeacon.service.ExportStudentHandler'),

    ]

app = webapp2.WSGIApplication(
    url_map,
    config=webapp_config
)


