
class App.SOSAdmin.Model.School extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/school'
    defaults: ->
        return {
            key: null,
            name: "",
            owner: "",
            invited: [],
            users: [],
        }

    initialize: =>
        @users = new App.SOSAdmin.Collection.UserList()
        users = @get('users')
        if not _.isEmpty(users)
            url = @users.url + '/' + users.join()
            @users.fetch({url: url, async: false})

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors


