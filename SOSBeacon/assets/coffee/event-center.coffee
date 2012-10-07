class App.SOSBeacon.Model.Event extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/event'
    defaults: ->
        return {
            key: null,
            event_type: 'e',
            title: "",
            content: "",
            groups: [],
            modified: null
            date: null
            last_broadcast_date: null
            student_count: 0
            contact_count: 0
            responded_count: 0
            status: ""
        }

    validators:
        title: new App.Util.Validate.string(len: {min: 1, max: 100}),
        content: new App.Util.Validate.string(len: {min: 1, max: 10000}),

    initialize: () ->
        @groups = new App.SOSBeacon.Collection.GroupList()

        @loadGroups()

    loadGroups: =>
        groups = @get('groups')
        if groups and not _.isEmpty(groups)
            url = @groups.url + '/' + groups.join()
            @groups.fetch({url: url, async: false})

    validate: (attrs) =>
        hasError = false
        errors = {}

        # TODO: This could be more robust.
        if _.isEmpty(attrs.title)
            hasError = true
            errors.title = "Missing title."

        if _.isEmpty(attrs.content)
            hasError = true
            errors.summary = "Content must be provided."

        if _.isEmpty(attrs.groups)
            hasError = true
            errors.groups = "Must be associated with at least one group."

        if hasError
            return errors


class App.SOSBeacon.Collection.EventList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.Event

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/event'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'modified'
        orderDirection: 'desc'
    }

    server_api: {}


class App.SOSBeacon.View.EventCenterEditApp extends Backbone.View
    template: JST['event-center/itemheader']
    id: "sosbeaconapp"
    className: "top_view row-fluid"
    isNew: true

    initialize: (id) =>
        if not id
            @model = new App.SOSBeacon.Model.Event()
        else
            @model = new App.SOSBeacon.Model.Event({key: id})
            @model.fetch({async: false})
            @model.initialize()
            @isNew = false

        @editForm = new App.SOSBeacon.View.EventCenterEditForm(@model)
        App.SOSBeacon.Event.bind("model:save", @modelSaved, this)

    modelSaved: () =>
        #TODO: redirect to edit page
        console.log('saved')
        console.log(@model)

    render: =>
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


class App.SOSBeacon.View.EventCenterEditForm extends Backbone.View
    template: JST['event-center/edit']
    className: "row-fluid"
    id: "add_area"

    propertyMap:
        title: "input.title"
        groups: "select.groups"
        content: "textarea.content"

    events:
        "change": "change"
        "submit form": "save"
        "keypress .edit": "updateOnEnter"

    initialize: (model) =>
        App.Util.TrackChanges.track(this)

        @model = model

        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap,
            validatorMap: @model.validators
        )

        @model.bind('error', App.Util.Form.displayValidationErrors)

    render: =>
        @$el.html(@template(@model.toJSON()))

        @renderGroups()

        @$("#title").focus()

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

    change: (event) =>
        App.Util.Form.hideAlert()

    save: (e) =>
        if e
            e.preventDefault()

        groupIds = @$("#group-select").val()
        if not groupIds
            groupIds = []

        @model.save(
            title: @$('input.title').val()
            groups: groupIds
            content: $.trim(@$('textarea.content').val())
        )

        if @model.isValid()
            App.Util.Form.hideAlert()
            App.Util.Form.showAlert(
                "Successs!", "Save successful", "alert-success")

            App.SOSBeacon.Event.trigger('model:save', @model, this)
            App.Util.TrackChanges.clear(this)

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            @save()

            return false

    onClose: () =>
        App.Util.TrackChanges.stop(this)


class App.SOSBeacon.View.EventCenterApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['event-center/view']
    modelType: App.SOSBeacon.Model.Event

    events:
        "click .add-button": "add"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.EventList()
        @listView = new App.SOSBeacon.View.EventCenterList(@collection)

    add: =>
        App.SOSBeacon.router.navigate("/eventcenter/new", {trigger: true})


class App.SOSBeacon.View.EventCenterListItem extends App.Skel.View.ListItemView
    template: JST['event-center/list']

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


class App.SOSBeacon.View.EventCenterListHeader extends App.Skel.View.ListItemHeader
    template: JST['event-center/listheader']


class App.SOSBeacon.View.EventCenterList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.EventCenterListItem
    headerView: App.SOSBeacon.View.EventCenterListHeader
    gridFilters: null

    initialize: (collection) =>
        @gridFilters = new App.Ui.Datagrid.FilterList()

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Title'
                type: 'text'
                prop: 'flike_title'
                default: false
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Group'
                type: 'text'
                prop: 'feq_groups'
                default: false
                control: App.SOSBeacon.View.GroupTypeahaedFilter
            }
        ))

        super(collection)


