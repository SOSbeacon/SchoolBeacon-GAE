<%inherit file="base.mako"/>

<div id="sosbeaconcontainer" class="container">
  <div class="row-fluid header">
    <div class="span2"><a href="http://sosbeacon.com" id="logo"></a></div>
    <div class="span10">
      <h3>SBeacon</h3> A non-profit corporation dedicated to safety and security.
    </div>
  </div>
  <div class="row-fluid">
      <div class="span2"></div>
    <div class="span10">
        <div class="row-fluid">
            <div><h2>${event.title}</h2></div>
        </div>
        <br />
        <div class="row-fluid">
            <div>${event.content}</div>
        </div>
        <br />
        <br />
        <br />
        <div class="row-fluid">
            <h2>Messages</h2>
            <br />
            <div id="event-messages">
            </div> 
        </div>
        <br />
        <br />
        <br />
    </div>
</div>

<%block name="title">${event.title} - ${parent.title()}</%block>

<%block name="body_script">

<script type="application/javascript" src="/static/script/skel.js"></script>

<script type="text/javascript">
    $(function(){
        function render(message) {
            template = "<div class='header row-fluid'>" +
                "A user - " + message.modified + ", wrote";
            if (message.type == "c") {
                template += "<div class='message-content'>" + message.message.body;
            } else {
                template += "<div class='message-broadcast'>" +
                    "<div class='broadcast-sms'>" +
                    "<h5>SMS:</h5>" + message.message.sms + "</div>" +
                    "<div class='broadcast-title'>" +
                    "<h5>Title:</h5>" + message.message.title + "</div>" +
                    "<div class='broadcast-email'>" +
                    "<h5>Email:</h5>" + message.message.email + "</div>";
            }
            template += "</div><br /><br />";

            return template;
        }
        $.ajax({
            type: "GET",
            url: "/service/message?feq_event=${event.key.urlsafe()}&orderBy=timestamp&orderDirection=desc",
            success: function(results){
                console.log(results);
                for (var i = 0; i < results.length; i++) {
                    $("#event-messages").append(render(results[i]));
                }
            },
            })

    });
</script>

</%block>

