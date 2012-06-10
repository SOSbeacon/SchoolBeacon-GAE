
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

    initialize: =>
        @groups = new App.SOSBeacon.Collection.GroupList()
        groups = @get('groups')
        if not _.isEmpty(groups)
            url = @groups.url + '/' + groups.join()
            @groups.fetch({url: url})

        @contacts = @nestCollection(
            'contacts',
            new App.SOSBeacon.Collection.ContactList(@get('contacts')))

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

        groupList = []
        @model.groups.each((group) ->
            groupList.push(group.id)
        )

        @model.contacts.each((contact) ->
            contact.editView.close()
        )

        @model.save({
            name: @$('input.name').val()
            identifier: @$('input.identifier').val()
            groups: groupList
            notes: $.trim(@$('textarea.notes').val())
        }, {
            error: App.Util.Form.processErrors
        })

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @model.groups.each((group, i) ->
            editView = new App.SOSBeacon.View.GroupSelect({model: group})
            el.find('fieldset.groups').append(editView.render().el)
        )

        contactList = @$('ul.contacts')
        @model.contacts.each((contact, i) ->
            editView = new App.SOSBeacon.View.ContactEdit({model: contact})
            contact.editView = editView
            contactList.append(editView.render().el)
        )

        return super(asModal)

    addGroup: () =>
        editView = new App.SOSBeacon.View.GroupSelect(
            model: new @model.groups.model()
            groupCollection: @model.groups
        )
        rendered = editView.render()
        @$el.find('fieldset.groups').append(rendered.el)

        rendered.$el.find('input.group').focus()

        return false

    addContact: () =>
        contact = new @model.contacts.model()
        @model.contacts.add(contact)

        editView = new App.SOSBeacon.View.ContactEdit(
            model: new @model.contacts.model())
        contact.editView = editView
        rendered = editView.render()
        @$('ul.contacts').append(rendered.el)

        rendered.$el.find('input.name').focus()

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
    id: "sosbeaconapp"
    template: JST['student/view']
    modelType: App.SOSBeacon.Model.Student
    form: App.SOSBeacon.View.StudentEdit

    initialize: =>
        @collection = new App.SOSBeacon.Collection.StudentList()
        @listView = new App.SOSBeacon.View.StudentList(@collection)

        @collection.fetch()


class App.SOSBeacon.View.StudentListItem extends App.Skel.View.ListItemView
    template: JST['student/list']


class App.SOSBeacon.View.StudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['student/listheader']


class App.SOSBeacon.View.StudentList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.StudentListItem
    headerView: App.SOSBeacon.View.StudentListHeader
    gridFilters: null

