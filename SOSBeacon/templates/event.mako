<%inherit file="base.mako"/>

<div id="sosbeaconcontainer" class="container">
  <div class="row-fluid header">
    <div class="span2"><a href="http://sosbeacon.com" id="logo"></a></div>
    <div class="span10">
      <h3>SBeacon</h3> A non-profit corporation dedicated to safety and security.
    </div>
  </div>
  <div class="container-fluid">
    <div class="row-fluid">
      <div class="span1"><strong>Title:</strong></div>
      <div class="span11">${event.title}</div>
    </div>
    <div class="row-fluid">
      <div class="span1"><strong>Details:</strong></div>
      <div class="span11">${event.detail}</div>
    </div>
  </div>
</div>

<%block name="title">${event.title} - ${parent.title()}</%block>

<%block name="body_script"/>

