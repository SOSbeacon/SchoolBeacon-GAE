<%inherit file="base.mako"/>

<div id="sosbeaconcontainer" class="container public-event-details">
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
        <div class="row-fluid event-messages-container">
            <h2>Messages</h2>
            <div id="event-messages">
            </div> 
        </div>
    </div>
</div>

<%block name="title">${event.title} - ${parent.title()}</%block>

<%block name="body_script">

<script type="application/javascript" src="/static/script/skel.js"></script>
<script type="application/javascript" src="/static/script/template.js"></script>
<script type="application/javascript" src="/static/script/sosbeacon.js"></script>

<script type="text/javascript">
    $(function(){
        var messageList = new App.SOSBeacon.View.MessageListApp(
            '${event.key.urlsafe()}', true);
        $("#event-messages").append(messageList.render().$el);
    });
</script>

</%block>

