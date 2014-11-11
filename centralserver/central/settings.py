import os
import uuid

try:
    import local_settings
except ImportError:
    local_settings = object()

DEBUG = getattr(local_settings, "DEBUG", False)


##############################
# Django settings
##############################

EMAIL_BACKEND           = getattr(local_settings, "EMAIL_BACKEND", "postmark.backends.PostmarkBackend")

INSTALLED_APPS = getattr(local_settings, 'INSTALLED_APPS', tuple())
INSTALLED_APPS = (
    "django.contrib.sessions",
    "django.contrib.auth",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "announcements",  # display announcements in the header
    "south",
    "fle_utils.django_utils",  # custom template tags
    "securesync",
    "kalite.facility",
    "kalite.coachreports",  # in both apps; reachable on central via control_panel
    "kalite.control_panel",  # in both apps
    "kalite.khanload",  # zip_kalite must know about the entire kalite project structure.  Boo, bad code placement!
    "kalite.playlist",
    "kalite.testing",  # browser testing
    "kalite.updates",
    "kalite.student_testing",
    "kalite.store",
    # central-only apps
    "centralserver.contact",
    "centralserver.deployment",
    "centralserver.faq",
    "centralserver.i18n",
    "centralserver.khanload",
    "centralserver.registration",
    "centralserver.stats",
    "centralserver.testing",  # needed to run tests
) + INSTALLED_APPS  # append local_settings installed_apps, in case of dependencies

MIDDLEWARE_CLASSES = getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())
MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "fle_utils.django_utils.middleware.GetNextParam",
    "django.middleware.csrf.CsrfViewMiddleware",
) + MIDDLEWARE_CLASSES  # append local_settings middleware, in case of dependencies

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    __package__ + ".custom_context_processors.custom",
)

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), "templates"),)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)
if DEBUG:
    INSTALLED_APPS += ("django_snippets",)   # used in contact form and (debug) profiling middleware
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

##############################
# KA Lite settings
##############################

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

# Duplicated from contact
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")

#
CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.%s/" % CENTRAL_SERVER_DOMAIN)

LOGIN_REDIRECT_URL = '/organization/'
