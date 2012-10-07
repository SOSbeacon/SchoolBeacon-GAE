class App.SOSBeacon.Model.Event extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/event'
    defaults: ->
        return {
            key: null,
            active: true,
            type: 'e',
            who_to_notify: 'a',
            response_wait_seconds: 3600,
            title: "",
            summary: "",
            detail: "",
            groups: [],
            notice_sent: false,
            notice_sent_at: null,
            notice_sent_by: null
            modified: null
        }

    validators:
        active: new App.Util.Validate.bool(),
        type: new App.Util.Validate.string(choices: ['e', 'n']),
        who_to_notify: new App.Util.Validate.string(choices: ['a', 'p']),
        response_wait_seconds: new App.Util.Validate.integer(min: -1, max: 86400),
        title: new App.Util.Validate.string(len: {min: 1, max: 100}),
        summary: new App.Util.Validate.string(len: {min: 1, max: 100}),
        detail: new App.Util.Validate.string(len: {min: 1, max: 1048576}),

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


class App.SOSBeacon.Collection.EventList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.Event

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/event'
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



