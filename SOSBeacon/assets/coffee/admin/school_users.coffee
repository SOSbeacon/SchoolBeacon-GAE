class App.SOSAdmin.Collection.SchoolUserList extends Backbone.Paginator.requestPager
    model: App.SOSAdmin.Model.User

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/admin/user'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    server_api: {}


class App.SOSAdmin.View.SchoolUsersApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['admin/school_user/view']
    userList: null

    events:
        'click button#moveToUser': 'moveToUser'
        'click button#moveToSchool': 'moveToSchool'

    initialize: (id) =>
        @model = new App.SOSAdmin.Model.School({key: id})
        @model.fetch({async: false})

        @allusers = new App.SOSAdmin.Collection.UserList()
        @schoolusers = new App.SOSAdmin.Collection.SchoolUserList()
        @users = new App.SOSAdmin.Collection.UserList()

        @userList = new App.SOSAdmin.View.SelectableUserList(@users)
        App.Skel.Event.bind("userlist:filter:#{@userList.cid}", @filterUsers, this)

        @schoolUserList = new App.SOSAdmin.View.SelectableUserList(@schoolusers)
        App.Skel.Event.bind("userlist:filter:#{@schoolUserList.cid}", @schoolFilterUsers, this)

    filterUsers: (filters) =>
        @users.reset()
        @allusers.server_api = {feq_is_admin:false}

        if filters
            _.extend(@allusers.server_api, filters)

        that = this
        @allusers.fetch({success: (users) =>
            users.each((user) =>
                not_in = true
                user.schools.each((school) =>
                    if school.id == @model.id
                        not_in = false
                )

                if not_in
                    that.users.add(user)
            )
        })

    schoolFilterUsers: (filters) =>
        @schoolusers.server_api['feq_schools'] = @model.id
        @schoolusers.fetch()

    render: =>
        @$el.html(@template(@model.toJSON()))

        @$("#userlist").append(@userList.render().el)
        @$("#schooluserlist").append(@schoolUserList.render().el)

        return this

    moveToUser: =>
        that = this

        users_to_move = []
        @schoolusers.each((schooluser) ->

            if schooluser.selected
                users_to_move.push(schooluser)
                schools = schooluser.get('schools')

                schools.pop(that.model.id)
                schooluser.save({schools: schools})
        )
        _.each(users_to_move, (user) ->
            that.users.add(user)
            that.schoolusers.remove(user)
        )
        @schoolusers.trigger('reset')

    moveToSchool: =>
        that = this

        users_to_move = []
        @users.each((user) ->
            if user.selected
                users_to_move.push(user)
                schools = user.get('schools')

                schools.push(that.model.id)
                user.save({schools: schools})
        )

        _.each(users_to_move, (user) ->
            that.schoolusers.add(user)
            that.users.remove(user)
        )
        @users.trigger('reset')

    onClose: =>
        @userList.close()


