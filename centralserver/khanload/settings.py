try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.sessions",  # distributed_callback_url
    "django.contrib.auth",  # central login
    "kalite.facility",  # for setting / saving data
    "kalite.main",  # *Log objects for data creation
    "kalite.topic_tools",  # validating imported data to our topic tree.
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
)


#######################
# Set module settings
#######################
