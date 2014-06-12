import subprocess
from django.contrib.auth.models import make_password
from django.test import LiveServerTestCase

from .utils.crypto_key_factory import KeyFactory
from .utils.mixins import CreateAdminMixin, CentralServerMixins
from .utils.mixins import FakeDeviceMixin
from .utils.distributed_server_factory import DistributedServer
from kalite.facility.models import FacilityGroup, FacilityUser


class SameVersionTests(CreateAdminMixin,
                       CentralServerMixins,
                       FakeDeviceMixin,
                       LiveServerTestCase):

    def setUp(self):
        self.setup_fake_device()
        self.user = self.create_admin()
        self.org = self.create_organization(owner=self.user)
        self.zone = self.create_zone(organizations=[self.org])

        self._key_factory = KeyFactory()

        self.settings = {
            'CENTRAL_SERVER_HOST': self.live_server_url,
            'SECURESYNC_PROTOCOL': 'http',
        }

    def get_distributed_server(self, **kwargs):

        config = {"key": self._key_factory.next()}
        config.update(self.settings)
        config.update(kwargs)

        return DistributedServer(**config)

    def test_can_run_on_distributed_server(self):
        with self.get_distributed_server() as d:
            d.call_command('validate')

            _stdout, stderr, ret = d.wait()

            # the command shouldn't have printed anything to stderr
            self.assertFalse(stderr)
            self.assertEquals(0, ret, "validate command return non-0 ret code")

    def test_can_instantiate_two_distributed_servers(self):
        d1 = self.get_distributed_server()
        d2 = self.get_distributed_server()

        with d1, d2:
            d1.call_command('validate')
            d2.call_command('validate')

            _, _, ret1 = d1.wait()
            _, _, ret2 = d2.wait()

            assert ret1 == ret2 == 0

    def test_can_create_one_facility(self):
        with self.get_distributed_server() as d:
            model_id = d.addmodel('kalite.facility.models.Facility',
                                  name='test')

            self.assertTrue(model_id, "addmodel didn't run as intended")

    def test_create_incomplete_facility_fails(self):
        with self.get_distributed_server() as d:
            with self.assertRaises(subprocess.CalledProcessError):
                d.addmodel('kalite.facility.models.Facility')  # lacks a name

    def test_simple_sync_between_two_servers(self):
        d1 = self.get_distributed_server()
        d2 = self.get_distributed_server()
        with d1, d2:
            model_name = 'kalite.facility.models.Facility'

            # Register devices.
            d1.register(
                username=self.user.username,
                password=self.user.real_password,
                zone_id=self.zone.id
            )

            d2.register(
                username=self.user.username,
                password=self.user.real_password,
                zone_id=self.zone.id
            )

            # Create object in d1.
            model_id = d1.addmodel(model_name, name='kir1')
            self.assertTrue(model_id)

            # Sync d1 with central server.
            d1.sync()

            # The object should not at first exist in d1.
            with self.assertRaises(subprocess.CalledProcessError):
                d2.readmodel(model_name, id=model_id)

            # now we sync with the second distributed server.
            # we should now have kir1 in here
            d2.sync()
            obj = d2.readmodel(
                model_name,
                id=model_id,
            )

            self.assertTrue(obj[0]['fields']['name'] == 'kir1')

    def test_groups_sync(self):

        # TODO (aron): port to mixins once latest 0.12.0 has been merged
        group_name = 'should-be-synced'
        facility_model_name = 'kalite.facility.models.Facility'
        group_model_name = 'kalite.facility.models.FacilityGroup'

        with self.get_distributed_server() as source:
            source.register(
                username=self.user.username,
                password=self.user.real_password,
                zone_id=self.zone.id
            )

            facility_id = source.addmodel(facility_model_name, name='fac1')
            group_id = source.addmodel(group_model_name,
                                       name=group_name,
                                       facility_id=facility_id)
            source.sync()

        # .get() shouldn't raise an error
        FacilityGroup.objects.get(name=group_name)

        with self.get_distributed_server() as sink:
            sink.register(
                username=self.user.username,
                password=self.user.real_password,
                zone_id=self.zone.id
            )

            sink.sync()

            # this should not raise a CalledProcessError
            synced_groups = sink.readmodel(group_model_name, id=group_id)

            self.assertTrue(synced_groups[0]['pk'] == group_id,
                            'Group has a different ID')

    def test_syncing_of_students_to_another_group_to_central_server(self):
        # Addresses issue #2124 of learningequality/ka-lite

        facility_model_name = 'kalite.facility.models.Facility'
        group_model_name = 'kalite.facility.models.FacilityGroup'
        student_model_name = 'kalite.facility.models.FacilityUser'

        with self.get_distributed_server() as source:
            source.register(
                username=self.user.username,
                password=self.user.real_password,
                zone_id=self.zone.id
            )

            facility_id = source.addmodel(facility_model_name,
                                          name='fac1')
            old_group_id = source.addmodel(group_model_name,
                                           name='group1',
                                           facility_id=facility_id)
            student_password = make_password('password', '10000', 'sha1')
            student_id = source.addmodel(student_model_name,
                                         username='student1',
                                         password=student_password,
                                         group_id=old_group_id,
                                         facility_id=facility_id)

            source.sync()

            new_group_name = 'should-transfer-here'
            new_group_id = source.addmodel(group_model_name,
                                           name=new_group_name,
                                           facility_id=facility_id)
            source.modifymodel(student_model_name,
                               student_id,
                               group_id=new_group_id)

            source.sync()

            student = FacilityUser.objects.get(id=student_id)
            self.assertEquals(student.group_id, new_group_id)
