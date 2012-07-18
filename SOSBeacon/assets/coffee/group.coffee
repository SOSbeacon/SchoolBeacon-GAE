
class App.SOSBeacon.Model.Group extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/group'

    defaults: ->
        return {
            key: "",
            name: "",
            active: true,
            notes: "",
        }

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors


class App.SOSBeacon.Collection.GroupList extends Backbone.Collection
    url: '/service/group'
    model: App.SOSBeacon.Model.Group


class App.SOSBeacon.View.GroupEdit extends App.Skel.View.EditView
    template: JST['group/edit']
    modelType: App.SOSBeacon.Model.Group
    focusButton: 'input#name'

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
            name: @$('input.name').val()
            active: @$('input.active').prop('checked')
            notes: $.trim(@$('textarea.notes').val())
        )

        return super()

    render: (asModal) =>
        el = @$el
        el.html(@template(@model.toJSON()))

        return super(asModal)

    updateOnEnter: (e) =>
        focusItem = $("*:focus")

        return super(e)


class App.SOSBeacon.View.GroupApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['group/view']
    modelType: App.SOSBeacon.Model.Group
    form: App.SOSBeacon.View.GroupEdit

    initialize: =>
        @collection = new App.SOSBeacon.Collection.GroupList()
        @listView = new App.SOSBeacon.View.GroupList(@collection)

        @collection.fetch()


class App.SOSBeacon.View.GroupListItem extends App.Skel.View.ListItemView
    template: JST['group/list']

    initialize: =>
        @events['click .students-button'] = 'viewStudents'

    viewStudents: =>
        App.Skel.Event.trigger("groupstudents:selected", @model.id, this)
        return false


class App.SOSBeacon.View.GroupListHeader extends App.Skel.View.ListItemHeader
    template: JST['group/listheader']


class App.SOSBeacon.View.GroupList extends App.Skel.View.ListView
    itemView: App.SOSBeacon.View.GroupListItem
    headerView: App.SOSBeacon.View.GroupListHeader
    gridFilters: null


class App.SOSBeacon.View.GroupSelect extends Backbone.View
    template: JST['group/select']
    className: "control"

    render: () =>
        @$el.html(@template(@model.toJSON()))
        @$el.find('input.name').typeahead({
            value_property: 'name'
            updater: (item) =>
                @model.set(item, {silent: true})
                if @options.groupCollection
                    @options.groupCollection.add(@model)
                return item.name
            matcher: (item) ->
                return true
            source: (typeahead, query) ->
                $.ajax({
                    type: 'GET'
                    dataType: 'json'
                    url: '/service/group'
                    data: {flike_name: query}
                    success: (data) ->
                        typeahead.process(data)
                })
        })
        return this

