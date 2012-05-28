
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
            response_wait_seconds: parseInt(@$('input.response_wait_seconds').val())
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @model.groups.each((group, i) ->
            editView = new App.SOSBeacon.View.GroupSelect({model: group})
            el.find('fieldset.groups').append(editView.render().el)
        )

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
    el: $("#sosbeaconapp")
    template: JST['event/view']
    modelType: App.SOSBeacon.Model.Event
    form: App.SOSBeacon.View.EventEdit
    module: 'SOSBeacon'

class App.SOSBeacon.View.EventList extends App.Skel.View.ListView
    template: JST['event/list']
    modelType: App.SOSBeacon.Model.Event


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


class App.SOSBeacon.View.PendingEventApp extends App.Skel.View.ListApp
    el: $("#sosbeaconapp")

    initialize: () =>
        @fetchArgs.data ?= {}
        @fetchArgs.data.sent = false
        super('SOSBeacon', 'PendingEventList', @$el, 'EventList')
        App.SOSBeacon.Event.on('Event:send', @onSend)

    onSend: (event) =>
        #App.SOSBeacon.Event.bind("#{@modelType.name}:save", this.editSave, this)

        @confirmView = new App.SOSBeacon.View.ConfirmSendEvent({model: event})

        el = @confirmView.render(true).$el
        el.modal('show')
        el.find('input.code').focus()

        if @confirmView.focusButton
            el.find(@confirmView.focusButton).focus()


class App.SOSBeacon.View.PendingEventList extends App.Skel.View.ListView
    template: JST['event/pendinglist']
    modelType: App.SOSBeacon.Model.Event

    events:
        "click .send-button": "onSend"

    onSend: =>
        App.SOSBeacon.Event.trigger('Event:send', @model)


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

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        return super(asModal)

    updateOnEnter: (e) =>
        return

