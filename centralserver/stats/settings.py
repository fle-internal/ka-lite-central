import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

PROJECT_PATH = os.path.join(os.path.dirname(__file__), '..')
STATS_DATA_PATH = os.path.join(PROJECT_PATH, '..', 'data') #os.path.dirname(__file__), "data")