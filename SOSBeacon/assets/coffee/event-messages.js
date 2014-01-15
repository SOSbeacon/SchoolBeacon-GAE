// Generated by CoffeeScript 1.6.3
(function() {
  var _ref, _ref1, _ref10, _ref11, _ref12, _ref2, _ref3, _ref4, _ref5, _ref6, _ref7, _ref8, _ref9,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  App.SOSBeacon.Model.Message = (function(_super) {
    __extends(Message, _super);

    function Message() {
      this.validate = __bind(this.validate, this);
      _ref = Message.__super__.constructor.apply(this, arguments);
      return _ref;
    }

    Message.prototype.idAttribute = 'key';

    Message.prototype.urlRoot = '/service/message';

    Message.prototype.defaults = function() {
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
        latitude: "",
        longitude: "",
        link_audio: '',
        is_ie: false
      };
    };

    Message.prototype.validators = {
      type: new App.Util.Validate.string({
        len: {
          min: 1,
          max: 100
        }
      }),
      message: new App.Util.Validate.string({
        len: {
          min: 1,
          max: 1000
        }
      })
    };

    Message.prototype.validate = function(attrs) {
      var errors, hasError;
      hasError = false;
      errors = {};
      if (_.isEmpty(attrs.message)) {
        hasError = true;
        errors.message = "Missing message.";
      }
      if (hasError) {
        return errors;
      }
    };

    return Message;

  })(Backbone.Model);

  App.SOSBeacon.Collection.MessageList = (function(_super) {
    __extends(MessageList, _super);

    function MessageList() {
      _ref1 = MessageList.__super__.constructor.apply(this, arguments);
      return _ref1;
    }

    MessageList.prototype.model = App.SOSBeacon.Model.Message;

    MessageList.prototype.paginator_core = {
      type: 'GET',
      dataType: 'json',
      url: '/service/message'
    };

    MessageList.prototype.paginator_ui = {
      firstPage: 0,
      currentPage: 0,
      perPage: 100,
      totalPages: 100
    };

    MessageList.prototype.query_defaults = {
      orderBy: 'modified',
      orderDirection: 'desc'
    };

    MessageList.prototype.server_api = {};

    return MessageList;

  })(Backbone.Paginator.requestPager);

  App.SOSBeacon.View.EditMessage = (function(_super) {
    __extends(EditMessage, _super);

    function EditMessage() {
      this.saveComment = __bind(this.saveComment, this);
      this.hide = __bind(this.hide, this);
      this.renderMessages = __bind(this.renderMessages, this);
      this.renderTotalComment = __bind(this.renderTotalComment, this);
      this.render = __bind(this.render, this);
      this.initialize = __bind(this.initialize, this);
      _ref2 = EditMessage.__super__.constructor.apply(this, arguments);
      return _ref2;
    }

    EditMessage.prototype.template = JST['event-center/add-message'];

    EditMessage.prototype.id = "add-message-area";

    EditMessage.prototype.events = {
      "click .event-submit-comment": "saveComment",
      "click .event-cancel-comment": "hide"
    };

    EditMessage.prototype.initialize = function(options) {
      this.event = options.event;
      if (options.message != null) {
        return this.message = options.message;
      } else {
        return this.message = new App.SOSBeacon.Model.Message({
          message: {
            message: ''
          }
        });
      }
    };

    EditMessage.prototype.render = function() {
      this.$el.html(this.template(this.message.toJSON()));
      try {
        this.$("textarea#add-message-box").wysihtml5({
          "image": false,
          "audio": false,
          'link': false
        });
      } catch (_error) {}
      return this;
    };

    EditMessage.prototype.renderTotalComment = function() {
      var total_comment;
      this.event.fetch({
        async: false
      });
      total_comment = parseInt($(".total_comment").attr('data')) + 1;
      $(".total_comment").text(total_comment + " comments");
      return $(".total_comment").attr('data', total_comment);
    };

    EditMessage.prototype.renderMessages = function() {
      var _this = this;
      this.collection = new App.SOSBeacon.Collection.MessageList();
      _.extend(this.collection.server_api, {
        'feq_event': this.event.id,
        'orderBy': 'timestamp',
        'orderDirection': 'desc'
      });
      $("#view-message-area").remove();
      $("#event-center-message").append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 45%" class="image">');
      this.collection.fetch({
        success: function() {
          return $('.image').css('display', 'none');
        },
        error: function() {
          return window.location = '/school';
        }
      });
      this.messageListView = new App.SOSBeacon.View.MessageList(this.collection, false);
      return $("#event-center-message").append(this.messageListView.render().el);
    };

    EditMessage.prototype.hide = function() {
      return this.$el.html('');
    };

    EditMessage.prototype.saveComment = function() {
      var _this = this;
      this.collection = new App.SOSBeacon.Collection.MessageList();
      if (this.$('textarea#add-message-box').val()) {
        this.message.save({
          message: {
            body: this.$('textarea#add-message-box').val()
          },
          type: 'c',
          event: this.event.id,
          is_admin: true,
          user_name: "" + current_user
        }, {
          success: function(xhr) {
            return _this.renderTotalComment();
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.message, this);
        return this.hide();
      } else {
        return alert("Please insert message body!");
      }
    };

    return EditMessage;

  })(Backbone.View);

  App.SOSBeacon.View.AddBroadcast = (function(_super) {
    __extends(AddBroadcast, _super);

    function AddBroadcast() {
      this.smsUpdated = __bind(this.smsUpdated, this);
      this.saveBroadcast = __bind(this.saveBroadcast, this);
      this.hide = __bind(this.hide, this);
      this.handerError = __bind(this.handerError, this);
      this.mapLocation = __bind(this.mapLocation, this);
      this.searchResult = __bind(this.searchResult, this);
      this.searchAddress = __bind(this.searchAddress, this);
      this.submitLocation = __bind(this.submitLocation, this);
      this.renderGoogleMap = __bind(this.renderGoogleMap, this);
      this.renderMessages = __bind(this.renderMessages, this);
      this.render = __bind(this.render, this);
      this.initialize = __bind(this.initialize, this);
      _ref3 = AddBroadcast.__super__.constructor.apply(this, arguments);
      return _ref3;
    }

    AddBroadcast.prototype.template = JST['event-center/add-broadcast'];

    AddBroadcast.prototype.id = "add-message-area";

    AddBroadcast.prototype.position = null;

    AddBroadcast.prototype.events = {
      "click .event-submit-broadcast": "saveBroadcast",
      "click .event-cancel-broadcast": "hide",
      "keyup textarea#add-sms-box": "smsUpdated",
      "click button#google_map": "renderGoogleMap"
    };

    AddBroadcast.prototype.initialize = function(options) {
      this.event = options.event;
      this.position = {
        'latitude': '',
        'longitude': ''
      };
      return this.model = new App.SOSBeacon.Model.Message();
    };

    AddBroadcast.prototype.render = function() {
      this.$el.html(this.template());
      try {
        this.$("textarea#add-email-box").wysihtml5({
          "uploadUrl": "/uploads/new"
        });
      } catch (_error) {}
      return this;
    };

    AddBroadcast.prototype.renderMessages = function() {
      var _this = this;
      this.collection = new App.SOSBeacon.Collection.MessageList();
      _.extend(this.collection.server_api, {
        'feq_event': this.event.id,
        'orderBy': 'timestamp'
      });
      $("#view-message-area").remove();
      $("#event-center-message").append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 45%" class="image">');
      this.collection.fetch({
        success: function() {
          return $('.image').css('display', 'none');
        },
        error: function() {
          return window.location = '/school';
        }
      });
      this.messageListView = new App.SOSBeacon.View.MessageList(this.collection, false, this.event.id);
      return $("#event-center-message").append(this.messageListView.render().el);
    };

    AddBroadcast.prototype.renderGoogleMap = function() {
      var el, support;
      this.google_edit = new App.SOSBeacon.View.GoogleEdit();
      App.Skel.Event.bind('submitLocation', this.submitLocation, this);
      App.Skel.Event.bind('search_address', this.searchAddress, this);
      el = this.google_edit.render(true).$el;
      el.modal('show');
      if ($.browser.msie) {
        if ($.browser.version === 8) {
          alert("Your browser not support get location. Please input your address or zipcode, then press SEARCH.");
          this.mapLocation(null);
          return this;
        }
      }
      support = window.navigator.geolocation.getCurrentPosition(this.mapLocation, this.handerError);
      if (support === null) {
        return this.mapLocation(null);
      }
    };

    AddBroadcast.prototype.submitLocation = function() {
      this.position.latitude = this.marker.getPosition().lat();
      return this.position.longitude = this.marker.getPosition().lng();
    };

    AddBroadcast.prototype.searchAddress = function(address) {
      var geocoder;
      if (!address) {
        return;
      }
      geocoder = new google.maps.Geocoder();
      return geocoder.geocode({
        'address': address
      }, this.searchResult);
    };

    AddBroadcast.prototype.searchResult = function(results, status) {
      if (status === google.maps.GeocoderStatus.OK) {
        this.map.setCenter(results[0].geometry.location);
        return this.marker.setPosition(results[0].geometry.location);
      } else {
        return alert('Incorrect location');
      }
    };

    AddBroadcast.prototype.mapLocation = function(position) {
      var lat, long;
      lat = 21.0;
      long = 105.0;
      if (this.position.latitude !== '' && this.position.longitude !== '') {
        lat = this.position.latitude;
        long = this.position.longitude;
      } else if (position !== null) {
        lat = position.coords.latitude;
        long = position.coords.longitude;
      }
      this.opt = {
        center: new google.maps.LatLng(lat, long),
        zoom: 12,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      this.map = new google.maps.Map(document.getElementById('mapCanvasView'), this.opt);
      return this.marker = new google.maps.Marker({
        position: new google.maps.LatLng(lat, long),
        map: this.map,
        draggable: true
      });
    };

    AddBroadcast.prototype.handerError = function(error) {
      this.position = {
        'latitude': '',
        'longitude': ''
      };
      return alert('Geolocation is not supported in this browser!');
    };

    AddBroadcast.prototype.hide = function() {
      return this.$el.html('');
    };

    AddBroadcast.prototype.saveBroadcast = function() {
      var path_to_audio,
        _this = this;
      path_to_audio = '';
      if ($("textarea#add-sms-box").attr("data")) {
        path_to_audio = $("textarea#add-sms-box").attr("data");
      }
      if (this.$('textarea#add-sms-box').val()) {
        if (!confirm("Are you sure you want to send this group broadcast?")) {
          return false;
        }
        this.model.save({
          message: {
            sms: this.$('textarea#add-sms-box').val(),
            email: this.$('textarea#add-email-box').val()
          },
          user_name: "" + current_user,
          type: 'b',
          event: this.event.id,
          latitude: "" + this.position.latitude,
          longitude: "" + this.position.longitude,
          is_admin: true,
          link_audio: path_to_audio
        }, {
          success: function(xhr) {
            return console.log("ngon");
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.model, this);
        return this.hide();
      } else {
        return alert("Please insert SMS Message!");
      }
    };

    AddBroadcast.prototype.smsUpdated = function() {
      var cutString, maxSMS, remaining, smsMessage, textSMS;
      smsMessage = this.$('textarea#add-sms-box').val();
      textSMS = "Preview SMS: Broadcast from " + current_user + " (" + current_school + "). Link http://8.sos-beacon-dev.appspot.com/xxx/xxx";
      maxSMS = 140 - textSMS.length;
      remaining = 140 - smsMessage.length - textSMS.length;
      if (remaining <= 0) {
        remaining = 0;
      }
      this.$('span.sms-remain').text(textSMS + (" " + smsMessage + " (" + remaining + " characters remaining)"));
      if (smsMessage.length >= maxSMS) {
        cutString = smsMessage.substr(0, maxSMS);
        this.$('textarea#add-sms-box').val(cutString);
        return this.$('span.sms-remain').text(textSMS + (" " + cutString + " (" + remaining + " characters remaining)"));
      }
    };

    return AddBroadcast;

  })(Backbone.View);

  App.SOSBeacon.View.AddEmergency = (function(_super) {
    __extends(AddEmergency, _super);

    function AddEmergency() {
      this.smsUpdated = __bind(this.smsUpdated, this);
      this.saveEmergency = __bind(this.saveEmergency, this);
      _ref4 = AddEmergency.__super__.constructor.apply(this, arguments);
      return _ref4;
    }

    AddEmergency.prototype.template = JST['event-center/add-emergency'];

    AddEmergency.prototype.id = "add-message-area";

    AddEmergency.prototype.position = null;

    AddEmergency.prototype.events = {
      "click .event-submit-broadcast": "saveEmergency",
      "click .event-cancel-broadcast": "hide",
      "keyup textarea#add-sms-box": "smsUpdated",
      "click button#google_map": "renderGoogleMap"
    };

    AddEmergency.prototype.saveEmergency = function() {
      var path_to_audio,
        _this = this;
      path_to_audio = '';
      if ($("textarea#add-sms-box").attr("data")) {
        path_to_audio = $("textarea#add-sms-box").attr("data");
      }
      if (this.$('textarea#add-sms-box').val()) {
        if (!confirm("Are you sure you want to send this group broadcast?")) {
          return false;
        }
        this.model.save({
          message: {
            sms: this.$('textarea#add-sms-box').val(),
            email: this.$('textarea#add-email-box').val()
          },
          user_name: "" + current_user,
          type: 'em',
          event: this.event.id,
          latitude: "" + this.position.latitude,
          longitude: "" + this.position.longitude,
          is_admin: true,
          link_audio: path_to_audio
        }, {
          success: function(xhr) {
            return console.log("emergency");
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.model, this);
        return this.hide();
      } else {
        return alert("Please insert SMS Message!");
      }
    };

    AddEmergency.prototype.smsUpdated = function() {
      var cutString, maxSMS, remaining, smsMessage, textSMS;
      smsMessage = this.$('textarea#add-sms-box').val();
      textSMS = "Preview SMS: Broadcast from " + current_user + " (" + current_school + "). Link http://8.sos-beacon-dev.appspot.com/xxx/xxx";
      maxSMS = 140 - textSMS.length;
      remaining = 140 - smsMessage.length - textSMS.length;
      if (remaining <= 0) {
        remaining = 0;
      }
      this.$('span.sms-remain').text(textSMS + (" " + smsMessage + " (" + remaining + " characters remaining)"));
      if (smsMessage.length >= maxSMS) {
        cutString = smsMessage.substr(0, maxSMS);
        this.$('textarea#add-sms-box').val(cutString);
        return this.$('span.sms-remain').text(textSMS + (" " + cutString + " (" + remaining + " characters remaining)"));
      }
    };

    return AddEmergency;

  })(App.SOSBeacon.View.AddBroadcast);

  App.SOSBeacon.View.AddCall = (function(_super) {
    __extends(AddCall, _super);

    function AddCall() {
      this.saveCall = __bind(this.saveCall, this);
      this.render = __bind(this.render, this);
      _ref5 = AddCall.__super__.constructor.apply(this, arguments);
      return _ref5;
    }

    AddCall.prototype.template = JST['event-center/add-call'];

    AddCall.prototype.id = "add-message-area";

    AddCall.prototype.position = null;

    AddCall.prototype.events = {
      "click .event-submit-broadcast": "saveCall",
      "click .event-cancel-broadcast": "hide",
      "click button#google_map": "renderGoogleMap"
    };

    AddCall.prototype.render = function() {
      this.$el.html(this.template());
      try {
        this.$("textarea#add-sms-box").wysihtml5({
          "uploadUrl": "/uploads/new"
        });
      } catch (_error) {}
      return this;
    };

    AddCall.prototype.saveCall = function() {
      var path_to_audio,
        _this = this;
      path_to_audio = '';
      if ($("textarea#add-sms-box").attr("data")) {
        path_to_audio = $("textarea#add-sms-box").attr("data");
      }
      if (this.$('textarea#add-sms-box').val()) {
        if (!confirm("Are you sure you want to send this group broadcast?")) {
          return false;
        }
        this.model.save({
          message: {
            sms: '',
            email: this.$('textarea#add-sms-box').val()
          },
          user_name: "" + current_user,
          type: 'ec',
          event: this.event.id,
          latitude: "" + this.position.latitude,
          longitude: "" + this.position.longitude,
          is_admin: true,
          link_audio: path_to_audio
        }, {
          success: function(xhr) {
            return console.log("call");
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.model, this);
        return this.hide();
      } else {
        return alert("Please insert body email!");
      }
    };

    return AddCall;

  })(App.SOSBeacon.View.AddBroadcast);

  App.SOSBeacon.View.AddEmail = (function(_super) {
    __extends(AddEmail, _super);

    function AddEmail() {
      this.saveEmail = __bind(this.saveEmail, this);
      this.render = __bind(this.render, this);
      _ref6 = AddEmail.__super__.constructor.apply(this, arguments);
      return _ref6;
    }

    AddEmail.prototype.template = JST['event-center/add-email'];

    AddEmail.prototype.id = "add-message-area";

    AddEmail.prototype.position = null;

    AddEmail.prototype.events = {
      "click .event-submit-broadcast": "saveEmail",
      "click .event-cancel-broadcast": "hide",
      "click button#google_map": "renderGoogleMap"
    };

    AddEmail.prototype.render = function() {
      this.$el.html(this.template());
      try {
        this.$("textarea#add-sms-box").wysihtml5({
          "uploadUrl": "/uploads/new"
        });
      } catch (_error) {}
      return this;
    };

    AddEmail.prototype.saveEmail = function() {
      var path_to_audio,
        _this = this;
      path_to_audio = '';
      if ($("textarea#add-sms-box").attr("data")) {
        path_to_audio = $("textarea#add-sms-box").attr("data");
      }
      if (this.$('textarea#add-sms-box').val()) {
        if (!confirm("Are you sure you want to send this group broadcast?")) {
          return false;
        }
        this.model.save({
          message: {
            sms: '',
            email: this.$('textarea#add-sms-box').val()
          },
          user_name: "" + current_user,
          type: 'eo',
          event: this.event.id,
          latitude: "" + this.position.latitude,
          longitude: "" + this.position.longitude,
          is_admin: true,
          link_audio: path_to_audio
        }, {
          success: function(xhr) {
            return console.log("email");
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.model, this);
        return this.hide();
      } else {
        return alert("Please insert body email!");
      }
    };

    return AddEmail;

  })(App.SOSBeacon.View.AddBroadcast);

  App.SOSBeacon.View.MessageList = (function(_super) {
    __extends(MessageList, _super);

    function MessageList() {
      this.reset = __bind(this.reset, this);
      this.addAll = __bind(this.addAll, this);
      this.insertOne = __bind(this.insertOne, this);
      this.addOne = __bind(this.addOne, this);
      this.render = __bind(this.render, this);
      this.initialize = __bind(this.initialize, this);
      _ref7 = MessageList.__super__.constructor.apply(this, arguments);
      return _ref7;
    }

    MessageList.prototype.id = "view-message-area";

    MessageList.prototype.initialize = function(option) {
      this.collection = option.collection;
      this.collection.bind('add', this.insertOne, this);
      this.collection.bind('reset', this.reset, this);
      return this.collection.bind('all', this.show, this);
    };

    MessageList.prototype.render = function() {
      console.log(this.collection);
      return this;
    };

    MessageList.prototype.addOne = function(object) {
      var item, view;
      view = new App.SOSBeacon.View.MessageListItem({
        model: object
      });
      item = view.render().el;
      if (this.hideButtons) {
        $(item).find('.message-item-buttons').css('display', 'none');
      }
      return this.$el.append(item);
    };

    MessageList.prototype.insertOne = function(object) {
      var view;
      view = new App.SOSBeacon.View.MessageListItem({
        model: object
      });
      return this.$el.prepend(view.render().el);
    };

    MessageList.prototype.addAll = function() {
      return this.collection.each(this.addOne);
    };

    MessageList.prototype.reset = function() {
      console.log("rest phat nao");
      this.$el.html('');
      return this.addAll();
    };

    return MessageList;

  })(Backbone.View);

  App.SOSBeacon.View.MessageListItem = (function(_super) {
    __extends(MessageListItem, _super);

    function MessageListItem() {
      this.removeMessage = __bind(this.removeMessage, this);
      this.replyMessage = __bind(this.replyMessage, this);
      this.renderMap = __bind(this.renderMap, this);
      this.render = __bind(this.render, this);
      this.stripAudioTag = __bind(this.stripAudioTag, this);
      this.loadReplyMessage = __bind(this.loadReplyMessage, this);
      this.initialize = __bind(this.initialize, this);
      _ref8 = MessageListItem.__super__.constructor.apply(this, arguments);
      return _ref8;
    }

    MessageListItem.prototype.template = JST['event-center/message-list-item'];

    MessageListItem.prototype.className = "view-message-item";

    MessageListItem.prototype.events = {
      "click #message-item-button-remove": "removeMessage",
      "mouseover .message-content": "replyMessage"
    };

    MessageListItem.prototype.initialize = function() {
      this.model.bind('change', this.render, this);
      return this.model.bind('destroy', this.remove, this);
    };

    MessageListItem.prototype.loadReplyMessage = function(model) {
      var myTextField,
        _this = this;
      this.replyList = new App.SOSBeacon.Collection.ReplyMessageList();
      _.extend(this.replyList.server_api, {
        'feq_message': model.id,
        'limit': 1,
        'orderBy': 'added',
        'orderDirection': 'desc'
      });
      this.replyList.fetch({
        async: false
      });
      myTextField = document.getElementById(model.id);
      if (myTextField) {
        this.replyList.each(function(reply, i) {
          return myTextField.innerHTML = reply.get('content');
        });
        return false;
      }
      return this.replyList.each(function(reply, i) {
        return _this.$('.message-content div').html($("<div></div>").attr('value', reply.get('key')).attr('id', reply.get('message')).html(reply.get('content')).css('padding-left', '5px'));
      });
    };

    MessageListItem.prototype.stripAudioTag = function(text) {
      var partern;
      console.log(text);
      partern = /<embed[^>]+>/g;
      return text.replace(partern, '');
    };

    MessageListItem.prototype.render = function() {
      var audio, audioPlayer, key, lat, long, message,
        _this = this;
      if ((/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)) || $.browser.msie) {
        message = this.model.get('message');
        if (message['email']) {
          message['email'] = this.stripAudioTag(message['email']);
          this.model.set('message', message);
        }
      }
      this.$el.html(this.template(this.model.toJSON()));
      this.reply = new App.SOSBeacon.Model.ReplyMessage();
      this.reply_view = new App.SOSBeacon.View.ReplyMessageEdit(this.reply, this.model.id, this.model.get("event"));
      if (this.model.get('type') === 'c') {
        this.$('#message-item-button-remove').css('display', 'block');
      }
      if (this.model.id) {
        this.loadReplyMessage(this.model);
      }
      if (this.model.get('link_audio')) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)) {
          audioPlayer = new Audio();
          audioPlayer.controls = "controls";
          audioPlayer.src = this.model.get('link_audio');
          audioPlayer.id = "audio-1";
          this.$('.message-broadcast').append(audioPlayer);
        } else {
          audio = document.createElement("EMBED");
          audio.setAttribute('height', '28');
          audio.setAttribute('width', '348px');
          audio.setAttribute('bgcolor', '#000000');
          audio.setAttribute('tabindex', '0');
          audio.setAttribute('class', 'audio_insert');
          audio.setAttribute('type', 'application/x-shockwave-flash');
          audio.setAttribute('src', 'http://www.google.com/reader/ui/3523697345-audio-player.swf');
          audio.setAttribute('flashvars', 'audioUrl=' + this.model.get("link_audio"));
          audio.setAttribute('quality', 'best');
          this.$('.message-broadcast').append(audio);
        }
      }
      key = this.model.get('key');
      lat = this.model.get('latitude');
      long = this.model.get('longitude');
      if (lat.length === 0 && long.length === 0) {
        return this;
      }
      setTimeout((function() {
        $('#mapCanvasView' + key).attr('style', 'width: 100% !important; height: 150px; margin-top: 15px;margin-bottom: 15px;display: block;');
        return _this.renderMap(key, lat, long);
      }), 500);
      return this;
    };

    MessageListItem.prototype.renderMap = function(key, lat, long) {
      var map;
      this.opt = {
        center: new google.maps.LatLng(lat, long),
        zoom: 12,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      map = new google.maps.Map(document.getElementById('mapCanvasView' + key), this.opt);
      return new google.maps.Marker({
        position: new google.maps.LatLng(lat, long),
        map: map
      });
    };

    MessageListItem.prototype.replyMessage = function() {
      if (this.$('div div.fQuickReply').length > 0) {
        return false;
      }
      $('.fQuickReply').remove();
      $(this.el).append(this.reply_view.render().el);
      return $(".tbQuickReply").focus();
    };

    MessageListItem.prototype.removeMessage = function() {
      var proceed, total_comment;
      proceed = confirm('Are you sure you want to delete?  This cannot be undone.');
      if (proceed) {
        this.model.destroy();
      }
      total_comment = parseInt($(".total_comment").attr('data')) - 1;
      $(".total_comment").text(total_comment + " comments");
      return $(".total_comment").attr('data', total_comment);
    };

    return MessageListItem;

  })(Backbone.View);

  App.SOSBeacon.Model.MessageType = (function(_super) {
    __extends(MessageType, _super);

    function MessageType() {
      _ref9 = MessageType.__super__.constructor.apply(this, arguments);
      return _ref9;
    }

    MessageType.prototype.idAttribute = 'type';

    MessageType.prototype.defaults = function() {
      return {
        label: "",
        type: ''
      };
    };

    return MessageType;

  })(Backbone.Model);

  App.SOSBeacon.Collection.MessageType = (function(_super) {
    __extends(MessageType, _super);

    function MessageType() {
      _ref10 = MessageType.__super__.constructor.apply(this, arguments);
      return _ref10;
    }

    MessageType.prototype.model = App.SOSBeacon.Model.MessageType;

    return MessageType;

  })(Backbone.Collection);

  App.SOSBeacon.eventTypes = new App.SOSBeacon.Collection.MessageType([
    {
      type: 'c',
      label: "Comment"
    }, {
      type: 'b',
      label: "Broadcast"
    }
  ]);

  App.SOSBeacon.View.NewMessageListItem = (function(_super) {
    __extends(NewMessageListItem, _super);

    function NewMessageListItem() {
      this.removeMessage = __bind(this.removeMessage, this);
      this.render = __bind(this.render, this);
      _ref11 = NewMessageListItem.__super__.constructor.apply(this, arguments);
      return _ref11;
    }

    NewMessageListItem.prototype.template = JST['event-center/student-message-list-item'];

    NewMessageListItem.prototype.render = function() {
      var audioPlayer, key, lat, long, source,
        _this = this;
      this.$el.html(this.template(this.model.toJSON()));
      if (this.model.id) {
        this.loadReplyMessage(this.model);
      }
      if (/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)) {
        if (this.model.get('link_audio')) {
          audioPlayer = new Audio();
          audioPlayer.controls = "controls";
          source = document.createElement('source');
          source.setAttribute('src', this.model.get('link_audio'));
          source.setAttribute('type', 'audio/mpeg');
          audioPlayer.appendChild(source);
          this.$('.message-broadcast').append(audioPlayer);
        }
      }
      key = this.model.get('key');
      lat = this.model.get('latitude');
      long = this.model.get('longitude');
      if (lat.length === 0 && long.length === 0) {
        return this;
      }
      setTimeout((function() {
        $('#mapCanvasView' + key).attr('style', 'width: 60% !important; height: 250px; margin: 15px auto;display: block;');
        return _this.renderMap(key, lat, long);
      }), 500);
      return this;
    };

    NewMessageListItem.prototype.removeMessage = function() {
      var proceed, total_comment;
      proceed = confirm('Are you sure you want to delete?  This cannot be undone.');
      if (proceed) {
        this.model.destroy();
      }
      total_comment = parseInt($(".total_comment").attr('data')) - 1;
      $(".total_comment").text(total_comment + " comments");
      return $(".total_comment").attr('data', total_comment);
    };

    return NewMessageListItem;

  })(App.SOSBeacon.View.MessageListItem);

  App.SOSBeacon.View.MessageListApp = (function(_super) {
    __extends(MessageListApp, _super);

    function MessageListApp() {
      this.reset = __bind(this.reset, this);
      this.addAll = __bind(this.addAll, this);
      this.insertOne = __bind(this.insertOne, this);
      this.addOne = __bind(this.addOne, this);
      this.saveComment = __bind(this.saveComment, this);
      this.renderTotalComment = __bind(this.renderTotalComment, this);
      this.renderTotalComments = __bind(this.renderTotalComments, this);
      this.render = __bind(this.render, this);
      this.renderMessages = __bind(this.renderMessages, this);
      this.renderMS = __bind(this.renderMS, this);
      this.initialize = __bind(this.initialize, this);
      _ref12 = MessageListApp.__super__.constructor.apply(this, arguments);
      return _ref12;
    }

    MessageListApp.prototype.id = "view-message-areas";

    MessageListApp.prototype.template = JST['event-center/event-messages'];

    MessageListApp.prototype.events = {
      'click .event-submit-comment': 'saveComment'
    };

    MessageListApp.prototype.initialize = function(id, contact_name, hideButtons) {
      var interval, _i,
        _this = this;
      this.contact_name = contact_name;
      this.hideButtons = hideButtons;
      this.collection = new App.SOSBeacon.Collection.MessageList();
      this.eventId = id;
      interval = 0;
      for (interval = _i = 0; _i < 1000; interval = ++_i) {
        clearInterval(interval);
        interval++;
      }
      return interval = setInterval((function() {
        _this.collection.fetch({
          async: false
        });
        return _this.renderTotalComments();
      }), 30000);
    };

    MessageListApp.prototype.renderMS = function() {
      var messageList,
        _this = this;
      _.extend(this.collection.server_api, {
        'feq_event': this.eventId,
        'orderBy': 'timestamp',
        'orderDirection': 'desc'
      });
      $("#event-messages").empty();
      $("#event-messages").append('<img src="/static/img/spinner_squares_circle.gif" style="display: block; margin-left: 45%" class="image">');
      this.collection.fetch({
        success: function() {
          return $('.image').css('display', 'none');
        },
        error: function() {
          return window.location = '/school';
        }
      });
      messageList = new App.SOSBeacon.View.MessageListApp(this.eventId, this.contact_name, false);
      return $("#event-messages").append(messageList.render().$el);
    };

    MessageListApp.prototype.renderMessages = function() {
      _.extend(this.collection.server_api, {
        'feq_event': this.eventId,
        'orderBy': 'timestamp',
        'orderDirection': 'asc',
        'limit': 200
      });
      this.collection.bind('reset', this.reset, this);
      return this.collection.fetch({
        async: false
      });
    };

    MessageListApp.prototype.render = function() {
      this.event = new App.SOSBeacon.Model.Event({
        key: this.eventId
      });
      this.event.fetch({
        async: false
      });
      this.total = {};
      this.total['total_comment'] = this.event.get('total_comment');
      this.total['contact_name'] = this.contact_name;
      this.$el.html(this.template(this.total));
      this.collection = new App.SOSBeacon.Collection.MessageList();
      _.extend(this.collection.server_api, {
        'feq_event': this.eventId,
        'orderBy': 'timestamp',
        'orderDirection': 'asc',
        'limit': 200
      });
      this.collection.fetch();
      this.collection.bind('add', this.insertOne, this);
      this.collection.bind('reset', this.reset, this);
      this.collection.bind('all', this.show, this);
      return this;
    };

    MessageListApp.prototype.renderTotalComments = function() {
      var total_comment;
      this.event.fetch({
        async: false
      });
      total_comment = this.event.get('total_comment');
      return $('.total_comment').text(total_comment + " comments");
    };

    MessageListApp.prototype.renderTotalComment = function() {
      var total_comment;
      total_comment = parseInt($(".total_comment").attr('data')) + 1;
      $(".total_comment").text(total_comment + " comments");
      return $(".total_comment").attr('data', total_comment);
    };

    MessageListApp.prototype.saveComment = function() {
      var model,
        _this = this;
      console.log($(".total_comment").val());
      model = new App.SOSBeacon.Model.Message();
      if (this.$('.add-message-box-area').find('.guest').attr('readonly')) {
        model.save({
          message: {
            body: this.$('textarea#add-message-box').val()
          },
          type: 'c',
          event: this.eventId,
          is_admin: false,
          is_student: true
        }, {
          success: function(data) {
            var button, input;
            _this.renderTotalComment();
            button = '<textarea id="add-message-box" class="span9"></textarea>';
            input = '<input type="text" name="user_name" class="guest" readonly="" value="">';
            _this.$('.add-message-box-area').html(button);
            _this.$('.add-message-box-area').append(input);
            _this.$('.add-message-box-area').find('input').val(data.get('user_name'));
            return $('#add-message-box').focus();
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.message, this);
      } else {
        model.save({
          message: {
            body: this.$('textarea#add-message-box').val()
          },
          type: 'c',
          event: this.eventId,
          is_admin: false,
          is_student: false,
          user_name: this.$('.add-message-box-area').find('.guest').val()
        }, {
          success: function(data) {
            var button, input;
            _this.renderTotalComment();
            button = '<textarea id="add-message-box" class="span9"></textarea>';
            input = '<input type="text" name="user_name" class="guest" value="">';
            _this.$('.add-message-box-area').html(button);
            _this.$('.add-message-box-area').append(input);
            _this.$('.add-message-box-area').find('input').val("Guest");
            try {
              _this.$("textarea#add-message-box").wysihtml5({
                "image": false,
                "audio": false,
                'link': false
              });
            } catch (_error) {}
            return $('#add-message-box').focus();
          }
        });
        App.SOSBeacon.Event.trigger("message:add", this.message, this);
      }
      return this.addOne(model);
    };

    MessageListApp.prototype.addOne = function(object) {
      var item, view;
      view = new App.SOSBeacon.View.NewMessageListItem({
        model: object
      });
      item = view.render().el;
      if (this.hideButtons) {
        $(item).find('.message-item-buttons').css('display', 'none');
      }
      return this.$('#event-message-list').append(item);
    };

    MessageListApp.prototype.insertOne = function(object) {
      var view;
      view = new App.SOSBeacon.View.NewMessageListItem({
        model: object
      });
      return this.$el.prepend(view.render().el);
    };

    MessageListApp.prototype.addAll = function() {
      return this.collection.each(this.addOne);
    };

    MessageListApp.prototype.reset = function() {
      this.$("#event-message-list").html('');
      return this.addAll();
    };

    return MessageListApp;

  })(Backbone.View);

}).call(this);
