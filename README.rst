GAE Framework
=============


Dependencies
------------
- Python2.7
- Pip (2.7)
- Google Appengine SDK
  - You will also need to add the sdk to your python path.
  - For example on OSX you could create a path file in your python 2.7 site-packages directory ::

    $ echo /usr/local/google_appengine >> gae.pth


Installation
------------

Install app dependencies: ::

    $ sudo pip install .

* You may need to use your 2.7 pip if you have another version of python and pip default ::

    $ sudo pip-2.7 install .

Install Node.js (this is for compiling coffeescript and less): ::

    http://nodejs.org/#download

Install node packages: ::

    $ sudo sh node_packages.sh


Development
-----------

Lets work. Go to your appdirectory (SOSbeacon here) ::

    $ cd SOSbeacon

Once everything is installed you can now compile the app and go into dev watch mode.
- In this mode you can edit your coffeescript and less files and it will auto compile them for you for easy development. ::

    $ python build.py dev

To run the local server: ::
- https://developers.google.com/appengine/docs/python/gettingstartedpython27/devenvironment

    $ dev_appserver.py .
or ::

    $ dev_appserver.py -p 8001 . --enable_sendmail

The Framework
-------------

First you will need to setup the skeleton framework.  Add a remote for the
skeleton framework ::

    $ git remote add sbeacon git@github.com:{organization}/sbeacon.git

Fetch from the skeleton so you are up to date ::

    $ git fetch sbeacon

Then setup a branch to track the framework ::

    $ git checkout -b sbeacon sbeacon/master

In the future you can keep your application up to date with the skeleton by
using the sbeacon branch ::

    $ git checkout sbeacon

Now make sure you have the latest version of your code in sbeacon ::

    $ git merge master

And then pull in the latest skeleton ::

    $ git pull sbeacon

You can now run your tests, correct merge conflicts, if any, then commit and
submit a pull-request back to your master branch.

