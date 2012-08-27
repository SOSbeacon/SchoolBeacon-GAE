
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

    #initialize: =>
        #@groups = new App.SOSAdmin.Collection.GroupList()
        #groups = @get('groups')
        #if groups and not _.isEmpty(groups)
            #url = @groups.url + '/' + groups.join()
            #@groups.fetch({url: url, async: false})

        #@contacts = @nestCollection(
            #'contacts',
            #new App.SOSAdmin.Collection.ContactList(@get('contacts')))

    validate: (attrs) =>
        hasError = false
        errors = {}

        if _.isEmpty(attrs.name)
            hasError = true
            errors.name = "Missing name."

        if hasError
            return errors


