
class App.SOSAdmin.Model.Invitation extends Backbone.Model
    idAttribute: 'key'

    defaults: ->
        return {
            name: "",
            email: "",
            isnew: true
        }

    initialize: (args) =>
        if not args or not args.key
            uuid = 'xxx_xxx9xxxx-4xxx'.replace(
                /[xy]/g,
                (c) ->
                    r = Math.random() * 16 | 0
                    v = if c == 'x' then r else (r & 0x3 | 0x8)
                    return v.toString(16)
            )
            @set('key': uuid)

    @emailValidator: (email) =>
        email = $.trim(email) # Drop leading and trailing whitespace

        # Is it possibly a valid email?
        if not /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
            return new App.Util.Validate.Error(email, 'Invalid email.')

        return email

    validators:
        name: new App.Util.Validate.string(len: {min: 1, max: 50}),
        email: @emailValidator


class App.SOSAdmin.Collection.InvitationList extends Backbone.Collection
    model: App.SOSAdmin.Model.Invitation


class App.SOSAdmin.View.Invitation extends Backbone.View
    tagName: "div"
    className: "invitation-view"
    template: JST['admin/invitation/view']

    initialize: ->
        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)

    render: =>
        @$el.html(@template(@model.toJSON()))
        return this


class App.SOSAdmin.View.InvitationEdit extends Backbone.View
    tagName: "fieldset"
    className: "invitation-edit"
    template: JST['admin/invitation/edit']

    propertyMap:
        name: "input.name"
        email: "input.email"

    events:
        "click a.remove-method": "destroy"

    validate: =>
        if not @model.get('isnew')
            return true

        bad_properties = _.filter(@propertyMap, (field, property) =>
            result = (@validator._runValidator(property))()
            if result instanceof App.Util.Validate.Error
                return true
            return false
        )
        if not _.isEmpty(bad_properties)
            return false
        return true

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

    destroy: =>
        @trigger('removed', @)
        @model.destroy()
        @close()

