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
import pathlib
import polib
import os
import requests
import shutil
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ... import POT_DIRPATH, CROWDIN_API_URL
from fle_utils.general import ensure_dir
from kalite.i18n import get_po_filepath
from kalite.i18n.management.commands import test_wrappings
from kalite import version

logging = settings.LOG

TRANSLATOR_VARIABLE_COMMENT = "Translators: do not change variable names (anything with format %(xxxx)s)."


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
        po_filepaths = run_makemessages(verbosity=options["verbosity"])

        insert_translator_comments(po_filepaths)

        update_templates(po_filepaths)

        if options["upload"]:
            if not getattr(settings, "CROWDIN_PROJECT_KEY", None):
                raise CommandError("CROWDIN_PROJECT_KEY must be set in order to upload.")
            upload_to_crowdin(project_key=settings.CROWDIN_PROJECT_KEY)


def delete_current_templates():
    """Delete existing en po/pot files"""

    logging.info("Deleting English language pot files")
    if os.path.exists(POT_DIRPATH):
        shutil.rmtree(POT_DIRPATH)


def run_makemessages(verbosity=0):

    python_package_dirs = glob.glob(os.path.join(test_wrappings.PROJECT_ROOT, 'ka-lite', 'python-packages', '*'))
    ignored_packages = [os.path.join('*/python-packages/', os.path.basename(pp))
                        for pp in python_package_dirs
                        if os.path.basename(pp) not in ['securesync', 'fle_utils']]

    # Central-specific patterns, added on the distributed versions
    ignore_patterns_py = ignore_patterns_js = ignored_packages + ['*/centralserver/*']

    test_wrappings.run_makemessages(ignore_patterns_py=ignore_patterns_py,
                                    ignore_patterns_js=ignore_patterns_js,
                                    verbosity=verbosity)

    # Return the list of files created.
    return glob.glob(os.path.join(get_po_filepath(lang_code="en"), "*.po"))


def insert_translator_comments(po_filepaths):
    """We want to make sure that translators do not tweak format strings.
    We inserted a comment into relevant translation entries when we
    detect format strings, to try and help guide the translators.
    """
    for po_filepath in po_filepaths:
        logging.debug("Adding translator comments to %s" % po_filepath)
        pofile = polib.pofile(po_filepath)
        for po_entry in pofile:
            if "%(" in po_entry.msgid and "%(" not in po_entry.comment:  # variable detected.
                po_entry.comment += "\n%s" % TRANSLATOR_VARIABLE_COMMENT
        pofile.save()


def update_templates(po_filepaths):
    """Update template po files"""
    logging.info("Copying english po files to %s" % POT_DIRPATH)

    #  post them to exposed URL
    ensure_dir(POT_DIRPATH)
    for po_filepath in po_filepaths:
        pot_filename = os.path.basename(po_filepath) + 't'
        pot_filepath = os.path.join(POT_DIRPATH, pot_filename)
        shutil.copy(po_filepath, pot_filepath)


def upload_to_crowdin(project_key, project_id="ka-lite", update_files_only=False):

    logging.info("Uploading to CrowdIn.")

    # url template for our API calls
    url_template = "{crowdin_api_url}/project/{project_id}/{api_call}"
    get_params = {"key": project_key}

    # first we have to ensure that the directory that we're gonna put
    # our po files in crowdin is present. We also don't care that it fails.
    api_call = "add-directory"
    url = url_template.format(project_id=project_id,
                              crowdin_api_url=CROWDIN_API_URL,
                              api_call=api_call)
    data = {"name": "/versioned/"}
    requests.post(url, params=get_params, data=data)

    api_call = "update-file" if update_files_only else "add-file"

    url = "https://api.crowdin.com/api/project/{project_id}/{api_call}"
    url = url_template.format(project_id=project_id,
                              api_call=api_call)

    version_namespace = "%s.%s" % (version.MAJOR_VERSION, version.MINOR_VERSION)

    pot_path = pathlib.Path(POT_DIRPATH)
    files_to_upload = {
        "files[/versioned/%s-django.po]" % version_namespace: open((pot_path / "django.pot").resolve().__str__()),
        "files[/versioned/%s-djangojs.po]" % version_namespace: open((pot_path / "djangojs.pot").resolve().__str__())
    }
    get_params = {"key": project_key}
    r = requests.post(url, params=get_params, files=files_to_upload)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # This is probably because the files already exist on CrowdIn. If so, just update them.
        if "File with such name is already uploaded" in e.response.text:
            upload_to_crowdin(project_key, update_files_only=True)
