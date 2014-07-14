"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os

from django.conf import settings
from django.test import LiveServerTestCase, TestCase, Client
from django.core.management import call_command

from .utils.mixins import CreateAdminMixin, CentralServerMixins

class AuthTestCases(LiveServerTestCase, CreateAdminMixin):
    """Check some high-level permission- and login-related scenarios."""

    def setUp(self):
        self.client = Client()
        self.admin_user = self.create_admin()

    def validate_url(self, url, status_code=200, find_str=None):
        resp = self.client.get(url)

        self.assertEquals(resp.status_code, status_code, "%s (status code was %d, should have been %d)" % (url, resp.status_code, status_code))

        if find_str is not None:
            self.assertTrue(find_str in resp.content, "%s (string '%s' not found)" % (url, find_str))

    def test_no_securesync_auth_urls(self):
        self.validate_url("/securesync/login/", 404)
        self.validate_url("/securesync/logout/", 404)

    def test_user_creation_endpoints(self):
        self.validate_url("/securesync/student/", 302)
        self.validate_url("/securesync/teacher/", 302)
        self.validate_url("/securesync/signup/", 404)
        self.validate_url("/accounts/register/", 200)


