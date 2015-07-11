import os

try:
    from centralserver import local_settings
except ImportError:
    local_settings = object()

#######################
# Set module settings
#######################

# Duplicated from contact
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")
CENTRAL_FROM_EMAIL    = getattr(local_settings, "CENTRAL_FROM_EMAIL",    "kalite@%s" % CENTRAL_SERVER_DOMAIN)

# Only for registration
ACCOUNT_ACTIVATION_DAYS = getattr(local_settings, "ACCOUNT_ACTIVATION_DAYS", 7)
DEFAULT_FROM_EMAIL      = getattr(local_settings, "DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)
