
<%inherit file="base.mako"/>
<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container">
      <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="brand" href="/">SBeacon Administration</a>
      <div id="sosbeaconheader" class="nav-collapse">
        <ul id="sosbeacon-menu" class="nav"></ul>
      </div>
    </div>
  </div>
</div>

<div id="sosbeacon">
  <div id="sosadmincontainer" class="container"></div>
</div>

<%block name="body_script">
  <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
  <script type="application/javascript" src="/static/script/sosadmin.js"></script>
  <script type="text/javascript">
    $(function() {
        var sosadmin = new App.SOSAdmin.Router
        Backbone.history.start();
        App.SOSAdmin.router = sosadmin;
      });
  </script>
</%block>

