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
  <div id="sosbeaconcontainer" class="container">
    <div id="sosbeaconapp">
      <div class="top_view row-fluid">
        <form action="${upload_url}" enctype="multipart/form-data"
          method="POST" class="import containter-fluid well form-horizontal">
          <div class="row-fluid">
            <div class="modal-header">
              <h3>Uplaod Imange or Audio Clip</h3>
            </div>
            <div class="modal-body">
              <fieldset>
                <div class="control-group">
                  <label class="control-label" for="file">File:</label>
                  <div class="controls">
                    <input type="file" name="file" id="file" />
                  </div>
                </div>
              </fieldset>
            </div>
          </div>
          <div class="modal-footer form-actions">
            <button class="save btn btn-primary">
              <i class="icon-download-alt icon-white"></i> Upload
            </button>
          </div>
        </form>
      </div> 
    </div>
  </div>
</div>

<%block name="body_script">
</%block>

