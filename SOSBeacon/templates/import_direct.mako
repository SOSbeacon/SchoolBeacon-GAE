<%inherit file="base.mako"/>
<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container">
      <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="brand" href="/">School Beacon</a>
      <div id="sosbeaconheader" class="nav-collapse">
        <ul id="sosbeacon-menu" class="nav">
            <li class="menu" id="menu-item-student">
                <a href="/#contacts">
                    <i class="icon-user"></i>
                    Contacts
                </a>
            </li>
            <li class="menu" id="menu-item-group">
                <a href="/#group">
                    <i class="icon-th"></i>
                    Group
                </a>
            </li>
            <li class="menu" id="menu-item-eventcenter">
                <a href="/#eventcenter">
                    <i class="icon-share"></i>
                    Event Center
                </a>
            </li>
            <li class="menu" id="menu-item-settings" style="float: right">
                <a href="/settings">
                    <i class="icon-wrench"></i>
                    Settings
                </a>
            </li>
        </ul>
        <ul class="nav pull-right">
            <li id="prefs" class="dropdown">
                <a class="dropdown-toggle"  href="#prefs" data-toggle="dropdown"
                   data-target="prefs">
                    ${school_name | h} - ${user_name | h}
                    <b class="caret"></b>
                </a>
                <ul class="dropdown-menu">
                    <li>
                        <ul style="margin: 0;">
                                %for school in schools:
                                    <li style="list-style: none;">
                                        <a href="/school/${ school.key.urlsafe() }" class="choose_school">
                                        ${school.name }
                                        </a>
                                    </li>
                                %endfor
                        </ul>
                    </li>
                    <li class="divider"></li>
                    <li><a href="account">Account Preferences</a></li>
                    <li class="divider"></li>
                    <li><a id="logout">Log Out</a></li>
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
      <div class="top_view row-fluid" style="margin-top: 73px">
          <form action="/import/contacts/upload/" enctype="multipart/form-data" method="post"
                class="import containter-fluid well form-horizontal" id="form_direct">
              <div class="row-fluid">
                  <div class="modal-header">
                      <h3>Import Direct Contact</h3>
                  </div>
                  <div class="modal-body">
                      <fieldset>
                          <div class="control-group">
                              <label class="control-label" name="students_file">Contacts CSV</label>
                              <div class="controls">
                                  <input type="file" name="contacts_file" id="contacts_file" value="direct"/>
                              </div>
                              <div class="controls">
                                  <input type="hidden" id="value" name="importListString" value="${value}" />
                              </div>
                          </div>
                          <div class="control-group">
                              <div class="controls">
                                  <p>CSV file format like this:
                                      Group Name | Contact name | Email | Text phone | Voice phone
                                      <br>(Not import first row (heading))</p>
                              </div>
                          </div>
                          <div class="control-group">
                              <div class="controls">
                                  <a href="${download}">You can download sample CSV here</a>
                              </div>
                          </div>
                      </fieldset>
                  </div>
              </div>
              <div class="modal-footer form-actions">
                  <button type="submit" name="preview_import" value="Preview List" id="preview" form="form_direct">Preview List</button>
                  <button type="submit" name="import" value="Start Import" disabled="disabled" id="import" form="form_direct">Start Import</button>
              </div>
          </form>
      </div>

      <div class="top_view row-fluid" id="results" style="display: none">
          <h2 class="span8">${count}</h2>
          <table class="table table-striped">
            <thead>
              <th>Contact Name</th>
              <th>Group Name</th>
              <th>Email</th>
              <th>Text Phone</th>
              <th>Voice Phone</th>
            </thead>
            <tbody class="listitems">
              % for ri in success:
                ${makerow(ri)}
              % endfor
          </table>
          <br />
      </div>
  </div>
</div>

<%def name="makerow(row)">
  <tr>
    <td>${row.name}</td>
    <td>${row.group}</td>
    <td>${row.email}</td>
    <td>${row.text_phone}</td>
    <td>${row.voice_phone}</td>
  </tr>
</%def>
<%block name="body_script">
    <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
    <script type="text/javascript">
        $("#logout").click(function() {
            window.location = "/authentication/logout"
        })
        var results_contact = "${results_contact}"

        if (results_contact == 'true') {
            $("#import").removeAttr('disabled')
            $("#results").css('display', 'block')
        }

        $('#preview').click(function(){
            $("#value").val('direct')
            $('form.import').submit(function(e) {
                var $this = $(this);
                var $input =  $this.find('input').val();

                if ($input == '') {
                    $("#import").attr('disabled', 'disabled')
                    $("#results").css('display', 'none')
                    alert("Too less files, minimum '1' are expected but '0' are given, The file 'csvFile' was not uploaded");
                    return false;
                } if (! /\.csv$/.test($input)) {
                    alert("Please select a csv file")
                    return false
                } else {
                    $("#import").removeAttr('disabled')
                    $("#results").css('display', 'block')
                    return true
                }
            });
        });

        $('#import').click(function(){
            $('form.import').submit()
        });
    </script>
</%block>

