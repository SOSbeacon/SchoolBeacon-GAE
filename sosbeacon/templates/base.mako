<!DOCTYPE html>
<html>
    <head>
        <title>sosbeacon</title>
        <link rel="stylesheet" type="text/css" href="/static/css/lib.css">
        <link rel="stylesheet" type="text/css" href="/static/css/sosbeacon.css">
    </head>
    <body>
        <div id="sosbeacon">
            <div class="navbar navbar-fixed-top">
                <div class="navbar-inner">
                    <div class="container">
                        <a class="brand" href="#">sosbeacon</a>
                        <div id="sosbeaconheader" class="nav-collapse">
                            <ul id="sosbeacon-menu" class="nav">
                            </ul>
                        </div><!--/.nav-collapse -->
                    </div>
                </div>
            </div>
            <div id="sosbeaconcontainer" class="container">
                <div id="sosbeaconapp"></div>
            </div>
        </div>
        <div class="footer">
          <center><strong>View the source at:</strong> <a href="https://github.com/ezoxsystems/gae-skeleton">https://github.com/ezoxsystems/gae-skeleton</a></center>
        </div>
        <script type="application/javascript" src="/static/script/libs.js"></script>
        <script type="application/javascript" src="/static/script/template.js"></script>
        <script type="application/javascript" src="/static/script/skel.js"></script>
        <script type="application/javascript" src="/static/script/sosbeacon.js"></script>
        <script type="text/javascript">
        $(function(){
            var sosbeacon = new App.sosbeacon.Router
            Backbone.history.start();
            App.sosbeacon.router = sosbeacon;
        });
        </script>
    </body>
</html>
