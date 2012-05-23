
class App.SOSBeacon.Model.Student extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/student'
    defaults: ->
        return {
            key: "",
            name: "",
            identifier: "",
            groups: [],
            contacts: [],
            notes: "",
        }

    initialize: () ->
        #@contacts = @nestCollection(
            #'contacts',
            #new App.SOSBeacon.Collection.ContactList(@get('contacts')))

        @groups = @nestCollection(
            'groups',
            new App.SOSBeacon.Collection.GroupList(@get('groups')))

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if _.isEmpty(attrs.identifier)
            hasError = true
            errors.identifier = "Missing identifier."

        if hasError
            return errors


class App.SOSBeacon.Collection.StudentList extends Backbone.Collection
    url: '/service/student'
    model: App.SOSBeacon.Model.Student


class App.SOSBeacon.View.StudentEdit extends App.Skel.View.EditView
    template: JST['student/edit']
    modelType: App.SOSBeacon.Model.Student
    focusButton: 'input#name'

    events:
        "change": "change"
        "click button.add_group": "addGroup"
        "click button.add_contact": "addContact"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "click .remove-button": "clear"
        "hidden": "close"

    save: (e) =>
        if e
            e.preventDefault()

        @model.contacts.each((contact) ->
            contact.editView.close()
        )

        groupList = []
        @model.groups.each((group) ->
            groupList.push(group)
        )

        @model.save(
            name: @$('input.name').val()
            identifier: @$('input.identifier').val()
            groups: groupList
            notes: $.trim(@$('textarea.notes').val())
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @model.groups.each((group, i) ->
            editView = new App.SOSBeacon.View.GroupSelect({model: group})
            el.find('fieldset.groups').append(editView.render().el)
        )

        console.log(@model.get('contacts'))
        for contact_key in @model.get('contacts')
            console.log(contact_key)
            contact = new App.SOSBeacon.Model.Contact()
            contact.id = contact_key
            contact.fetch({
                silent: true
                success: (data) ->
                    console.log(data)
                error: (data, e) ->
                    console.log(e)
                    console.log(data)
            })
            editView = new App.SOSBeacon.View.ContactSelect({model: contact})
            el.find('fieldset.contacts').append(editView.render().el)

        return super(asModal)

    addGroup: () =>
        group = new @model.groups.model()
        @model.groups.add(group)

        editView = new App.SOSBeacon.View.GroupSelect({model: group})
        rendered = editView.render()
        @$el.find('fieldset.groups').append(rendered.el)

        rendered.$el.find('input.group').focus()

        return false

    addContact: () =>
        contact = new @model.contacts.model()
        @model.contacts.add(contact)

        editView = new App.SOSBeacon.View.ContactSelect({model: contact})
        rendered = editView.render()
        @$el.find('fieldset.contacts').append(rendered.el)

        rendered.$el.find('input.contact').focus()

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            if focusItem.hasClass('group')
                @addGroup()
                return false

            if focusItem.hasClass('contact')
                @addContact()
                return false

        return super(e)


class App.SOSBeacon.View.StudentApp extends App.Skel.View.ModelApp
    el: $("#sosbeaconapp")
    template: JST['student/view']
    modelType: App.SOSBeacon.Model.Student
    form: App.SOSBeacon.View.StudentEdit
    module: 'SOSBeacon'

class App.SOSBeacon.View.StudentList extends App.Skel.View.ListView
    template: JST['student/list']
    modelType: App.SOSBeacon.Model.Student


