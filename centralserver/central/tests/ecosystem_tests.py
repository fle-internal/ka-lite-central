import subprocess
from django.contrib.auth.models import User
from django.test import LiveServerTestCase

from centralserver.central.models import Organization
from kalite.facility.models import Facility
from securesync.tests import SecuresyncTestCase
from securesync.devices.models import Device, Zone

from .utils.distributed_server_factory import DistributedServer


class SameVersionTests(SecuresyncTestCase, LiveServerTestCase):

    def setUp(self):
        # TODO (aron): move this entire thing into its own mixins
        Device.own_device = None
        self.setUp_fake_device()

        self.user = User.objects.create(username='test_user',
                                        password='invalid')
        self.user.set_password('invalid')
        self.user.save()

        self.test_org = Organization.objects.create(name='test_org',
                                                    owner=self.user)
        self.test_org.users.add(self.user)
        self.test_org.save()

        self.test_zone = Zone.objects.create(name='test_zone')
        self.test_zone.organization_set.add(self.test_org)
        self.test_zone.save()

        self.settings = {
            'CENTRAL_SERVER_HOST': self.live_server_url,
            'SECURESYNC_PROTOCOL': 'http',
        }

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


    def test_sync_two_dist_server_via_central_server(self):
        with DistributedServer(**self.settings) as d1, DistributedServer(**self.settings) as d2:
            model_name = 'kalite.facility.models.Facility'

            # Register devices.
            d1.call_command('register', username="test_user", password="invalid",
                zone=self.test_zone.id)
            d1.wait()

            d2.call_command('register', username="test_user", password="invalid",
                zone=self.test_zone.id)
            d2.wait()

            # Create object in d1.
            model_id = d1.addmodel(model_name, name='kir1')
            self.assertTrue(model_id)

            # Sync d1 with central server.
            d1.sync()

            # The object should not at first exist in d1.
            d2.call_command('readmodel', model_name, id=model_id,
                            output_to_stdout=False,
                            output_to_stderr=False)
            _, _, read_ret_code = d2.wait()
            self.assertEquals(1, read_ret_code)

            # Sync d2 with central server.
            d2.sync()
            # The object now exists in d2.
            d2.call_command('readmodel', model_name, id=model_id,
                            output_to_stdout=False,
                            output_to_stderr=False)
            _stdout, _, _ = d2.wait()
            # Expecting to see the "name" field to be set to "kir1"
            self.assertRegexpMatches(_stdout, '"name": "kir1"')

