<!DOCTYPE html>
<html>
  <head>
    <title><%block name="title">SBeacon</%block></title>
    <link rel="stylesheet" type="text/css" href="/static/css/lib.css">
    <link rel="stylesheet" type="text/css" href="/static/css/responsive.css">
    <link rel="stylesheet" type="text/css" href="/static/css/sosbeacon.css">
  </head>
  <body>
    <div id="sosbeacon">${self.body()}</div>
    <div class="footer"><%block name="footer">
      <center>
        <span><strong>Copyright &copy; 2012 SBeacon - All Rights Reserved</strong></span> -
        <span><a href="http://sosbeacon.com/web/about/terms">Terms of Service</a></span> -
        <span><a href="http://sosbeacon.com/web/about/privacy">Privacy Policy</a></span>
        <p><span>Development by <a href="http://ezoxsystems.com">Ezox Systems, LLC</a></span></p>
      </center>
    </%block></div>
    <%block name="body_script"/>
  </body>
</html>
