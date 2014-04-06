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

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), "templates"),)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "centralserver.central.custom_context_processors.custom",
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

MIDDLEWARE_CLASSES = getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())
MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "fle_utils.django_utils.middleware.GetNextParam",
    "django.middleware.csrf.CsrfViewMiddleware",
    #"facility.middleware.AuthFlags",  # this must come first in app-dependent middleware--many others depend on it.
    #"facility.middleware.FacilityCheck",
    #"securesync.middleware.RegisteredCheck",
    "securesync.middleware.DBCheck",
    #"distributed.middleware.LockdownCheck",
) + MIDDLEWARE_CLASSES  # append local_settings middleware, in case of dependencies

INSTALLED_APPS = getattr(local_settings, 'INSTALLED_APPS', tuple())
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions", # needed for clean_pyc (testing)
    "announcements",
    "south",
    "fle_utils.config",
    "fle_utils.django_utils",
    "kalite.coachreports",  # in both apps; reachable on central via control_panel
    "kalite.control_panel",  # in both apps
    "kalite.facility",
    "kalite.i18n",  #
    "kalite.main",  # *Log objects
    # central-only apps
    "centralserver.contact",
    "centralserver.deployment",
    "centralserver.faq",
    "centralserver.i18n",
    "centralserver.khanload",
    "centralserver.registration",
    "centralserver.stats",
    "centralserver.testing",  # needed to run tests
    "securesync",
) + INSTALLED_APPS  # append local_settings installed_apps, in case of dependencies

if DEBUG:
    INSTALLED_APPS += ("django_snippets",)   # used in contact form and (debug) profiling middleware


##############################
# KA Lite settings
##############################

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

# Duplicated from contact
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")

#
CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.%s/" % CENTRAL_SERVER_DOMAIN)
