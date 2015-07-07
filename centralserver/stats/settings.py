import os

try:
    from centralserver import local_settings
except ImportError:
    local_settings = object()

#######################
# Set module settings
#######################

INSTALLER_BASE_URL = getattr(local_settings, 'INSTALLER_BASE_URL', 'https://www.dropbox.com/s/mich3t4rsw2q6hc/')
INSTALLER_BASE_URL = INSTALLER_BASE_URL.rstrip("/") + "/"  # make sure there's a trailing slash
