try:
    import local_settings
except ImportError:
    local_settings = object()


##############################
# Django settings
##############################

INSTALLED_APPS = (
    "django.contrib.sessions",
    "django.contrib.auth",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
)

#######################
# Set module settings
#######################

