import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

STATS_DATA_PATH = ROOT_DATA_PATH #os.path.join(os.path.dirname(__file__), "data")

INSTALLER_BASE_URL = getattr(local_settings, 'INSTALLER_BASE_URL', 'https://www.dropbox.com/s/mich3t4rsw2q6hc/')
INSTALLER_BASE_URL = INSTALLER_BASE_URL.rstrip("/") + "/"  # make sure there's a trailing slash
