<%inherit file="base_home.mako"/>
<title><%block name="title">School Beacon Select School</%block></title>
<%block name="body_content">
    <div class="content">
        <div id="login_form" class="row-fluid">
                % if not is_loggedin:
                    <div class="login-panel">
                        <form method="POST" name="frmLogin" id="frmLogin">
                            <div class="login-title">&nbsp;</div>
                            <p class="error">${error}</p>

                            <div class="div1">
                                <div class="left">Email address</div>
                                <div class="right_input">
                                    <input type="text" name="email" class="text">
                                </div>
                            </div>
                            <div class="div1">
                                <div class="left">Password</div>
                                <div class="right_input">
                                    <input type="password" name="password" class="text">
                                </div>
                            </div>
                            <div class="div1">
                                <div class="left" style="float: left; width: 65%">
                                    <a href="/school/web/users/forgot" style="color: #000000">Forgot login?</a>
                                </div>
                                <div class="right" style="float: left; width: 20%">
                                    <input class="button-login" type="submit" name="btnLogin" value=""
                                           style="width: 52px">
                                </div>
                            </div>
                        </form>
                    </div>
                % elif schools :
                <div class="login-panel">
                <form method="POST" name="frmLogin"
                      id="frmLogin">
                    <div class="login-title">&nbsp;Member Select School</div>
                    <h2 style="font-size: 14px; margin: 5px 0; color: #ff0000;font-weight: bold;">Please select
                        a school to go to school dashboard</h2>

                <div class="select-school">
                <table style="width: 100%">
                    <thead>
                    <tr>
                        <th><input type="hidden" name="hdslSchool" value="1"></th>
                    </tr>
                    </thead>
                <tbody>
                    % for school in schools :
                    <tr>
                        <td><input type="radio" name="school" id="rSchoolId"
                                   value="${ school.key.urlsafe() }">
                            <!--[if !IE]>-->
                            <label id="label">${school.name }</label>
                            <!--<![endif]-->

                            <!--[if IE]>
                            <label id="label" style="margin-top: 1px;">${school.name }</label>
                            <!--<![endif]-->
                        </td>
                    </tr>
                    % endfor
                </tbody>
                </table>
                </div>
                    <div class="div2" style="width: 100%;  margin-top: 3%;">
                        <input class="button-select-school" id="select-school" type="submit" name="btnLogin" value="" style="width: 104px; margin-right: 0;">
                    </div>
                </form>
                </div>
                %else:
                    <p class="error all_error">${error}</p>
                % endif
        </div>
    </div>
</%block>