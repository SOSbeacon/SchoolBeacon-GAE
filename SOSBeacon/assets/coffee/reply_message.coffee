
class App.SOSBeacon.Model.ReplyMessage extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/reply_message'
    defaults: ->
        return {
            content: "",
            message: null,
        }

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty($.trim(attrs.content))
            hasError = true
            errors.name = "Missing content."

        if hasError
            return errors


class App.SOSBeacon.Collection.ReplyMessageList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.ReplyMessage

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/reply_message'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'message'
        orderDirection: 'desc'
    }
    server_api: {}


class App.SOSBeacon.View.ReplyMessageEdit extends Backbone.View
    template: JST['reply-message/edit']

    events:
        "click .btnCancel": "cancelReply"
        "click .btnQuickReply": "saveReply"

    initialize:(model, message_id, event_id) =>
        @model = model
        @message_id = message_id
        @event_id = event_id

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        return false

    saveReply: =>
        if @$('.tbQuickReply').val()
            @model.save({
                content: @$('.tbQuickReply').val()
                message: @message_id
            },
                success: (model) =>
                    App.SOSBeacon.Event.trigger('model:save', @model, this)
                    myTextField = $("#"+model.get('message'))
                    if myTextField
                        $('.fQuickReply').remove()
                        myTextField.html(
                            $("<div></div>")
                            .html(model.get('content'))
                            .css('padding-left', '5px')
                        )
                    else
                        alert "Error"
            )
        else
            alert "Please insert body!."

        return false

    cancelReply: =>
        $(".fQuickReply").remove()
