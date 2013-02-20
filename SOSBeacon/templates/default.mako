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
                    <li class="menu" id="menu-item-settings" style="float: right">
                        <a href="/settings" id="settings">
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
                            <li><a id="account">Account Preferences</a></li>
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
    <div id="sosbeaconcontainer" class="container"></div>
</div>

<%block name="body_script">
    <script type="text/javascript" src="https://maps.google.com/maps/api/js?sensor=false"></script>
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
##      Two this variable is used to for event center
        current_user = "${user_name}"
        current_school = "${school_name}"

        $("#logout").click(function() {
            window.location = "/authentication/logout"
        })

        $("#account").click(function() {
            window.location = "/account"
        })

        $(".choose_school").click(function() {
            $("input").attr('checked', 'checked')
        });

        var default_timezone = "${timezone}"

        $(document).ready(function() {
            jQuery("#selectTimeZone option").each(function(){
                if(jQuery(this).val() == default_timezone){
                    jQuery(this).attr("selected","selected");
                    return false;
                }
            });
        });
    </script>
</%block>
