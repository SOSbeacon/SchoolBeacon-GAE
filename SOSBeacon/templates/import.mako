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
        <ul id="sosbeacon-menu" class="nav">
          <li class="menu" id="menu-item-student">
            <a href="/#/student">Home</a>
          </li>
        </ul>
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
    <div class="top_view row-fluid ">
      <h1 class="span8">Student Import Results</h1>
    </div>
    <div class="top_view row-fluid">
      <h2 class="span8">Imported Successfully</h2>
      <table class="table table-striped">
        <thead>
          <th>Student Name</th>
          <th>Messages</th>
        </thead>
        <tbody class="listitems">
          % for ri in success:
            ${makerow(ri)}
          % endfor
      </table>
      <br />
      <h2 class="span8">Failed to Import</h2>
      <table class="table table-striped">
        <thead>
          <th>Student Name</th>
          <th>Messages</th>
        </thead>
        <tbody class="listitems">
          % for ri in failures:
            ${makerow(ri)}
          % endfor
      </table>
    </div>
  </div>
</div>

<%def name="makerow(row)">
  <tr>
    <td>${row.name}</td>
    <td>
      <%
        ','.join(row.messages)
      %>
    </td>
  </tr>
</%def>
