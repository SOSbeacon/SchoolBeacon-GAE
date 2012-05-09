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


class App.Appname.Models.Person extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/person'
    defaults: ->
        return {
            key: "",
            name: "",
            contact_info: [],
            notes: "",
        }

    initialize: () ->
        @contact_info = @nestCollection(
            'contact_info',
            new App.Appname.Collections.ContactInfo(@get('contact_info')))

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors

    clear: =>
        @destroy()


class App.Appname.Collections.PersonList extends Backbone.Collection
    url: '/service/person'
    model: App.Appname.Models.Person


class App.Appname.Views.PersonEdit extends Backbone.View
    template: JST['person/edit']
    tagName: "div"

    events:
        "click a.destroy": "clear"
        "click a.add_contact": "addContactInfo"
        "keypress .edit": "updateOnEnter"
        "click .remove-button": "clear"
        "hidden": "close"

    render: (as_modal) =>
        el = @$el
        el.html(@template(@model.toJSON()))
        @model.contact_info.each((info, i) ->
            editView = new App.Appname.Views.ContactInfoEdit({model: info})
            el.find('fieldset.contact_info').append(editView.render().el)
        )
        if as_modal
            el.attr('class', 'modal')
        return this

    clear: =>
        @model.clear()

    save: =>
        @model.contact_info.each((info) ->
            info.edit_view.close()
        )
        @model.save(
            name: @$('input.name').val()
            notes: $.trim(@$('textarea.notes').val())
        )
        App.Appname.Events.trigger('Person:save', @model)

    addContactInfo: () =>
        newModel = new @model.contact_info.model()
        @model.contact_info.add(newModel)

        editView = new App.Appname.Views.ContactInfoEdit({model: newModel})
        @$el.find('fieldset.contact_info').append(editView.render().el)

    updateOnEnter: (e) =>
        if e.keyCode == 13
            @save()

class App.Appname.Views.PersonApp extends App.Appname.Views.ModelApp
    template: JST['person/view']
    modelType: App.Appname.Models.Person
    form: App.Appname.Views.PersonEdit

class App.Appname.Views.PersonList extends App.Appname.Views.ListView
    template: JST['person/list']
    modelType: App.Appname.Models.Person

    #edit: =>
        #@editView = new App.Appname.Views.PersonEdit({model: @model})
        #@editView.on("save", this.save, this)
        #el = @editView.render(true).$el
        #el.modal('show')
        #el.find('input.code').focus()

    #save: (model) =>
        #@editView.$el.modal('hide')
        #@editView.close()


