<!DOCTYPE html>
<html>
<head>
    <title><%block name="title">School Beacon</%block></title>
    <link rel="stylesheet" type="text/css" href="/static/css/lib.css">
    <link rel="stylesheet" type="text/css" href="/static/css/responsive.css">
    <link rel="stylesheet" type="text/css" href="/static/css/sosbeacon.css">
    <link rel="stylesheet" type="text/css" href="/static/css/home.css">

    <script type="text/javascript" src="/static/script/sosbeacon.js"></script>
    <script type="text/javascript" src="http://ajax.aspnetcdn.com/ajax/jquery.validate/1.11.0/jquery.validate.js"></script>
    <script type="text/javascript">
        $(document).ready(function () {
            $(".home").click(function () {
                window.location = "/school"
            })
            $(".about").click(function () {
                window.location = "/school/web/about/index"
            })
            $(".features").click(function () {
                window.location = "/school/web/about/features"
            })
            $(".testimonials").click(function () {
                window.location = "/school/web/about/testimonials"
            })
            $(".contact").click(function () {
                window.location = "/school/web/about/contact"
            })
            $(".privacy").click(function () {
                window.location = "/school/web/about/privacy"
            })
            $(".bt-get-free-account").click(function () {
                window.location = "/school/web/about/school-account"
            })

            $("#submitForm").validate({
                rules: {
                    schoolPhone: "This field is required.",
                    contactEmail: {
                        required: true,
                        email: true
                    },
                    contactPhone: "This field is required"
                }
            });

            $("#frm").validate({
                rules: {
                    name: "This field is required.",
                    email: {
                        required: true,
                        email: true
                    },
                    contactPhone: "This field is required"
                }
            });

        });
    </script>
</head>
<body>
<div class="wrapper">
    <div id="Header">
        <div class="header">
            <div class="logo"><a class="logo-img" href="http://sosbeacon.org/school"></a></div>
            <%block name="login">
                    <div id="loginRegion" class="login-region">
                            % if not is_loggedin:
                                <form action="/school/web/users/login/" method="POST" id="frmLogin" name="frmLogin">
                                    <input class="text textbox-auto-clear" type="text" name="email" id="user"
                                           placeholder="Email address"/>
                                    <br/>
                                    <input class="text" type="password" name="password" value="password"
                                           onfocus="this.value=''"/>
                                    <br/>

                                    <div class="row">
                                        <div class="right">
                                            <input class="button-login" type="submit" name="btnLogin"
                                                                  value="" style="width: 22%"/>
                                            <a href="/school/web/users/forgot" style="color: #ffffff">Forgot login?</a>
                                        </div>
                                    </div>
                                </form>
                            %else:
                                <div class="account">
                            <span>Welcome
                            <strong>${school_name | h} - ${user_name | h}</strong>!</span><br>
                                    <a id="contact" href="/#/contacts">Contact</a> |
                                    <a id="group" href="/#/group">Group</a> |
                                    <a id="eventcenter" href="/#/eventcenter">Event Center</a> |
                                    <a id="logout" href="/school/web/users/logout/">Logout</a>
                                </div>
                            % endif
                    </div>
            </%block>
        </div>
        <div class="menubar-color"></div>
        <div class="menubar">
            <div class="menubar-position">
                <ul class="sf-menu">
                    <li class="current first home">
                        <a href="/school">&nbsp;</a>
                    </li>
                    <li class="about">
                        <a href="/school/web/about/index">&nbsp;</a>
                    </li>
                    <li class="features">
                        <a href="/school/web/about/features">&nbsp;</a>
                    </li>
                    <li class="testimonials">
                        <a href="/school/web/about/testimonials">&nbsp;</a>
                    </li>
                    <li class="contact">
                        <a href="/school/web/about/contact">&nbsp;</a>
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <%block name="body_content">
    </%block>
    <div id="Footer">
        <div class="copyright">
            Copyright 2012 Copyright 2012 School Beacon
            - All Rights Reserved
            - <a href="/school/web/about/terms">Terms of service</a>
            - <a href="/school/web/about/privacy">Privacy</a>
            - Developed by <a target="_blank" href="http://www.cncsoftgroup.com">CNC Software Group.</a>
        </div>
    </div>
</div>
</body>
</html>