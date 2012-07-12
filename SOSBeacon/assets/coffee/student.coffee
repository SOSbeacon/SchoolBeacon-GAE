
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
        @groups = new App.SOSBeacon.Collection.GroupList()
        groups = @get('groups')
        if not _.isEmpty(groups)
            url = @groups.url + '/' + groups.join()
            @groups.fetch({url: url, async: false})

        @contacts = new App.SOSBeacon.Collection.ContactList()
        contacts = @get('contacts')
        if not _.isEmpty(contacts)
            url = @contacts.url + '/' + contacts.join()
            @contacts.fetch({url: url, async: false})

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

        contactList = []
        @model.contacts.each((contact) ->
            contactList.push(contact.id)
        )

        @model.save(
            name: @$('input.name').val()
            identifier: @$('input.identifier').val()
            groups: groupList
            contacts: contactList
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

        @model.contacts.each((contact, i) ->
            editView = new App.SOSBeacon.View.ContactSelect({model: contact})
            el.find('fieldset.contacts').append(editView.render().el)
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
        editView = new App.SOSBeacon.View.ContactSelect(
            model: new @model.contacts.model()
            contactCollection: @model.contacts
        )
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


class App.SOSBeacon.View.SelectableStudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['student/selectable-listheader']


class App.SOSBeacon.View.SelectableStudentListItem extends App.SOSBeacon.View.StudentListItem
    template: JST['student/selectable-listitem']
    className: "selectable"

    events:
        "click": "select"

    select: =>
        selected = !@model.selected
        @$('input.selected').prop('checked', selected)
        @model.selected = selected

class App.SOSBeacon.View.SelectableStudentList extends App.SOSBeacon.View.StudentList
    itemView: App.SOSBeacon.View.SelectableStudentListItem
    headerView: App.SOSBeacon.View.SelectableStudentListHeader
    gridFilters: null

