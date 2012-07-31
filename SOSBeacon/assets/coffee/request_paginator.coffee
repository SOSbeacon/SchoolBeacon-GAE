window.App.Skel.REST = App.module('REST')

# @name: RequestPager
# Paginator for server-side data being requested from a backend/API
#
# @description:
# This paginator is responsible for providing pagination
# and sort capabilities for requests to a server-side
# data service (e.g an API)
#
	
class App.Skel.REST.RequestPager extends Backbone.Collection

    # You have to define:
    # paginator_core: {}
    # paginator_ui: {}
    # server_api: {}

    sync: (method, model, options) =>

        # Create default values if others are not specified
        _.defaults(@paginator_ui, {
            firstPage: 0,
            currentPage: 1,
            perPage: 5,
            totalPages: 10
        })

        # Change scope of 'paginator_ui' object values
        _.each(@paginator_ui, (value, key) =>
            if _.isUndefined(this[key])
                this[key] = @paginator_ui[key]
        )

        # Values may be functions, if so run them under current scope.
        queryAttributes = {}
        _.each(@server_api, (value, key) =>
            if _.isFunction(value)
                value = _.bind(value, self)
            queryAttributes[key] = value
        )

        queryOptions = _.clone(@paginator_core)

        # Create default values if no others are specified
        queryOptions = _.defaults(queryOptions, {
            timeout: 25000,
            cache: false,
            type: 'GET',
            dataType: 'jsonp'
        })

        queryOptions = _.extend(queryOptions, {
            jsonpCallback: 'callback',
            data: decodeURIComponent($.param(queryAttributes)),
            processData: false,
            url: _.result(queryOptions, 'url')
        }, options)

        return $.ajax(queryOptions)

    requestNextPage: =>
        if _.isUndefined(@currentPage)
            return

        @currentPage += 1
        @pager()

    requestPreviousPage: =>
        if _.isUndefined(@currentPage)
            return

        @currentPage -= 1
        @pager()

    updateOrder: (column) =>
        if _.isUndefined(column)
            return

        @sortField = column
        @pager()

    goTo: (page) =>
        if _.isUndefined(page)
            return

        @currentPage = parseInt(page, 10)
        @pager()

    howManyPer: (count) =>
        if _.isUndefined(count)
            return

        @currentPage = @firstPage
        @perPage = count
        @pager()

    sort: =>
        # assign to as needed.

    info: =>
        @info =
            currentPage: @currentPage
            firstPage: @firstPage
            totalPages: @totalPages
            lastPage: @totalPages
            perPage: @perPage

        return @info

    # Fetches the latest results from the server
    pager: =>
        @fetch({})

