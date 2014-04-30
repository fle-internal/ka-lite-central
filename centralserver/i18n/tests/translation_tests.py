"""
"""
import glob
import os
import polib
import sys

from django.conf import settings
from django.core.management import call_command
from django.test import LiveServerTestCase
from django.utils import unittest

from .. import POT_DIRPATH


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
