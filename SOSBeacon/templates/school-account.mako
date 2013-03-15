<%inherit file="base_home.mako"/>
<%block name="body_content">
    <div id="Content" class="main-content" style="height: 700px">
        <div class="contact-index submitForm schoolAccountForm">
            <h2>School Account Information Form</h2>

            <div class="message">${error}</div>
            <form id="submitForm" action="" method="post">
                <div class="col-1">
                    <div class="row">
                        <label class="label">Name of School:</label>
                        <input type="text" name="schoolName" size="35" id="schoolName" class="text right required"
                               value="" title="*"/>
                    </div>
                    <div class="row">
                        <label class="label">Name of Principal:</label>
                        <input type="text" name="principalName" id="principalName" class="text right required" value=""
                               size="35" title="*"/>
                    </div>
                    <div class="row">
                        <label class="label">Name of Contact Admin:</label>
                        <input type="text" name="adminName" id="adminName" class="text required right" value=""
                               size="35" title="*"/>
                    </div>
                    <div class="row">
                        <label class="label">Address:</label>
                        <textarea name="address" id="address" rows="2" cols="40" class="text required right"
                                  title="*"></textarea>
                    </div>
                    <div class="row">
                        <div class="left" style="width: 45%;">
                            <label class="">School phone #:</label>
                            <input type="text" name="schoolPhone" id="schoolPhone" class="text required phoneUS"
                                   value="" size="15"/>
                        </div>
                        <div class="right" style="width: 45%; margin-right: 10px">
                            <label class="">Contact phone #:</label>
                            <input type="text" name="contactPhone" id="contactPhone" class="text required phoneUS"
                                   value="" size="15"/>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label">Contact email address:</label>
                        <input type="text" name="contactEmail" id="contactEmail" class="text required email right"
                               value="" size="35" style="width: 50%"/>
                    </div>
                    <div class="row">
                        <div class="left" style="width: 45%;">
                            <label>Number of Students:</label>
                            <input type="text" name="studentNo" id="studentNo" class="text number" min="0" value=""
                                   size="10"/>
                        </div>
                        <div class="right" style="width: 45%; margin-right: 10px">
                            <label>Number of classes:</label>
                            <input type="text" name="classNo" id="classNo" class="text number" min="0" value=""
                                   size="10"/>
                        </div>
                    </div>
                    <div class="row">
                        <div class="left" style="width: 45%">
                            <label>Student Age range:</label>
                            <input type="text" name="ageRange" id="ageRange" class="text" value="" size="15"/>
                        </div>
                        <div class="right" style="width: 45%; margin-right: 10px">
                            <label>Grade range:</label>
                            <input type="text" name="gradeRange" id="gradeRange" class="text" value="" size="15"/>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label" style="float: left; width: 20%">Is your school:</label>

                        <div class="left" style="width: 45%">
                            <input type="radio" value="For-profit" name="profitType" id="profitType1" class=""
                                   style="float: left"/>
                            <label for="profitType1" style="float: left; margin: 0 10px">For-profit</label>
                            <input type="radio" value="For-profit" name="profitType" id="profitType2"
                                   style="float: left"/>
                            <label for="profitType2" style="float: left; margin: 0 10px">Non-profit</label>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label">Date of School Founding <em>(m/d/y)</em>:</label>

                        <div class="right" style="width: 55%; margin-right: 10px">
                            <input type="text" name="foundingDate" size="20" id="foundingDate" class="text date"
                                   value=""/>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label">School Website:</label>
                        <input type="text" name="website" id="website" class="text right" value="" size="35"/>
                    </div>
                </div>
                <div class="col-2">
                    <div class="row">
                        <label class="label">Have you downloaded the free School Beacon app yet?</label>

                        <div class="left">
                            <input type="radio" value="Yes" name="downloadApp" id="downloadApp1" class=""
                                   style="float: left;margin: 3px 10px;"/>
                            <label for="downloadApp1" style="float: left">Yes</label>
                            <input type="radio" value="No" name="downloadApp" id="downloadApp2"
                                   style="float: left; margin: 3px 10px;"/>
                            <label for="downloadApp2" style="float: left">No</label>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label">What mobile phone # will you use for School Beacon service?</label>
                        <input type="text" name="sosPhone" id="sosPhone" class="text phoneUS right" value="" size="15" style="width: 30%"/>
                    </div>
                    <div class="row">
                        <label class="label">Type of mobile phone and carrier:</label>
                        <input type="text" name="sosPhoneCarrier" id="sosPhoneCarrier" class="text right" value=""
                               size="30" style="width: 45%"/>
                    </div>
                    <div class="row">
                        <label class="label">How did you hear about School Beacon?</label>
                        <input type="text" name="howHear" id="howHear" class="text right" value="" size="60"/>
                    </div>
                    <div class="row">
                        <label class="label">Do you have an emergency communications system now?</label>

                        <div class="left">
                            <input type="radio" value="Yes" name="haveEmergency" id="haveEmergency1" style="float: left; margin: 3px 10px"/>
                            <label for="haveEmergency1" style="float: left">Yes</label>
                            <input type="radio" value="No" name="haveEmergency" id="haveEmergency2" style="float: left; margin: 3px 10px"/>
                            <label for="haveEmergency2" style="float: left">No</label>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label">If so, what is it?</label>
                        <input type="text" name="whatEmergency" id="whatEmergency" class="text right" value=""
                               size="50"/>
                    </div>
                    <div class="row">
                        <label class="label">When would you like to get the School Beacon emergency communications
                            system <br /> started at your school?</label>
                        <input type="text" name="whenGetSos" id="whenGetSos" class="text right" value="" size="60"/>
                    </div>
                    <div class="row">
                        <label class="label">Do you have approval to start this service? </label>

                        <div class="left">
                            <input type="radio" value="Yes" name="approval" id="approval1" style="float: left; margin: 3px 10px"/>
                            <label for="approval1" style="float: left">Yes</label>
                            <input type="radio" value="No" name="approval" id="approval2" style="float: left; margin: 3px 10px"/>
                            <label for="approval2" style="float: left">No</label>
                        </div>
                    </div>
                    <div class="row">
                        <label class="label">If NO, what is required to get approval?</label>
                        <input type="text" name="whatApproval" id="whatApproval" class="text right" value="" size="30" style="width: 40%"/>
                    </div>
                </div>
                <div class="row" style="font-size:0.9em;font-weight: bold;padding-left: 5px">
                    After you send this form you will be contacted by School Beacon staff by email or phone within a
                    week. Thank you for your interest.
                </div>
                <input type="submit" id="submits" class="submit" value="SUBMIT" style="float: left"/>
                <!-- p class="loader">
                    <img src="/images/ajax_spinner.gif" alt="Loading..." />
                </p>
                <div class="flag" id="flag"></div -->
            </form>
        </div>
        <div class="clr"></div>
    </div>
</%block>