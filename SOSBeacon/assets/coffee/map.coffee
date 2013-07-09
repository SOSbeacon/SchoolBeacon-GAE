class App.SOSBeacon.View.GoogleEdit extends Backbone.View
    id: "google_edit"
    tagName:'div'
    template: JST['map/view']

    events:
        'click button#yes_location': 'submitLocation'
        'click button#cancel_location': 'close'
        'submit form#searchlocationform': 'search'
        "hidden": "close"

    render: =>
        @$el.html(@template())
        return this

    submitLocation:=>
        console.log 1
        @close()
        @$(".modal-backdrop").hide()
        @$("#google_edit").hide()
        App.Skel.Event.trigger('submitLocation')

    search:=>
        address = @$('#address_location').val()
        App.Skel.Event.trigger('search_address', address)
        return false



