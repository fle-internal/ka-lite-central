import os
import sys
import warnings
import kalite

warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

# Dynamically add bundled KA Lite packages to the path
sys.path = [
    os.path.join(os.path.dirname(kalite.__file__), 'packages', 'bundled'),
    os.path.join(os.path.dirname(kalite.__file__), 'packages', 'dist'),
] + sys.path

from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()
