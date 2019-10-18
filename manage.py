#!/usr/bin/env python
import os
import sys
import warnings

import kalite

sys.path = [
    os.path.join(os.path.dirname(kalite.__file__), 'packages', 'bundled'),
    os.path.join(os.path.dirname(kalite.__file__), 'packages', 'dist'),
] + sys.path

if __name__ == "__main__":

    # We are overriding a few packages (like Django) from the system path.
    #   Suppress those warnings
    warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

    # Also ignore settings-related warning, since it blows up Ansible, and the central server is its own boss.
    warnings.filterwarnings('ignore', message=r'Wrong settings module imported', append=True)

    # Ignore Python-version-related warning, since it blows up Ansible, and the central server is happy with 2.7.6
    warnings.filterwarnings('ignore', message=r'recommended that you install Python version', append=True)

    ########################
    # Run it.
    ########################

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "centralserver.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
