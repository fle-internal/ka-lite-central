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
import subprocess
import sys
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from fle_utils.django_utils import call_command_with_output
from fle_utils.general import ensure_dir
from kalite.i18n import get_po_filepath
from kalite.i18n.management.commands import test_wrappings

POT_PATH = os.path.join(settings.I18N_CENTRAL_DATA_PATH, "pot")


class Command(test_wrappings.Command):
    option_list = BaseCommand.option_list + (
        make_option(
            '--upload',
            '-u',
            dest='upload',
            action="store_true",
            default=False,
            help='Uploads the pot files to crowdin. NOTE: This requires the settings.CROWDIN_KEY to be set to the proper value.',
        ),
    )
    help = 'USAGE: \'python manage.py update_pot\' creates new po file templates, used for translations in crowdin.'

    def handle(self, **options):

        # (safety measure) prevent any english or test translations from being uploaded
        delete_current_templates()

        # Create new files
        run_makemessages(verbosity=options["verbosity"])

        update_templates()

        if options["upload"]:
            if not getattr(settings, "CROWDIN_PROJECT_KEY", None):
                raise CommandError("CROWDIN_PROJECT_KEY must be set in order to upload.")
            upload_to_crowdin(project_key=settings.CROWDIN_PROJECT_KEY, files={
                os.path.join(POT_PATH, "kalite.pot"): os.path.join("KA Lite UI", "kalite.pot"),
                os.path.join(POT_PATH, "kalitejs.pot"): os.path.join("KA Lite UI", "kalitejs.pot"),
            })


def delete_current_templates():
    """Delete existing en po/pot files"""

    logging.info("Deleting English language pot files")
    if os.path.exists(POT_PATH):
        shutil.rmtree(POT_PATH)


def run_makemessages(verbosity=0):

    python_package_dirs = glob.glob(os.path.join(test_wrappings.PROJECT_ROOT, 'ka-lite', 'python-packages', '*'))
    ignored_packages = [os.path.join('*/python-packages/', os.path.basename(pp)) for pp in python_package_dirs if os.path.basename(pp) not in ['securesync', 'fle_utils']]

    # Central-specific patterns, added on the distributed versions
    ignore_patterns_py = ignore_patterns_js = ignored_packages + ['*/centralserver/*']

    test_wrappings.run_makemessages(ignore_patterns_py=ignore_patterns_py, ignore_patterns_js=ignore_patterns_js, verbosity=verbosity)


def update_templates():
    """Update template po files"""
    logging.info("Copying english po files to %s" % POT_PATH)

    #  post them to exposed URL
    ensure_dir(POT_PATH)
    shutil.copy(get_po_filepath(lang_code="en", filename="django.po"), os.path.join(POT_PATH, "kalite.pot"))
    shutil.copy(get_po_filepath(lang_code="en", filename="djangojs.po"), os.path.join(POT_PATH, "kalitejs.pot"))


def upload_to_crowdin(files, project_key, project_id="ka-lite"):
    for src_filepath, dest_filepath in files.iteritems():
        cmd = ['curl', '-F', 'files[%(dest_filepath)s]=@%(src_filepath)s' % {
            "src_filepath": src_filepath,
            "dest_filepath": dest_filepath,
        },  'http://api.crowdin.net/api/project/%(project_id)s/update-file?key=%(project_key)s' % {
            "project_key": project_key,
            "project_id": project_id,
        }]
        logging.info("Uploading %s" % os.path.basename(src_filepath))
        upload_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        if "success" not in upload_output:
            logging.error("Failed to upload %s: %s" % (src_filepath, upload_output))
