class App.SOSBeacon.Model.ContactMarker extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/contact_marker'
    defaults: ->
        return {
            key: null,
            short_id: '',
            event: null,
            name: "",
            acknowledged: false,
            last_viewed_date: null
            students: {}
            methods: ''
            place_holder: null
        }


class App.SOSBeacon.Collection.ContactMarkerList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.ContactMarker

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/contact_marker'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'name'
        orderDirection: 'desc'
    }

    server_api: {}


class App.SOSBeacon.View.ContactMarkerListItem extends App.Skel.View.ListItemView
    template: JST['responders/list']


class App.SOSBeacon.View.ContactMarkerListHeader extends App.Skel.View.ListItemHeader
    template: JST['responders/listheader']


class App.SOSBeacon.View.ContactMarkerList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.ContactMarkerListItem
    headerView: App.SOSBeacon.View.ContactMarkerListHeader
    gridFilters: null
    ackFlag: false

    initialize: (collection, ackFlag) =>
        @ackFlag = ackFlag
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
            limit: @$("div.gridFooter > .filter-controls > .controls > .size-select").val() ? 200
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)

        filters['feq_acknowledged'] = @ackFlag

        #add filter to always flag by the ack type
        _.extend(@collection.server_api, filters)

        @collection.fetch()

        return false


