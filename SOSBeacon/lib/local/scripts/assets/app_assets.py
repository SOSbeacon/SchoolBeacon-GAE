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

"""Defines how the assets are combined, compiled, and moved into the static
directory structures.

You currently must add you coffeescripts to the list in _bundle_app_coffee.
This is to ensure files are included in the correct order in the compiled
javascript.

Some common things to do here:
    Compile coffeescript, uglify the resultant js into demo.js.
    Compile your JST templates into template.js.
    Compile and minify your less into demo.css.
    Combine third party js into one libs.js package.
"""

import logging

from os import path

from webassets import Bundle
from webassets import Environment
from webassets.script import CommandLineEnvironment

from . import BASE_LOCATION
from . import INPUT_FILES
from . import _bundle_images

APP_NAME = 'SOSBeacon'


def _bundle_app_js(env, debug=False):
    """Combine all js libs into sosbeacon.js.

    For debug, they are left uncompressed.  For production the minified
    versions are used.  We suggest using the vendor supplied minified version
    of each library.
    """

    all_js = Bundle(
        _bundle_3rd_party_js(debug),
        #this needs to be debug false to handle recurisve templates
        Bundle(
            path.join('templates', '**', '*.jst'), filters='jst', debug=False),
        _bundle_app_coffee(debug),
        output=path.join('..', '..', APP_NAME, 'static', 'script',
                         'sosbeacon.js')
    )

    env.add(all_js)

    if not debug:
        all_js.filters = 'closure_js'


def _bundle_admin_js(env, debug=False):
    """Combine all js libs into sosadmin.js.

    For debug, they are left uncompressed.  For production the minified
    versions are used.  We suggest using the vendor supplied minified version
    of each library.
    """

    all_js = Bundle(
        _bundle_3rd_party_js(debug),
        #this needs to be debug false to handle recurisve templates
        Bundle(
            path.join('templates', '**', '*.jst'), filters='jst', debug=False),
        _bundle_admin_coffee(debug),
        output=path.join(
            '..', '..', APP_NAME, 'static', 'script', 'sosadmin.js')
    )

    env.add(all_js)

    if not debug:
        all_js.filters = 'closure_js'


def _bundle_3rd_party_js(debug=False):
    JS_LIB_PATH = path.join('js', 'lib')
    return Bundle(
        path.join(JS_LIB_PATH, 'json2.js'),
        path.join(JS_LIB_PATH, 'jquery.js'),
        path.join(JS_LIB_PATH, 'underscore.js'),
        path.join(JS_LIB_PATH, 'backbone.js'),
        path.join(JS_LIB_PATH, 'backbone.paginator.js'),
        path.join(JS_LIB_PATH, 'bootstrap.js'),
        path.join(JS_LIB_PATH, 'bootstrap-typeahead-improved.js'),
        path.join(JS_LIB_PATH, 'date.js'),
        path.join(JS_LIB_PATH, 'select2.js'),
        path.join(JS_LIB_PATH, 'prettify.js'),
        path.join(JS_LIB_PATH, 'wysihtml5-0.3.0.js'),
        path.join(JS_LIB_PATH, 'bootstrap-wysihtml5.js'),
        path.join(JS_LIB_PATH, 'jquery.uploadify.js'),
        path.join(JS_LIB_PATH, 'jquery.uploadifive.js'),
        path.join(JS_LIB_PATH, 'jquery.fineuploader-3.3.1.js'),
        path.join(JS_LIB_PATH, 'iframe.xss.response-3.3.1.js'),
        path.join(JS_LIB_PATH, 'jwplayer.js'),
        path.join(JS_LIB_PATH, 'html5media.min.js'),
#        path.join(JS_LIB_PATH, 'audio.min.js'),
    )


def _bundle_app_coffee(app, debug=False):
    """Compile the apps coffeescript and bundle it into sosbeacon.js"""
    COFFEE_PATH = 'coffee'
    scripts = (
        path.join(COFFEE_PATH, 'skel', 'nested.coffee'),
        path.join(COFFEE_PATH, 'skel', 'app.coffee'),
        path.join(COFFEE_PATH, 'skel', 'datagrid.coffee'),
        path.join(COFFEE_PATH, 'skel', 'skel.coffee'),
        path.join(COFFEE_PATH, 'skel', 'channel.coffee'),
        path.join(COFFEE_PATH, 'skel', 'utils.coffee'),
        path.join(COFFEE_PATH, 'skel', 'smartbox.coffee'),
        path.join(COFFEE_PATH, 'request_paginator.coffee'),
        path.join(COFFEE_PATH, 'app.coffee'),
        path.join(COFFEE_PATH, 'responders.coffee'),
        path.join(COFFEE_PATH, 'contact-method.coffee'),
        path.join(COFFEE_PATH, 'event-messages.coffee'),
        path.join(COFFEE_PATH, 'event-center.coffee'),
        path.join(COFFEE_PATH, 'contact.coffee'),
        path.join(COFFEE_PATH, 'group.coffee'),
        path.join(COFFEE_PATH, 'student.coffee'),
        path.join(COFFEE_PATH, 'event_view.coffee'),
        path.join(COFFEE_PATH, 'group_students.coffee'),
        path.join(COFFEE_PATH, 'menu.coffee'),
        path.join(COFFEE_PATH, 'router.coffee'),
        path.join(COFFEE_PATH, 'map.coffee'),
        path.join(COFFEE_PATH, 'reply_message.coffee'),
    )

    return Bundle(
        *scripts,
        filters='coffeescript'
    )


def _bundle_admin_coffee(app, debug=False):
    """Compile the admin coffeescript and bundle it into sosadmin.js"""
    COFFEE_PATH = 'coffee'
    ADMIN_PATH = path.join(COFFEE_PATH, 'admin')
    scripts = (
        path.join(COFFEE_PATH, 'skel', 'nested.coffee'),
        path.join(COFFEE_PATH, 'skel', 'app.coffee'),
        path.join(COFFEE_PATH, 'skel', 'datagrid.coffee'),
        path.join(COFFEE_PATH, 'skel', 'skel.coffee'),
        path.join(COFFEE_PATH, 'skel', 'channel.coffee'),
        path.join(COFFEE_PATH, 'skel', 'utils.coffee'),
        path.join(COFFEE_PATH, 'skel', 'smartbox.coffee'),
        path.join(COFFEE_PATH, 'request_paginator.coffee'),
        path.join(ADMIN_PATH, 'app.coffee'),
        path.join(ADMIN_PATH, 'menu.coffee'),
        path.join(ADMIN_PATH, 'router.coffee'),
        path.join(ADMIN_PATH, 'school.coffee'),
        path.join(ADMIN_PATH, 'user.coffee'),
        path.join(ADMIN_PATH, 'school_users.coffee'),
        path.join(ADMIN_PATH, 'dashboard.coffee'),
        path.join(ADMIN_PATH, 'message.coffee'),
    )

    return Bundle(
        *scripts,
        filters='coffeescript'
    )


def _bundle_3rd_party_css(env, debug=False):
    """Bundle any thrid party CSS files."""
    if debug:
        bundle = Bundle(
            path.join('css', 'bootstrap.css'),
            path.join('css', 'select2.css'),
            path.join('css', 'prettify.css'),
            path.join('css', 'wysiwyg-color.css'),
            path.join('css', 'bootstrap-wysihtml5.css'),
            path.join('css', 'uploadify.css'),
            path.join('css', 'uploadifive.css'),
            path.join('css', 'fineuploader-3.3.1.css'),
            output=path.join(
                '..', '..', APP_NAME, 'static', 'css', 'lib.css')
        )
    else:
        bundle = Bundle(
            path.join('css', 'min', 'bootstrap.min.css'),
            path.join('css', 'select2.css'),
            path.join('css', 'prettify.css'),
            path.join('css', 'wysiwyg-color.css'),
            path.join('css', 'bootstrap-wysihtml.css'),
            path.join('css', 'uploadify.css'),
            path.join('css', 'uploadifive.css'),
            path.join('css', 'fineuploader-3.3.1.css'),
            output=path.join(
                '..', '..', APP_NAME, 'static', 'css', 'lib.css')
        )

    env.add(bundle)

    resp_bundle = Bundle(
        path.join('css', 'bootstrap-responsive.css'),
        output=path.join(
            '..', '..', APP_NAME, 'static', 'css', 'responsive.css')
    )
    env.add(resp_bundle)


def _bundle_app_less(app, env, debug):
    """Compile and minify demo's less files into demo.css."""
    bundle = Bundle(
        Bundle(path.join('less', '%s.less' % (app.lower(),)), filters='less'),
        output=path.join(
            '..', '..', app, 'static', 'css', '%s.css' % (app.lower(),))
    )

    if not debug:
        bundle.filters = 'cssmin'

    env.add(bundle)


def _setup_env(app, debug=True, cache=True):
    """Setup the webassets environment."""
    env = Environment(INPUT_FILES, path.join(BASE_LOCATION, app))
    # We use underscore's templates by default.
    env.config['JST_COMPILER'] = '_.template'
    if debug:
        env.config['CLOSURE_COMPRESSOR_OPTIMIZATION'] = 'WHITESPACE_ONLY'
        env.manifest = False
    else:
        env.config[
            'CLOSURE_COMPRESSOR_OPTIMIZATION'] = 'ADVANCED_OPTIMIZATIONS'

    env.debug = False
    env.cache = cache

    #javascript
    _bundle_app_js(env, debug)
    _bundle_admin_js(env, debug)

    #css
    _bundle_app_less(app, env, debug)
    _bundle_3rd_party_css(env, debug)

    #images
    _bundle_images(app, env)

    return env


def _load_logger():
    # Setup a logger
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)
    return log


def build(app='', debug=True, cache=True):
    env = _setup_env(app, debug, cache)
    log = _load_logger()
    cmdenv = CommandLineEnvironment(env, log)

    cmdenv.build()


def watch(app='', debug=False, cache=False):
    env = _setup_env(app, debug, cache)
    log = _load_logger()
    cmdenv = CommandLineEnvironment(env, log)

    cmdenv.watch()
