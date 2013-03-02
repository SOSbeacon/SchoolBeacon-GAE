<%inherit file="base.mako"/>

<div id="sosbeaconcontainer" class="container public-event-details">
    <div class="row-fluid header">
        <div class="span2"><a href="http://sosbeacon.com" id="logo"></a></div>
        <div class="span10">
            <h3>School Beacon</h3> A non-profit corporation dedicated to safety and security.
        </div>
    </div>
    <div class="row-fluid">
        <div class="span2">
            <select onload="alert(this.value);" id="change_timezone" onchange="change_timezone(this.value)">
                <option selected="selected" value="-10">America/San Francisco</option>
                <option value="-9">America/Denver</option>
                <option value="-8">America/Chicago</option>
                <option value="-7">America/New York</option>
                <option value="-2">America/Rio De Janeiro</option>
                <option value="0">Atlantic/Reykjavik</option>
                <option value="0">Europe/London</option>
                <option value="1">Europe/Zurich</option>
                <option value="2">Europe/Athens</option>
                <option value="4">Europe/Moscow</option>
                <option value="6">Asia/New Delhi</option>
                <option value="7">Asia/Ho Chi Minh</option>
                <option value="8">Asia/Hong Kong</option>
                <option value="9">Asia/Tokyo</option>
                <option value="10">Pacific/Guam</option>
                <option value="14">Pacific/Honolulu</option>
                <option value="15">America/Anchorage</option>
            </select>
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
                <h2>Messages</h2>
                <div id="event-messages">
                </div>
            </div>
        </div>
    </div>

    <%block name="title">${event.title} - ${parent.title()}</%block>

    <%block name="body_script">
            <script type="text/javascript" src="https://maps.google.com/maps/api/js?sensor=false"></script>
            <script type="application/javascript" src="/static/script/sosbeacon.js"></script>

            <script type="text/javascript">
                var messageList = new App.SOSBeacon.View.MessageListApp(
                        '${event.key.urlsafe()}', false);
                messageList.setDefaultValue(10);
                $("#event-messages").append(messageList.render().$el);

                function change_timezone(value){
                    messageList.setDefaultValue(Number(value));
                    var els = $('.comment-meta');
                    els.each(function(index, el){
                        var timestring = el.getAttribute('initvalue');
                        var date = Date.parse(timestring);

                        date.setHours(date.getHours()+Number(value));
                        timestring = date.toString('yyyy-MM-dd hh:mm');

                        timestring = timestring.replace(/(ICT$)|(GMT\+0700 \(ICT\)$)/,'').replace(/^(\w+) /, "");
                        el.innerHTML = '- '+timestring+', wrote';
                    });
                }
                    % if contact_marker:
                        $(".add-message-box-area").append('<input type="text" class="guest" name="user_name" readonly="" value=${contact_name}>');
                    %else:
                        $(".add-message-box-area").append('<input type="text" class="guest" name="user_name" value="Guest">');
                    % endif
            </script>

    </%block>

</div>