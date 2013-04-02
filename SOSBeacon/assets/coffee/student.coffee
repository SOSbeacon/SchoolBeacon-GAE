
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

        if _.isEmpty(attrs.contacts[0].methods[0].value) and _.isEmpty(attrs.contacts[0].methods[1].value)
            alert "Please enter method email or mobile number for the first student contact"
            return errors

        if _.isEmpty(attrs.contacts[0].name)
            alert "Name is required for the first student contact"
            return errors

#        if not attrs.key
        if attrs.contacts.length > 1
            if attrs.contacts[1].name.length > 0
                if _.isEmpty(attrs.contacts[1].methods[0].value) and _.isEmpty(attrs.contacts[1].methods[1].value)
                    attrs.contacts[1].name = ''
            else
                attrs.contacts[1].methods[0].value = ''
                attrs.contacts[1].methods[1].value = ''
                attrs.contacts[1].methods[2].value = ''

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
        feq_is_direct: true
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
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"

    initialize: (model) =>
        App.Util.TrackChanges.track(this)

        @model = model

        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap,
            validatorMap: @model.validators
        )

        @model.bind('error', App.Util.Form.displayValidationErrors)

        @contactEdits = []

    render: () =>
        @$el.html(@template(@model.toJSON()))

        @renderGroups()

        if @model.get('default_student')
            @renderDirectContacts()
            @$('.name').attr('readonly',true)
            @$('.method').attr('readonly',true)
            @$('.save').hide()
            return this

        if @model.is_direct
            @renderDirectContacts()
            @$("#name").focus()
            return this

        @renderStudentContacts()
        @$("#name").focus()

        return this

    renderGroups: () =>
        allGroups = new App.SOSBeacon.Collection.GroupList()
        allGroups.fetch(async: false)
        allGroups.each((group, i) =>
            @$("#group-select").append(
                $("<option></option>")
                    .attr('value', group.get('key'))
                    .html(group.get('name'))
            )
        )

        @$("#group-select").val(@model.get('groups')).select2({
            placeholder: "Select a group...",
            openOnEnter: false,
        })

        @$("input.select2-input").css('width', '100%')

    renderDirectContacts: () =>
        contactList = @$('ul.contacts')
        if @model.contacts.length == 0
            contact = new @model.contacts.model()
            @model.contacts.add(contact)

            editView = new App.SOSBeacon.View.ContactEdit(model: contact)
            editView.on('removed', @removeContact)
            @contactEdits.push(editView)

            rendered = editView.render()
            @$('ul.contacts').append(rendered.el)

            rendered.$el.find('select.contact-type').focus()
            @$('input.contact-name').hide()
            return false

        @model.contacts.each((contact, i) =>
            editView = new App.SOSBeacon.View.ContactEdit({model: contact})
            editView.on('removed', @removeContact)
            @contactEdits.push(editView)
            contactList.append(editView.render().el)
        )
        @$('input.contact-name').hide()

    renderStudentContacts: () =>
        contactList = @$('ul.contacts')

        if @model.contacts.length == 0
            contact1 = new @model.contacts.model()
            @model.contacts.add(contact1)

            editView1 = new App.SOSBeacon.View.StudentEdit(model: contact1)
            editView1.on('removed', @removeContact)
            @contactEdits.push(editView1)

            rendered = editView1.render()
            @$('ul.contacts').append(rendered.el)

            rendered.$el.find('select.contact-type').focus()

            contact2 = new @model.contacts.model()
            @model.contacts.add(contact2)

            editView2 = new App.SOSBeacon.View.StudentEdit(model: contact2)
            editView2.on('removed', @removeContact)
            @contactEdits.push(editView2)

            rendered = editView2.render()
            @$('ul.contacts').append(rendered.el)

            rendered.$el.find('select.contact-type').focus()

            return false

        @model.contacts.each((contact, i) =>
            editView = new App.SOSBeacon.View.StudentEdit({model: contact})
            editView.on('removed', @removeContact)
            @contactEdits.push(editView)
            contactList.append(editView.render().el)
        )

    change: (event) =>
        App.Util.Form.hideAlert()

    removeContact: (contactEdit) =>
        # Remove group from model.
        @model.contacts.remove(contactEdit.model)

        # Remove group list of group selects.
        contactEdit.close()
        index = _.indexOf(@contactEdits, contactEdit)
        delete @contactEdits[index]

        return true

    save: (e) =>
        if e
            e.preventDefault()

        groupIds = @$("#group-select").val()
        if not groupIds
            groupIds = []

        if @model.is_direct
            badContacts = _.filter(@contactEdits, (contactEdit) ->
                contactValid = contactEdit.validate()
                return not contactValid
            )
        else
            badContacts = _.filter(@contactEdits, (contactEdit, i) ->
                if i == 0
                    contactValid = contactEdit.validate()
                    if contactValid
                        return not contactValid
                    else
                        return contactValid
            )
        if not _.isEmpty(badContacts)
            return false

        @model.save({
            name: @$('input.name').val()
        #            identifier: @$('input.identifier').val()
        #            groups: groupIds
        #            notes: $.trim(@$('textarea.notes').val())
            is_direct: @model.is_direct
        },
            success: (model) =>
                if @model.isValid()
                    App.Util.Form.hideAlert()
                    App.Util.Form.showAlert(
                        "Successs!", "Save successful", "alert-success")

                    App.Util.TrackChanges.clear(this)
                    App.SOSBeacon.Event.trigger('model:save', @model, this)
        )
        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            if focusItem.hasClass('contact')
                @addContact()
                return false

            @save()

            return false

    onClose: () =>
        #        App.Util.TrackChanges.stop(this)

        for view in @contactEdits
            if view
                view.close()


class App.SOSBeacon.View.StudentEditApp extends Backbone.View
    template: JST['student/itemheader']
    id: "sosbeaconapp"
    className: "top_view row-fluid"
    isNew: true

    events:
        "click .view-button": "viewStudents"

    initialize: (id) =>
        if not id
            @model = new App.SOSBeacon.Model.Student()
        else
            @model = new App.SOSBeacon.Model.Student({key: id})
            @model.fetch({async: false})
            @model.initialize()
            @isNew = false

        @model.is_direct = false
        @editForm = new App.SOSBeacon.View.StudentEditForm(@model)
        App.SOSBeacon.Event.bind("model:save", @modelSaved, this)

    modelSaved: (model) =>
        #TODO: navigate to view page
        App.SOSBeacon.router.navigate(
            "/contacts/student/view", {trigger: true})

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.append(@editForm.render().el)

        @renderHeader()

        return this

    renderHeader: () =>
        header = @$("#editheader")

        if @addMode
            header.html("Add Student Contact")
        else
            header.html("Edit Student Contact")

    onClose: () =>
        App.SOSBeacon.Event.unbind(null, null, this)

        @editForm.close()

    viewStudents: () =>
        App.SOSBeacon.router.navigate(
            "/contacts/student/view", {trigger: true})


class App.SOSBeacon.View.ContactEditApp extends Backbone.View
    template: JST['student/itemheader']
    id: "sosbeaconapp"
    className: "top_view row-fluid"
    isNew: true

    events:
        "click .view-button": "viewStudents"

    initialize: (id) =>
        if not id
            @model = new App.SOSBeacon.Model.Student()
        else
            @model = new App.SOSBeacon.Model.Student({key: id})
            @model.fetch({async: false})
            @model.initialize()
            @isNew = false

        @model.is_direct = true
        @editForm = new App.SOSBeacon.View.StudentEditForm(@model)
        App.SOSBeacon.Event.bind("model:save", @modelSaved, this)

    modelSaved: (model) =>
        App.SOSBeacon.router.navigate(
            "/contacts", {trigger: true})

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.append(@editForm.render().el)

        @renderHeader()

        return this

    renderHeader: () =>
        header = @$("#editheader")

        if @addMode
            header.html("Add Direct Contact")
        else
            if @model.get('default_student')
                header.html("View User Contact")
            else
                header.html("Edit Direct Contact")

    onClose: () =>
        App.SOSBeacon.Event.unbind(null, null, this)

        @editForm.close()

    viewStudents: () =>
        App.SOSBeacon.router.navigate("/contacts", {trigger: true})


class App.SOSBeacon.View.UserContactEditApp extends Backbone.View
    template: JST['student/itemheader']
    id: "sosbeaconapp"
    className: "top_view row-fluid"
    isNew: true

    events:
        "click .view-button": "viewStudents"

    initialize: (id) =>
        if not id
            @model = new App.SOSBeacon.Model.Student()
        else
            @model = new App.SOSBeacon.Model.Student({key: id})
            @model.fetch({async: false})
            @model.initialize()
            @isNew = false

        @model.is_direct = true
        @editForm = new App.SOSBeacon.View.StudentEditForm(@model)
        App.SOSBeacon.Event.bind("model:save", @modelSaved, this)

    modelSaved: (model) =>
        if @isNew
            @isNew = false
            Backbone.history.navigate(
                "/student/edit/#{model.id}")

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.append(@editForm.render().el)

        @renderHeader()

        return this

    renderHeader: () =>
        header = @$("#editheader")

        if @addMode
            header.html("Add Direct Contact")
        else
            header.html("View User Contact")

    onClose: () =>
        App.SOSBeacon.Event.unbind(null, null, this)

        @editForm.close()

    viewStudents: () =>
        App.SOSBeacon.router.navigate("/contacts", {trigger: true})


class App.SOSBeacon.View.StudentApp extends Backbone.View
    id: "sosbeaconapp"
    template: JST['student/view']

    events:
        "click .add-button-student": "addStudent"
        "click .add-button-contact": "addContact"
        "click .export-student-contact": "exportStudentContact"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.StudentList()
        @listView = new App.SOSBeacon.View.StudentList(@collection)

    render: =>
        @$el.html(@template())
        @$el.append(@listView.render().el)
        return this

    addContact: =>
        App.SOSBeacon.router.navigate("/contacts/contact/new", {trigger: true})

    addStudent: =>
        App.SOSBeacon.router.navigate("/contacts/student/new", {trigger: true})

    exportStudentContact: () =>
        if !confirm("Are you sure you want to export these student datas to CSV file?")
            return;
        url = '/service/export/student'
        window.open(url)

        return false

    onClose: =>
        @listView.close()


class App.SOSBeacon.View.StudentContactApp extends App.SOSBeacon.View.StudentApp
    id: "sosbeaconapp"
    template: JST['student/view']

    events:
        "click .add-button-student": "addStudent"
        "click .add-button-contact": "addContact"
        "click .export-student-contact": "exportStudentContact"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.StudentList()
        @listViews = new App.SOSBeacon.View.ContactStudentList(@collection)

    render: =>
        @$el.html(@template())
        @$el.append(@listViews.render().el)

        @$("button.add-button-contact").css('display', 'none')
        @$("button.import-direct-contact").css('display', 'none')
        @$("button.add-button-student").css('display', 'block')
        @$("button.import-student-contact").css('display', 'block')
        @$("button.export-student-contact").css('display', 'block')

        return this

    onClose: =>
        @listViews.close()


class App.SOSBeacon.View.ImportStudentsApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['student/import-student-contact']

    events:
        'submit form' : 'importCSV'

    render: =>
        @$el.html(@template())
        return this

    importCSV: ->
        input = @$('#students_file').val()
        if input is ""
            alert "You must choose a file"
            return false


class App.SOSBeacon.View.ImportContactsApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['student/import-direct-contact']

    events:
        'submit form' : 'importCSV'

    render: =>
        @$el.html(@template())
        return this

    importCSV: ->
        input = @$('#contacts_file').val()
        if input is ""
            alert "You must choose a file"
            return false


class App.SOSBeacon.View.StudentListItem extends App.Skel.View.ListItemView
    template: JST['student/list']

    events:
        "click .edit-button-contact": 'editContact'
        "click .edit-button-student": 'editStudent'
        "click .remove-button": "delete"

    editContact: =>
        App.SOSBeacon.router.navigate(
            "/contacts/contact/edit/#{@model.id}", {trigger: true})

    editStudent: =>
        App.SOSBeacon.router.navigate(
            "/contacts/student/edit/#{@model.id}", {trigger: true})

    render: =>
        model_props = @model.toJSON()
        group_links = []
        _.each(@model.groups.models, (acs) =>
            #TODO: convert to links
            #group_links.push("&nbsp;<a href=''>#{acs.get('name')}</a>")
            group_links.push(" #{acs.get('name')}")
        )
        model_props['group_list'] = group_links

        if @model.get('is_direct')
            contacts = @model.get('contacts')
            emails = []
            voice_phone = []
            text_phone = []

            $.each contacts, (key, value) ->
                $.each value, (key, value) ->
                    if key == 'methods'
                        for method in value
                            if method.type == 'e'
                                emails.push(method.value)
                            if method.type == 'p'
                                voice_phone.push(method.value)
                            if method.type == 't'
                                text_phone.push(method.value)

            model_props['email'] = emails
            model_props['voice_phone'] = voice_phone
            model_props['text_phone'] = text_phone

        @$el.html(@template(model_props))
        return this


class App.SOSBeacon.View.StudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['student/listheader']


class App.SOSBeacon.View.BaseStudentList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.StudentListItem
    headerView: App.SOSBeacon.View.StudentListHeader
    gridFilters: null

    events:
        'change .typeOfContact' :'filter_student'

    filter_student:(e) =>
        @$el.append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')
        value = false
        $(".typeOfContact option").each ->
            if $(this).val() is $(e.target).attr('value')
                $(this).attr "selected", "selected"
            else
                $(this).removeAttr('selected')

        if $('.typeOfContact').val() == 'student'
            if $('#menu-item-contacts').length > 0
                $('#menu-item-contacts a').attr('href', '#/contacts/student/view')

            App.SOSBeacon.router.navigate(
                "/contacts/student/view", {trigger: true})

        if $('.typeOfContact').val() == 'contact'
            if $('#menu-item-contacts').length > 0
                $('#menu-item-contacts a').attr('href', '#/contacts')

            App.SOSBeacon.router.navigate(
                "/contacts", {trigger: true})

    initialize: (collection) =>
        @gridFilters = new App.Ui.Datagrid.FilterList()
        super(collection)

    render: =>
        @$el.html(@template())
        @$el.append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')

        if @headerView
            @$("table.table").prepend(new @headerView().render().el)

        if @gridFilters
            @filter = new App.SOSBeacon.View.NewGridView({
                gridFilters: @gridFilters
                collection: @collection
                id: @cid
            })
            @$("div.gridfilters").html(@filter.render().el)
#            @$("div.gridFooter").html(@footer_template())
            App.Skel.Event.bind("filter:run:#{@filter.cid}", @run({'feq_is_direct': true}), this)

            @filter.runFilter()

        return this


class App.SOSBeacon.View.StudentList extends App.SOSBeacon.View.BaseStudentList

    initialize: (collection) =>
        #the super needs to be first here to generate the gridfilters list
        #in the inherited class
        super(collection)


class App.SOSBeacon.View.ContactStudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['student/listheader_student']


class App.SOSBeacon.View.BaseContactStudentList extends App.SOSBeacon.View.BaseStudentList
    itemView: App.SOSBeacon.View.StudentListItem
    headerView: App.SOSBeacon.View.ContactStudentListHeader
    gridFilters: null

    render: =>
        @$el.html(@template())
        @$el.append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')

        if @headerView
            @$("table.table").prepend(new @headerView().render().el)

        if @gridFilters
            @filter = new App.SOSBeacon.View.NewStudentGridView({
                gridFilters: @gridFilters
                collection: @collection
                id: @cid
            })
            @$("div.gridfilters").html(@filter.render().el)
#            @$("div.gridFooter").html(@footer_template())
            App.Skel.Event.bind("filter:run:#{@filter.cid}", @run({'feq_is_direct': false}), this)

            @filter.runFilter()

        return this


class App.SOSBeacon.View.ContactStudentList extends App.SOSBeacon.View.BaseContactStudentList

    initialize: (collection) =>
        #the super needs to be first here to generate the gridfilters list
        #in the inherited class
        super(collection)


class App.SOSBeacon.View.SelectableStudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['student/selectable-listheader']


class App.SOSBeacon.View.SelectableStudentListItem extends App.SOSBeacon.View.StudentListItem
    template: JST['student/selectable-listitem']
    className: "selectable"

    events:
        "click input": "select"

    select: =>
        if !@model.selected
            selected = !@model.selected
            @$('input.selected').prop('checked', selected)
            @model.selected = selected

    render: =>
        model_props = @model.toJSON()
        group_links = []
        _.each(@model.groups.models, (acs) =>
            #TODO: convert to links
            #group_links.push("&nbsp;<a href=''>#{acs.get('name')}</a>")
            group_links.push(" #{acs.get('name')}")
        )
        @sortGroup(group_links)
        model_props['group_list'] = group_links
        @$el.html(@template(model_props))
        return this

    sortGroup: (group_links)=>
        group_links.sort()
        group_defaults = []

        for i of group_links
            if group_links[i] == " Admin"
                group_links.splice i,1
                group_defaults.push("Admin")

            if group_links[i] == " Staff"
                group_links.splice i,1
                group_defaults.push("Staff")

        group_defaults  = group_defaults.sort()
        if group_defaults.length > 0
            group_links.unshift(group_defaults)
            return group_links

        return group_links

class App.SOSBeacon.View.SelectableStudentList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.SelectableStudentListItem
    headerView: App.SOSBeacon.View.SelectableStudentListHeader
    gridFilters: null

    events:
        'change .typeOfContact' :'filter_students'

    filter_students:(e) =>
        @$("div.gridfilters").append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')
        value = false
        $(".typeOfContact option").each ->
            if $(this).val() is $(e.target).attr('value')
                $(this).attr "selected", "selected"
            else
                $(this).removeAttr('selected')

        if $('.typeOfContact').val() == 'student'
            @run({'feq_is_direct':false})
            App.Skel.Event.trigger("filter_students", false)

        if $('.typeOfContact').val() == 'contact'
            @run({'feq_is_direct':true})
            App.Skel.Event.trigger("filter_students", true)

        if $('.typeOfContact').val() == 'all'
            @run({})
            App.Skel.Event.trigger("filter_students")

    initialize: (collection) =>
        @gridFilters = new App.Ui.Datagrid.FilterList()
        super(collection)

    render: =>
        @$el.html(@template())
        @$("div.gridfilters").append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')

        if @headerView
            @$("table.table").prepend(new @headerView().render().el)

        if @gridFilters
            @filter = new App.SOSBeacon.View.GroupNewGridView({
                gridFilters: @gridFilters
                collection: @collection
                id: @cid
            })
            @$("div.gridfilters").html(@filter.render().el)
            #            @$("div.gridFooter").html(@footer_template())
            App.Skel.Event.bind("filter:run:#{@filter.cid}", @run, this)

            @filter.runFilter()

        return this

    run: (filters) =>
        @collection.server_api = {
            limit: @$("div.gridFooter > .size-select").val() ? 200
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)
        _.extend(@collection.server_api, filters)

        App.Skel.Event.trigger("studentlist:filter:#{@.cid}", filters)


class App.SOSBeacon.View.NewGridView extends App.Ui.Datagrid.GridView
    template: JST['student/filter_direct']

class App.SOSBeacon.View.NewStudentGridView extends App.Ui.Datagrid.GridView
    template: JST['student/filter_student']

class App.SOSBeacon.View.GroupNewGridView extends App.Ui.Datagrid.GridView
    template: JST['student/group_filter_direct']

class App.SOSBeacon.View.GroupNewStudentGridView extends App.Ui.Datagrid.GridView
    template: JST['student/group_filter_student']