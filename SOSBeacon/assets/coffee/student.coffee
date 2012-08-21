
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
        if groups and not _.isEmpty(groups)
            url = @groups.url + '/' + groups.join()
            @groups.fetch({url: url, async: false})

        @contacts = @nestCollection(
            'contacts',
            new App.SOSBeacon.Collection.ContactList(@get('contacts')))

    validate: (attrs) =>
        hasError = false
        errors = {}

        if attrs.type != 'd' and _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors


class App.SOSBeacon.Collection.StudentList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.Student

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/student'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'name'
    }

    server_api: {}


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
        "hidden": "close"

    save: (e) =>
        if e
            e.preventDefault()

        groupList = []
        badGroups = @model.groups.filter((group) ->
            groupValid = group.editView.checkGroup()
            if group.id and groupValid
                groupList.push(group.id)
            return not groupValid
        )
        if not _.isEmpty(badGroups)
            return false

        @model.contacts.each((contact) ->
            contact.editView.close()
        )
        saved = @model.save({

            name: @$('input.name').val()
            identifier: @$('input.identifier').val()
            groups: groupList
            notes: $.trim(@$('textarea.notes').val())
        }, {
            error: App.Util.Form.processErrors
        })
        if saved == false
            return false

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @model.groups.each((group, i) =>
            editView = new App.SOSBeacon.View.GroupSelect(
                model: group,
                groupCollection: @model.groups,
                autoAdd: false
            )
            group.editView = editView
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
        badGroup = @model.groups.find((group) ->
            if group.id
                return false
            return true
        )
        if badGroup
            badGroup.editView.$('input.name').focus()
            return false

        group = new @model.groups.model()
        @model.groups.add(group)

        editView = new App.SOSBeacon.View.GroupSelect(
            model: group,
            groupCollection: @model.groups,
            autoAdd: false
        )
        group.editView = editView

        rendered = editView.render()
        @$el.find('fieldset.groups').append(rendered.el)

        rendered.$el.find('input.group').focus()

        return false

    addContact: () =>
        contact = new @model.contacts.model()
        @model.contacts.add(contact)

        editView = new App.SOSBeacon.View.ContactEdit(model: contact)
        contact.editView = editView
        rendered = editView.render()
        @$('ul.contacts').append(rendered.el)

        rendered.$el.find('select.type').focus()

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

    events:
        "click .add-button": "add"
        "click .import-button": "import"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.StudentList()
        @listView = new App.SOSBeacon.View.StudentList(@collection)

    import: =>
        #todo prompt for doc to import
        App.SOSBeacon.router.navigate("/student/import", {trigger: true})


class App.SOSBeacon.View.ImportStudentsApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['student/import']

    render: =>
        @$el.html(@template())
        return this


class App.SOSBeacon.View.StudentListItem extends App.Skel.View.ListItemView
    template: JST['student/list']

    render: =>
        model_props = @model.toJSON()
        group_links = []
        _.each(@model.groups.models, (acs) =>
            #TODO: convert to links
            #group_links.push("&nbsp;<a href=''>#{acs.get('name')}</a>")
            group_links.push(" #{acs.get('name')}")
        )
        model_props['group_list'] = group_links
        @$el.html(@template(model_props))
        return this


class App.SOSBeacon.View.StudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['student/listheader']


class App.SOSBeacon.View.BaseStudentList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.StudentListItem
    headerView: App.SOSBeacon.View.StudentListHeader
    gridFilters: null

    initialize: (collection) =>
        @gridFilters = new App.Ui.Datagrid.FilterList()

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Name'
                type: 'text'
                prop: 'flike_name'
                default: false
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        super(collection)


class App.SOSBeacon.View.StudentList extends App.SOSBeacon.View.BaseStudentList

    initialize: (collection) =>
        #the super needs to be first here to generate the gridfilters list
        #in the inherited class
        super(collection)

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Group'
                type: 'text'
                prop: 'feq_groups'
                default: false
                control: App.SOSBeacon.View.GroupTypeahaedFilter
            }
        ))


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


class App.SOSBeacon.View.SelectableStudentList extends App.SOSBeacon.View.BaseStudentList
    itemView: App.SOSBeacon.View.SelectableStudentListItem
    headerView: App.SOSBeacon.View.SelectableStudentListHeader
    gridFilters: null

    run: (filters) =>
        @collection.server_api = {
            limit: @$("div.gridFooter > .size-select").val() ? 25
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)
        _.extend(@collection.server_api, filters)

        App.Skel.Event.trigger("studentlist:filter:#{@.cid}", filters)

