<!DOCTYPE html>
<html>
<head>
    <title>School Beacon Login</title>
    <link rel="stylesheet" type="text/css" href="/static/css/lib.css">
    <link rel="stylesheet" type="text/css" href="/static/css/responsive.css">
    <link rel="stylesheet" type="text/css" href="/static/css/sosbeacon.css">
</head>
<body>
<div id="sosbeacon">
    <div id="sosbeaconlogin">
        <div id="sosbeaconcontainer" class="container">
            <h2 class="login_title">School Beacon Admin Login</h2>
            <div id="login_form" class="row-fluid">
                <form method="post" class="student-edit edit form-horizontal">
                    <div class="container standard-back">
                        <p class="error">${error}</p>
                        <div class="span5">
                            <div class="control-group">
                                <label for="email" class="control-label">Email:</label>
                                <div class="controls">
                                    <input id="email" name="email" type="text" value=""
                                           autocomplete="off" class="email" placeholder="Email..." />
                                </div>
                            </div>
                            <div class="control-group">
                                <label for="password" class="control-label">Password:</label>
                                <div class="controls">
                                    <input id="password" name="password" type="password" value=""
                                           autocomplete="off" class="password" placeholder="Password..." />
                                </div>
                            </div>
                        </div>
                        <div class="row-fluid">
                            <button class="save btn btn-info">
                                <i class="icon-ok icon-white"></i> Submit
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
</body>
</html>
