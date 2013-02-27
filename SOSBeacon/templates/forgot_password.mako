<%inherit file="base_home.mako"/>
<%block name="body_content">
    <div id="Content" class="main-content">
        <script type="text/javascript">
            $(document).ready(function () {
                $('#requestButton').click(function () {
                    $('#requestSending').show();
                    $(this).hide();
                });
            });
        </script>

        <div id='user-forgot'>
            <div id="title">Sbeacon - Forgot password</div>

            If you have forgotten your password, you can request to have a new password sent to your email address.
            Please enter your email address below. Then log in and reset your password in Account Settings using your
            Sbeacon mobile phone app or the WebApp on your browser.

            <br/><br/>

            <div class="message">
                <strong>${message}</strong>
            </div>

            <form name="frm" action="" method="POST">
                Email Address:<br/><input type="text" name="email" class="txt"/><br/>
                <input type="submit" name="submit" value="Request Account Information Now" class="btn"
                       id="requestButton"/>

                <h3 id="requestSending" style="display: none">Sending...</h3>
            </form>

        </div>
        <div class="clr"></div>
    </div>
</%block>