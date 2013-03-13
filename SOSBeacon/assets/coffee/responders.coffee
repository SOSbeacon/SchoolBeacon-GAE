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
            methods: []
            place_holder: null
            count_visit: 0
            count_comment: 0
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
        orderBy: 'is_admin'
        limit: 200
    }

    server_api: {}


class App.SOSBeacon.Model.StudentMarker extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/student_marker'
    defaults: ->
        return {
            key: null,
            contacts: {},
            last_broadcast: null,
            name: "",
            acknowledged: false,
            acknowledged_at: 0,
            all_acknowledged: false,
            all_acknowledged_at: 0,
        }


class App.SOSBeacon.Collection.StudentMarkerList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.StudentMarker

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/student_marker'
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
        limit: 200
    }

    server_api: {}


class App.SOSBeacon.Model.DirectMarker extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/student_marker'
    defaults: ->
        return {
            key: null,
            contacts: {},
            last_broadcast: null,
            name: "",
            acknowledged: false,
            acknowledged_at: 0,
            all_acknowledged: false,
            all_acknowledged_at: 0,
        }


class App.SOSBeacon.Collection.DirectMarkerList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.DirectMarker

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/student_marker'
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
        limit: 200
    }

    server_api: {}


class App.SOSBeacon.View.MarkerListItem extends App.Skel.View.ListItemView
    template: JST['responders/list']

    render: =>
        model_props = @model.toJSON()
        if @model.get('methods').length > 1
            model_props['phone'] = @model.get('methods')[1]
            model_props['email'] = @model.get('methods')[0]
        else
            model_props['phone'] = @model.get('methods')[0]
            model_props['email'] = ''

        @$el.html(@template(model_props))
        return this


class App.SOSBeacon.View.MarkerListHeader extends App.Skel.View.ListItemHeader
    template: JST['responders/listheader']


class App.SOSBeacon.View.MarkerList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.MarkerListItem
    headerView: App.SOSBeacon.View.MarkerListHeader
    gridFilters: null
    ackFlag: false

    initialize: (collection, eventKey, ackFlag) =>
        @eventKey = eventKey
        @ackFlag = ackFlag

        @gridFilters = new App.Ui.Datagrid.FilterList()
        super(collection)

    run: (filters) =>
        @collection.server_api = {
            limit: @$("div.gridFooter > .filter-controls > .controls > .size-select").val() ? 200
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)

        filters['feq_acknowledged'] = @ackFlag
        filters['feq_event'] = @eventKey

        #add filter to always flag by the ack type
        _.extend(@collection.server_api, filters)

        @collection.fetch(
            success: =>
                #remove loading image when collection loading successful
                @$('.image').css('display', 'none')
            error: =>
                #reidrect login page if user not login
                window.location = '/school'
        )
        return false


class App.SOSBeacon.View.DirectMarkerListItem extends App.Skel.View.ListItemView
    template: JST['responders/directlist']

    render: =>
        model_props = @model.toJSON()
        contacts = @model.get('contacts')
        emails = []
        voice_phone = []
        text_phone = []

        $.each contacts, (key, value) ->
            $.each value, (key, value) ->
                if key == 'methods'
                    for method in value
                        if method.type == 'e'
                            emails.push(method.value)
                        if method.type == 'p'
                            voice_phone.push(method.value)
                        if method.type == 't'
                            text_phone.push(method.value)

        model_props['email'] = emails
        model_props['voice_phone'] = voice_phone
        model_props['text_phone'] = text_phone
        @$el.html(@template(model_props))
        return this


class App.SOSBeacon.View.DirectMarkerListHeader extends App.Skel.View.ListItemHeader
    template: JST['responders/direct-listheader']


class App.SOSBeacon.View.MarkerListDirect extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.DirectMarkerListItem
    headerView: App.SOSBeacon.View.DirectMarkerListHeader
    gridFilters: null
    ackFlag: false

    initialize: (collection, eventKey, ackFlag) =>
        @eventKey = eventKey
        @ackFlag = ackFlag

        @gridFilters = new App.Ui.Datagrid.FilterList()
        super(collection)

    render: =>
        @$el.html(@template())
        #        image loading before collection is loaded
        @$el.append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')

        if @headerView
            @$("table.table").prepend(new @headerView().render().el)

        if @gridFilters
            @filter = new App.Ui.Datagrid.GridView({
                gridFilters: @gridFilters
                collection: @collection
                id: @cid
            })
            @$("div.gridfilters").html(@filter.render().el)
            App.Skel.Event.bind("filter:run:#{@filter.cid}", @run, this)

            @filter.runFilter()

        return this

    run: (filters) =>
        @collection.server_api = {
            limit: @$("div.gridFooter > .filter-controls > .controls > .size-select").val() ? 200
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)

        filters['feq_acknowledged'] = @ackFlag
        filters['feq_event'] = @eventKey
        filters['feq_is_direct'] = true

        #add filter to always flag by the ack type
        _.extend(@collection.server_api, filters)

        @collection.fetch(
            success: =>
                #remove loading image when collection loading successful
                @$('.image').css('display', 'none')
            error: =>
                #reidrect login page if user not login
                window.location = '/school'
        )

        return false


class App.SOSBeacon.View.StudentMarkerListItem extends App.Skel.View.ListItemView
    template: JST['responders/studentlist']

    render: =>
        model_props = @model.toJSON()
        contacts = @model.get('contacts')
        emails = []
        voice_phone = []
        text_phone = []
        names = []

        $.each contacts, (key, value) ->
            $.each value, (key, value) ->
                if key == 'name'
                    names.push(value)
                if key == 'methods'
                    for method in value
                        if method.type == 'e'
                            emails.push(method.value)
                        if method.type == 'p'
                            voice_phone.push(method.value)
                        if method.type == 't'
                            text_phone.push(method.value)

        model_props['parent1'] = 'hide'
        if names[0] != ''
            model_props['parent1'] = 'show'
            model_props['email1'] = emails[0]
            model_props['voice_phone1'] = voice_phone[0]
            model_props['text_phone1'] = text_phone[0]
            model_props['names1'] = names[0]

        model_props['parent2'] = 'hide'
        if names[1] != ''
            model_props['parent2'] = 'show'
            model_props['email2'] = emails[1]
            model_props['voice_phone2'] = voice_phone[1]
            model_props['text_phone2'] = text_phone[1]
            model_props['names2'] = names[1]

        @$el.html(@template(model_props))
        return this


class App.SOSBeacon.View.StudentMarkerListHeader extends App.Skel.View.ListItemHeader
    template: JST['responders/student-listheader']


class App.SOSBeacon.View.MarkerListStudent extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.StudentMarkerListItem
    headerView: App.SOSBeacon.View.StudentMarkerListHeader
    gridFilters: null
    ackFlag: false

    initialize: (collection, eventKey, ackFlag) =>
        @eventKey = eventKey
        @ackFlag = ackFlag

        @gridFilters = new App.Ui.Datagrid.FilterList()
        super(collection)

    render: =>
        @$el.html(@template())
        #        image loading before collection is loaded
        @$el.append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 50%" class="image">')

        if @headerView
            @$("table.table").prepend(new @headerView().render().el)

        if @gridFilters
            @filter = new App.Ui.Datagrid.GridView({
                gridFilters: @gridFilters
                collection: @collection
                id: @cid
            })
            @$("div.gridfilters").html(@filter.render().el)
            App.Skel.Event.bind("filter:run:#{@filter.cid}", @run, this)

            @filter.runFilter()

        return this

    run: (filters) =>
        @collection.server_api = {
            limit: @$("div.gridFooter > .filter-controls > .controls > .size-select").val() ? 200
        }
        if @collection.query_defaults
            _.extend(@collection.server_api, @collection.query_defaults)

        filters['feq_acknowledged'] = @ackFlag
        filters['feq_event'] = @eventKey
        filters['feq_is_direct'] = false

        #add filter to always flag by the ack type
        _.extend(@collection.server_api, filters)

        @collection.fetch(
            success: =>
                #remove loading image when collection loading successful
                @$('.image').css('display', 'none')
            error: =>
                #reidrect login page if user not login
                window.location = '/school'
        )

        return false
