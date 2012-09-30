
class App.SOSBeacon.Model.Group extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/group'

    initialize: =>
        @on('sync', @groupSynced)

    groupSynced:  =>
        #check if in cache
        group = App.SOSBeacon.Cache.Groups.get(@id)
        if group
            App.SOSBeacon.Cache.Groups.remove(group, {silent: true})

    defaults: ->
        return {
            key: null,
            name: "",
            active: true,
            notes: "",
        }

    validators:
        name: new App.Util.Validate.string(len: {min: 1, max: 50}),
        active: new App.Util.Validate.bool()

    validate: (attrs, options) =>
        if options?.unset or options?.loading
            return

        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors

    reset: =>
        @set(@defaults(), loading: true)


class App.SOSBeacon.Collection.GroupList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.Group
    url: '/service/group'

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/group'
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

    fetch: (options) =>
        #handle caching when looking for specific groups
        #if options and 'url' of options
        if options and options.url?
            urls = options.url.split('/')
            ids = _.last(urls).split(',')

            idsToFetch = []
            _.each(ids, (id) =>
                group = App.SOSBeacon.Cache.Groups.get(id)
                if group
                    @add(group, {silent: true})
                else
                    idsToFetch.push(id)
            )

            if _.isEmpty(idsToFetch)
                return

            options.url = @url + '/' + idsToFetch.join()

        super(options)
        @addToCache()


    addToCache: =>
        @each((group) ->
            App.SOSBeacon.Cache.Groups.add(group, {silent: true})
        )

class App.SOSBeacon.View.GroupEdit extends App.Skel.View.EditView
    template: JST['group/edit']
    modelType: App.SOSBeacon.Model.Group
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

        valid = @model.save(
            name: @$('input.name').val()
            active: @$('input.active').prop('checked')
            notes: $.trim(@$('textarea.notes').val())
        )
        if valid == false
            return false

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        return super(asModal)

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        return super(e)


class App.SOSBeacon.View.GroupApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['group/view']
    modelType: App.SOSBeacon.Model.Group
    form: App.SOSBeacon.View.GroupEdit

    initialize: =>
        @collection = new App.SOSBeacon.Collection.GroupList()
        @listView = new App.SOSBeacon.View.GroupList(@collection)


class App.SOSBeacon.View.GroupListItem extends App.Skel.View.ListItemView
    template: JST['group/list']

    events:
        "click .students-button": "viewStudents"
        "click .edit-button": "edit"
        "click .remove-button": "delete"

    viewStudents: =>
        App.Skel.Event.trigger("groupstudents:selected", @model.id, this)
        return false

    onClose: =>
        App.Skel.Event.unbind(null, null, this)


class App.SOSBeacon.View.GroupListHeader extends App.Skel.View.ListItemHeader
    template: JST['group/listheader']


class App.SOSBeacon.View.GroupList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.GroupListItem
    headerView: App.SOSBeacon.View.GroupListHeader
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

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Is Active'
                type: 'checkbox'
                prop: 'feq_active'
                default: true
                control: App.Ui.Datagrid.CheckboxFilter
                default_value: true
            }
        ))

        super(collection)


class App.SOSBeacon.View.GroupSelect extends Backbone.View
    template: JST['group/select']
    className: "control-group"

    propertyMap:
        "name": "input.group-name-select"

    events:
        "click a.remove": "removeSelect"
        "blur input.group-name-select": "checkGroup"

    initialize: =>
        @options.autoAdd ?= true
        @validator = new App.Util.Form(@el, propertyMap: @propertyMap)

    checkGroup: =>
        if @typeahead?.shown
            return true

        candidateName = $.trim(@$('input.group-name-select').val())

        if @model.id or not candidateName
            @validator.clearMessage('name')
            return true

        @validator.displayMessage('name', 'error', 'Group does not exist')
        return false

    render: =>
        @$el.html(@template(@model.toJSON()))
        @$('input.group-name-select').typeahead({
            value_property: 'name'
            updater: (item) =>
                @model.set(item, {silent: true})
                if @options.groupCollection and @options.autoAdd
                    @options.groupCollection.add(@model)
                return item.name
            matcher: (item) ->
                return true
            source: (typeahead, query) =>
                @maybeClear(typeahead)
                $.ajax({
                    type: 'GET'
                    dataType: 'json'
                    url: '/service/group'
                    data: {flike_name: query}
                    success: (data) ->
                        typeahead.process(data)
                })
        })
        return this

    maybeClear: (typeahead) =>
        @typeahead = typeahead

        candidateName = @$('input.group-name-select').val()
        if not @model.id or @model.get('name') == candidateName
            return

        @model.reset()
        @$('input.group-name-select').val(candidateName)

    removeSelect: =>
        @trigger('removed', @)
        return @close()

    onClose: =>
        @$('input.group-name-select').trigger('cleanup')
        if @options.groupCollection
            @options.groupCollection.remove(@model)


class App.SOSBeacon.View.GroupTypeahaedFilter extends App.Ui.Datagrid.TypeaheadFilter

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
                    url: '/service/group'
                    data: {flike_name: query}
                    success: (data) ->
                        typeahead.process(data)
                })
        })
            
        return this

    onClose: =>
        @$('input.filter-input').trigger('cleanup')

