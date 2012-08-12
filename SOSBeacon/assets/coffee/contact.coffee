
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

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if _.isEmpty(attrs.methods)
            hasError = true
            errors.methods = "Supply at least one contact method."

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
        "click button.add_method": "addMethod"
        "change select.type": "typeChanged"
        "keypress .edit": "updateOnEnter"

    typeChanged: =>
        type = @$('select.type').val()
        if type == "d"
            name = @$('div.name').hide()
        else
            name = @$('div.name').show()

    close: =>
        @model.methods.each((method) ->
            method.editView.close()
        )

        @model.set(
            name: @$('input.name').val(),
            type: @$('select.type').val(),
            notes: $.trim(@$('textarea.notes').val())
        )

    render: =>
        @$el.html(@template(@model.toJSON()))

        @model.methods.each((info, i) =>
            editView = new App.SOSBeacon.View.ContactMethodEdit({model: info})
            @$el.find('fieldset.methods').append(editView.render().el)
        )

        contactType = @model.get('type')

        select = @$('select.type')
        App.SOSBeacon.contactTypes.each((type, i) =>
            option = $('<option></option>')
                .attr('value', type.get('type'))
                .html(type.get('label'))

            if contactType == type.get('type')
                option.attr('selected', 'selected')

            select.append(option)
        )
        if contactType == "d"
            name = @$('div.name').hide()

        return this

    addMethod: =>
        for method in @model.methods.models
            if _.isEmpty(method.get('value'))
                return false

        method = new @model.methods.model()
        @model.methods.add(method)

        editView = new App.SOSBeacon.View.ContactMethodEdit({model: method})
        rendered = editView.render()
        @$el.find('fieldset.methods').append(rendered.el)

        rendered.$el.find('input.method').focus()

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            if focusItem.hasClass('method')
                @addMethod()
                return false

        return false


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
        @model.editView = this

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

