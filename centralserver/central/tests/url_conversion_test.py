"""
"""
import polib

from mock import MagicMock
from django.test import TestCase

from centralserver.i18n.management.commands.update_language_packs import convert_aws_urls_to_localhost_urls

class UrlConversionTestCase(TestCase):

    def test_poentry_urls_converted(self):
        """ poentry urls should be converted from aws urls to localhost urls """
        poentry = MagicMock(autospec=polib.POEntry)
        poentry.msgid = "I love https://something.aws.org/cat_picture.jpg"
        poentry.msgstr = "Ich liebe https://something.aws.org/cat_picture.jpg"
        poentry.msgid_plural = ""
        poentry.msgstr_plural = dict("")

        poentry = convert_aws_urls_to_localhost_urls(poentry)

        converted_url = "/content/khan/cat_picture.jpg"
        self.assertIn(converted_url, poentry.msgid)
        self.assertIn(converted_url, poentry.msgstr)
