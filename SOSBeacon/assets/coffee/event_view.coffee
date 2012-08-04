class App.SOSBeacon.Model.StudentMarker extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/event/student'
    defaults: ->
        return {
            key: "",
            acknowledged: false,
            name: "",
            method: "",
            responded: "contacts",
        }


class App.SOSBeacon.Collection.EventStudentList extends App.Skel.REST.RequestPager
    model: App.SOSBeacon.Model.StudentMarker

    server_api: {}

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/event/student'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    defaults: =>
        return {
            fan_key: @event_key,
            feq_acknowledged: @acked,
        }

    initialize: (options) =>
        @event_key = options.event_key
        @acked = if options.acked then 'true' else 'false'


class App.SOSBeacon.View.EventStudentListItem extends App.Skel.View.ListItemView
    template: JST['event_view/studentmarker-listitem']

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this


class App.SOSBeacon.View.EventStudentListHeader extends App.Skel.View.ListItemHeader
    template: JST['event_view/studentmarker-listheader']


class App.SOSBeacon.View.EventStudentList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.EventStudentListItem
    headerView: App.SOSBeacon.View.EventStudentListHeader
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

        super(collection)

    run: (filters) =>
        @collection.server_api = {
            limit: @$("div.gridFooter > select.size-select").val() ? 25
        }

        defaults = @collection.defaults() ? {}
        _.extend(@collection.server_api, defaults, filters)

        App.Skel.Event.trigger("eventstudentlist:filter:#{@cid}", filters)


class App.SOSBeacon.View.ViewEventApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['event_view/view']
    ackList: null
    nonAckList: null

    initialize: (id) =>
        @model = new App.SOSBeacon.Model.Event({key: id})
        @model.fetch({async: false})

        @acknowledged = new App.SOSBeacon.Collection.EventStudentList(
            {event_key: id, acked: true})
        @nonacknowledged = new App.SOSBeacon.Collection.EventStudentList(
            {event_key: id, acked: false})

        @ackList = new App.SOSBeacon.View.EventStudentList(@acknowledged)
        App.Skel.Event.bind("eventstudentlist:filter:#{@ackList.cid}",
                            @filterAcked, this)

        @nonAckList = new App.SOSBeacon.View.EventStudentList(@nonacknowledged)
        App.Skel.Event.bind("eventstudentlist:filter:#{@nonAckList.cid}",
                            @filterNonAcked, this)

    filterAcked: (filters) =>
        @acknowledged.fetch()

    filterNonAcked: (filters) =>
        @nonacknowledged.fetch()

    render: =>
        @$el.html(@template(@model.toJSON()))

        @$("#acknowledged").append(@ackList.render().el)
        @$("#nonacknowledged").append(@nonAckList.render().el)

        return this

    onClose: =>
        @ackList.close()
        @nonAckList.close()

