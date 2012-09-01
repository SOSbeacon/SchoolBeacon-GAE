
class App.SOSAdmin.Model.School extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/school'
    defaults: ->
        return {
            key: null,
            name: "",
            owner: "",
            invitations: [],
            users: [],
        }

    initialize: =>
        #@users = new App.SOSBeacon.Collection.UserList()
        #users = @get('users')
        #if not _.isEmpty(users)
        #    url = @users.url + '/' + users.join()
        #    @users.fetch({url: url, async: false})

        @invitations = @nestCollection(
            'invitations',
            new App.SOSAdmin.Collection.InvitationList(@get('invitations')))

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors


class App.SOSAdmin.Collection.SchoolList extends Backbone.Paginator.requestPager
    model: App.SOSAdmin.Model.School
    url: '/service/school'

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/school'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'name'
    }

    server_api: {}


class App.SOSAdmin.View.SchoolEdit extends App.Skel.View.EditView
    template: JST['admin/school/edit']
    modelType: App.SOSAdmin.Model.School
    focusButton: 'input#name'

    propertyMap:
        active: "input.active",
        name: "input.name",

    events:
        "change": "change"
        "click button.add_invitation": "addInvitation"
        "submit form" : "save"
        "keypress .edit": "updateOnEnter"
        "hidden": "close"

    initialize: =>
        @validator = new App.Util.FormValidator(this,
            propertyMap: @propertyMap
            validatorMap: @model.validators
        )

        @invitationViews = []
        @model.invitations.each((invitation, i) =>
            editView = new App.SOSAdmin.View.InvitationEdit({model: invitation})
            editView.on('removed', @removeInvitation)
            @invitationViews.push(editView)
        )

        return super()

    removeInvitation: (invitationView) =>
        # Remove invitation from model.
        @model.invitations.remove(invitationView.model)

        # Remove invitationView from of invitationViews.
        index = _.indexOf(@invitationViews, invitationView)
        delete @invitationViews[index]

        return true

    addInvitation: (e) =>
        if e
            e.preventDefault()

        invitation = new @model.invitations.model()
        @model.invitations.add(invitation)

        view = new App.SOSAdmin.View.InvitationEdit(model: invitation)
        view.on('removed', @removeInvitation)
        @invitationViews.push(view)

        rendered = view.render()
        @$('fieldset.invitations').append(rendered.el)

        rendered.$el.find('input.name').focus()

        return false

    save: (e) =>
        if e
            e.preventDefault()

        badInvitations = _.filter(@invitationViews, (view) ->
            return not view.validate()
        )
        if not _.isEmpty(badInvitations)
            return false

        valid = @model.save(
            name: @$('input.name').val()
        )
        if valid == false
            return false

        return super()

    render: (asModal) =>
        $el = @$el
        $el.html(@template(@model.toJSON()))

        _.each(@invitationViews, (view, i) =>
            $el.find('fieldset.invitations').append(view.render().el)
        )

        return super(asModal)


class App.SOSAdmin.View.SchoolApp extends App.Skel.View.ModelApp
    id: "sosbeaconapp"
    template: JST['admin/school/view']
    modelType: App.SOSAdmin.Model.School
    form: App.SOSAdmin.View.SchoolEdit

    initialize: =>
        @collection = new App.SOSAdmin.Collection.SchoolList()
        @listView = new App.SOSAdmin.View.SchoolList(@collection)


class App.SOSAdmin.View.SchoolListItem extends App.Skel.View.ListItemView
    template: JST['admin/school/list-item']

    events:
        "click .edit-button": "edit"
        "click .remove-button": "delete"

    onClose: =>
        App.Skel.Event.unbind(null, null, this)


class App.SOSAdmin.View.SchoolListHeader extends App.Skel.View.ListItemHeader
    template: JST['admin/school/list-header']


class App.SOSAdmin.View.SchoolList extends App.Skel.View.ListView
    itemView: App.SOSAdmin.View.SchoolListItem
    headerView: App.SOSAdmin.View.SchoolListHeader
    gridFilters: null

    initialize: (collection) =>
        @gridFilters = new App.Ui.Datagrid.FilterList()

        @gridFilters.add(new App.Ui.Datagrid.FilterItem(
            {
                name: 'Name'
                type: 'text'
                prop: 'flike_name'
                default: false
                control: App.Ui.Datagrid.InputFilter
            }
        ))

        super(collection)

