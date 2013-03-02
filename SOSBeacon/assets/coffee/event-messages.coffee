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
            user_name: "",
            is_admin: false,
            is_student: false
            latitude: "",
            longitude: ""
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


class App.SOSBeacon.View.EditMessage extends Backbone.View
    template: JST['event-center/add-message']
    id: "add-message-area"

    events:
        "click .event-submit-comment": "saveComment"
        "click .event-cancel-comment": "hide"

    initialize: (options) =>
        @event = options.event
        if options.message?
            @message = options.message
        else
            @message = new App.SOSBeacon.Model.Message({
                message: {
                    message: ''
                }
            })

    render: () =>
        @$el.html(@template(@message.toJSON()))

        try
            @$("textarea#add-message-box").wysihtml5({
                "uploadUrl": "/uploads/new",
            })

        return this

    hide: () =>
        @$el.html('')

    saveComment: =>
        if @$('textarea#add-message-box').val()
            @message.save(
                message: {
                    body: @$('textarea#add-message-box').val()
                }
                type: 'c' #c for comment
                event: @event.id
                is_admin: true
            )
            App.SOSBeacon.Event.trigger("message:add", @message, this)
            @hide()

        else
            alert "Please insert message body!"

class App.SOSBeacon.View.AddBroadcast extends Backbone.View
    template: JST['event-center/add-broadcast']
    id: "add-message-area"
    position:null

    events:
        "click .event-submit-broadcast": "saveBroadcast"
        "click .event-cancel-broadcast": "hide"
        "keyup textarea#add-sms-box": "smsUpdated"
        "click button#google_map": "renderGoogleMap"

    initialize: (options) =>
        @event = options.event
        @position = {'latitude': '', 'longitude': '',}
        @model = new App.SOSBeacon.Model.Message()

    render: () =>
        @$el.html(@template())

        try
            @$("textarea#add-email-box").wysihtml5({
                "uploadUrl": "/uploads/new",
            })

        return this

    #render map container
    renderGoogleMap:() =>
        @google_edit = new App.SOSBeacon.View.GoogleEdit()
        App.Skel.Event.bind('submitLocation', @submitLocation, this)
        App.Skel.Event.bind('search_address', @searchAddress, this)
        el = @google_edit.render(true).$el
        el.modal('show')

        support = window.navigator.geolocation.getCurrentPosition(@mapLocation, @handerError)
        if support == null
            @mapLocation(null)

    #get postion submited
    submitLocation:=>
        @position.latitude = @marker.getPosition().hb
        @position.longitude = @marker.getPosition().ib

    #make search address that input from search input
    searchAddress:(address)=>
        if not address
            return
        geocoder = new google.maps.Geocoder();
        geocoder.geocode( { 'address': address}, @searchResult);

    searchResult: (results, status) =>
        if status == google.maps.GeocoderStatus.OK
            @map.setCenter(results[0].geometry.location)
            @marker.setPosition(results[0].geometry.location)
        else
            alert('Incorrect location')

    #render map
    mapLocation:(position)=>
        lat = 21.0
        long = 105.0

        if @position.latitude != '' and @position.longitude != ''
            lat = @position.latitude
            long = @position.longitude

        else if position != null
            lat = position.coords.latitude
            long = position.coords.longitude

        @opt = {
            center: new google.maps.LatLng(lat, long),
            zoom: 12,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        }
        @map = new google.maps.Map(document.getElementById('mapCanvasView'), @opt);

        @marker = new google.maps.Marker({
            position: new google.maps.LatLng(lat, long),
            map: @map
            draggable: true
        })

    #render error occur
    handerError: (error) =>
        @position = {'latitude': '', 'longitude': ''}
        alert 'Sorry, system have just encounted an exception'

    hide: () =>
        @$el.html('')

    saveBroadcast: =>
        if @$('textarea#add-sms-box').val()
            if !confirm("Are you sure you want to send this group broadcast?")
                return false

            @model.save(
                message: {
                    sms: @$('textarea#add-sms-box').val(),
                    email: @$('textarea#add-email-box').val()
                },
                type: 'b', #b for broadcast
                event: @event.id
                latitude: ""+@position.latitude
                longitude: ""+@position.longitude
                is_admin: true
            )

            App.SOSBeacon.Event.trigger("message:add", @model, this)
            @hide()

        else
            alert "Please insert SMS Message!"

    smsUpdated: =>
        smsMessage = @$('textarea#add-sms-box').val()
        textSMS = "Preview SMS: Broadcast from #{current_user} (#{current_school}). Link http://8.sos-beacon-dev.appspot.com/xxx/xxx"
        maxSMS = 140 - textSMS.length
        remaining = 140 - smsMessage.length - textSMS.length
        if remaining <= 0
            remaining = 0
        @$('span.sms-remain').text(textSMS + " #{smsMessage} (#{remaining} characters remaining)")
        if (smsMessage.length >= maxSMS)
            cutString = smsMessage.substr(0, maxSMS)
            @$('textarea#add-sms-box').val(cutString)
            @$('span.sms-remain').text(textSMS + " #{cutString} (#{remaining} characters remaining)")


class App.SOSBeacon.View.AddEmergency extends App.SOSBeacon.View.AddBroadcast
    template: JST['event-center/add-emergency']
    id: "add-message-area"
    position:null

    events:
        "click .event-submit-broadcast": "saveEmergency"
        "click .event-cancel-broadcast": "hide"
        "keyup textarea#add-sms-box": "smsUpdated"
        "click button#google_map": "renderGoogleMap"

    saveEmergency: =>
        if @$('textarea#add-sms-box').val()
            if !confirm("Are you sure you want to send this group broadcast?")
                return false

            @model.save(
                message: {
                    sms: @$('textarea#add-sms-box').val(),
                    email: @$('textarea#add-email-box').val()
                },
                type: 'em', #em for emergency
                event: @event.id
                latitude: ""+@position.latitude
                longitude: ""+@position.longitude
                is_admin: true
            )

            App.SOSBeacon.Event.trigger("message:add", @model, this)
            @hide()

        else
            alert "Please insert SMS Message!"

    smsUpdated: =>
        smsMessage = @$('textarea#add-sms-box').val()
        textSMS = "Preview SMS: Broadcast from #{current_user} (#{current_school}). Link http://8.sos-beacon-dev.appspot.com/xxx/xxx"
        maxSMS = 140 - textSMS.length
        remaining = 140 - smsMessage.length - textSMS.length
        if remaining <= 0
            remaining = 0
        @$('span.sms-remain').text(textSMS + " #{smsMessage} (#{remaining} characters remaining)")
        if (smsMessage.length >= maxSMS)
            cutString = smsMessage.substr(0, maxSMS)
            @$('textarea#add-sms-box').val(cutString)
            @$('span.sms-remain').text(textSMS + " #{cutString} (#{remaining} characters remaining)")


class App.SOSBeacon.View.AddCall extends App.SOSBeacon.View.AddBroadcast
    template: JST['event-center/add-call']
    id: "add-message-area"
    position:null

    events:
        "click .event-submit-broadcast": "saveCall"
        "click .event-cancel-broadcast": "hide"
        "click button#google_map": "renderGoogleMap"

    saveCall: =>
        if @$('textarea#add-email-box').val()
            if !confirm("Are you sure you want to send this group broadcast?")
                return false

            @model.save(
                message: {
                    sms: '',
                    email: @$('textarea#add-email-box').val()
                },
                type: 'ec', #cl for call
                event: @event.id
                latitude: ""+@position.latitude
                longitude: ""+@position.longitude
                is_admin: true
            )

            App.SOSBeacon.Event.trigger("message:add", @model, this)
            @hide()

        else
            alert "Please insert body email!"


class App.SOSBeacon.View.AddEmail extends App.SOSBeacon.View.AddBroadcast
    template: JST['event-center/add-email']
    id: "add-message-area"
    position:null

    events:
        "click .event-submit-broadcast": "saveEmail"
        "click .event-cancel-broadcast": "hide"
        "click button#google_map": "renderGoogleMap"

    saveEmail: =>
        if @$('textarea#add-email-box').val()
            if !confirm("Are you sure you want to send this group broadcast?")
                return false

            @model.save(
                message: {
                    sms: '',
                    email: @$('textarea#add-email-box').val()
                },
                type: 'eo', #email only
                event: @event.id
                latitude: ""+@position.latitude
                longitude: ""+@position.longitude
                is_admin: true
            )

            App.SOSBeacon.Event.trigger("message:add", @model, this)
            @hide()

        else
            alert "Please insert body email!"


class App.SOSBeacon.View.MessageList extends Backbone.View
    id: "view-message-area"

    initialize: (collection, hideButtons) =>
        @hideButtons = hideButtons

        @collection = collection
        @collection.bind('add', @insertOne, this)
        @collection.bind('reset', @reset, this)
        @collection.bind('all', @show, this)

    render: =>
        return this

    addOne: (object) =>
        view = new App.SOSBeacon.View.MessageListItem({model: object})
        item = view.render().el

        if @hideButtons
            $(item).find('.message-item-buttons').css('display', 'none')

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

    events:
        #"click #message-item-button-edit": "editMessage"
        "click #message-item-button-remove": "removeMessage"
        "mouseover .message-content": "replyMessage"

    initialize: =>
        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)

    loadReplyMessage: (model)=>
        @replyList = new App.SOSBeacon.Collection.ReplyMessageList()
        _.extend(@replyList.server_api, {
            'feq_message': model.id
            'limit': 1
            'orderBy': 'added'
            'orderDirection': 'desc'
        })
        @replyList.fetch(async: false)
        myTextField = document.getElementById(model.id)

        if myTextField
            @replyList.each((reply, i) =>
                myTextField.innerHTML = reply.get('content')
            )
            return false

        @replyList.each((reply, i) =>
            @$('.message-content div').html(
                $("<div></div>")
                    .attr('value', reply.get('key'))
                    .attr('id', reply.get('message'))
                    .html(reply.get('content'))
            )
        )

    render: =>
        @$el.html(@template(@model.toJSON()))

        @reply = new App.SOSBeacon.Model.ReplyMessage()
        @reply_view = new App.SOSBeacon.View.ReplyMessageEdit(@reply, @model.id)

        if @model.get('type') == 'c'
            @$('#message-item-button-remove').css('display','block')
        if @model.id
            @loadReplyMessage(@model)

        key = @model.get('key')
        lat = @model.get('latitude')
        long = @model.get('longitude')

        if lat.length is 0 and long.length is 0
            return this

        setTimeout((=>
            $('#mapCanvasView'+key).attr('style', 'width: 100% !important; height: 150px; margin-top: 15px;margin-bottom: 15px;display: block;');
            @renderMap(key, lat, long)
        ), 500)

        return this

    renderMap:(key, lat, long) =>
        @opt = {
            center: new google.maps.LatLng(lat, long),
            zoom: 12,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        }
        map = new google.maps.Map(document.getElementById('mapCanvasView'+key), @opt);

        new google.maps.Marker({
            position: new google.maps.LatLng(lat, long),
            map: map
        })

    #TODO: get the edit message interface working.
    #editMessage: =>
        #if @model.type == "c"
            #@messageView = new App.SOSBeacon.View.EditMessage({
                #message: @model
            #})
            #@$(".message-entry").append(@messageView.render().el)

        #else
            #"edit broadcast"

    replyMessage: =>
        $('.fQuickReply').remove();
        $(@el).append(@reply_view.render().el)

    removeMessage: =>
        proceed = confirm('Are you sure you want to delete?  This can not be undone.')
        if proceed
            @model.destroy()


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


#class App.SOSBeacon.View.MessageListApp extends Backbone.View
#    template: JST['event-center/event-messages']
#
#    events:
#        "click .event-submit-comment": "saveComment"
#        "keypress .edit": "updateOnEnter"
#
#    initialize: (id, hideButtons) =>
#        @hideButtons = hideButtons
#        @eventId = id
#
#        @loadMessages()
#
#    loadMessages: =>
#        @messages = new App.SOSBeacon.Collection.MessageList()
#        _.extend(@messages.server_api, {
#            'feq_event': @eventId
#            'orderBy': 'timestamp'
#            'orderDirection': 'asc'
#            'limit': 200
#        })
#
#        @messages.fetch()
#
#    render: =>
#        @$el.html(@template())
#
#        @renderMessages()
#
#        try
#            @$("textarea#add-message-box").wysihtml5({"image": false, "audio" : false, 'link': false})
#
#        return this
#
#    saveComment: =>
#        @$('button.event-submit-comment').attr("disabled", "disabled")
#
#        model = new App.SOSBeacon.Model.Message()
#        model.save({
#            message: {
#                body: @$('textarea#add-message-box').val()
#            }
#            type: 'c' #c for comment
#            event: @eventId
#        }, success: =>
##            location.reload()
#        )
#
#    renderMessages: =>
#        @messageListView = new App.SOSBeacon.View.MessageList(
#            @messages, @hideButtons)
#        @$("#event-message-list").append(@messageListView.render().el)
#
#    updateOnEnter: (e) =>
#        focusItem = $("*:focus")
#
#        if e.keyCode == 13
#            @saveComment()
#
#            return false
#
#    onClose: () =>
#        @messageListView.close()

class App.SOSBeacon.View.NewMessageListItem extends App.SOSBeacon.View.MessageListItem
    template: JST['event-center/student-message-list-item']

    setDefaultValue:(defvalue)=>
        @defvalue = defvalue

    render:(object) =>
        new_model = @model.toJSON()
        time = @model.get('modified')
        if object != undefined
            time = object.get('modified')

        new_model['initmodified'] = time
        date = Date.parse(time)
        if date != null
            date.setHours(date.getHours() + @defvalue)
            time = date.toString('yyyy-MM-dd hh:mm')

        new_model['modified'] = time
        @$el.html(@template(new_model))
        @loadReplyMessage(@model)

        key = @model.get('key')
        lat = @model.get('latitude')
        long = @model.get('longitude')

        if lat.length is 0 and long.length is 0
            return this

        setTimeout((=>
            $('#mapCanvasView'+key).attr('style', 'width: 60% !important; height: 250px; margin: 15px auto;display: block;');
            @renderMap(key, lat, long)
        ), 500)

        return this


class App.SOSBeacon.View.MessageListApp extends Backbone.View
    id: "view-message-area"
    template: JST['event-center/event-messages']
    defvalue = 10

    events:
        'click .event-submit-comment': 'saveComment'

    initialize: (id, hideButtons) =>
        @hideButtons = hideButtons
        @eventId = id
        @collection = new App.SOSBeacon.Collection.MessageList()
        _.extend(@collection.server_api, {
            'feq_event': @eventId
            'orderBy': 'timestamp'
            'orderDirection': 'asc'
            'limit': 200
        })

        @collection.bind('add', @insertOne, this)
        @collection.bind('reset', @reset, this)
        @collection.bind('all', @show, this)
        @collection.fetch()

    render: =>
        @$el.html(@template())
        try
            @$("textarea#add-message-box").wysihtml5({
                "image": false,
                "audio" : false,
                'link': false
            })
        return this

    saveComment: =>
        model = new App.SOSBeacon.Model.Message()
        if @$('.add-message-box-area').find('.guest').attr('readonly')
#           save comment for student
            model.save({
                message: {
                    body: @$('textarea#add-message-box').val()
                }
                type: 'c' #c for comment
                event: @eventId
                is_admin: false
                is_student: true
            }
                success: (data) =>
                    console.log JSON.stringify(data)
                    button = '<textarea id="add-message-box" class="span9"></textarea>'
                    input = ('<input type="text" name="user_name" class="guest" readonly="" value="">');
                    @$('.add-message-box-area').html(button)
                    @$('.add-message-box-area').append(input)
                    @$('.add-message-box-area').find('input').val(data.get('user_name'))
                    try
                        @$("textarea#add-message-box").wysihtml5({
                            "image": false,
                            "audio" : false,
                            'link': false
                        })
            )

        else
#           user comn
            model.save({
                message: {
                    body: @$('textarea#add-message-box').val()
                }
                type: 'c' #c for comment
                event: @eventId
                is_admin: false
                is_student: false
                user_name: @$('.add-message-box-area').find('.guest').val()
            }
                success: (data) =>
                    button = '<textarea id="add-message-box" class="span9"></textarea>'
                    input = ('<input type="text" name="user_name" class="guest" value="">');
                    @$('.add-message-box-area').html(button)
                    @$('.add-message-box-area').append(input)
                    @$('.add-message-box-area').find('input').val("Guest")
                    try
                        @$("textarea#add-message-box").wysihtml5({
                            "image": false,
                            "audio" : false,
                            'link': false
                        })
            )

        @addOne(model)

    setDefaultValue:(defvalue)=>
        @defvalue = defvalue

    addOne: (object) =>
        view = new App.SOSBeacon.View.NewMessageListItem({model: object})
        view.setDefaultValue(@defvalue)
        item = view.render().el

        if @hideButtons
            $(item).find('.message-item-buttons').css('display', 'none')

        @$('#event-message-list').append(item)

    insertOne: (object) =>
        view = new App.SOSBeacon.View.NewMessageListItem({model: object})
        view.setDefaultValue(@defvalue)
        @$el.prepend(view.render().el)

    addAll: =>
        @collection.each(@addOne)

    reset: =>
        @$(".listitems").html('')
        @addAll()
