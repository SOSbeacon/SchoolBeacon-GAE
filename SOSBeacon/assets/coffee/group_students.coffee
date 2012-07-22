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

        @groupStudentList = new App.SOSBeacon.View.SelectableStudentList(@groupstudents)
        App.Skel.Event.bind("studentlist:filter:#{@groupStudentList.cid}", @groupFilterStudents, this)

    filterStudents: (filters) =>
        @students.reset()
        @allstudents.server_api = {}

        if filters
            _.extend(@allstudents.server_api, filters)

        that = this
        @allstudents.fetch({success: (students) =>
            students.each((student) =>
                not_in = true
                student.groups.each((group) =>
                    if group.id == @model.id
                        not_in = false
                )
                if not_in
                    that.students.add(student)
            )
        })

    groupFilterStudents: (filters) =>
        @groupstudents.server_api['feq_groups'] = @model.id
        @groupstudents.fetch()

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
        )
        _.each(students_to_move, (student) ->
            that.students.add(student)
            that.groupstudents.remove(student)
        )
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
        )

        _.each(students_to_move, (student) ->
            that.groupstudents.add(student)
            that.students.remove(student)
        )
        @students.trigger('reset')

    onClose: =>
        @studentList.close()


