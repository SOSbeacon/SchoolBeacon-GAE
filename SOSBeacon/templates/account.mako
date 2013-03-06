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
                    <li class="menu" id="menu-item-home" style="float: left">
                        <a href="/school" id="home">
                            <i class="icon-home"></i>
                            Home
                        </a>
                    </li>
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
##                    <li class="menu" id="menu-item-settings" style="float: right">
##                        <a href="/settings">
##                            <i class="icon-wrench"></i>
##                            Settings
##                        </a>
##                    </li>
                </ul>
                <ul class="nav pull-right">
                    <li id="prefs" class="dropdown">
                        <a class="dropdown-toggle"  href="#prefs" data-toggle="dropdown"
                           data-target="prefs">
                            ${school_name | h} - ${user.name}
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
        <form method="post" class="student-edit edit form-horizontal" id="account">
            <div class="container standard-back">
                <p class="error">${error}</p>
                <div class="span4">
                    <div class="control-group">
                        <label for="name" class="control-label">Name:</label>
                        <div class="controls">
                            <input id="name" name="name" type="text" value="${user.name}"
                                   autocomplete="off" class="name" placeholder="Name..." />
                        </div>
                    </div>

                    <div class="control-group">
                        <label for="email" class="control-label">Email:</label>
                        <div class="controls">
                            <input id="email" name="email" type="text" value="${user.email}"
                                   autocomplete="off" class="email" readonly=""/>
                        </div>
                    </div>

                    <div class="control-group">
                        <label for="phone" class="control-label">Phone:</label>
                        <div class="controls">
                            <input id="phone" name="phone" type="text" value="${user.phone}"
                                   autocomplete="off" class="phone" placeholder="Phone..." />
                        </div>
                    </div>

                    <div class="control-group">
                        <label for="current_password" class="control-label">Current Password:</label>
                        <div class="controls">
                            <input id="current_password" name="current_password" type="password" value=""
                                   autocomplete="off" class="password" placeholder="Current password..." />
                            <p>Confirm your current password to update account informations.</p>
                        </div>

                    </div>

                    <div class="control-group">
                        <label for="new_password" class="control-label">New Password:</label>
                        <div class="controls">
                            <input id="new_password" name="new_password" type="password" value=""
                                   autocomplete="off" class="new_password" placeholder="New password..." />
                            <p>Blank to skip change password.</p>
                        </div>
                    </div>

                    <div class="control-group">
                        <label for="confirm_password" class="control-label">Confirm Password:</label>
                        <div class="controls">
                            <input id="confirm_password" name="confirm_password" type="password" value=""
                                   autocomplete="off" class="confirm_password" placeholder="Confirm password..." />
                        </div>
                    </div>

                    <div class="row-fluid">
                        <button class="save btn btn-info" id="submit">
                            <i class="icon-ok icon-white"></i> Submit
                        </button>
                    </div>
                </div>
            </div>
        </form>
    </div>
</div>

<%block name="body_script">
    <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
    <script type="text/javascript">
##        $(function(){
##            var sosbeacon = new App.SOSBeacon.Router
##            Backbone.history.start();
##            App.SOSBeacon.router = sosbeacon;
##
##            //setup some urls.
##            //TODO: move this to urls file?
##            App.Skel.Event.bind("groupstudents:selected", function(id) {
##                sosbeacon.showGroupStudents(id)
##                sosbeacon.navigate('groupstudents/' + id);
##            })
##        });

        $("#logout").click(function() {
            window.location = "/school/web/users/logout/"
        })

        $('#submit').click(function(){
            if($('#phone').val() == '') {
                alert('Phone field cannot be null !');
                $('#phone').focus();
                return false
            }
            if ($("#phone").val().length < 9 || $("#phone").val().length > 11) {
                alert("Invalid Phone Number")
                $('#phone').focus();
                return false;
            }
            else {
                return true
            }//End of else
        });
    </script>
</%block>

