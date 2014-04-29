import os

try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "kalite.testing",  # topic_tools
)
MIDDLEWARE_CLASSES = tuple()


########################
# Module-specific settings
########################

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

if getattr(local_settings, "DEBUG", False):
    INSTALLED_APPS += (
        "django.contrib.admin",  # this and the following are needed to enable django admin.
    )

    # add ?prof to URL, to see performance stats
    MIDDLEWARE_CLASSES += (
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        'django_snippets.profiling_middleware.ProfileMiddleware',
    )

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
    )

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["fast", "medium", "long"])), "TESTS_TO_SKIP must contain only 'fast', 'medium', and 'long'"

CENTRALSERVER_TEST_RUNNER = __package__ + ".testrunner.CentralTestRunner"
