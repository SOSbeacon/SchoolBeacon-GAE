class App.SOSAdmin.View.DashboardApp extends App.Skel.View.ModelApp
    id        : "sosbeaconapp"
    template  : JST['admin/dashboard/view']
    modelType : App.SOSAdmin.Model.User
    formatDate: "MM/dd/yyyy hh:mm"

    events:
        'click button#btn_gmt': 'convertTime'

    initialize: =>
        @userCollection = new App.SOSAdmin.Collection.UserList()
        @listView = new App.SOSAdmin.View.DashboardUserListOne(@userCollection)
        App.Skel.Event.bind("userlistone:filter:#{@listView.cid}", @runFilterUser, this)

        @usermessages = new App.SOSAdmin.Collection.MessageList()
        @userMessageList = new App.SOSAdmin.View.DashboardMessageList(@usermessages)
        App.Skel.Event.bind('viewdetail', @renderMessage, this)

    runFilterUser: (filters) =>
        if filters.feq_email != undefined and @emailValidator(filters.feq_email) == false
            @$('.user_info > .listitems').html('<h2 id="no_result">Invalid email</h2>')
            @$('.message_list').html('')

            return

        if filters.feq_phone != undefined and @phoneValidator(filters.feq_phone) == false
            @$('.user_info > .listitems').html('<h2 id="no_result">Invalid phone</h2>')
            @$('.message_list').html('')

            return

        @userCollection.fetch({success: (users) =>
            if users.length == 0
                @$('.user_info > .listitems').html('<h2 id="no_result">No result of search</h2>')
                @$('.message_list').html('')

                return

            users.each((user) =>
                @usermessages.server_api = {
                    feq_user: user.id
                }

                @usermessages.fetch(
                    success: =>
#                remove loading image when collection loading successful
                        @$('.image').css('display', 'none')
                    error: =>
#                reidrect login page if user not login
                        window.location = '/school'
                )
                @$('.message_list').html(@userMessageList.render().el)
            )
        })

    render: =>
        @$el.html(@template())
        @$('#dashboard').append(@listView.render().el)
        #render current time to input
        date = new Date()
        gmtstring = date.toGMTString()

        gmtstring = gmtstring.replace(/^(\w*,\s)/, '').replace(/( GMT)$/, '')
        @$('#gmt_input').val(gmtstring)
        @convertTime()

        return this

    renderMessage: (detail)=>
        @$('#message-title').html('Content')
        @$('#message').html(detail.content)

        @$('#latitude-title').html('Latitude')
        @$('#latitude').html(detail.latitude)

        @$('#longitude-title').html('Longitude')
        @$('#longitude').html(detail.longitude)

        if detail.latitude != '' and detail.longitude != ''
            @renderMap(detail.latitude, detail.longitude)

        else
            @$('#mapCanvas').html('No map data')

    renderMap: (lat, long) =>
        @$('#mapCanvas').css('width', '470px')
        @$('#mapCanvas').css('height', '400px')

        opt = {
            center   : new google.maps.LatLng(lat, long),
            zoom     : 6,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        }

        @map = new google.maps.Map(document.getElementById('mapCanvas'), opt);

        new google.maps.Marker({
            position: new google.maps.LatLng(lat, long),
            map     : @map
        });

    emailValidator: (email) =>
        email = $.trim(email)
        partern = /^([a-zA-Z0-9])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/

        if not partern.test(email)
            return false

        return true


    phoneValidator: (phone) =>
        phone = $.trim(phone)

        if not /^\d+$/.test(phone) or phone.length < 10
            return false

        return true

    convertTime: ()=>
        reg = /(ICT$)|(GMT\+0700 \(ICT\)$)/
        timestring = @$('#gmt_input').val()

        sandate = Date.parse(timestring)
        hanoidate = Date.parse(timestring)

        sandate.setHours(sandate.getHours() - 8);
        hanoidate.setHours(hanoidate.getHours() + 7);

        sanstring = sandate.toLocaleString().replace(reg, '')
        hanoistring = hanoidate.toLocaleString().replace(reg, '')
        @$('#output').html('San Francisco: ' + sanstring + ' | Hanoi: ' + hanoistring)
