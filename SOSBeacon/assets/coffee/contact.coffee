
class App.SOSBeacon.Model.Contact extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/contact'
    defaults: ->
        return {
            name: "",
            type: "",
            methods: [],
            notes: "",
        }

    initialize: () ->
        @methods = @nestCollection(
            'methods',
            new App.SOSBeacon.Collection.ContactMethodList(@get('methods')))

    validate: (attrs) =>
        hasError = false
        errors = {}

        if attrs.type != 'd' and _.isEmpty($.trim(attrs.name))
            hasError = true
            errors.name = "Missing name."

            #if _.isEmpty(attrs.methods)
            #    hasError = true
            #    errors.methods = "Supply at least one contact method."

        if hasError
            return errors


class App.SOSBeacon.Collection.ContactList extends Backbone.Collection
    url: '/service/contact'
    model: App.SOSBeacon.Model.Contact


class App.SOSBeacon.Model.ContactType extends Backbone.Model
    idAttribute: 'key'
    defaults: ->
        return {
            type: "",
            label: ""
        }


class App.SOSBeacon.Collection.ContactType extends Backbone.Collection
    model: App.SOSBeacon.Model.ContactType


App.SOSBeacon.contactTypes = new App.SOSBeacon.Collection.ContactType([
    {type: 'p', label: 'Parent/Guardian'},
    {type: 'o', label: 'Other'},
    {type: 'd', label: 'Direct (self)'},
])


class App.SOSBeacon.View.ContactEdit extends Backbone.View
    template: JST['contact/edit']
    tagName: 'li'
    className: 'contact'
    modelType: App.SOSBeacon.Model.Contact

    events:
        "click button#student-remove-contact": "destroy"
        "change select.contact-type": "typeChanged"
        "blur select.contact-type": "typeChanged"
        "change input.contact-name": "validate"
        "blur input.contact-name": "validate"
        "change textarea.contact-notes": "validate"
        "blur textarea.contact-notes": "validate"
        "keypress .edit": "updateOnEnter"

    initialize: =>
        @contactMethodViews = []
        return super()

    validate: ->
        type = @$('select.contact-type').val()
        name_input = @$('input.contact-name')
        name = $.trim(name_input.val())

        if not @validateContacts(type, name, name_input)
            return false

        saved = @model.set({
            name: if type != 'd' then name else '',
            type: type,
            notes: $.trim(@$('textarea.contact-notes').val())
        })
        if saved == false
            return false

        App.Util.Form._clearMessage(name_input)
        return true

    validateContacts: (type, name, name_input) =>
        if type != "d" and _.isEmpty(name)
            App.Util.Form._displayMessage(
                name_input,
                'error',
                'Name is required for non-direct contacts.')
            return false

        badMethods = false

        @contactMethodViews.filter((methodView) ->
            error = methodView.validate()
            if not error
                badMethods = true
        )
        if badMethods
            return false

        return true

    typeChanged: =>
        type = @$('select.contact-type').val()
        if type == "d"
            name = @$('input.contact-name').hide()
        else
            name = @$('input.contact-name').show()

        @validate()

    render: =>
        @$el.html(@template(@model.toJSON()))

        @render_methods()
        @render_types()

        return this

    render_methods: =>
        for method in ['e', 't', 'p']
            # get the method if it exists
            contact_method = @model.methods.find((m) ->
                return m.get('type') == method
            )
            if not contact_method
                contact_method = new App.SOSBeacon.Model.ContactMethod(
                    {type: method})
                @model.methods.add(contact_method)

            editView = new App.SOSBeacon.View.ContactMethodEdit(
                {model: contact_method})

            @contactMethodViews.push(editView)
            @$el.find('div.methods').append(editView.render().el)

    render_types: =>
        contactType = @model.get('type')

        select = @$('select.contact-type')
        App.SOSBeacon.contactTypes.each((type, i) =>
            option = $('<option></option>')
                .attr('value', type.get('type'))
                .html(type.get('label'))

            if contactType == type.get('type')
                option.attr('selected', 'selected')

            select.append(option)
        )
        if contactType == "d"
            name = @$('input.contact-name').hide()

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        return false

    destroy: =>
        @trigger('removed', @)
        @model.destroy()

    onClose: =>
        App.SOSBeacon.Event.unbind(null, null, this)

        for view in @contactMethodViews
            view.close()


class App.SOSBeacon.View.ContactListItem extends App.Skel.View.ListItemView
    template: JST['contact/list']


class App.SOSBeacon.View.ContactListHeader extends App.Skel.View.ListItemHeader
    template: JST['contact/listheader']


class App.SOSBeacon.View.ContactList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.ContactListItem
    headerView: App.SOSBeacon.View.ContactListHeader
    gridFilters: null


class App.SOSBeacon.View.ContactSelect extends Backbone.View
    template: JST['contact/select']
    className: "control"

    initialize: ->
        @model.bind('change', @render, this)
        @model.bind('destroy', @remove, this)

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.find('input.name').typeahead({
            value_property: 'name'
            updater: (item) =>
                @model.set(item, {silent: true})
                if @options.contactCollection
                    @options.contactCollection.add(@model)
                return item.name
            matcher: (item) ->
                return true
            source: (typeahead, query) ->
                $.ajax({
                    type: 'GET'
                    dataType: 'json'
                    url: '/service/contact'
                    data: {query: query}
                    success: (data) ->
                        typeahead.process(data)
                })
        })
        return this

