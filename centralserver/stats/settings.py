import os

try:
    import local_settings
except ImportError:
    local_settings = object()



########################
# Django dependencies
########################

INSTALLED_APPS = (
    "fle_utils.django_utils",  # templatetags
    "securesync",  # for querying data
    "kalite.i18n",  # video info
    "kalite.main",  # timeline of *Log syncing
    "kalite.control_panel",  # direct links to zone syncing summaries.
    "kalite.topic_tools",  # for video stats, need to map youtube_id to video_id
    "centralserver.i18n",  # for redirecting to resource paths
)


#######################
# Set module settings
#######################

INSTALLER_BASE_URL = getattr(local_settings, 'INSTALLER_BASE_URL', 'https://www.dropbox.com/s/mich3t4rsw2q6hc/')
INSTALLER_BASE_URL = INSTALLER_BASE_URL.rstrip("/") + "/"  # make sure there's a trailing slash
