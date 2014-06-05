import os

try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.sessions",
    "django.contrib.auth",
    "django.contrib.messages",  # default_language, language_choices, etc
    "django.contrib.humanize",
    "securesync",  # creates a Zone on registration
    "centralserver.central",  # creates an Organization on registration
    "centralserver.contact",  # for auto-subscribe to newsletter.
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",  # needed for django admin
    "django.middleware.csrf.CsrfViewMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",  # needed for django admin
)


#######################
# Set module settings
#######################

# Duplicated from contact
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")
CENTRAL_FROM_EMAIL    = getattr(local_settings, "CENTRAL_FROM_EMAIL",    "kalite@%s" % CENTRAL_SERVER_DOMAIN)

# Only for registration
ACCOUNT_ACTIVATION_DAYS = getattr(local_settings, "ACCOUNT_ACTIVATION_DAYS", 7)
DEFAULT_FROM_EMAIL      = getattr(local_settings, "DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), "templates"),)
