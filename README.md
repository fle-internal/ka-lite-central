# KA Lite Central Server

This is the code for the KA Lite Central Server: [https://kalite.learningequality.org](https://kalite.learningequality.org)

## Environment Setup 

1. Install requirements: 
    - [install node](http://nodejs.org/download/) if you don't have it already. 
2. Get the codebase: `git clone git@github.com:fle-internal/ka-lite-central.git`
3. Install the dependencies listed in packages.json: `sudo npm install`
4. Install grunt: `sudo npm install -g grunt-cli`
5. Run grunt in the root directory: `grunt`
6. **Go into the centralserver directory: `cd centralserver`**
7. Set up the server: `python manage.py setup`
8. Set up a custom `local_settings.py` file (see below)
9. Run the server: `python manage.py runserver`

### Local_settings.py setup

You may create a `centralserver/local_settings.py` file to customize your setup.  Here are a few options to consider:

#### For debugging

* `DEBUG = True` - turns on debug messages
* `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` - will output email messages (like account registration and contact) to the console
* `USE_DEBUG_TOOLBAR = True` - Use the Django debug toolbar, which gives info about queries, context values, and more!

#### For building language packs
* `CROWDIN_PROJECT_ID` and `CROWDIN_PROJECT_KEY` - these are private; you'll have to get in touch with a (FLE) team member who has them.
* * `KA_CROWDIN_PROJECT_ID` and `KA_CROWDIN_PROJECT_KEY` - these are private (from Khan Academy); you'll have to get in touch with a (FLE) team member who has them.
