
class App.SOSBeacon.Model.ContactMethod extends Backbone.Model
    defaults: ->
        return {
            type: "",
            value: "",
        }

    @isEmail: (value) =>
        # Do we have an email?
        if /^[^\d].+$/.test(value) or value.indexOf('@') != -1
            return true
        return false

    @validateEmail: (value) =>
        # Is it possibly a valid email?
        if not /^\b[A-Z0-9._%-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b$/i.test(value)
            return false
        return true

    @validatePhoneNumber: (value) =>
        # Do we have a possibly valid phone number?
        value = value.replace(/[^\d]/g, "")
        if value.length < 10 or value.length > 11
            return false
        return true

    @formatPhoneNumber: (value) =>
        value = value.replace(/[^\d]/g, "")
        if value.length == 10
            value = '1' + value
        else if value.length != 11
            return value

        return (value[0] + ' (' + value.substr(1, 3) + ') ' +
                 value.substr(4, 3) + '-' + value.substr(7, 4))

    @methodValidator: (value) =>
        value = $.trim(value) # Drop leading and trailing whitespace

        if value.length == 0
            return value

        if @isEmail(value)
            if @validateEmail(value)
                return value
            else
                return new App.Util.Validate.Error(value, 'Invalid email.')

        if not @validatePhoneNumber(value)
            return new App.Util.Validate.Error(value, 'Invalid phone number.')

        value = @formatPhoneNumber(value)

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
    className: "contact-method-edit input-prepend"
    template: JST['contact-method/edit']

    propertyMap:
        #type: "input.type"
        value: "input.value"

    initialize: ->
        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap
            validatorMap: @model.validators
        )
        @validator.on('validate', @updateValue)

        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)

    render: =>
        obj_json = @model.toJSON()
        if @model.get('type') == 'e'
            obj_json.icon = 'envelope'
            obj_json.type_name = 'email'
        else if @model.get('type') == 'p'
            obj_json.icon = 'volume-up'
            obj_json.type_name = 'phone'
        else if @model.get('type') == 't'
            obj_json.icon = 'phone'
            obj_json.type_name = 'text'
        else
            obj_json.icon = ''
            obj_json.type_name = ''

        @$el.html(@template(obj_json))
        return this

    updateValue: (property, value) =>
        changes = {}
        changes[property] = value
        @model.set(changes)

    destroy: =>
        @trigger('removed', @)
        @model.destroy()
        @close()

    validate: =>
        item = @$('input.value')
        value = App.SOSBeacon.Model.ContactMethod.methodValidator(item.val())
        if value instanceof App.Util.Validate.Error
            App.Util.Form._displayMessage(
                item,
                'error',
                value.message
            )
            return false

        @updateValue('value', value)

        return true

