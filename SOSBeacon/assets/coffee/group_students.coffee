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

        @students = new App.SOSBeacon.Collection.StudentList()
        @groupstudents = new App.SOSBeacon.Collection.StudentList()

        @studentList = new App.SOSBeacon.View.SelectableStudentList(@students)
        @groupStudentList = new App.SOSBeacon.View.SelectableStudentList(@groupstudents)

    render: =>
        @$el.html(@template(@model.toJSON()))

        that = this
        @allstudents.fetch({success: (students) =>
            students.each((student) =>
                set_student = false
                student.groups.each((group) =>
                    if group.id == @model.id
                        that.groupstudents.add(student)
                        set_student = true
                )
                if not set_student
                    that.students.add(student)
            )
        })

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


