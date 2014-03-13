# KA Lite Central Server

This is the code for the KA Lite Central Server: [https://kalite.learningequality.org](https://kalite.learningequality.org)

## Environment Setup 

1. Install requirements: 
    - [install node](http://nodejs.org/download/) if you don't have it already. 

2. Get the codebase: `git clone git@github.com:fle-internal/ka-lite-central.git`
 
3. Install the dependencies listed in packages.json: `sudo npm install`

4. Install grunt: 'sudo npm install -g grunt-cli'

5. Run grunt in the root directory: 'grunt'

6. Go into the code directory: 'cd code'

7. Set up the database: `python manage.py syncdb --migrate`

8. Run the server: `python manage.py runserver`