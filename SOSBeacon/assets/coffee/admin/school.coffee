
class App.SOSAdmin.Model.School extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/admin/school'

    defaults: ->
        return {
            key: null,
            name: "",
            owner: "",
            users: [],
            added: "Loading...",
            modified: 'Loading...'
        }

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors


class App.SOSAdmin.Collection.SchoolList extends Backbone.Paginator.requestPager
    model: App.SOSAdmin.Model.School
    url: '/service/admin/school'

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/admin/school'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'added'
    }

    server_api: {}


class App.SOSAdmin.View.SchoolEdit extends App.Skel.View.EditView
    template: JST['admin/school/edit']
    modelType: App.SOSAdmin.Model.School
    focusButton: 'input#name'

    propertyMap:
        active: "input.active",
        name: "input.name",

    events:
        "change": "change"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "hidden": "close"

    initialize: =>
        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap
            validatorMap: @model.validators
        )
        return super()

    save: (e) =>
        if e
            e.preventDefault()

        valid = @model.save({
            name: @$('input.name').val()
        },
            complete: (xhr, textStatus) =>
                if xhr.status == 400
                    valid = 'exits'
        )

        setTimeout(( =>
            if valid == false
                return false

            if valid == 'exits'
                App.Util.Form.hideAlert()
                App.Util.Form.showAlert("Error!", "Duplicate school names not allowed.", "alert-warning")
                return false

            return super()
        ), 300)

    render: (asModal) =>
        $el = @$el
        $el.html(@template(@model.toJSON()))

        return super(asModal)


class App.SOSAdmin.View.SchoolApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['admin/school/view']
    modelType: App.SOSAdmin.Model.School
    form: App.SOSAdmin.View.SchoolEdit

    initialize: =>
        @collection = new App.SOSAdmin.Collection.SchoolList()
        @listView = new App.SOSAdmin.View.SchoolList(@collection)


class App.SOSAdmin.View.SchoolListItem extends App.Skel.View.ListItemView
    template: JST['admin/school/list-item']

    events:
        "click .users-button": "viewUsers"
        "click .edit-button": "edit"
        "click .remove-button": "delete"

    viewUsers: =>
        App.SOSAdmin.router.navigate("/schoolusers/"+@model.id, {trigger: true})
        return false

    onClose: =>
        App.Skel.Event.unbind(null, null, this)


class App.SOSAdmin.View.SchoolListHeader extends App.Skel.View.ListItemHeader
    template: JST['admin/school/list-header']


class App.SOSAdmin.View.SchoolList extends App.Skel.View.ListView
    itemView: App.SOSAdmin.View.SchoolListItem
    headerView: App.SOSAdmin.View.SchoolListHeader
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

class App.SOSAdmin.View.SchoolTypeahaedFilter extends App.Ui.Datagrid.TypeaheadFilter

    render: =>
        @$el.html(@template(@model.toJSON()))

        @$('input.filter-input').typeahead({
        value_property: 'name'
        updater: (item) =>
            @value = item.key
            return item.name

        matcher: (item) ->
            return true

        source: (typeahead, query) =>
            $.ajax({
                type: 'GET'
                dataType: 'json'
                url: '/service/admin/school'
                data: {flike_name: query}
                success: (data) ->
                    typeahead.process(data)
            })
        })

        return this

    onClose: =>
        @$('input.filter-input').trigger('cleanup')