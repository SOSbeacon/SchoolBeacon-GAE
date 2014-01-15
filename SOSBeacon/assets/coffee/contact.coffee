
class App.SOSBeacon.Model.Contact extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/contact'
    defaults: ->
        return {
            first_name: "",
            last_name: "",
            type: "p",
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

        if attrs.type != 'd' and _.isEmpty($.trim(attrs.first_name))
            hasError = true
            errors.first_name = "Missing first name."

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
    {type: 'd', label: 'Direct'},
])

App.SOSBeacon.contactStudentTypes = new App.SOSBeacon.Collection.ContactType([
    {type: 'p', label: 'Parent/Guardian'},
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
        "change input.contact-first-name": "validate"
        "change input.contact-last-name": "validate"
        "blur input.contact-first-name": "validate"
        "blur input.contact-last-name": "validate"
        "change textarea.contact-notes": "validate"
        "blur textarea.contact-notes": "validate"

    initialize: =>
        @contactMethodViews = []
        return super()

    validate: ->
        type = @$('select.contact-type').val()
        first_name_input = @$('input.contact-first-name')
        last_name_input = @$('input.contact-last-name')
        first_name = $.trim(first_name_input.val())
        last_name = $.trim(last_name_input.val())
        first_name_direct = $('input.first_name').val()
        last_name_direct = $('input.last_name').val()

        if not @validateContacts(type, first_name, first_name_input)
            return false

        saved = @model.set({
            first_name: if type != 'd' then first_name else first_name_direct
            last_name: if type != 'd' then last_name else last_name_direct
            type: type,
        })

        if saved == false
            return false

        App.Util.Form._clearMessage(first_name_input)
        return true

    validateContacts: (type, name, name_input) =>
#        if type != "d" and _.isEmpty(name)
#            App.Util.Form._displayMessage(
#                name_input,
#                'error',
#                'Name is required for non-direct contacts.')
#            return false

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
            first_name = @$('input.contact-first-name').hide()
            last_name = @$('input.contact-last-name').hide()

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


class App.SOSBeacon.View.StudentEdit extends App.SOSBeacon.View.ContactEdit
    template: JST['contact/edit']
    tagName: 'li'
    className: 'contact'
    modelType: App.SOSBeacon.Model.Contact

    events:
        "click button#student-remove-contact": "destroy"
        "change select.contact-type": "typeChanged"
        "blur select.contact-type": "typeChanged"
        "change input.contact-first-name": "validate"
        "change input.contact-last-name": "validate"
        "blur input.contact-first-name": "validate"
        "blur input.contact-last-name": "validate"
        "change textarea.contact-notes": "validate"
        "blur textarea.contact-notes": "validate"
        "keypress .edit": "updateOnEnter"

    render: =>
        @$el.html(@template(@model.toJSON()))

        @render_methods()
        @render_types_contact()

        return this

    render_types_contact: =>
        contactType = @model.get('type')

        select = @$('select.contact-type')
        App.SOSBeacon.contactStudentTypes.each((type, i) =>
            option = $('<option></option>')
                .attr('value', type.get('type'))
                .html(type.get('label'))

            if contactType == type.get('type')
                option.attr('selected', 'selected')

            select.append(option)
        )
        if contactType == "d"
            name = @$('input.contact-name').hide()


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

