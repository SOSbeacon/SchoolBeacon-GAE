<%inherit file="base.mako"/>

<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container">
      <a class="brand" href="#">SOSBeacon</a>
      <div id="sosbeaconheader" class="nav-collapse">
        <ul id="sosbeacon-menu" class="nav">
        </ul>
      </div><!--/.nav-collapse -->
    </div>
  </div>
</div>
<div id="sosbeaconcontainer" class="container">
  <div id="sosbeaconapp"></div>
</div>

<%block name="body_script">
  <script type="application/javascript" src="/static/script/libs.js"></script>
  <script type="application/javascript" src="/static/script/template.js"></script>
  <script type="application/javascript" src="/static/script/skel.js"></script>
  <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
  <script type="text/javascript">
    $(function(){
        var sosbeacon = new App.SOSBeacon.Router
        Backbone.history.start();
        App.SOSBeacon.router = sosbeacon;
        });
  </script>
</%block>

