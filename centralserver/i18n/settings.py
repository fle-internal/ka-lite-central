import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

CROWDIN_PROJECT_ID      = getattr(local_settings, "CROWDIN_PROJECT_ID", None)
CROWDIN_PROJECT_KEY     = getattr(local_settings, "CROWDIN_PROJECT_KEY", None)

KA_CROWDIN_PROJECT_ID      = getattr(local_settings, "KA_CROWDIN_PROJECT_ID", None)
KA_CROWDIN_PROJECT_KEY     = getattr(local_settings, "KA_CROWDIN_PROJECT_KEY", None)

AMARA_USERNAME          = getattr(local_settings, "AMARA_USERNAME", None)
AMARA_API_KEY           = getattr(local_settings, "AMARA_API_KEY", None)

I18N_CENTRAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")