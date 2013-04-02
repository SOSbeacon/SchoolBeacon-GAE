<%inherit file="base.mako"/>

<div id="sosbeaconcontainer" class="container public-event-details">
    <span id="confirmDialogContent" style="display: none" title="Test dialog"></span>
    <div class="row-fluid header">
        <div class="span2"><a href="http://sosbeacon.com" id="logo"></a></div>
        <div class="span10">
            <h3>School Beacon</h3> A non-profit corporation dedicated to safety and security.<br />
            <div class="span5" style="margin: auto">
                <label style="float: left; margin-top: 13px;margin-right: 3%;">Timezone:</label>
                <select id="selectTimeZone" name="timezone" style="width: 60%; margin-top: 10px;">
                    <option  value="America/Los_Angeles">America/San Francisco</option>
                    <option  value="America/Denver">America/Denver</option>
                    <option  value="America/Chicago">America/Chicago</option>
                    <option  value="America/New_York">America/New York</option>
                    <option  value="America/Sao_Paulo">America/Rio De Janeiro</option>
                    <option  value="Atlantic/Reykjavik">Atlantic/Reykjavik</option>
                    <option  value="Europe/London">Europe/London</option>
                    <option  value="Europe/Zurich">Europe/Zurich</option>
                    <option  value="Europe/Athens">Europe/Athens</option>
                    <option  value="Europe/Moscow">Europe/Moscow</option>
                    <option  value="Asia/Calcutta">Asia/New Delhi</option>
                    <option  value="Asia/Ho_Chi_Minh">Asia/Ho Chi Minh</option>
                    <option  value="Asia/Hong_Kong">Asia/Hong Kong</option>
                    <option  value="Asia/Tokyo">Asia/Tokyo</option>
                    <option  value="Pacific/Guam">Pacific/Guam</option>
                    <option  value="Pacific/Honolulu">Pacific/Honolulu</option>
                    <option  value="America/Anchorage">America/Anchorage</option>
                </select>
            </div>
        </div>
    </div>
    <div class="row-fluid">
        <div class="span2">
        </div>
        <div class="span10">
            <div class="row-fluid">
                <div><h2>${event.title}</h2></div>
            </div>
            <br />
            <div class="row-fluid">
                <div>${event.content}</div>
            </div>
            <div class="row-fluid event-messages-container">
                <h2>Message Center</h2>
                <div id="event-messages">
                </div>
            </div>
        </div>
    </div>

    <%block name="title">${event.title} - ${parent.title()}</%block>

    <%block name="body_script">
            <link rel="stylesheet" href="http://code.jquery.com/ui/1.10.1/themes/base/jquery-ui.css" />

            <script type="text/javascript" src="https://maps.google.com/maps/api/js?sensor=false"></script>
            <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
            <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
            <script src="http://code.jquery.com/ui/1.10.1/jquery-ui.js"></script>

            <script type="text/javascript">
                var messageList = new App.SOSBeacon.View.MessageListApp(
                        '${event.key.urlsafe()}', false);
                $("#event-messages").append(messageList.render().$el);

##                function change_timezone(value){
##                    messageList.setDefaultValue(Number(value));
##                    var els = $('.comment-meta');
##                    els.each(function(index, el){
##                        var timestring = el.getAttribute('initvalue');
##                        var date = Date.parse(timestring);
##
##                        date.setHours(date.getHours()+Number(value));
##                        timestring = date.toString('yyyy-MM-dd hh:mm');
##
##                        timestring = timestring.replace(/(ICT$)|(GMT\+0700 \(ICT\)$)/,'').replace(/^(\w+) /, "");
##                        el.innerHTML = '- '+timestring+', wrote';
##                    });
##                }

                $('#selectTimeZone').change(function() {
                    var select = $("#selectTimeZone").val();

                    url = '/service/timezone/' + select;
                    $.ajax({
                        url: url,
                        type: "GET",
                        async: false,
                        success: function(data) {
                            var result;
                            return result = data;
                        }
                    });

                    location.reload();
                    return false
                });

                % if contact_marker:
                        $(".add-message-box-area").append('<input type="text" class="guest" name="user_name" readonly="" value="${contact_name}">');
                    %else:
                        $(".add-message-box-area").append('<input type="text" class="guest" name="user_name" value="Guest">');
                    % endif

                function setChatName() {
                    var chatName = '${contact_name}';
                    var chatId = '';
                    var isSentUrl = false; // only use if user open link as send url (format /r/cid/token)
                    if (chatName != '') {  // confirm name, and set to cookie
                        $confirmNameText = 'Are you ' + chatName + '?';
                        //if (!confirm($confirmNameText)) {
                        //    chatName = '';
                        //}
                        $('#confirmDialogContent').html($confirmNameText);
                        $('#confirmDialogContent').dialog({
                            title : 'School Beacon',
                            resizable: false,
                            height:150,
                            modal: true,
                            buttons: {
                                "Yes": function() {
                                    $(this).dialog( "close" );
                                    $('.guest').attr('readonly', 'readonly');
                                },
                                "No": function() {
                                    chatName = '';
                                    $('.guest').val('Enter your name');
                                    $('.guest').removeAttr('readonly');
                                    $(this).dialog( "close" );
                                }
                            }
                        });

                        //      $.cookie('sosbeacon_detect_username', chatName);
                    }
                    //}
                    if (chatName.length > 0) {
                        $('#rcvCId').val(chatId);
                        $('#noteFrom').val(chatName);
                    }
                }
                $(document).ready(function() {
                    setChatName();
                    var default_timezone = "${timezone}"
                    select = $("#selectTimeZone")
                    select.val(default_timezone)
                });
            </script>

    </%block>

</div>