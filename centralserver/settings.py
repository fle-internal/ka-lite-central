import logging
import os
import platform
import uuid

##############################
# Basic setup
##############################

# import the base settings from kalite up here, since we need things from there but also don't
# want stuff like INSTALLED_APPS from there to swamp the settings defined in the current file
from kalite.settings.base import *

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = object()

# Used everywhere, so ... set it up top.
DEBUG          = getattr(local_settings, "DEBUG", False)

CENTRAL_SERVER = True  # Hopefully will be removed soon.

##############################
# Basic setup of logging
##############################

# Set logging level based on the value of DEBUG (evaluates to 0 if False, 1 if True)
LOGGING_LEVEL = getattr(local_settings, "LOGGING_LEVEL", logging.DEBUG if DEBUG else logging.INFO)
LOG = getattr(local_settings, "LOG", logging.getLogger("kalite"))
TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

logging.basicConfig()
LOG.setLevel(LOGGING_LEVEL)
logging.getLogger("requests").setLevel(logging.WARNING)  # shut up requests!

ADMINS = (('FLE Errors', 'errors@learningequality.org'),)
SERVER_EMAIL = 'kalite@learningequality.org'

EMAIL_BACKEND = getattr(local_settings, "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend" if DEBUG else "postmark.backends.PostmarkBackend")

##############################
# Basic Django settings
##############################

# Not really a Django setting, but we treat it like one--it's eeeeverywhere.
PROJECT_PATH = os.path.realpath(getattr(local_settings, "PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))) + "/"
ROOT_DATA_PATH = os.path.realpath(getattr(local_settings, "ROOT_DATA_PATH", os.path.join(PROJECT_PATH, "..", "data"))) + "/"
STATS_PATH = ROOT_DATA_PATH
KALITE_PATH    = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'ka-lite-submodule') + "/"

LOCALE_PATHS   = getattr(local_settings, "LOCALE_PATHS", (PROJECT_PATH + "/../locale",))
LOCALE_PATHS   = tuple([os.path.realpath(lp) + "/" for lp in LOCALE_PATHS])

DATABASES = getattr(local_settings, "DATABASES", {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "data.sqlite",
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

ALLOWED_HOSTS = getattr(local_settings, "ALLOWED_HOSTS", ['*'])
INTERNAL_IPS   = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = getattr(local_settings, "TIME_ZONE", None)
#USE_TZ         = True  # needed for timezone-aware datetimes (particularly in updates code)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE  = getattr(local_settings, "LANGUAGE_CODE", "en")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N       = getattr(local_settings, "USE_I18N", True)

# If you set this to True, Django will format dates, numbers and
# calendars according to the current locale
USE_L10N       = getattr(local_settings, "USE_L10N", False)

MEDIA_URL      = getattr(local_settings, "MEDIA_URL", "/media/")
MEDIA_ROOT     = os.path.realpath(getattr(local_settings, "MEDIA_ROOT", PROJECT_PATH + "/media/")) + "/"
STATIC_URL     = getattr(local_settings, "STATIC_URL", "/static/")
STATIC_ROOT    = os.path.realpath(getattr(local_settings, "STATIC_ROOT", PROJECT_PATH + "/static/")) + "/"

 # Make this unique, and don't share it with anybody.
SECRET_KEY     = getattr(local_settings, "SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

AUTH_PROFILE_MODULE     = "centralserver.central.UserProfile"
CSRF_COOKIE_NAME        = "csrftoken_central"
LANGUAGE_COOKIE_NAME    = "django_language_central"
SESSION_COOKIE_NAME     = "sessionid_central"

ROOT_URLCONF = "centralserver.central.urls"

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), "templates"),)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'kalite.i18n.custom_context_processors.languages',
    'django.contrib.messages.context_processors.messages',
    'centralserver.central.custom_context_processors.custom'
) + getattr(local_settings, 'TEMPLATE_CONTEXT_PROCESSORS', tuple())

INSTALLED_APPS = (
    'kalite.topic_tools',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'fle_utils.config',
    'fle_utils.chronograph',
    'fle_utils.django_utils',
    'django.contrib.staticfiles',
    'south',
    'kalite.facility',
    'kalite.i18n',
    'kalite.testing',
    'securesync',
    'kalite.main',
    'django.contrib.admin',
    'kalite.testing.loadtesting',
    'kalite.contentload',
    'kalite.control_panel',
    'centralserver.central',
    'kalite.coachreports',
    'django.contrib.humanize',
    'centralserver.contact',
    'kalite.updates',
    'kalite.caching',
    'centralserver.i18n',
    'tastypie',
    'announcements',
    'fle_utils.backbone',
    'kalite.playlist',
    'kalite.student_testing',
    'kalite.store',
    'centralserver.deployment',
    'centralserver.faq',
    'centralserver.khanload',
    'centralserver.registration',
    'centralserver.stats',
    'centralserver.testing',
    'django_snippets',
    'django.contrib.contenttypes',
    'securesync.devices',
    'fle_utils.handlebars',
    'kalite.dynamic_assets',
    'centralserver.ab_testing'
) + getattr(local_settings, 'INSTALLED_APPS', tuple())

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'securesync.middleware.RegisteredCheck',
    'securesync.middleware.DBCheck',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'fle_utils.django_utils.middleware.GetNextParam',
    'kalite.facility.middleware.AuthFlags',
    'kalite.facility.middleware.FacilityCheck',
    'django_snippets.profiling_middleware.ProfileMiddleware',
    'kalite.i18n.middleware.SessionLanguage',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'centralserver.middleware.DummySessionForAPIUrls'
) + getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, '..', 'static-libraries'),
    os.path.join(PROJECT_PATH, '..', 'ka-lite-submodule', 'static-libraries'),
)  # libraries common to all apps

DEFAULT_ENCODING = 'utf-8'

##############################
# Settings for purposes of testing/debugging
##############################

USE_DEBUG_TOOLBAR = getattr(local_settings, "USE_DEBUG_TOOLBAR", False)

if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'HIDE_DJANGO_SQL': False,
        'ENABLE_STACKTRACES' : True,
    }

if DEBUG:

    INSTALLED_APPS += ('django_extensions',)

    # add ?prof to URL, to see performance stats
    MIDDLEWARE_CLASSES += (
        'django_snippets.profiling_middleware.ProfileMiddleware',
    )

    # TEMPLATE_CONTEXT_PROCESSORS += (
    #     "django.contrib.auth.context_processors.auth",
    # )


########################
# Storage and caching
########################

# Sessions use the default cache, and we want a local memory cache for that.
CACHES = {
    "default": {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Separate session caching from file caching.
SESSION_ENGINE = getattr(local_settings, "SESSION_ENGINE", 'django.contrib.sessions.backends.cache' + (''))

# Use our custom message storage to avoid adding duplicate messages
MESSAGE_STORAGE = 'fle_utils.django_utils.classes.NoDuplicateMessagesSessionStorage'


########################
# After all settings, but before config packages,
#   import settings from other apps.
#
# This allows app-specific settings to be localized and augment
#   the settings here, while also allowing
#   config packages to override settings.
########################


#CONTENT_ROOT   = None  # needed for shared functions that are distributed-only
#CONTENT_URL    = None

CACHE_TIME = 0
CACHE_NAME = None
CENTRAL_SERVER_HOST = ""

RUNNING_IN_TRAVIS = bool(os.environ.get("TRAVIS"))

# LOG.debug("======== MIDDLEWARE ========")
# LOG.debug("\n".join(MIDDLEWARE_CLASSES))
# LOG.debug("====== INSTALLED_APPS ======")
# LOG.debug("\n".join(INSTALLED_APPS))
# LOG.debug("============================")

########################
# Now that we've imported the settings from all other installed apps,
#   override their settings as necessary to get desired central server config.
########################

# Don't want to have a limited number of SyncSession records on the central server (save them all!)
SYNC_SESSIONS_MAX_RECORDS = getattr(local_settings, "SYNC_SESSIONS_MAX_RECORDS", None)

LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'

CONFIG_PACKAGE = []
AUTH_PROFILE_MODULE = "central.UserProfile"

# Tastypie stuff
TASTYPIE_DEFAULT_FORMATS = ['json']
API_LIMIT_PER_PAGE = 0

POSTMARK_API_KEY = getattr(local_settings, "POSTMARK_API_KEY", "")

# Whether this was built by a build server; it's not.
BUILT = getattr(local_settings, "BUILT", False)

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

# Duplicated from contact
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")

CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.%s/" % CENTRAL_SERVER_DOMAIN)

LOGIN_REDIRECT_URL = '/organization/'

########################
#
# (The following approach is borrowed from the distributed server.)
#
# After all settings, but before config packages,
#   import settings from other apps.
#
# This allows app-specific settings to be localized and augment
#   the settings here, while also allowing
#   config packages to override settings.
########################

#from kalite.distributed.settings import *
#from kalite.django_cherrypy_wsgiserver.settings import *
#from securesync.settings import *
#from fle_utils.chronograph.settings import *
from kalite.facility.settings import *
from kalite.main.settings import *
from kalite.playlist.settings import *
from kalite.student_testing.settings import *
from kalite.testing.settings import *

# Import from applications with problematic __init__.py files
from kalite.legacy.i18n_settings import *
from kalite.legacy.topic_tools_settings import *
from kalite.legacy.updates_settings import *


########################
#
# Now, the same as above, but for the centralserver apps.
#
########################

from registration.settings import *
from testing.settings import *
from contact.settings import *
from stats.settings import *

# Import from applications with problematic __init__.py files
from centralserver.legacy.centralserver_i18n_settings import *

