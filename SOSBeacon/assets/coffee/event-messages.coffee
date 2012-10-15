class App.SOSBeacon.Model.Message extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/message'
    defaults: ->
        return {
            key: null,
            event: null,
            type: "",
            message: {},
            modified: '',
            timestamp: null,
            user: null,
            user_name: ""
        }

    validators:
        type: new App.Util.Validate.string(len: {min: 1, max: 100}),
        message: new App.Util.Validate.string(len: {min: 1, max: 1000}),

    validate: (attrs) =>
        hasError = false
        errors = {}

        # TODO: This could be more robust.
        if _.isEmpty(attrs.message)
            hasError = true
            errors.message = "Missing message."

        if hasError
            return errors


class App.SOSBeacon.Collection.MessageList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.Message

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/message'
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


class App.SOSBeacon.View.AddMessage extends Backbone.View
    template: JST['event-center/add-message']
    id: "add-message-area"

    events:
        "click .event-submit-comment": "saveComment"
        "click .event-cancel-comment": "hide"

    initialize: (options) =>
        @event = options.event

    render: () =>
        @$el.html(@template())

        try
            @$("textarea#add-message-box").wysihtml5()

        return this

    hide: () =>
        @$el.html('')

    saveComment: =>
        model = new App.SOSBeacon.Model.Message()
        model.save(
            message: {
                body: @$('textarea#add-message-box').val()
            }
            type: 'c' #c for comment
            event: @event.id
        )

        App.SOSBeacon.Event.trigger("message:add", model, this)

        @hide()


class App.SOSBeacon.View.AddBroadcast extends Backbone.View
    template: JST['event-center/add-broadcast']
    id: "add-message-area"

    events:
        "click .event-submit-broadcast": "saveBroadcast"
        "click .event-cancel-broadcast": "hide"
        "keyup textarea#add-sms-box": "smsUpdated"

    initialize: (options) =>
        @event = options.event

    render: () =>
        @$el.html(@template())

        try
            @$("textarea#add-email-box").wysihtml5()

        return this

    hide: () =>
        @$el.html('')

    saveBroadcast: =>
        model = new App.SOSBeacon.Model.Message()
        model.save(
            message: {
                sms: @$('textarea#add-sms-box').val(),
                title: @$('input#add-title-box').val(),
                email: @$('textarea#add-email-box').val()
            },
            type: 'b', #b for broadcast
            event: @event.id
        )

        App.SOSBeacon.Event.trigger("message:add", model, this)

        @hide()

    smsUpdated: =>
        smsMessage = @$('textarea#add-sms-box').val()
        remaining = 100 - smsMessage.length
        @$('span.sms-remain').text("#{remaining} characters remaining.")


class App.SOSBeacon.View.MessageList extends Backbone.View
    id: "view-message-area"

    initialize: (collection) =>
        @collection = collection
        @collection.bind('add', @insertOne, this)
        @collection.bind('reset', @reset, this)
        @collection.bind('all', @show, this)

    render: =>
        return this

    addOne: (object) =>
        view = new App.SOSBeacon.View.MessageListItem({model: object})
        item = view.render().el

        @$el.append(item)

     insertOne: (object) =>
        view = new App.SOSBeacon.View.MessageListItem({model: object})
        @$el.prepend(view.render().el)
    
    addAll: =>
        @collection.each(@addOne)

    reset: =>
        @$(".listitems").html('')
        @addAll()


class App.SOSBeacon.View.MessageListItem extends Backbone.View
    template: JST['event-center/message-list-item']
    className: "view-message-item"

    initialize: =>
        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this


class App.SOSBeacon.Model.MessageType extends Backbone.Model
    idAttribute: 'type'
    defaults: ->
        return {
            label: "",
            type: '',
        }


class App.SOSBeacon.Collection.MessageType extends Backbone.Collection
    model: App.SOSBeacon.Model.MessageType


App.SOSBeacon.eventTypes = new App.SOSBeacon.Collection.MessageType([
    {type: 'c', label: "Comment"},
    {type: 'b', label: "Broadcast"},
])


class App.SOSBeacon.View.MessageListApp extends Backbone.View
    template: JST['event-center/event-messages']

    events:
        "click .event-submit-comment": "saveComment"
        "keypress .edit": "updateOnEnter"

    initialize: (id) =>
        @eventId = id

        @loadMessages()

    loadMessages: =>
        @messages = new App.SOSBeacon.Collection.MessageList()
        _.extend(@messages.server_api, {
            'feq_event': @eventId
            'orderBy': 'timestamp'
            'orderDirection': 'asc'
            'limit': 200
        })

        @messages.fetch()

    render: =>
        @$el.html(@template())

        @renderMessages()

        try
            @$("textarea#add-message-box").wysihtml5({"image": false})

        return this

    saveComment: =>
        @$('button.event-submit-comment').attr("disabled", "disabled")

        model = new App.SOSBeacon.Model.Message()
        model.save({
            message: {
                body: @$('textarea#add-message-box').val()
            }
            type: 'c' #c for comment
            event: @eventId
        }, success: =>
            #location.reload()
        )

    renderMessages: =>
        @messageListView = new App.SOSBeacon.View.MessageList(@messages)
        @$("#event-message-list").append(@messageListView.render().el)

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            @saveComment()

            return false

    onClose: () =>
        @messageListView.close()
