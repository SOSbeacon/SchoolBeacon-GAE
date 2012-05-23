
class App.SOSBeacon.Model.Event extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/event'
    defaults: ->
        return {
            key: "",
            active: true,
            title: "",
            summary: "",
            detail: "",
            groups: ""
        }

    validate: (attrs) =>
        hasError = false
        errors = {}

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
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "click .remove-button": "clear"
        "hidden": "close"

    save: (e) =>
        if e
            e.preventDefault()

        @model.save(
            active: @$('input.active').val()
            title: @$('input.title').val()
            summary: @$('input.summary').val()
            detail: @$('input.detail').val()
            groups: @$('input.groups').val()
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        return super(asModal)

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

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

