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


class App.SOSBeacon.Router extends Backbone.Router
    el: $("#sosbeaconcontainer")
    menu: null

    routes:
        "": "showContacts"
        "groupstudents/:id": "showGroupStudents"
        "contacts": "showContacts"
        "contacts/student/view": "showStudentContact"
        "contacts/student/new": "addStudent"
        "contacts/contact/new": "addContact"
        "contacts/contact/edit/:id": "editContact"
        "contacts/student/edit/:id": "editStudent"
        "contacts/import/student": "showImportStudents"
        "contacts/import/contact": "showImportContacts"
        "group": "showGroup"
        "broadcast": "showBroadcast"
        "broadcast/send": "showSendBroadcast"
        "broadcast/view/:id": "showViewBroadcast"
        "eventcenter": "showEventCenter"
        "eventcenter/new": "addEventCenter"
        "eventcenter/edit/:id": "editEventCenter"
        "eventcenter/view/:id": "viewEventCenter"

    initialize: (data) ->
        @menu = new App.SOSBeacon.View.Menu()
        @menu.render()

        @setCache()

    setCache: ->
        App.SOSBeacon.Cache.Groups = new App.SOSBeacon.Collection.GroupList()

    swap: (newView, args) =>
        if @currentView
            @currentView.close()

        @currentView = new newView(args)
        $(@el).append(@currentView.render().el)

    showContacts: () =>
        @swap(App.SOSBeacon.View.StudentApp)

    showStudentContact: () =>
        @swap(App.SOSBeacon.View.StudentContactApp)

    addStudent: () =>
        @swap(App.SOSBeacon.View.StudentEditApp)

    addContact: () =>
        @swap(App.SOSBeacon.View.ContactEditApp)

    editStudent: (id) =>
        @swap(App.SOSBeacon.View.StudentEditApp, id)

    editContact: (id) =>
        @swap(App.SOSBeacon.View.ContactEditApp, id)

    showGroup: () =>
        @swap(App.SOSBeacon.View.GroupApp)

    showBroadcast: () =>
        @swap(App.SOSBeacon.View.EventApp)

    showSendBroadcast: () =>
        @swap(App.SOSBeacon.View.PendingEventApp)

    showViewBroadcast: (id) =>
        @swap(App.SOSBeacon.View.ViewEventApp, id)

    showGroupStudents: (id) =>
        @swap(App.SOSBeacon.View.GroupStudentsApp, id)

    showImportStudents: () =>
        @swap(App.SOSBeacon.View.ImportStudentsApp)

    showImportContacts: () =>
        @swap(App.SOSBeacon.View.ImportContactsApp)

    showEventCenter: () =>
        @swap(App.SOSBeacon.View.EventCenterApp)

    addEventCenter: () =>
        @swap(App.SOSBeacon.View.EventCenterEditApp)

    editEventCenter: (id) =>
        @swap(App.SOSBeacon.View.EventCenterEditApp, id)

    viewEventCenter: (id) =>
        @swap(App.SOSBeacon.View.EventCenterAppView, id)

    navigate: (fragment, options) =>
        return App.Util.TrackChanges.routerNavigate(
            @navigateHistory, fragment, options)

    navigateHistory: (fragment, options) =>
        return Backbone.history.navigate(fragment, options)
