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
        "click .event-add-emergency": "addEmergency"
        "click .event-add-call": "addCall"
        "click .event-add-email": "addEmail"
        "click #edit-event-button": "editEvent"
        "click #details-tabs a": "triggerTab"
        "click #no-students #robocall": "robocallToStudent"
        "click #no-directs #robocall": "robocallToDirect"
        "click #email-download-button": "downloadEvent"

    initialize: (id) =>
        @groupViews = []
        @messageView = null
        @broadcastView = null
        @respondedView = null
        @nonRespondedView = null
        @noStudentsView = null
        @noDirectsView = null
        @studentMarkerList = new App.SOSBeacon.Collection.StudentMarkerList()
        @directMarkerList = new App.SOSBeacon.Collection.DirectMarkerList()

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

        @messageListView = new App.SOSBeacon.View.MessageList(
            @collection, false)
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

    downloadEvent: =>
        @downloadEmail = new App.SOSBeacon.View.EventDownloadEmail(@model)
        el = @downloadEmail.render(true).$el
        el.modal('show')

    messageAdd: (message) =>
        @collection.add(message, {at: 0})

    addComment: =>
        if @broadcastView
            @broadcastView.hide()

        if @messageView
            @messageView.close()

        @messageView = new App.SOSBeacon.View.EditMessage({event: @model})

        @$(".message-entry").append(@messageView.render().el)

    addBroadcast: =>
        if @messageView
            @messageView.hide()

        if @broadcastView
            @broadcastView.close()

        @broadcastView = new App.SOSBeacon.View.AddBroadcast({event: @model})

        @$(".message-entry").append(@broadcastView.render().el)

    addEmail: =>
        if @messageView
            @messageView.hide()

        if @broadcastView
            @broadcastView.close()

        @broadcastView = new App.SOSBeacon.View.AddEmail({event: @model})

        @$(".message-entry").append(@broadcastView.render().el)

    addEmergency: =>
        if @messageView
            @messageView.hide()

        if @broadcastView
            @broadcastView.close()

        @broadcastView = new App.SOSBeacon.View.AddEmergency({event: @model})

        @$(".message-entry").append(@broadcastView.render().el)

    addCall: =>
        if @messageView
            @messageView.hide()

        if @broadcastView
            @broadcastView.close()

        @broadcastView = new App.SOSBeacon.View.AddCall({event: @model})

        @$(".message-entry").append(@broadcastView.render().el)


    editEvent: =>
        App.SOSBeacon.router.navigate(
            "/eventcenter/edit/#{@model.id}", {trigger: true})

    triggerTab: (e) =>
        el = $(e.target)
        href = el.attr('href')
        if href == "#responded" and not @respondedView
            @respondedView = new App.SOSBeacon.View.MarkerList(
                new App.SOSBeacon.Collection.ContactMarkerList,
            @model.id, true)

            @$("#responded").append(@respondedView.render().el)

        else if href == "#not-responded" and not @nonRespondedView
            @nonRespondedView = new App.SOSBeacon.View.MarkerList(
                new App.SOSBeacon.Collection.ContactMarkerList,
            @model.id, false)

            @$("#not-responded").append(@nonRespondedView.render().el)

        else if href == "#no-students" and not @noStudentsView
            @model.fetch({async: false})
            @model.initialize()

            @noStudentsView = new App.SOSBeacon.View.MarkerListStudent(
                @studentMarkerList,
            @model.id, false)

            @$("#no-students").append(@noStudentsView.render().el)
            if @model.get('message_type') == 'rc'
                @$("#no-students fieldset").append("<button class='btn btn-primary' id='robocall'>Robocall non-responders parents</button>")

        else if href == "#no-directs" and not @noDirectsView
            @model.fetch({async: false})
            @model.initialize()

            @noDirectsView = new App.SOSBeacon.View.MarkerListDirect(
                @directMarkerList,
            @model.id, false)

            @$("#no-directs").append(@noDirectsView.render().el)
            if @model.get('message_type') == 'rc'
                @$("#no-directs fieldset").append("<button class='btn btn-primary' id='robocall'>Robocall non-responders contacts</button>")
        el.tab('show')

    robocallToStudent: =>
        if !confirm("Do you really to make calls to students contact?")
            return
        $.ajax '/service/event/' + @model.id + '/robocall/student',  {'type':'POST'}
        return false

    robocallToDirect: =>
        if !confirm("Do you really to make calls to directs contact?")
            return
        $.ajax '/service/event/' + @model.id + '/robocall/direct',  {'type':'POST'}
        return false

    onClose: =>
        App.SOSBeacon.Event.unbind(null, null, this)

        for view in [@messageView, @broadcastView, @respondedView,
            @nonRespondedView, @noStudentsView, @noDirectsView]
            if view
                view.close()

        for view in @groupViews
            view.close()

        @messageListView.close()


class App.SOSBeacon.View.EventDownloadEmail extends Backbone.View
    id: "downloademail"
    tagName:'div'
    template: JST['event-center/download-email']

    events:
        "click #send-email-select #email-download-button": "downloadEmail"

    initialize: (model) =>
        @model = model

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this

    downloadEmail: =>

        downloadOptions = $(".de-option")
        selectCount = ""
        $.each downloadOptions, ->
            if $(this).is(":checked")
                selectCount = selectCount + $(this).val()

        if selectCount.length > 0
            if confirm("Are you sure you want to send phone website data to your email?")
                $(".message-info").html "<h4 style='color: blue'>Start sending email, please wait and don't reload your browser ...</h4>"
                $.ajax
                    url: '/service/event/' + @model.id + '/' + selectCount + '/download',
                    type: "GET",
                    async: false,
                    success: (data) ->
                        selectCount = ""
                        $('.message-info').hide()
                        App.Util.Form.showAlert(
                            "Successs!", "Sent successful to your email", "alert-success")
            else
                false
        else
            alert "Please select your download options."
            false

        return false


class App.SOSBeacon.View.EventGroup extends Backbone.View
    tagName:'a'
    className:'editGroup'

    events:
        "click": "editGroup"

    initialize: (model) =>
        @model = model

    render: =>
        @$el.html("#{@model.get('name')} <br />")
        #        @$el.attr('href','/#groupstudents/'+@model.get('key'))
        return this

    editGroup: =>
        @groupEdit = new App.SOSBeacon.View.GroupStudentsEdit(@model.id)
        el = @groupEdit.render(true).$el
        el.modal('show')


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
            @$("#content").wysihtml5({
                "uploadUrl": "/uploads/new",
            })

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
        "change #selectTimeZone" : "timezone"

    initialize: =>
        @collection = new App.SOSBeacon.Collection.EventList()
        @listView = new App.SOSBeacon.View.EventCenterList(@collection)
        _.extend(@collection.server_api, {
            'limit': 200
            'orderBy': 'added'
            'orderDirection': 'desc'
        })
        @collection.fetch()

    render: =>
        @$el.html(@template())
        @$el.append(@listView.render().el)
        #
        select = @$el.find("#selectTimeZone")
        select.val(default_timezone)

        $("#add_new").focus()

        return this

    timezone: =>
        select = @$el.find("#selectTimeZone")
        default_timezone = select.val()

        url = '/service/timezone/' + default_timezone
        default_timezone = @sendAjax(url)

        location.reload()
        return false

    sendAjax: (url) ->
        result = null
        $.ajax
            url: url,
            type: "GET",
            async: false,
            success: (data) ->
                result = data
        return result

    add: =>
        App.SOSBeacon.router.navigate("/eventcenter/new", {trigger: true})


class App.SOSBeacon.View.EventCenterListItem extends App.Skel.View.ListItemView
    template: JST['event-center/list']

    events:
        "click .view-button": "view"
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


