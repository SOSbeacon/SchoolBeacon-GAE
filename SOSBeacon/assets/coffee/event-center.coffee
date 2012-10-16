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
            errors.content = "Content must be provided."

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


class App.SOSBeacon.View.EventCenterAppView extends Backbone.View
    template: JST['event-center/detail']
    id: "sosbeaconapp"
    className: "top_view row-fluid event-center-details"

    events:
        "click .event-add-comment": "addComment"
        "click .event-add-broadcast": "addBroadcast"
        "click #edit-event-button": "editEvent"
        "click #details-tabs a": "triggerTab"

    initialize: (id) =>
        @groupViews = []
        @messageView = null
        @broadcastView = null
        @respondedView = null
        @nonRespondedView = null

        @model = new App.SOSBeacon.Model.Event({key: id})
        @model.fetch({async: false})
        @model.initialize()

        App.SOSBeacon.Event.bind("message:add", @messageAdd, this)
        #App.SOSBeacon.Event.bind("message:edit", @messageEdit, this)

    render: =>
        @$el.html(@template(@model.toJSON()))

        @renderGroups()
        @renderMessages()

        $('#details-tabs a[href="#details"]').tab('show')

        return this

    renderMessages: =>
        @collection = new App.SOSBeacon.Collection.MessageList()
        _.extend(@collection.server_api, {
            'feq_event': @model.id
            'orderBy': 'timestamp'
            'orderDirection': 'desc'
        })

        @collection.fetch()

        @messageListView = new App.SOSBeacon.View.MessageList(@collection)
        @$("#event-center-message").append(@messageListView.render().el)

    renderGroups: =>
        groupEl = @$('.event-groups')
        _.each(@model.groups.models, (group) =>
            groupView = new App.SOSBeacon.View.EventGroup(group)
            #TODO: move view creaton out
            #https://github.com/EzoxSystems/SOSbeacon/pull/102/files#r1808979
            groupEl.append(groupView.render().el)
            @groupViews.push(groupView)
        )

    messageAdd: (message) =>
        @collection.add(message, {at: 0})

    addComment: =>
        if @broadcastView
            @broadcastView.hide()

        if not @messageView
            @messageView = new App.SOSBeacon.View.EditMessage({event: @model})

        @$(".message-entry").append(@messageView.render().el)

    addBroadcast: =>
        if @messageView
            @messageView.hide()

        if not @broadcastView
            @broadcastView = new App.SOSBeacon.View.AddBroadcast({event: @model})

        @$(".message-entry").append(@broadcastView.render().el)

    editEvent: =>
        App.SOSBeacon.router.navigate(
            "/eventcenter/edit/#{@model.id}", {trigger: true})

    triggerTab: (e) =>
        el = $(e.target)
        href = el.attr('href')
        if href == "#responded" and not @respondedView
            console.log('load responded')
        else if href == "#not-responded" and not @nonRespondedView
            console.log('load not responded')

        el.tab('show')

    onClose: =>
        App.SOSBeacon.Event.unbind(null, null, this)

        for view in [
            @messageView, @broadcastView, @respondedView, @nonRespondedView]
            if view
                view.close()

        for view in @groupViews
            view.close()

        @messageListView.close()


class App.SOSBeacon.View.EventGroup extends Backbone.View

    initialize: (model) =>
        @model = model

    render: =>
        @$el.html("#{@model.get('name')} <br />")
        return this


class App.SOSBeacon.View.EventCenterEditApp extends Backbone.View
    template: JST['event-center/itemheader']
    id: "sosbeaconapp"
    className: "top_view container"
    isNew: true

    events:
        "click .view-button": "view"

    initialize: (id) =>
        if not id
            @model = new App.SOSBeacon.Model.Event()
            @isNew = true
        else
            @model = new App.SOSBeacon.Model.Event({key: id})
            @model.fetch({async: false})
            @model.initialize()
            @isNew = false

        @editForm = new App.SOSBeacon.View.EventCenterEditForm(@model)
        App.SOSBeacon.Event.bind("model:save", @modelSaved, this)

    modelSaved: (model) =>
        #TODO: navigate to view page
        App.SOSBeacon.router.navigate(
            "/eventcenter/view/#{model.id}", {trigger: true})

    render: =>
        @$el.html(@template(@model.toJSON()))
        @$el.append(@editForm.render().el)

        @renderHeader()

        try
            @$("#content").wysihtml5()

        return this

    renderHeader: () =>
        header = @$("#editheader")

        if @addMode
            header.html("Add New #{header.text()}")
        else
            header.html("Edit #{header.text()}")

    view: =>
        App.SOSBeacon.router.navigate("/eventcenter", {trigger: true})

    onClose: () =>
        App.SOSBeacon.Event.unbind(null, null, this)

        @editForm.close()


class App.SOSBeacon.View.EventCenterEditForm extends Backbone.View
    template: JST['event-center/edit']
    className: "row-fluid"

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

        #TODO: build a way in our FormValidator to handle not wiring all hooks
        delete @events['blur textarea.content']

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

        @model.save({
                title: @$('input.title').val()
                groups: groupIds
                content: $.trim(@$('textarea.content').val())
            },
            success: (model) =>
                App.Util.Form.hideAlert()
                App.Util.Form.showAlert(
                    "Successs!", "Save successful", "alert-success")

                App.Util.TrackChanges.clear(this)
                App.SOSBeacon.Event.trigger('model:save', @model, this)
        )

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13 and focusItem.attr('id') != 'content'
            @save()

            return false

    onClose: () =>
        App.Util.TrackChanges.stop(this)


class App.SOSBeacon.View.EventCenterApp extends Backbone.View
    id: "sosbeaconapp"
    template: JST['event-center/view']

    events:
        "click .add-button": "add"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.EventList()
        @listView = new App.SOSBeacon.View.EventCenterList(@collection)

    render: =>
        @$el.html(@template())
        @$el.append(@listView.render().el)

        $("#add_new").focus()

        return this

    add: =>
        App.SOSBeacon.router.navigate("/eventcenter/new", {trigger: true})


class App.SOSBeacon.View.EventCenterListItem extends App.Skel.View.ListItemView
    template: JST['event-center/list']

    events:
        "click .view-button": "view"
        "click .edit-button": "edit"
        "click .remove-button": "delete"

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

    edit: =>
        App.SOSBeacon.router.navigate(
            "/eventcenter/edit/#{@model.id}", {trigger: true})

    view: =>
        App.SOSBeacon.router.navigate(
            "/eventcenter/view/#{@model.id}", {trigger: true})

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


