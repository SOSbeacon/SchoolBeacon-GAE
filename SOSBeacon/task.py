#!/usr/bin/env python

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

url_map = [
    ('.*/event/tx/start', 'sosbeacon.task.GroupsTxHandler'),
    ('.*/event/tx/group', 'sosbeacon.task.GroupTxHandler'),
    ('.*/event/tx/student', 'sosbeacon.task.StudentTxHandler'),
    ('.*/event/tx/contact', 'sosbeacon.task.ContactTxHandler'),
    ('.*/event/tx/method', 'sosbeacon.task.MethodTxHandler'),
    ('.*/event/update/event/counts',
     'sosbeacon.task.UpdateEventCountsHandler'),
    ('.*/event/update/contact_marker',
     'sosbeacon.task.UpdateContactMarkerHandler'),
    ('.*/event/merge/contact_marker',
     'sosbeacon.task.MergeContactMarkerHandler'),
    ('.*/event/ack/contact_marker', 'sosbeacon.task.AckContactMarkerHandler'),
]

app = webapp2.WSGIApplication(url_map)

