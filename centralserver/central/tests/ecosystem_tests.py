from django.test import LiveServerTestCase

from .utils.distributed_server_factory import DistributedServer


class SameVersionTests(LiveServerTestCase):

    def test_can_run_on_distributed_server(self):
        with DistributedServer() as d1:
            d1.call_command('validate')
            _stdout, stderr = d1.wait()
            # the command shouldn't have printed anything to stderr
            self.assertFalse(stderr)
