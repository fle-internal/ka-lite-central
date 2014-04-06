import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

STATS_DATA_PATH = ROOT_DATA_PATH #os.path.join(os.path.dirname(__file__), "data")