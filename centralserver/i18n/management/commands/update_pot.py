"""
CENTRAL SERVER ONLY

This command automates the process of generating template po files, which can be uploaded to crowdin.
It runs the django commands makemessages and compilemessages and moves the created files to an
exposed url, so that they can be downloaded from the web by KA's scripts.

It has an optional flag, -t, which inserts asterisks around the strings in the po files, and
compiles them, so that when you run the server, English has been translated to *English* in the
hope of making it easy to identify unwrapped strings.

This can be run independently of the "update_language_packs" command
"""
import glob
import re
import os
import shutil
import sys
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from fle_utils.django_utils import call_command_with_output
from fle_utils.general import ensure_dir
from kalite.i18n.management.commands import test_wrappings


class Command(test_wrappings.Command):
    help = 'USAGE: \'python manage.py update_pot\' creates new po file templates, used for translations in crowdin.'

    def handle(self, **options):
        # All commands must be run from project root
        test_wrappings.change_dir_to_project_root()

        # (safety measure) prevent any english or test translations from being uploaded
        test_wrappings.delete_current_templates()

        # Create new files
        test_wrappings.run_makemessages()

        update_templates()


def update_templates():
    """Update template po files"""
    logging.info("Copying english po files to %s" % test_wrappings.POT_PATH)

    #  post them to exposed URL
    ensure_dir(test_wrappings.POT_PATH)
    shutil.copy(get_po_filepath(lang_code="en", filename="django.po"), os.path.join(test_wrappings.POT_PATH, "kalite.pot"))
    shutil.copy(get_po_filepath(lang_code="en", filename="djangojs.po"), os.path.join(test_wrappings.POT_PATH, "kalitejs.pot"))
