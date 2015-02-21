"""
Test support harness to make setup.py test work.
"""
import importlib
import pathlib

from django.conf import settings
from django.db.models import get_apps
from django.test.simple import DjangoTestSuiteRunner, build_test, build_suite
from django.test.utils import setup_test_environment, teardown_test_environment
from django.utils import unittest


class CentralTestRunner(DjangoTestSuiteRunner):

    def build_suite(self, test_labels=None, *args, **kwargs):

        suite = unittest.TestSuite()
        # we don't do unittest.defaultTestLoader.discover since modules will get double-imported,
        # registering modules twice on the admin app. That's not a good thing.

        # so instead we loop over all apps and use the builtin
        # django function build_suite to find tests within those
        # apps.
        if not test_labels:
            validapps = (app for app in get_apps()
                         if "kalite." not in app.__name__
                         if "securesync." not in app.__name__)
            for validapp in validapps:
                subsuite = build_suite(validapp)
                suite.addTest(subsuite)
        else:
            suite.addTest(self.make_test_suite(test_labels))

        return suite

    def make_test_suite(self, labels):
        suite = unittest.TestSuite()
        for label in labels:
            suite.addTests(self.collect_tests_for_label(label))

        return suite

    def collect_tests_for_label(self, label):
        return unittest.defaultTestLoader.loadTestsFromName(label)
