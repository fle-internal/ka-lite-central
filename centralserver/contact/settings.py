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

# Email addresses
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")
CENTRAL_FROM_EMAIL    = getattr(local_settings, "CENTRAL_FROM_EMAIL",    "kalite@%s" % CENTRAL_SERVER_DOMAIN)
CENTRAL_DEPLOYMENT_EMAIL = getattr(local_settings, "CENTRAL_DEPLOYMENT_EMAIL", "deployments@learningequality.org")
CENTRAL_SUPPORT_EMAIL = getattr(local_settings, "CENTRAL_SUPPORT_EMAIL",    "support@learningequality.org")
CENTRAL_DEV_EMAIL     = getattr(local_settings, "CENTRAL_DEV_EMAIL",        "dev@learningequality.org")
CENTRAL_INFO_EMAIL    = getattr(local_settings, "CENTRAL_INFO_EMAIL",       "info@learningequality.org")
CENTRAL_CONTACT_EMAIL = getattr(local_settings, "CENTRAL_CONTACT_EMAIL", "info@%s" % CENTRAL_SERVER_DOMAIN)
CENTRAL_ADMIN_EMAIL   = getattr(local_settings, "CENTRAL_ADMIN_EMAIL",   "errors@%s" % CENTRAL_SERVER_DOMAIN)

# Mailchimp
CENTRAL_SUBSCRIBE_URL    = getattr(local_settings, "CENTRAL_SUBSCRIBE_URL",    "http://adhocsync.us6.list-manage.com/subscribe/post?u=023b9af05922dfc7f47a4fffb&amp;id=97a379de16")

