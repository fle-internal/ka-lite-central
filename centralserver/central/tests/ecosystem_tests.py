import subprocess
from django.conf import settings
from django.contrib.auth.models import make_password
from django.test import LiveServerTestCase
from django.test.utils import override_settings

from .utils.crypto_key_factory import KeyFactory
from .utils.mixins import CreateAdminMixin, CentralServerMixins
from .utils.mixins import FakeDeviceMixin
from .utils.distributed_server_factory import DistributedServer
from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from securesync.models import Device, DeviceZone

FACILITY_MODEL = 'kalite.facility.models.Facility'
GROUP_MODEL = 'kalite.facility.models.FacilityGroup'
FACILITY_USER_MODEL = 'kalite.facility.models.FacilityUser'

DUMMY_PASSWORD = make_password('password', '10000', 'sha1')

# @override_settings(SYNCING_MAX_RECORDS_PER_REQUEST=10)
class SameVersionTests(CreateAdminMixin,
                       CentralServerMixins,
                       FakeDeviceMixin,
                       LiveServerTestCase):

    def setUp(self):
        self.setup_fake_device(name="Central")
        self.user = self.create_admin()
        self.org = self.create_organization(owner=self.user)
        self.zone = self.create_zone(organizations=[self.org])

        self._key_factory = KeyFactory()

        self.settings = {
            'CENTRAL_SERVER_HOST': self.live_server_url,
            'SECURESYNC_PROTOCOL': 'http',
            'SYNCING_MAX_RECORDS_PER_REQUEST': settings.SYNCING_MAX_RECORDS_PER_REQUEST,
        }

    def get_distributed_server(self, **kwargs):

        config = {"key": self._key_factory.next()}
        config.update(self.settings)
        config.update(kwargs)

        return DistributedServer(**config)

    def register(self, dist_server, zone_id=None, noerr=False):
        return dist_server.register(
            username=self.user.username,
            password=self.user.real_password,
            zone_id=zone_id or self.zone.id,
            noerr=noerr
        )

    def test_can_run_on_distributed_server(self):
        with self.get_distributed_server() as d:
            d.validate()

            _stdout, stderr, ret = d.wait()

            # the command shouldn't have printed anything to stderr
            self.assertFalse(stderr)
            self.assertEquals(0, ret, "validate command return non-0 ret code")

    def test_can_instantiate_two_distributed_servers(self):
        d1 = self.get_distributed_server()
        d2 = self.get_distributed_server()

        with d1, d2:
            d1.validate()
            d2.validate()

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

            # Register devices.
            self.register(d1)
            self.register(d2)

            # Create object in d1.
            model_id = d1.addmodel(FACILITY_MODEL, name='kir1')
            self.assertTrue(model_id)

            # Sync d1 with central server.
            d1.sync()

            # The object should not at first exist in d1.
            with self.assertRaises(subprocess.CalledProcessError):
                d2.readmodel(FACILITY_MODEL, id=model_id)

            # now we sync with the second distributed server.
            # we should now have kir1 in here
            d2.sync()
            obj = d2.readmodel(
                FACILITY_MODEL,
                id=model_id,
            )

            self.assertTrue(obj['name'] == 'kir1')

    def test_groups_sync(self):

        # TODO (aron): port to mixins once latest 0.12.0 has been merged
        group_name = 'should-be-synced'

        with self.get_distributed_server() as source:

            self.register(source)

            facility_id = source.addmodel(FACILITY_MODEL, name='fac1')
            group_id = source.addmodel(GROUP_MODEL,
                                       name=group_name,
                                       facility_id=facility_id)
            source.sync()

        # .get() shouldn't raise an error
        FacilityGroup.objects.get(name=group_name)

        with self.get_distributed_server() as sink:

            self.register(sink)

            sink.sync()

            # this should not raise a CalledProcessError
            synced_groups = sink.readmodel(GROUP_MODEL, id=group_id)

            self.assertTrue(synced_groups['id'] == group_id, 'Group has a different ID')

    def test_syncing_of_students_to_another_group_to_central_server(self):
        # Addresses issue #2124 of learningequality/ka-lite

        with self.get_distributed_server() as source:
            self.register(source)

            facility_id = source.addmodel(FACILITY_MODEL,
                                          name='fac1')
            old_group_id = source.addmodel(GROUP_MODEL,
                                           name='group1',
                                           facility_id=facility_id)
            student_password = make_password('password', '10000', 'sha1')
            student_id = source.addmodel(FACILITY_USER_MODEL,
                                         username='student1',
                                         password=student_password,
                                         group_id=old_group_id,
                                         facility_id=facility_id)

            source.sync()

            new_group_name = 'should-transfer-here'
            new_group_id = source.addmodel(GROUP_MODEL,
                                           name=new_group_name,
                                           facility_id=facility_id)
            source.modifymodel(FACILITY_USER_MODEL,
                               student_id,
                               group_id=new_group_id)

            source.sync()

            student = FacilityUser.objects.get(id=student_id)
            self.assertEquals(student.group_id, new_group_id)

    @override_settings(SYNCING_MAX_RECORDS_PER_REQUEST=2)
    def test_more_models_than_batch(self):

        config = {"SYNCING_MAX_RECORDS_PER_REQUEST": settings.SYNCING_MAX_RECORDS_PER_REQUEST}

        with self.get_distributed_server(**config) as d1, self.get_distributed_server(**config) as d2:

            self.register(d1)

            facility_id = d1.addmodel(FACILITY_MODEL, name='fac-%d')


            student_id = d1.addmodel(FACILITY_USER_MODEL,
                                         username='student-%d',
                                         first_name='first-name-%d',
                                         password=DUMMY_PASSWORD,
                                         facility_id=facility_id,
                                         count=5)[0]

            sync_results = d1.sync()

            student = FacilityUser.objects.get(id=student_id)
            student.first_name = "Bob"
            student.zone_fallback = self.zone
            student.save()

            facility = Facility.objects.get(id=facility_id)
            facility.name = "Home"
            facility.zone_fallback = self.zone
            facility.save()

            # student_id = d1.addmodel(FACILITY_USER_MODEL,
            #                              username='student-%db',
            #                              password=DUMMY_PASSWORD,
            #                              facility_id=facility_id,
            #                              count=1)

            # d1.modifymodel(FACILITY_MODEL, facility_id, name="fac1-mod")

            sync_results = d1.sync()

            self.assertEqual(d1.readmodel(FACILITY_USER_MODEL, id=student_id)["first_name"], "Bob")
            self.assertEqual(d1.readmodel(FACILITY_MODEL, id=facility_id)["name"], "Home")

            self.assertEqual(Facility.objects.count(), d1.countmodels(FACILITY_MODEL))
            self.assertEqual(FacilityUser.objects.count(), d1.countmodels(FACILITY_USER_MODEL))

            # sync_results = d2.sync()
            # print sync_results["results"]


            # student = FacilityUser.objects.get(id=student_id)


    def test_central_server_setting_zone_fallback(self):

        with self.get_distributed_server() as d:

            self.register(d)

            facility_id = d.addmodel(FACILITY_MODEL, name='Original')

            d.sync()

            facility = Facility.objects.get(id=facility_id)
            facility.name = "New"
            facility.save()

            sync_results = d.sync()

            self.assertEqual(d.readmodel(FACILITY_MODEL, id=facility_id)["name"], "New")

    def test_soft_deletion_sync_upload(self):

        with self.get_distributed_server() as d:

            self.register(d)

            facility_id = d.addmodel(FACILITY_MODEL, name='Original')

            d.sync()

            d.runcode("from kalite.facility.models import Facility; Facility.objects.get(id='%s').soft_delete()" % facility_id)

            sync_results = d.sync()

            self.assertEqual(sync_results["uploaded"], 1, "Soft-deleted facility was not uploaded")

            facility = Facility.all_objects.get(id=facility_id)
            self.assertTrue(facility.deleted, "Soft-deleted facility not marked as deleted on central server")

    def test_soft_deletion_sync_download(self):

        with self.get_distributed_server() as d:

            self.register(d)

            facility_id = d.addmodel(FACILITY_MODEL, name='Original')

            d.sync()

            Facility.all_objects.get(id=facility_id).soft_delete()

            sync_results = d.sync()

            self.assertEqual(sync_results["downloaded"], 1, "Soft-deleted facility was not downloaded")

            result = d.runcode("from kalite.facility.models import Facility; deleted = Facility.all_objects.get(id='%s').deleted" % facility_id)

            self.assertEqual(result["deleted"], True, "Soft-deleted facility not marked as deleted in distributed server")


    def test_records_created_before_reg_still_sync(self):

        with self.get_distributed_server() as d:

            # Create a facility on central server, in correct zone
            facility_central = Facility(name="Central Facility", zone_fallback=self.zone)
            facility_central.save()

            # Create a facility on distributed server
            facility_distributed_id = d.addmodel(FACILITY_MODEL, name='Distributed Facility')

            self.register(d)

            sync_results = d.sync()

            self.assertEqual(sync_results["downloaded"], 2, "Wrong number of records downloaded") # =2 because DeviceZone is redownloaded
            self.assertEqual(sync_results["uploaded"], 1, "Wrong number of records uploaded")

            self.assertEqual(Facility.objects.filter(id=facility_distributed_id).count(), 1, "Distributed server facility not found centrally.")
            results = d.runcode("from kalite.facility.models import Facility; count = Facility.objects.filter(id='%s').count()" % facility_central.id)
            self.assertEqual(results["count"], 1, "Central server facility not found on distributed.")

    def test_distributed_server_cannot_overwrite_central_device(self):

        with self.get_distributed_server() as d:

            self.register(d)

            sync_results = d.sync()

            results = d.runcode("from securesync.models import Device; d = Device(id='%s', name='Hahaha'); d.save()" % Device.get_own_device().id)

            with self.assertRaises(subprocess.CalledProcessError):
                sync_results = d.sync()

            self.assertNotEqual(Device.get_own_device().name, "Hahaha", "Eek! Distributed server overwrote central server Device.")


    def test_syncing_of_remotely_created_model_modified_locally(self):

        with self.get_distributed_server() as d:

            # Create a facility on central server
            facility_central = Facility(name="Central Facility", zone_fallback=self.zone)
            facility_central.save()

            self.register(d)

            sync_results = d.sync()

            d.modifymodel(FACILITY_MODEL,
                          facility_central.id,
                          name="Central Facility - Mod")

            sync_results = d.sync()

            self.assertEqual(sync_results["uploaded"], 1, "Wrong number of records uploaded")

            self.assertEqual(Facility.objects.get(id=facility_central.id).name, "Central Facility - Mod", "Updated Facility name not synced back to central server")

    @override_settings(DEBUG_ALLOW_DELETIONS=True)
    def test_bad_registration_handled_gracefully(self):
        """
        Testing issue 2872. Redirect loop can happen when there is:
        * An entry in `securesync_device` but not `securesync_devicezone` corresponding to the client_device (on central)
        * But no `securesync_zone` or `securesync_devicezone` in client database
        """
        # Set up a normal registration, then delete rows judiciously to get to right "bad" state.
        config = {"DEBUG_ALLOW_DELETIONS":True}
        with self.get_distributed_server(**config) as d:
            self.register(d)
            sync_results = d.sync()

            d.runcode("from securesync.models import Zone, DeviceZone; Zone.objects.all().delete(); DeviceZone.objects.all().delete()", noerr=True)
            distributed_device_id = d.runcode("from securesync.models import Device; id = Device.get_own_device().id", noerr=True)['id']
           
            DeviceZone.objects.filter(device_id=distributed_device_id).delete()

            # We'll expect a nonzero return value here
            result = self.register(d, noerr=True)
            self.assertFalse("device_already_registered" in result[1] or "AssertionError" in result[1],
                            "If corresponding RegisteredDevicePublicKey exists on server, then gracefully repair the db.")
