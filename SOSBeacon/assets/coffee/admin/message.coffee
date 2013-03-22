class App.SOSAdmin.Model.Message extends Backbone.Model
    idAttribute: 'key'
    urlRoot: '/service/message'
    defaults: ->
        return {
            key: null,
            event: null,
            type: "",
            message: {},
            modified: '',
            added: '',
            timestamp: null,
            user: null,
            user_name: "",
            is_admin: false,
            is_student: false,
            latitude:'',
            longitude:'',
            link_audio: ''
        }


class App.SOSAdmin.Collection.MessageList extends Backbone.Paginator.requestPager
    model: App.SOSAdmin.Model.Message

    paginator_core: {
        type: 'GET',
        dataType: 'json'
        url: '/service/message'
    }

    paginator_ui: {
        firstPage: 0
        currentPage: 0
        perPage: 100
        totalPages: 100
    }

    query_defaults: {
        orderBy: 'modified'
        orderDirection: 'desc'
    }

    server_api: {}

class App.SOSAdmin.View.DashboardMessageHeader extends App.Skel.View.ListItemHeader
    template: JST['admin/dashboard/message/message-list-header']

class App.SOSAdmin.View.DashboardMessageItem extends App.Skel.View.ListItemView
    template: JST['admin/dashboard/message/message-list-item']
    className: "selectable"

    events:
        'click': 'alertDetail'

    alertDetail: ()=>
        message = @model.get('message')
        type = @model.get('type')

        detail = {}
        content = ''

        if type == 'Message'
          content = message.body

        else
          content = message.sms + '<hr id="divider-message"/>'
          content += message.email

        detail['content'] = content
        detail['latitude'] = @model.get('latitude')
        detail['longitude'] = @model.get('longitude')

        JSON.stringify(detail)
        App.Skel.Event.trigger('viewdetail', detail)

class App.SOSAdmin.View.DashboardMessageList extends App.Skel.View.ListView
    itemView: App.SOSAdmin.View.DashboardMessageItem
    headerView: App.SOSAdmin.View.DashboardMessageHeader
    template: JST['admin/dashboard/message/messageview']
    order: 0

    addOne: (object) =>
        if @itemView
            if object.get('type') == 'b'
                object.set('type','Broadcast')

            if object.get('type') == 'eo'
                object.set('type','Email Only')

            if object.get('type') == 'em'
                object.set('type','Emergency')

            if object.get('type') == 'ec'
                object.set('type','Email Call')

            else
                object.set('type','Comment')

            view = new @itemView({model: object})
            @$(".listitems").append(view.render().el)
