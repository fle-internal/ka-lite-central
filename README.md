# KA Lite Central Server

This is the code for the KA Lite Central Server: [https://kalite.learningequality.org](https://kalite.learningequality.org)

## What this is

A django app which is "It's Complicated" with [ka-lite](https://github.com/learningequality/ka-lite.git).
Distributed servers are configured to point to an instance of the central server, which manages their syncing.
Could be managing many different versions of KA Lite at once.

## Environment Setup

#. Install requirements:
    - [install node](http://nodejs.org/download/) if you don't have it already.
    - install the requirements from ka-lite-submodule's requirements.txt.
    - install requirements from requirements.txt here
#. Get the codebase: `git clone --recursive https://github.com/fle-internal/ka-lite-central.git` (if you're planning to make changes, you should fork the repo and clone your fork instead)
#. Install the dependencies listed in packages.json: `sudo npm install`
    - Also install them in the ka-lite-submodule: `cd ka-lite-submodule` and `npm install`
#. Install grunt: `sudo npm install -g grunt-cli`
#. Go into the centralserver directory: `cd centralserver`
#. Set up the server: `python manage.py setup --no-assessment-items`
#. Return to the root directory: 'cd ..'
#. Run grunt in the root directory: `grunt`
#. Run `node build.js` in the ka-lite-submodule to build js assets.
#. Return to the code directory: `cd centralserver`
#. Set up a custom `centralserver/local_settings.py` file (see below)
#. Run the server: `python manage.py runserver 0.0.0.0:8000`

### Environment set up with vagrant

Hopefully we can standardize our dev environment and get up and running much more quickerer.
1. Get the latest version of vagrant. Warning: On Debian (even on testing) the version is far behind. Get it from the vagrant website.
2. Get the codebase: `git clone --recursive https://github.com/fle-internal/ka-lite-central.git` (if you're planning to make changes, you should fork the repo and clone your fork instead)
3. Run `git submodule update` in the directory created by the last command.
4. Run `vagrant up` to start the machine and provision it.
5. Run `vagrant ssh` to start an SSH session in the virtual machine. Move to the `/vagrant/centralserver` directory and run the command `./manage.py setup` to finish the setup process.

### Pointing distributed ka-lite servers to local central server

After cloning the distrbuted server codebase from https://github.com/learningequality/ka-lite, add the following to its `kalite/local_settings.py` prior to running `install.sh` or `install.bat`:
```
CENTRAL_SERVER_HOST   = "127.0.0.1:8000"
SECURESYNC_PROTOCOL   = "http"
```

This will cause it to point to your locally running instance of the central server for registering and syncing.

### Local_settings.py setup

You may create a `centralserver/local_settings.py` file to customize your setup.  Here are a few options to consider:

#### For debugging

* `DEBUG = True` - turns on debug messages
* `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` - will output email messages (like account registration and contact) to the console
* `USE_DEBUG_TOOLBAR = True` - Use the Django debug toolbar, which gives info about queries, context values, and more!

#### For building language packs
* `CROWDIN_PROJECT_ID` and `CROWDIN_PROJECT_KEY` - these are private; you'll have to get in touch with a (FLE) team member who has them.
* * `KA_CROWDIN_PROJECT_ID` and `KA_CROWDIN_PROJECT_KEY` - these are private (from Khan Academy); you'll have to get in touch with a (FLE) team member who has them.
