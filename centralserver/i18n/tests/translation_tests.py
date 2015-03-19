"""
"""
import glob
import os
import polib
import sys

from mock import MagicMock

from django.conf import settings
from django.core.management import call_command
from django.test import LiveServerTestCase, TestCase
from django.utils import unittest

from .. import POT_DIRPATH

from centralserver.i18n.management.commands.update_language_packs import convert_aws_urls_to_localhost_urls

class UrlConversionTestCase(TestCase):

    def test_poentry_urls_converted(self):
        """ poentry urls should be converted from aws urls to localhost urls """
        poentry = MagicMock(autospec=polib.POEntry)
        poentry.msgid = "I love https://something.aws.org/cat_picture.jpg"
        poentry.msgstr = "Ich liebe https://something.aws.org/cat_picture.jpg"

        poentry = convert_aws_urls_to_localhost_urls(poentry)

        converted_url = "/content/khan/cat_picture.jpg"
        self.assertIn(converted_url, poentry.msgid)
        self.assertIn(converted_url, poentry.msgstr)

class TranslationCommentTestCase(LiveServerTestCase):
    """
    """
    are_pot_files_set_up = False

    def setUp(self):
        if not self.are_pot_files_set_up:
            call_command("update_pot")
            self.are_pot_files_set_up = True

    def test_translation_comments(self):
        """Make sure that any variables within a translation have a comment pasted"""
        anybad = False
        for pot_filepath in glob.glob(os.path.join(POT_DIRPATH, "*.pot")):
            for po_entry in polib.pofile(pot_filepath):
                if "%(" in po_entry.msgid and "%(" not in po_entry.comment:
                    if not anybad:
                        print "Pot file translations that have format strings, but without a comment containing said format string:"
                    print "%s (%s; current comment: %s)" % (pot_filepath, po_entry.msgid, po_entry.comment)
                    anybad = True

        # After printing all bad strings, fail the test.
        self.assertTrue(not anybad, "All pot comments told translators NOT to touch variable names.")
