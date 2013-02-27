class App.SOSAdmin.Model.User extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/admin/user'
    defaults: ->
        return {
            key: null,
            name: "",
            schools: [],
            email: "",
            phone: "",
            password: "",
            is_admin: false,
            added: "Loading...",
            modified: 'Loading...'
        }

    initialize: =>
        @schools = new App.SOSAdmin.Collection.SchoolList()
        schools = @get('schools')
        if not _.isEmpty(schools)
            url = @schools.url + '/' + schools.join()
            @schools.fetch({url: url, async: false})

    @emailValidator: (email) =>
        email = $.trim(email)
        # Drop leading and trailing whitespace

        # Is it possibly a valid email?
        if not /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
            return new App.Util.Validate.Error(email, 'Invalid email.')

        return email

    customemailValidator: (email) =>
        email = $.trim(email)
        # Drop leading and trailing whitespace

        # Is it possibly a valid email?
        if not /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
            return new App.Util.Validate.Error(email, 'Invalid email.')

        return email


    @phoneValidator: (phone) =>
        phone = $.trim(phone)

        # Is it possibly a valid email?
        phone = phone.replace(/[^\d]/g, "")
        if phone.length < 10 or phone.length > 11
            return new App.Util.Validate.Error(phone, 'Invalid phone.')

        if phone.length == 10
            phone = '1' + phone

        else if phone.length != 11
            return phone

        return phone
    #      return (phone[0] + ' (' + phone.substr(1, 3) + ') ' +
    #            phone.substr(4, 3) + '-' + phone.substr(7, 4))

    customphoneValidator: (phone) =>
        phone = $.trim(phone)

        # Is it possibly a valid email?
        phone = phone.replace(/[^\d]/g, "")
        if phone.length < 10 or phone.length > 12
            return new App.Util.Validate.Error(phone, 'Invalid phone.')

        return phone

    customPasswordValidator: (password) =>
        password = $.trim(password)

        # Is it possibly a valid email?
        if password.length < 6
            return new App.Util.Validate.Error(password, 'Invalid Password.')

        return password

    validators:
        name: new App.Util.Validate.string(len: {min: 1, max: 50}),
        email: @emailValidator,
        phone: @phoneValidator,
#        password: new App.Util.Validate.string(len: {min: 6, max: 500}),


    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Must be at least 1 characters long."

        if _.isEmpty(attrs.email)
            hasError = true
            errors.email = "Invalid email."

        if typeof @customemailValidator(attrs.email) == 'object'
            hasError = true
            errors.email = "Invalid email."

        if _.isEmpty(attrs.phone)
            hasError = true
            errors.phone = "Invalid phone."

        if typeof @customphoneValidator(attrs.phone) == 'object'
            hasError = true
            errors.phone = "Invalid phone."

#        if _.isEmpty(attrs.password)
#            hasError = true
#            errors.password = "Invalid password."
#
#        if typeof @customPasswordValidator(attrs.password) == 'object'
#            hasError = true
#            errors.phone = "Invalid password."

        if hasError
            return errors


class App.SOSAdmin.Collection.UserList extends Backbone.Paginator.requestPager
    model: App.SOSAdmin.Model.User
    url: '/service/admin/user'

    paginator_core:
        {
            type: 'GET',
            dataType: 'json'
            url: '/service/admin/user'
        }

    paginator_ui:
        {
            firstPage: 0
            currentPage: 0
            perPage: 100
            totalPages: 100
        }

    query_defaults:
        {
            orderBy: 'added'
            feq_is_admin:false
        }

    server_api: {}


class App.SOSAdmin.View.UserEdit extends App.Skel.View.EditView
    template: JST['admin/user/edit']
    modelType: App.SOSAdmin.Model.User
    focusButton: 'input#name'

    propertyMap:
        active: "input.active",
        name: "input.name",

    events:
        "change": "change"
        "submit form": "save"
        "keypress .edit": "updateOnEnter"
        "hidden": "close"

    initialize: =>

        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap
            validatorMap: @model.validators
        )
        @contactViews = []

        return super()

    save: (e) =>

        if e
            e.preventDefault()

        valid = @model.save({
            name: @$('input.name').val()
            email: @$('input.email').val()
            phone: @$('input.phone').val()
            password: @$('input.password').val()
        },
            complete: (xhr, textStatus) =>
                console.log(xhr.status);
                if xhr.status == 400
                    valid = 'exits'
        )

        setTimeout(( =>
            if valid == false
                return false

            if valid == 'exits'
                App.Util.Form.hideAlert()
                App.Util.Form.showAlert("Error!", "Email of Phone are exits", "alert-warning")
                return false

            return super()
        ), 300)

    render: (asModal) =>

        $el = @$el
        $el.html(@template(@model.toJSON()))

        return super(asModal)


class App.SOSAdmin.View.UserApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['admin/user/view']

    modelType: App.SOSAdmin.Model.User
    form: App.SOSAdmin.View.UserEdit

    initialize: =>

        @collection = new App.SOSAdmin.Collection.UserList()
        @listView = new App.SOSAdmin.View.UserList(@collection)


class App.SOSAdmin.View.UserListItem extends App.Skel.View.ListItemView
    template: JST['admin/user/list-item']

    events:
        "click .edit-button": "edit"
        "click .remove-button": "delete"

    edit: =>
        setTimeout(( =>
            if ($("#name").length > 0)
                $('#email').attr('readonly', true)
                $('#phone').attr('readonly', true)
        ), 100)
        App.Skel.Event.trigger("model:edit", @model, this)

    onClose: =>
        App.Skel.Event.unbind(null, null, this)


class App.SOSAdmin.View.UserListHeader extends App.Skel.View.ListItemHeader
    template: JST['admin/user/list-header']


class App.SOSAdmin.View.UserList extends App.Skel.View.ListView
    itemView: App.SOSAdmin.View.UserListItem
    headerView: App.SOSAdmin.View.UserListHeader
    gridFilters: null

    initialize: (collection) =>

        @gridFilters = new App.Ui.Datagrid.FilterList()

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Name'
                type: 'text'
                prop: 'flike_name'
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Email'
                type: 'text'
                prop: 'flike_email'
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Phone'
                type: 'text'
                prop: 'flike_phone'
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        super(collection)

class App.SOSAdmin.View.SelectableUserListHeader extends App.Skel.View.ListItemHeader
    template: JST['admin/user/selectable-listheader']


class App.SOSAdmin.View.SelectableUserListItem extends App.SOSAdmin.View.UserListItem
    template: JST['admin/user/selectable-listitem']
    className: "selectable"

    events:
        "click": "select"

    select: =>
        selected = !@model.selected
        @$('input.selected').prop('checked', selected)
        @model.selected = selected


class App.SOSAdmin.View.SelectableUserList extends App.SOSAdmin.View.UserList
    itemView: App.SOSAdmin.View.SelectableUserListItem
    headerView: App.SOSAdmin.View.SelectableUserListHeader
    gridFilters: null

    run: (filters) =>

        @collection.server_api = {
            limit: @$("div.gridFooter > .size-select").val() ? 25
        }

        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)
        _.extend(@collection.server_api, filters)

        App.Skel.Event.trigger("userlist:filter:#{@.cid}", filters)

class App.SOSAdmin.View.DashboardUserListItem extends App.SOSAdmin.View.UserListItem
    template: JST['admin/dashboard/user/list-item']
    tagName: 'table'
    className:'user_table_vertical'

    render: =>

        model_props = @model.toJSON()
        added = @model.get("added")
        modified = @model.get("modified")

        model_props['added'] = added
        model_props['modified'] = modified
        @$el.html(@template(model_props))

        return this

class App.Ui.Datagrid.DashboardGridView extends App.Ui.Datagrid.GridView
    template: JST['admin/dashboard/grid/filter']

    events:
        "click button.add-optional": "addOptional",
        "click button.info-button": "runFilter"

    runFilter: (e) =>

        emailel = document.getElementById("feq_email")
        phoneel = document.getElementById("feq_phone")

        if (emailel == null or emailel.value == "") and (phoneel == null or phoneel.value == "")
            return

        filters = {}
        for prop, view of @views
            filters = _.extend(filters, view.addFilter(filters))

        App.Skel.Event.trigger("filter:run:#{@.cid}", filters)

        return false

class App.SOSAdmin.View.DashboardUserListOne extends App.Skel.View.ListView
    itemView: App.SOSAdmin.View.DashboardUserListItem
    template: JST['admin/dashboard/grid/view']
    gridFilters: null

    initialize: (collection) =>

        @gridFilters = new App.Ui.Datagrid.FilterList()

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Email'
                type: 'text'
                prop: 'feq_email'
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Phone'
                type: 'text'
                prop: 'feq_phone'
                control: App.Ui.Datagrid.InputFilter
            }
        ))
        super(collection)

    render: =>

        @$el.html(@template())

        if @gridFilters
            @filter = new App.Ui.Datagrid.DashboardGridView({
                gridFilters: @gridFilters
                collection: @collection
                id: @cid
            })

            @$("div.gridfilters").html(@filter.render().el)
            App.Skel.Event.bind("filter:run:#{@filter.cid}", @run, this)

        return this

    run: (filters) =>

        @collection.server_api = {
            limit: 1
        }

        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)
        _.extend(@collection.server_api, filters)

        App.Skel.Event.trigger("userlistone:filter:#{@.cid}", filters)

        return false
