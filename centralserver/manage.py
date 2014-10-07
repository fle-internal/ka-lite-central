#!/usr/bin/env python
import glob
import logging
import os
import sys
import warnings

if __name__ == "__main__":
    import warnings

    # We are overriding a few packages (like Django) from the system path.
    #   Suppress those warnings
    warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

    # Now build the paths that point to all of the project pieces
    PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
    PROJECT_PYTHON_PATHS = [
        os.path.join(PROJECT_PATH, "..", "ka-lite-submodule", "python-packages"),  # libraries (python-packages)
        os.path.join(PROJECT_PATH, ".."),  # centralserver.settings
        os.path.join(PROJECT_PATH, "..", 'ka-lite-submodule'),  #kalite.*
        os.path.join(PROJECT_PATH, "..", 'ka-lite-submodule', 'kalite'),  # direct import of modules inside kalite
    ]
    sys.path = [os.path.realpath(p) for p in PROJECT_PYTHON_PATHS] + sys.path


    ########################
    # manual clean_pyc
    ########################

    # Manually clean all pyc files before entering any real codepath
    for root, dirs, files in os.walk(os.path.join(PROJECT_PATH, "..")):
        for pyc_file in glob.glob(os.path.join(root, "*.pyc")):
            try:
                os.remove(pyc_file)
            except:
                pass


    ########################
    # Run it.
    ########################

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "centralserver.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
