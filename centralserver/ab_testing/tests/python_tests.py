import os
import json
import re

from django.conf import settings
from django.test import LiveServerTestCase, TestCase, Client
from django.core.management import call_command
from django.core.urlresolvers import reverse

from central.models import Organization
from central.tests.utils.mixins import CreateAdminMixin

class ABTestingTestCases(LiveServerTestCase, CreateAdminMixin):
    """
    Test that the dynamic settings are set to appropriate values.
    """

    def setUp(self):
        self.client = Client()
        self.admin_user = self.create_admin()
        success = self.client.login(username=CreateAdminMixin.DEFAULTS["username"], password=CreateAdminMixin.DEFAULTS["password"])
        self.assertTrue(success, "Was not able to login as the admin user")

    def _get_dynamic_settings(self):
        resp = self.client.get(reverse("dynamic_js"))
        self.assertEquals(resp.status_code, 200, "Error loading dynamic settings!")
        # extract the JSON data from the dynamic settings JS file
        ds = json.loads(re.findall("var ds = ([^;]+);", resp.content)[0])
        return ds

    def _create_org(self, name, users):
        org = Organization(name=name, owner=self.admin_user)
        org.save()
        for user in users:
            org.users.add(user)
        return org

    def test_nalanda_package_ds(self):
        """
        Ensure that ds.ab_testing.is_config_package_nalanda is True iff the user belongs to a "Nalanda" org.
        """
        self.assertEquals(self._get_dynamic_settings()["ab_testing"]["is_config_package_nalanda"], False)
        self._create_org("Some other org", users=[self.admin_user])
        self.assertEquals(self._get_dynamic_settings()["ab_testing"]["is_config_package_nalanda"], False)
        self._create_org("Nalanda Project", users=[self.admin_user])
        self.assertEquals(self._get_dynamic_settings()["ab_testing"]["is_config_package_nalanda"], True)

