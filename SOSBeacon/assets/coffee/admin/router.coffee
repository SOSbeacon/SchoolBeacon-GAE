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


class App.SOSAdmin.Router extends Backbone.Router
    el: $("#sosadmincontainer")
    menu: null

    routes:
        "": "showDashboard"
        "school": "showSchool"
        "schoolusers/:id": "showSchoolUsers"
        "user": "showUser"

    initialize: (data) ->
        @menu = new App.SOSAdmin.View.Menu()
        @menu.render()

    swap: (newView, args) =>
        if @currentView
            @currentView.close()

        @currentView = new newView(args)
        $(@el).append(@currentView.render().el)

    showDashboard: () =>
        @swap(App.SOSAdmin.View.DashboardApp)

    showSchool: () =>
        @swap(App.SOSAdmin.View.SchoolApp)

    showUser: () =>
        @swap(App.SOSAdmin.View.UserApp)

    showSchoolUsers: (id) =>
        @swap(App.SOSAdmin.View.SchoolUsersApp, id)