<%inherit file="base_home.mako"/>
<%block name="body_content">
    <div id="Content" class="main-content">
        <script type="text/javascript">
            <!--
            //Check valid email
            function IsValidEmail(email) {
                var filter = /^\b[A-Z0-9._%-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b$/i;

                return filter.test(email);
            }

            function setReadonly(status) {
                if (status == null)
                    status = false;

                document.getElementById('name').readOnly = status;
                document.getElementById('email').readOnly = status;
                document.getElementById('subject').readOnly = status;
                document.getElementById('message').readOnly = status;
                document.getElementById('submit').disabled = status;
            }

            function clearForm() {
                $('#name').val('');
                $('#email').val('');
                $('#subject').val('');
                $('#message').val('');
            }

            $().ready(function () {
                $('.submit').click(function () {
                    if ($('#name').val() == '') {
                        alert('Name field cannot be null !');
                        $('#name').focus();
                    }
                    else if ($('#email').val() == '') {
                        alert('Email field cannot be null !');
                        $('#email').focus();
                        return false
                    }
                    else if (!IsValidEmail($('#email').val())) {
                        alert('Email field is not valid - example@domain.com !');
                        $('#email').focus();
                        return false
                    }
                    else if ($('#subject').val() == '') {
                        alert('Subject field cannot be null !');
                        $('#subject').focus();
                        return false
                    }
                    else if ($('#message').val() == '') {
                        alert('Message field cannot be null !');
                        $('#message').focus();
                        return false
                    }
                    else {
                        var url = '/school/web/about/contact?name=' + $('#name').val() + '&email=' + $('#email').val();
                        url += '&subject=' + $('#subject').val() + '&message=' + $('#message').val();

                        //Show loader icon
                        $('.loader').show();
                        //Unable input form
                        setReadonly(true);

                        $.ajax({
                            type: "POST",
                            url: '/school/web/about/contact',
                            data: {},
                            success: function(xhr) {
                                console.log(xhr.status)
                                if (xhr.status == 400) {
                                    alert("ngon")
##                                    $('#flag').html('Email sending failed');
                                }
                                else if (xhr.status == 200){
                                    alert("loi roi")
##                                    $('#flag').html('Email sent successfully to our mail server.');
                                }
                                //Hide loader icon
                                $('.loader').hide();
                                //Clear form when send mail successfull
                                clearForm();
                                //Available input form
                                setReadonly(false);
                            }
                        });
                    }//End of else
                });
            });

            //-->
        </script>

        <div class="contact-index contactForm">
            <h2>Contact</h2>

            <div class="div1">
                <div class="left">
                    <form id="frm" method="post">
                        <label class="name" for="name">Name:</label>
                        <input type="text" name="name" id="name" class="text" value=""/>

                        <label class="email" for="email">Email:</label>
                        <input type="text" name="email" id="email" class="text" value=""/>

                        <label class="subject" for="subject">Subject:</label>
                        <input type="text" name="subject" id="subject" class="text" value=""/>

                        <label class="message" for="message">Message:</label>
                        <textarea name="message" rows="5" cols="40" id="message" class="textarea"></textarea>

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
        </div>
        <div class="clr"></div>
    </div>
</%block>