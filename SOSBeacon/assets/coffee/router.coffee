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


class App.SOSBeacon.Router extends Backbone.Router
    el: $("#sosbeaconcontainer")
    menu: null

    routes:
        "": "showPerson"
        "person": "showPerson"

    initialize: (data) ->
        @menu = new App.SOSBeacon.Views.Menu()
        @menu.render()

    swap: (newView, args) =>
        if @currentView
            @currentView.close()

        @currentView = new newView(args)
        $(@el).append(@currentView.render().el)

    showPerson: () =>
        @swap(App.SOSBeacon.Views.PersonApp)
