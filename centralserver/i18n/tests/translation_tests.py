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

from centralserver.i18n import POT_DIRPATH


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
                if "%(" in po_entry.msgid and po_entry.comment != "Translators: please do not change variable names (anything with the format %(xxxx)s), but it is OK to change its position.":
                    anybad = True
                    print "Bad pot file (%s): %s / %s" % (pot_filepath, po_entry.msgid, po_entry.comment)
        self.assertTrue(anybad, "All pot comments told translators NOT to touch variable names.")
