
class App.SOSBeacon.Model.ContactMethod extends Backbone.Model
    defaults: ->
        return {
            type: "",
            value: "",
        }


class App.SOSBeacon.Collection.ContactMethodList extends Backbone.Collection
    model: App.SOSBeacon.Model.ContactMethod


class App.SOSBeacon.View.ContactMethod extends Backbone.View
    tagName: "div"
    className: "contact-info-view"
    template: JST['contact-method/view']

    initialize: ->
        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)
        @model.view = this

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this


class App.SOSBeacon.View.ContactMethodEdit extends Backbone.View
    tagName: "fieldset"
    className: "contact-method-edit"
    template: JST['contact-method/edit']

    events:
        "click a.remove": "destroy"

    initialize: ->
        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)
        @model.editView = this

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this

    close: =>
        @model.set(
            #type: @$('input.type').val()
            value: @$('input.value').val()
        )
        return this

    destroy: =>
        @model.destroy()

