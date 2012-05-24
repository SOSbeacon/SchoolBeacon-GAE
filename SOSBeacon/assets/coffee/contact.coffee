
class App.SOSBeacon.Model.Contact extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/contact'
    defaults: ->
        return {
            key: "",
            name: "",
            students: [],
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


class App.SOSBeacon.View.ContactEdit extends App.Skel.View.EditView
    template: JST['contact/edit']
    modelType: App.SOSBeacon.Model.Contact
    focusButton: 'input#name'

    events:
        "change": "change"
        "click button.add_method": "addMethod"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "click .remove-button": "clear"
        "hidden": "close"

    save: (e) =>
        if e
            e.preventDefault()

        @model.methods.each((method) ->
            method.editView.close()
        )

        @model.save(
            name: @$('input.name').val()
            notes: $.trim(@$('textarea.notes').val())
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        @model.methods.each((info, i) ->
            editView = new App.SOSBeacon.View.ContactMethodEdit({model: info})
            el.find('fieldset.methods').append(editView.render().el)
        )

        return super(asModal)

    addMethod: () =>
        method = new @model.methods.model()
        @model.methods.add(method)

        editView = new App.SOSBeacon.View.ContactMethodEdit({model: method})
        rendered = editView.render()
        @$el.find('fieldset.methods').append(rendered.el)

        rendered.$el.find('input.type').focus()

        return false

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        if e.keyCode == 13
            if focusItem.hasClass('method')
                @addMethod()
                return false

        return super(e)


class App.SOSBeacon.View.ContactApp extends App.Skel.View.ModelApp
    el: $("#sosbeaconapp")
    template: JST['contact/view']
    modelType: App.SOSBeacon.Model.Contact
    form: App.SOSBeacon.View.ContactEdit
    module: 'SOSBeacon'


class App.SOSBeacon.View.ContactList extends App.Skel.View.ListView
    template: JST['contact/list']
    modelType: App.SOSBeacon.Model.Contact


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

