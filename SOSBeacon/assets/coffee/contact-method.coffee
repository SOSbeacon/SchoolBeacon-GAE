
class App.SOSBeacon.Model.ContactMethod extends Backbone.Model
    defaults: ->
        return {
            type: "",
            value: "",
        }

    @methodValidator: (value) =>
        value = $.trim(value) # Drop leading and trailing whitespace

        # Do we have an email?
        if /^[^\d].+$/.test(value) or value.indexOf('@') != -1
            # Is it possibly a valid email?
            if not /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
                return new App.Util.Validate.Error(value, 'Invalid email.')
            return value

        # Do we have a possibly valid phone number?
        value = value.replace(/[^\d]/g, "")
        if value.length != 11
            return new App.Util.Validate.Error(value, 'Invalid phone number.')

        value = (value[0] + ' (' + value.substr(1, 3) + ') ' +
                 value.substr(4, 3) + '-' + value.substr(7, 4))

        return value

    validators:
        #type: new App.Util.Validate.string()
        value: @methodValidator


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

    propertyMap:
        #type: "input.type"
        value: "input.value"

    events:
        "click a.remove": "destroy"

    initialize: ->
        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap
            validatorMap: @model.validators
        )
        @validator.on('validate', @updateValue)

        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)
        @model.editView = this

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this

    updateValue: (property, value) =>
        changes = {}
        changes[property] = value
        @model.set(changes)

    close: =>
        @model.set(
            #type: @$('input.type').val()
            value: @$('input.value').val()
        )
        return this

    destroy: =>
        @model.destroy()

