
class App.SOSBeacon.Model.NotifyLevel extends Backbone.Model
    idAttribute: 'level'
    defaults: ->
        return {
            label: "",
            level: "",
        }


class App.SOSBeacon.Collection.NotifyLevel extends Backbone.Collection
    model: App.SOSBeacon.Model.NotifyLevel

App.SOSBeacon.notifyLevels = new App.SOSBeacon.Collection.NotifyLevel([
    {level: 'a', label: "All Contacts"},
    {level: 'p', label: "Parents/Guardians Only"},
])


class App.SOSBeacon.Model.EventType extends Backbone.Model
    idAttribute: 'type'
    defaults: ->
        return {
            label: "",
            type: '',
        }


class App.SOSBeacon.Collection.EventType extends Backbone.Collection
    model: App.SOSBeacon.Model.EventType


App.SOSBeacon.eventTypes = new App.SOSBeacon.Collection.EventType([
    {type: 'e', label: "Emergency Broadcast"},
    {type: 'n', label: "Notification"},
])


class App.SOSBeacon.Model.ResendDelay extends Backbone.Model
    idAttribute: 'seconds'
    defaults: ->
        return {
            label: "",
            seconds: 0,
        }


class App.SOSBeacon.Collection.ResendDelay extends Backbone.Collection
    model: App.SOSBeacon.Model.ResendDelay


App.SOSBeacon.resendDelays = new App.SOSBeacon.Collection.ResendDelay([
    {seconds: 1800, label: "30 Mintues"},
    {seconds: 3600, label: "1 Hour"},
    {seconds: 7200, label: "2 Hours"},
    {seconds: 21600, label: "6 Hours"},
    {seconds: 86400, label: "1 Day"},
    {seconds: -1, label: "Never"}
])


class App.SOSBeacon.View.EventEdit extends App.Skel.View.EditView
    template: JST['event/edit']
    modelType: App.SOSBeacon.Model.Event
    focusButton: 'input#title'

    propertyMap:
        active: "input.active",
        type: "select.type",
        who_to_notify: "select.who_to_notify",
        response_wait_seconds: "select.response_wait_seconds",
        title: "input.title",
        summary: "textarea.summary",
        detail: "textarea.detail"

    events:
        "change": "change"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "hidden": "close"
        "keyup textarea.sms": "smsUpdated"

    initialize: =>
        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap
            validatorMap: @model.validators
        )

        return super()

    smsUpdated: =>
        smsMessage = @$('textarea.summary').val()
        remaining = 100 - smsMessage.length
        @$('p.sms-remain').text("#{remaining} characters remaining.")

    save: (e) =>
        if e
            e.preventDefault()

        groupIds = @$("#group-select").val()
        if not groupIds
            groupIds = []

        if _.isEmpty(groupIds)
            App.Util.FormValidator._displayMessage(
                @$('fieldset.groups'), 'error', "At least one group is required.")
            return false

        @model.save(
            active: @$('input.active').prop('checked')
            title: @$('input.title').val()
            summary: @$('textarea.summary').val()
            detail: @$('textarea.detail').val()
            groups: groupIds
            type: @$('select.type').val()
            who_to_notify: @$('select.who_to_notify').val()
            response_wait_seconds: parseInt(@$('select.response_wait_seconds').val())
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @renderGroups()

        select = @$('.type')
        App.SOSBeacon.eventTypes.each((eventType, i) =>
            option = $('<option></option>')
                .attr('value', eventType.get('type'))
                .html(eventType.get('label'))

            if @model.get('type') == eventType.get('type')
                option.attr('selected', 'selected')

            select.append(option)
        )

        select = @$('.who_to_notify')
        App.SOSBeacon.notifyLevels.each((notifyLevel, i) =>
            option = $('<option></option>')
                .attr('value', notifyLevel.get('level'))
                .html(notifyLevel.get('label'))

            if @model.get('who_to_notify') == notifyLevel.get('level')
                option.attr('selected', 'selected')

            select.append(option)
        )

        select = @$('.response_wait_seconds')
        App.SOSBeacon.resendDelays.each((resendDelay, i) =>
            option = $('<option></option>')
                .attr('value', resendDelay.get('seconds'))
                .html(resendDelay.get('label'))

            if parseInt(@model.get('response_wait_seconds')) == parseInt(resendDelay.get('seconds'))
                option.attr('selected', 'selected')

            select.append(option)
        )

        return super(asModal)

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

    updateOnEnter: (e) =>
        focusItem = $("*:focus")
        return super(e)


class App.SOSBeacon.View.EventApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['event/view']
    modelType: App.SOSBeacon.Model.Event
    form: App.SOSBeacon.View.EventEdit

    initialize: =>
        @collection = new App.SOSBeacon.Collection.EventList()
        @listView = new App.SOSBeacon.View.EventList(@collection)


class App.SOSBeacon.View.EventListItem extends App.Skel.View.ListItemView
    template: JST['event/list']


class App.SOSBeacon.View.EventListHeader extends App.Skel.View.ListItemHeader
    template: JST['event/listheader']


class App.SOSBeacon.View.EventList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.EventListItem
    headerView: App.SOSBeacon.View.EventListHeader
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
                name: 'Is Active'
                type: 'checkbox'
                prop: 'feq_active'
                default: true
                control: App.Ui.Datagrid.CheckboxFilter
                default_value: true
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

    render: =>
        App.SOSBeacon.Event.on('Event:send', @onSend, this)
        App.SOSBeacon.Event.on('Event:view', @onView, this)
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

    onView: (event) =>
        if not event.id
            return
        App.SOSBeacon.router.navigate("/broadcast/view/" + event.id, {trigger: true})

    onClose: =>
        App.SOSBeacon.Event.unbind(null, null, this)

        if @confirmView
            @confirmView.close()
        @listView.close()


class App.SOSBeacon.View.PendingEventListItem extends App.Skel.View.ListItemView
    template: JST['event/pendinglistitem']

    events:
        "click .send-button": "onSend"
        "click .view-button": "onView"

    onSend: =>
        App.SOSBeacon.Event.trigger('Event:send', @model)

    onView: =>
        App.SOSBeacon.Event.trigger('Event:view', @model)


class App.SOSBeacon.View.PendingEventListHeader extends App.Skel.View.ListItemHeader
    template: JST['event/pendinglistheader']


class App.SOSBeacon.View.PendingEventList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.PendingEventListItem
    headerView: App.SOSBeacon.View.PendingEventListHeader
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
                name: 'Is Active'
                type: 'checkbox'
                prop: 'feq_active'
                default: true
                control: App.Ui.Datagrid.CheckboxFilter
                default_value: true
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


class App.SOSBeacon.View.ConfirmSendEvent extends Backbone.View
    template: JST['event/confirmsend']

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

        App.Util.Form.hideAlert()
        App.Util.Form.showAlert(
            "Successs!", "Save successful", "alert-success")

        @$el.modal('hide')
        @close()
        return false

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        if asModal
            @$el.attr('class', 'modal')

            @$("editheadercontainter").prepend(
                $("<button class='close' data-dismiss='modal'>&times;</button>"))

        return this
