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


    def test_sync(self):
        """Add the given fake facility users to each of the given fake facilities.
        If no facilities are given, they are created."""
        with DistributedServer(**self.settings) as d1:
            # model_name = 'kalite.facility.models.Facility'
            # d1.call_command('createmodel', model_name, data='{"name" : "kir1"}',
            #                 output_to_stdout=False,
            #                 output_to_stderr=False)
            # _stdout, stderr, create_ret_code = d1.wait()
            # self.assertEquals(0, create_ret_code)
            # self.assertTrue(_stdout)
            # id = _stdout.strip()
            # # the command shouldn't have printed anything to stderr
            # self.assertFalse(stderr)
            # self.assertTrue(id)

            # # Read the model back
            # d1.call_command('readmodel', model_name, id=id,
            #                 output_to_stdout=False,
            #                 output_to_stderr=False)
            # _stdout, stderr, read_ret_code = d1.wait()
            # self.assertEquals(0, read_ret_code)
            # self.assertTrue(_stdout)
            # # Expecting to see the "name" field to be set to "kir1"
            # self.assertRegexpMatches(_stdout, '"name": "kir1"')

            d1.call_command('register', username="test_user", password="invalid",
                zone=self.test_zone.id)
            d1.wait()
            d1.call_command('syncmodels')
            _stdout, stderr, create_ret_code = d1.wait()
            # # the command shouldn't have printed anything to stderr
            self.assertFalse(stderr)
            # print Facility.objects.all()


        

