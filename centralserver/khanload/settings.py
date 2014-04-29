try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.auth",  # central login
    "django.contrib.sessions",  # distributed_callback_url
    "kalite.facility",  # for setting / saving data
    "kalite.main",  # *Log objects
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
)


#######################
# Set module settings
#######################
