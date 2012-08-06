## -*- coding: utf-8 -*-
<%inherit file="tos.mako"/>


${ parent.body() }

<form method="POST" action="/_userconfig/tosaccept">
  <input type="hidden" name="continue_to" value=""/>
  <input type="submit" class="btn btn-primary" name="accept"
  value="I Accept the Terms"/>
</form>

