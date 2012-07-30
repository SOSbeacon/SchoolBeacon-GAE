class App.SOSBeacon.Model.StudentMarker extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/event/student'
    defaults: ->
        return {
            key: "",
            all_acked: false,
            name: "",
            responded: "contacts",
        }


class App.SOSBeacon.Collection.EventStudentList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.StudentMarker

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

    query_defaults: {
        event: null
        all_acked: false
    }

    server_api: {}

    initialize: (event_key, acked) =>
        @query_defaults.event = event_key
        @query_defaults.all_acked = acked


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
            limit: @$("div.gridFooter > .size-select").val() ? 25
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)
        _.extend(@collection.server_api, filters)

        App.Skel.Event.trigger("eventstudentlist:filter:#{@cid}", filters)


class App.SOSBeacon.View.ViewEventApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['event_view/view']
    ackList: null
    nonAckList: null

    initialize: (id) =>
        @model = new App.SOSBeacon.Model.Event({key: id})
        @model.fetch({async: false})

        @acknowledged = new App.SOSBeacon.Collection.EventStudentList(id, true)
        @nonacknowledged = new App.SOSBeacon.Collection.EventStudentList(id, false)

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

