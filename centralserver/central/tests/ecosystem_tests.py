import subprocess
from django.contrib.auth.models import User
from django.test import LiveServerTestCase

from centralserver.central.models import Organization
from securesync.tests import SecuresyncTestCase
from securesync.devices.models import Device, Zone

from .utils.distributed_server_factory import DistributedServer


class SameVersionTests(SecuresyncTestCase, LiveServerTestCase):

    def setUp(self):
        # TODO (aron): move this entire thing into its own mixins
        Device.own_device = None
        self.setUp_fake_device()

        self.user = User.objects.create(username='test_user',
                                        password='invalid_password')
        self.test_org = Organization.objects.create(name='test_org',
                                                    owner=self.user)
        self.test_zone = Zone.objects.create(name='test_zone')
        self.test_zone.organization_set.add(self.test_org)
        self.test_zone.save()

        self.settings = {'CENTRAL_SERVER_HOST': self.live_server_url}

    def test_can_run_on_distributed_server(self):
        with DistributedServer(**self.settings) as d1:
            d1.call_command('validate')

            _stdout, stderr, ret = d1.wait()

            # the command shouldn't have printed anything to stderr
            self.assertFalse(stderr)
            self.assertEquals(0, ret, "validate command return non-0 ret code")

    def test_can_instantiate_two_distributed_servers(self):

        with DistributedServer(**self.settings) as d1, DistributedServer(**self.settings) as d2:
            d1.call_command('validate')
            d2.call_command('validate')

            _, _, ret1 = d1.wait()
            _, _, ret2 = d2.wait()

            assert ret1 == ret2 == 0

    def test_can_create_one_facility(self):
        with DistributedServer(**self.settings) as d:
            model_id = d.addmodel('kalite.facility.models.Facility',
                                  name='test')

            self.assertTrue(model_id, "addmodel didn't run as intended")

    def test_create_incomplete_facility_fails(self):
        with DistributedServer(**self.settings) as d:
            with self.assertRaises(subprocess.CalledProcessError):
                d.addmodel('kalite.facility.models.Facilty')  # lacks a name
