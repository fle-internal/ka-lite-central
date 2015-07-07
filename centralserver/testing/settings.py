import os

try:
    import local_settings
    from local_settings import *
except ImportError:
    local_settings = object()


########################
# Module-specific settings
########################

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["fast", "medium", "long"])), "TESTS_TO_SKIP must contain only 'fast', 'medium', and 'long'"

CENTRALSERVER_TEST_RUNNER = __package__ + ".testrunner.CentralTestRunner"
TEST_RUNNER = CENTRALSERVER_TEST_RUNNER