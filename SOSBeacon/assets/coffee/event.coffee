
class App.SOSBeacon.Model.Event extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/event'
    defaults: ->
        return {
            key: "",
            active: true,
            notify_primary_only: false,
            response_wait_seconds: 3600,
            title: "",
            summary: "",
            detail: "",
            groups: []
        }

    initialize: () ->
        @groups = new App.SOSBeacon.Collection.GroupList()
        groups = @get('groups')
        if not _.isEmpty(groups)
            url = @groups.url + '/' + groups.join()
            @groups.fetch({url: url})
        return this

    validate: (attrs) =>
        hasError = false
        errors = {}

        # TODO: This could be more robust.
        if not _.isFinite(attrs.response_wait_seconds)
            hasError = true
            errors.response_wait_seconds = "Invalid value for response wait seconds."

        if _.isEmpty(attrs.title)
            hasError = true
            errors.title = "Missing title."

        if _.isEmpty(attrs.summary)
            hasError = true
            errors.summary = "A brief summary must be provided."

        if _.isEmpty(attrs.detail)
            hasError = true
            errors.detail = "A detailed description is required."

        if _.isEmpty(attrs.groups)
            hasError = true
            errors.groups = "Must be associated with at least one group."

        if hasError
            return errors


class App.SOSBeacon.Collection.EventList extends Backbone.Collection
    url: '/service/event'
    model: App.SOSBeacon.Model.Event


class App.SOSBeacon.Model.ResendDelay extends Backbone.Model
    idAttribute: 'seconds'
    defaults: ->
        return {
            label: "",
            seconds: 0,
        }


class App.SOSBeacon.Collection.ResendDelay extends Backbone.Collection
    model: App.SOSBeacon.Model.ResendDelay


class App.SOSBeacon.View.EventEdit extends App.Skel.View.EditView
    template: JST['event/edit']
    modelType: App.SOSBeacon.Model.Event
    focusButton: 'input#title'

    events:
        "change": "change"
        "click button.add_group": "addGroup"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "click .remove-button": "clear"
        "hidden": "close"

    initialize: =>
        @resendDelays = new App.SOSBeacon.Collection.ResendDelay()
        @resendDelays.add({seconds: 1800, label: "30 Mintues"})
        @resendDelays.add({seconds: 3600, label: "1 Hour"})
        @resendDelays.add({seconds: 7200, label: "2 Hours"})
        @resendDelays.add({seconds: 21600, label: "6 Hours"})
        @resendDelays.add({seconds: 86400, label: "1 Day"})
        @resendDelays.add({seconds: -1, label: "Never"})

        super()

    save: (e) =>
        if e
            e.preventDefault()

        groupList = []
        @model.groups.each((group) ->
            groupList.push(group.id)
        )

        @model.save(
            active: @$('input.active').prop('checked')
            title: @$('input.title').val()
            summary: @$('textarea.summary').val()
            detail: @$('textarea.detail').val()
            groups: groupList
            notify_primary_only: @$('input.notify_primary_only').prop('checked')
            response_wait_seconds: parseInt(@$('select.response_wait_seconds').val())
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @model.groups.each((group, i) ->
            editView = new App.SOSBeacon.View.GroupSelect({model: group})
            el.find('fieldset.groups').append(editView.render().el)
        )

        select = @$('.response_wait_seconds')
        @resendDelays.each((resendDelay, i) =>
            option = $('<option></option>')
                .attr('value', resendDelay.get('seconds'))
                .html(resendDelay.get('label'))

            console.log(@model.get('response_wait_seconds'))
            console.log(resendDelay.get('seconds'))

            if parseInt(@model.get('response_wait_seconds')) == parseInt(resendDelay.get('seconds'))
                console.log('they are equal')
                option.attr('selected', 'selected')

            select.append(option)
        )
        console.log(select)

        return super(asModal)

    addGroup: () =>
        editView = new App.SOSBeacon.View.GroupSelect(
            model: new @model.groups.model()
            groupCollection: @model.groups
        )
        rendered = editView.render()
        @$el.find('fieldset.groups').append(rendered.el)

        rendered.$el.find('input.group').focus()

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            if focusItem.hasClass('group')
                @addGroup()
                return false

        return super(e)


class App.SOSBeacon.View.EventApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['event/view']
    modelType: App.SOSBeacon.Model.Event
    form: App.SOSBeacon.View.EventEdit

    initialize: =>
        @collection = new App.SOSBeacon.Collection.EventList()
        @listView = new App.SOSBeacon.View.EventList(@collection)

        @collection.fetch()
        console.log(@collection)


class App.SOSBeacon.View.EventListItem extends App.Skel.View.ListItemView
    template: JST['event/list']


class App.SOSBeacon.View.EventListHeader extends App.Skel.View.ListItemHeader
    template: JST['event/listheader']


class App.SOSBeacon.View.EventList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.EventListItem
    headerView: App.SOSBeacon.View.EventListHeader
    gridFilters: null


class App.SOSBeacon.View.EventSelect extends Backbone.View
    template: JST['event/select']
    className: "control"

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.find('input.event').typeahead({
            value_property: 'title'
            updater: (item) =>
                @model.set({'name': item.name},
                           {silent: true})
                return item.name
            matcher: (item) ->
                return true
            source: (typeahead, query) ->
                $.ajax({
                    type: 'GET'
                    dataType: 'json'
                    url: '/service/event'
                    data: {query: query}
                    success: (data) ->
                        typeahead.process(data)
                })
        })
        return this


class App.SOSBeacon.View.PendingEventApp extends App.Skel.View.App
    id: "sosbeaconapp"
    #template: JST['event/pendinglist']
    listView: null

    initialize: =>
        @collection = new App.SOSBeacon.Collection.EventList()
        @listView = new App.SOSBeacon.View.PendingEventList(@collection)

        @collection.fetch()

    render: =>
        App.SOSBeacon.Event.on('Event:send', @onSend)
        #@$el.html(@template())
        #
        @$el.append(@listView.render().el)

        fetchArgs = {
            data: {
                sent: false
            }
        }

        return this

    onSend: (event) =>
        #App.SOSBeacon.Event.bind("#{@modelType.name}:save", this.editSave, this)
        @confirmView = new App.SOSBeacon.View.ConfirmSendEvent({model: event})

        el = @confirmView.render(true).$el
        el.modal('show')
        el.find('input.code').focus()

        if @confirmView.focusButton
            el.find(@confirmView.focusButton).focus()

    onClose: =>
        App.SOSBeacon.Event.unbind(null, null, this)
        if @confirmView
            @confirmView.close()
        @listView.close()


class App.SOSBeacon.View.PendingEventListItem extends App.Skel.View.ListItemView
    template: JST['event/pendinglistitem']


class App.SOSBeacon.View.PendingEventListHeader extends App.Skel.View.ListItemHeader
    template: JST['event/pendinglistheader']


class App.SOSBeacon.View.PendingEventList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.PendingEventListItem
    headerView: App.SOSBeacon.View.PendingEventListHeader
    gridFilters: null

    events:
        "click .send-button": "onSend"

    onSend: =>
        App.SOSBeacon.Event.trigger('Event:send', @model)


#class App.SOSBeacon.View.PendingEventList extends App.Skel.View.ListView
    #template: JST['event/pendinglistitem']
    #modelType: App.SOSBeacon.Model.Event

    #events:
        #"click .send-button": "onSend"

    #onSend: =>
        #App.SOSBeacon.Event.trigger('Event:send', @model)


class App.SOSBeacon.View.ConfirmSendEvent extends App.Skel.View.EditView
    template: JST['event/confirmsend']
    modelType: App.SOSBeacon.Model.Event
    focusButton: 'input#title'

    events:
        "submit form" : "send"
        "hidden": "close"

    send: (e) =>
        if e
            e.preventDefault()

        # start sending the notices now
        $.ajax(
            type: 'POST'
            url: '/service/event/send'
            data:
                event: @model.id
        )

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        return super(asModal)

    updateOnEnter: (e) =>
        return

