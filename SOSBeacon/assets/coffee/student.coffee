
class App.SOSBeacon.Model.Student extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/student'
    defaults: ->
        return {
            key: null,
            name: "",
            identifier: "",
            groups: [],
            contacts: [],
            notes: "",
        }

    initialize: =>
        @groups = new App.SOSBeacon.Collection.GroupList()

        @loadGroups()
        @loadContacts()

        return this

    loadGroups: =>
        groups = @get('groups')
        if groups and not _.isEmpty(groups)
            url = @groups.url + '/' + groups.join()
            @groups.fetch({url: url, async: false})

    loadContacts: =>
        @contacts = @nestCollection(
            'contacts',
            new App.SOSBeacon.Collection.ContactList(@get('contacts')))

    validators:
        name: new App.Util.Validate.string(len: {min: 1, max: 100}),
 
    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
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


class App.SOSBeacon.View.StudentEditForm extends Backbone.View
    template: JST['student/edit']
    addMode: true
    focusButton: 'input#name'
    className: "row-fluid"
    id: "add_area"

    propertyMap:
        name: "input.name",

    events:
        "change": "change"
        "click button.add_contact": "addContact"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"

    initialize: (model) =>
        @model = model

        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap,
            validatorMap: @model.validators
        )

        @model.bind('error', App.Util.Form.displayValidationErrors)

        @groupSelects = []
        @contactEdits = []

    render: () =>
        @$el.html(@template(@model.toJSON()))

        @renderGroups()
        @renderContacts()

        @$("#name").focus()

        return this

    renderGroups: () =>
        #TODO: switch to a underscore filter
        ids = []
        @model.groups.each((group, i) =>
            ids.push(group.id)
        )
        @$("#group-select").val(ids)

        @$("#group-select").select2({
            placeholder: "Select a group...",
            openOnEnter: false,
        })

        allGroups = new App.SOSBeacon.Collection.GroupList()
        allGroups.fetch(async: false)
        allGroups.each((group, i) =>
            @$("#group-select").append(
                $("<option></option>")
                    .html(group.get('name'))
                    .attr('value', group.id)
            )
        )

        @$("input.select2-input").css('width', '100%')

    renderContacts: () =>
        contactList = @$('ul.contacts')
        @model.contacts.each((contact, i) =>
            editView = new App.SOSBeacon.View.ContactEdit({model: contact})
            editView.on('removed', @removeContact)
            @contactEdits.push(editView)
            contactList.append(editView.render().el)
        )

    change: (event) =>
        App.Util.Form.hideAlert()

    removeGroupSelect: (select) =>
        # Remove group from model.
        @model.groups.remove(select.model)

        # Remove group list of group selects.
        index = _.indexOf(@groupSelects, select)
        delete @groupSelects[index]

        return true

    removeContact: (contactEdit) =>
        # Remove group from model.
        @model.contacts.remove(contactEdit.model)

        # Remove group list of group selects.
        index = _.indexOf(@contactEdits, contactEdit)
        delete @contactEdits[index]

        return true

    save: (e) =>
        if e
            e.preventDefault()

        groupIds = @$("#group-select").val()
        if not groupIds
            groupIds = []

        badContacts = _.filter(@contactEdits, (contactEdit) ->
            contactValid = contactEdit.validate()
            return not contactValid
        )
        if not _.isEmpty(badContacts)
            return false

        @model.save(
            name: @$('input.name').val()
            identifier: @$('input.identifier').val()
            groups: groupIds
            notes: $.trim(@$('textarea.notes').val())
        )

        if @model.isValid()
            App.Util.Form.hideAlert()
            App.Util.Form.showAlert(
                "Successs!", "Save successful", "alert-success")

            App.SOSBeacon.Event.trigger('model:save', @model, this)

        return false

    addContact: () =>
        contact = new @model.contacts.model()
        @model.contacts.add(contact)

        editView = new App.SOSBeacon.View.ContactEdit(model: contact)
        editView.on('removed', @removeContact)
        @contactEdits.push(editView)

        rendered = editView.render()
        @$('ul.contacts').append(rendered.el)

        rendered.$el.find('select.contact-type').focus()

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            if focusItem.hasClass('contact')
                @addContact()
                return false

            @save()

            return false


class App.SOSBeacon.View.StudentEditApp extends Backbone.View
    template: JST['student/itemheader']
    id: "sosbeaconapp"
    className: "top_view row-fluid"
    isNew: true

    events:
        "click .view-button": "viewStudents"

    initialize: (id) =>
        if id
            @model = new App.SOSBeacon.Model.Student({key: id})
            @model.fetch({async: false})
            @model.initialize()
            @isNew = false
        else
            @model = new App.SOSBeacon.Model.Student()

        @editForm = new App.SOSBeacon.View.StudentEditForm(@model)
        App.SOSBeacon.Event.bind("model:save", @modelSaved, this)

    modelSaved: () =>
        if @isNew
            @model = new App.SOSBeacon.Model.Student()
            @editForm.initialize(@model)
            @editForm.$("form").each(() ->
                @reset()
            )

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.append(@editForm.render().el)

        @renderHeader()

        return this

    renderHeader: () =>
        header = @$("#editheader")

        if @addMode
            header.html("Add New #{header.text()}")
        else
            header.html("Edit #{header.text()}")

    onClose: () =>
        App.SOSBeacon.Event.unbind(null, null, this)

        @editForm.close()

    viewStudents: () =>
        App.SOSBeacon.router.navigate("/student", {trigger: true})


class App.SOSBeacon.View.StudentApp extends Backbone.View
    id: "sosbeaconapp"
    template: JST['student/view']

    events:
        "click .import-button": "import"
        "click .add-button": "add"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.StudentList()
        @listView = new App.SOSBeacon.View.StudentList(@collection)

    render: =>
        @$el.html(@template())
        @$el.append(@listView.render().el)

        $("#add_new").focus()

        return this

    import: =>
        App.SOSBeacon.router.navigate("/student/import", {trigger: true})

    add: =>
        App.SOSBeacon.router.navigate("/student/new", {trigger: true})

    onClose: =>
        @listView.close()


class App.SOSBeacon.View.ImportStudentsApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['student/import']

    render: =>
        @$el.html(@template())
        return this


class App.SOSBeacon.View.StudentListItem extends App.Skel.View.ListItemView
    template: JST['student/list']

    edit: =>
        App.SOSBeacon.router.navigate(
            "/student/edit/#{@model.id}", {trigger: true})

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

