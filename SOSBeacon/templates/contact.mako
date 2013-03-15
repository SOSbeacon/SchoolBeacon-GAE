<%inherit file="base_home.mako"/>
<%block name="body_content">
    <div id="Content" class="main-content">
        <div class="contact-index contactForm">
            <h2>Contact</h2>
            <div class="message">${error}</div>

            <div class="div1">
                <div class="left">
                    <form id="frm" method="post">
                        <label class="name">Name:</label>
                        <input type="text" name="name" size="35" id="name" class="text right required"
                               value="" title="*" style="width: 92%"/>

                        <label class="email" for="email">Email:</label>
                        <input type="text" name="email" id="email" class="text right required" value="" style="width: 92%"/>

                        <label class="subject" for="subject">Subject:</label>
                        <input type="text" name="subject" id="subject" class="text right required" value="" style="width: 92%"/>

                        <label class="message" for="message">Message:</label>
                        <textarea name="message" rows="5" cols="40" id="message" class="text right required" style="width: 92%"></textarea>

                        <input type="submit" name="submit" class="submit" value="Send..."/>

                        <p class="loader">
                            <img src="/static/img/ajax_spinner.gif" alt="Loading..."/>
                        </p>

                        <div class="flag" id="flag"></div>
                    </form>
                    </div>
                    <!-- .left /end -->
                    <div class="right">
                        <p>You can contact us using the form to your left, alternatively you can use any of the links
                            below:</p>
                        <ul>
                            <li>sosbeacon.org</li>
                        </ul>
                    </div>
                    <!-- .right /end -->
                    <div class="clearFloat"></div>
                </div>
                <!-- .left /end -->
                <div class="right">
                    <p>You can contact us using the form to your left, alternatively you can use any of the links
                        below:</p>
                    <ul>
                        <li>sosbeacon.org</li>
                    </ul>
                </div>
                <!-- .right /end -->
                <div class="clearFloat"></div>
            </div>
        </div>
        <div class="clr"></div>
    </div>
</%block>