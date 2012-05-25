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
    ('.*/event/tx/start', 'sosbeacon.task.EventStartTxHandler'),
    ('.*/event/tx/group', 'sosbeacon.task.EventGroupTxHandler'),
    ('.*/event/tx/contact', 'sosbeacon.task.EventContactTxHandler'),
    ('.*/event/update', 'sosbeacon.task.EventUpdateHandler'),
]

app = webapp2.WSGIApplication(url_map)

