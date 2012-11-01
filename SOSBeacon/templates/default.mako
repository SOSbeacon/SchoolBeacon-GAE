<%inherit file="base.mako"/>
<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container">
      <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="brand" href="/">SBeacon</a>
      <div id="sosbeaconheader" class="nav-collapse">
        <ul id="sosbeacon-menu" class="nav"></ul>
        <ul class="nav pull-right">
          <li id="prefs" class="dropdown">
            <a class="dropdown-toggle"  href="#prefs" data-toggle="dropdown"
               data-target="prefs">
              ${school_name | h}
              <b class="caret"></b>
            </a>
            <ul class="dropdown-menu">
              <li><a href="#">School Preferences</a></li>
              <li class="divider"></li>
              <li><a href="#">Account Preferences</a></li>
            </ul>
          </li>
          <li class="divider-vertical"></li>
        </ul>
      </div>
    </div>
  </div>
</div>

<div id="sosbeacon">
  <div id="sosbeaconcontainer" class="container"></div>
</div>

<%block name="body_script">
  <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
  <script type="text/javascript">
    $(function(){
        var sosbeacon = new App.SOSBeacon.Router
        Backbone.history.start();
        App.SOSBeacon.router = sosbeacon;

        //setup some urls.
        //TODO: move this to urls file?
        App.Skel.Event.bind("groupstudents:selected", function(id) {
          sosbeacon.showGroupStudents(id)
          sosbeacon.navigate('groupstudents/' + id);
        })
      });
  </script>
</%block>

