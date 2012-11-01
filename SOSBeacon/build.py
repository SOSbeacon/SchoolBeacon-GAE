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
"""Setup paths and App Engine's stubs, then run builds."""

import os
import sys

import argparse


sys.path.append(os.path.join('lib', 'local', 'scripts'))

APP = 'SOSBeacon'


def dev():
    from assets import app_assets

    app_assets.build(app=APP, debug=True, cache=False)
    app_assets.watch(app=APP, debug=True, cache=False)


def prod():
    import assets
    assets.build(app=APP, debug=False, cache=True)


BUILDS = {
    'dev': dev,
    'prod': prod
}


def run():
    parser = argparse.ArgumentParser(description='Run Sbeacon builds')
    parser.add_argument(
        'build',  default='dev', help="Build types to be run.")

    args = parser.parse_args()

    build = BUILDS.get(args.build)

    assert build

    build()


if __name__ == '__main__':
    run()
