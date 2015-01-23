"""
Test support harness to make setup.py test work.
"""
import importlib
import pathlib

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner, build_test
from django.test.utils import setup_test_environment, teardown_test_environment
from django.utils import unittest


class CentralTestRunner(DjangoTestSuiteRunner):

    def build_suite(self, test_labels=None, *args, **kwargs):

        if not test_labels:
            suite = unittest.defaultTestLoader.discover(settings.PROJECT_PATH, pattern="*.py")
        else:
            # remove all kalite.* apps
            test_labels = [label for label in test_labels if "kalite." not in label]
            suite = self.make_test_suite(test_labels)

        return suite

    def make_test_suite(self, labels):
        suite = unittest.TestSuite()
        for label in labels:
            suite.addTests(self.collect_tests_for_label(label))

        return suite

    def collect_tests_for_label(self, label):
        return unittest.defaultTestLoader.loadTestsFromName(label)
