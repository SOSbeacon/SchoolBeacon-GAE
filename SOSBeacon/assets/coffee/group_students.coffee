class App.SOSBeacon.Collection.GroupStudentList extends Backbone.Paginator.requestPager
    model: App.SOSBeacon.Model.Student

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/student'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'last_name_'
#        feq_is_direct: true
    }

    server_api: {}


class App.SOSBeacon.View.GroupStudentsApp extends App.Skel.View.App
    id: "sosbeaconapp"
    template: JST['group_students/view']
    studentList: null

    events:
        'click button#moveToStudent': 'moveToStudent'
        'click button#moveToGroup': 'moveToGroup'

    initialize: (id) =>
        @model = new App.SOSBeacon.Model.Group({key: id})
        @model.fetch({async: false})

        @allstudents = new App.SOSBeacon.Collection.StudentList()
        @groupstudents = new App.SOSBeacon.Collection.GroupStudentList()
        @students = new App.SOSBeacon.Collection.StudentList()

        @studentList = new App.SOSBeacon.View.SelectableStudentList(@students)
        App.Skel.Event.bind("studentlist:filter:#{@studentList.cid}", @filterStudents, this)
        App.Skel.Event.bind("filter_students", @filter_group, this)

        @groupStudentList = new App.SOSBeacon.View.SelectableStudentList(@groupstudents)
        App.Skel.Event.bind("studentlist:filter:#{@groupStudentList.cid}", @groupFilterStudents, this)

    filter_group:(filter) =>
        if filter == undefined
            @groupStudentList.run({})
            @studentList.run({})
            return

        @groupStudentList.run({feq_is_direct:filter})
        @studentList.run({feq_is_direct:filter})

    isEmpty: (obj) =>
        if obj == undefined
            return true

        return (Object.getOwnPropertyNames(obj).length == 0)

    filterStudents: (filters) =>
        @students.reset()
#        @allstudents.server_api = {feq_is_direct:true}
        if filters == undefined || @isEmpty(filters)
            @$("#studentlist h2").text("All Contacts")
            @allstudents.server_api = {}

        else
            if filters.feq_is_direct == true
                @$("#studentlist h2").text("Direct Contacts")
            else
                @$("#studentlist h2").text("Student Contacts")
            _.extend(@allstudents.server_api, filters)

        that = this
        @allstudents.fetch({success: (students) =>
            @$('.image').css('display', 'none')
            students.each((student) =>
                not_in = true
                student.groups.each((group) =>
                    if group.id == @model.id
                        not_in = false
                )

                if not_in
                    if student.get('default_student') == true
                        return
                    that.students.add(student)
            )
        })

    groupFilterStudents: (filters) =>
        @groupstudents.server_api['feq_groups'] = @model.id
        @groupstudents.fetch(
            success: =>
                @$('.image').css('display', 'none')
        )

    render: =>
        @$el.html(@template(@model.toJSON()))

        @$("#studentlist").append(@studentList.render().el)
        @$("#groupstudentlist").append(@groupStudentList.render().el)

        return this

    moveToStudent: =>
        that = this

        students_to_move = []
        @groupstudents.each((groupstudent) ->
            if groupstudent.selected
                students_to_move.push(groupstudent)

                groups = groupstudent.get('groups')
                groups.pop(that.model.id)
                groupstudent.save({groups: groups})
                groupstudent.selected = false
        )

        _.each(students_to_move, (student) ->
            that.students.add(student)
            that.groupstudents.remove(student)
        )
#
        @students.comparator = (model) ->
            model.get "last_name"

        @students.sort()
        @students.trigger('reset')

        @groupstudents.comparator = (model) ->
            if model.get('default_student') == true
                model.get "default_student"
            else
                model.get "last_name"
#
        @groupstudents.sort()
        @groupstudents.trigger('reset')

    moveToGroup: =>
        that = this

        students_to_move = []
        @students.each((student) ->
            if student.selected
                students_to_move.push(student)

                groups = student.get('groups')
                groups.push(that.model.id)
                student.save({groups: groups})
                student.selected = false
        )

        _.each(students_to_move, (student) ->
            that.groupstudents.add(student)
            that.students.remove(student)
        )

        @groupstudents.comparator = (model) ->
            if model.get('default_student') == true
                model.get "default_student"
            else
                model.get "last_name"
        #
        @groupstudents.sort()
        @groupstudents.trigger('reset')

        @students.comparator = (model) ->
            model.get "last_name"

        @students.sort()
        @students.trigger('reset')

    onClose: =>
        @studentList.close()


class App.SOSBeacon.View.GroupStudentsEdit extends App.Skel.View.EditView
    id: "editgroupstudent"
    tagName:'div'
    template: JST['group_students/edit']
    studentList: null

    events:
    #        'click button#moveToStudent': 'moveToStudent'
    #        'click button#moveToGroup': 'moveToGroup'
        "hidden": "close"

    initialize: (id) =>
        @model = new App.SOSBeacon.Model.Group({key: id})
        @model.fetch({async: false})

        @allstudents = new App.SOSBeacon.Collection.StudentList()
        @groupstudents = new App.SOSBeacon.Collection.GroupStudentList()
        @students = new App.SOSBeacon.Collection.StudentList()

        @studentList = new App.SOSBeacon.View.SelectableStudentList(@students)
        App.Skel.Event.bind("studentlist:filter:#{@studentList.cid}", @filterStudents, this)

        @groupStudentList = new App.SOSBeacon.View.SelectableStudentList(@groupstudents)
        App.Skel.Event.bind("studentlist:filter:#{@groupStudentList.cid}", @groupFilterStudents, this)

    filterStudents: (filters) =>
        @students.reset()
#        @allstudents.server_api = {feq_is_direct:true}

        if filters != undefined
            _.extend(@allstudents.server_api, filters)

        if filters == undefined
            @allstudents.server_api = {}

        that = this
        @allstudents.fetch({success: (students) =>
            @$('.image').css('display', 'none')
            students.each((student) =>
                not_in = true
                student.groups.each((group) =>
                    if group.id == @model.id
                        not_in = false
                )

                if not_in
                    if student.get('default_student') == true
                        return
                    that.students.add(student)
            )
        })

    groupFilterStudents: (filters) =>
        @groupstudents.server_api['feq_groups'] = @model.id
        @groupstudents.fetch(
            success: =>
                #  remove loading image when collection loading successful
                @$('.image').css('display', 'none')
            error: =>
                # reidrect login page if user not login
                window.location = '/school'
        )

    render: =>
        @$el.html(@template(@model.toJSON()))

        @$("#studentlist").append(@studentList.render().el)
        @$("#groupstudentlist").append(@groupStudentList.render().el)
        $('.selected').hide()

        return this

    onClose: =>
        @studentList.close()


