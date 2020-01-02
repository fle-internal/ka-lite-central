import csv
import logging
import os

from fle_utils.collections_local_copy import OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.template import RequestContext
from django.db.models import Q, Max, Min

from fle_utils.django_utils.classes import ExtendedModel
from securesync.models import Zone
from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.main.models import AttemptLog, ExerciseLog
from kalite.packages.bundled.fle_utils.general import ensure_dir
from kalite.main.content_rating_models import ContentRating
from kalite.topic_tools.content_models import get_content_item
from securesync.devices.models import Device
from securesync.engine.models import SyncSession


logger = logging.getLogger(__name__)


def get_or_create_user_profile(user):
    assert not user.is_anonymous(), "Should not be calling get_or_create_user_profile with an anonymous user."
    assert user.is_authenticated(), "Should not be calling get_or_create_user_profile with an anonymous user."

    return UserProfile.objects.get_or_create(user=user)[0]

class Organization(ExtendedModel):
    name = models.CharField(verbose_name="org name", max_length=100)
    description = models.TextField(help_text="<br/>How is this organization using KA Lite?", blank=True, )
    url = models.URLField(verbose_name="org URL", help_text="<br/>(optional)", blank=True)
    number = models.CharField(verbose_name="phone", max_length=100, blank=True)
    address = models.TextField(max_length=200, help_text="<br/>Street Address or PO Box, City/Town/Province, Postal Code", blank=True)
    country = models.CharField(max_length=100, blank=True)
    users = models.ManyToManyField(User)
    zones = models.ManyToManyField(Zone)
    owner = models.ForeignKey(User, related_name="owned_organizations", null=True)

    HEADLESS_ORG_NAME = "Unclaimed Networks"
    HEADLESS_ORG_PK = None  # keep the primary key of the headless org around, for efficiency
    HEADLESS_ORG_SAVE_FLAG = "internally_safe_headless_org_save"  # indicates safe save() call


    def add_zone(self, zone):
        return self.zones.add(zone)

    def get_zones(self):
        return self.zones.all().order_by("name")

    def add_member(self, user):
        return self.users.add(user)

    def get_members(self):
        return self.users.all()

    def is_member(self, user):
        return self.users.filter(pk=user.pk).count() > 0

    def __unicode__(self):
        return self.name

    def save(self, owner=None, *args, **kwargs):
        # backwards compatibility
        if not getattr(self, "owner_id", None):
            self.owner = owner
            assert self.owner or self.name == Organization.HEADLESS_ORG_NAME, "Organization must have an owner (save for the 'headless' org)"

        # Make org unique by name, for headless name only.
        #   So make sure that any save() call is coming either
        #   from a trusted source (passing HEADLESS_ORG_SAVE_FLAG),
        #   or doesn't overlap with our safe name
        if self.name == Organization.HEADLESS_ORG_NAME:
            if kwargs.get(Organization.HEADLESS_ORG_SAVE_FLAG, False):
                del kwargs[Organization.HEADLESS_ORG_SAVE_FLAG]  # don't pass it on, it's an error
            elif self.pk != Organization.get_or_create_headless_organization().pk:
                raise Exception("Cannot save to reserved organization name: %s" % Organization.HEADLESS_ORG_NAME)

        super(Organization, self).save(*args, **kwargs)


    @classmethod
    def from_zone(cls, zone):
        """
        Given a zone, figure out which organizations contain it.
        """
        return Organization.objects.filter(zones=zone)


    @classmethod
    def get_or_create_headless_organization(cls, refresh_zones=False):
        """
        Retrieve the organization encapsulating all headless zones.
        """
        if cls.HEADLESS_ORG_PK is not None:
            # Already exists and cached, just query fast and return
            try:
                headless_org = cls.objects.get(pk=cls.HEADLESS_ORG_PK)
            except cls.DoesNotExist:
                raise RuntimeError("Cached organization PK {} which does not exist".format(cls.HEADLESS_ORG_PK))

        else:
            # Potentially inefficient query, so limit this to once per server thread
            # by caching the results.  Here, we've had a cache miss
            headless_orgs = cls.objects.filter(name=cls.HEADLESS_ORG_NAME)
            if not headless_orgs:
                # Cache miss because the org actually doesn't exist.  Create it!
                headless_org = Organization(name=cls.HEADLESS_ORG_NAME)
                headless_org.save(**({cls.HEADLESS_ORG_SAVE_FLAG: True}))
                cls.HEADLESS_ORG_PK = headless_org.pk

            else:
                # Cache miss because it's the first relevant query since this thread started.
                assert len(headless_orgs) == 1, "Cannot have multiple HEADLESS ZONE organizations"
                cls.HEADLESS_ORG_PK = headless_orgs[0].pk
                headless_org = headless_orgs[0]

        # TODO(bcipolli): remove this code!
        #
        # In the future, when we self-register headless zones, we'll
        #    add them directly to the headless organization.
        #    For now, we'll have to do an exhaustive search.
        if refresh_zones:
            headless_org.zones.add(*Zone.get_headless_zones())

        return headless_org


class UserProfile(ExtendedModel):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        """
        Return all organizations that this user manages.

        If this user is a super-user, then the headless org will be appended at the end.
        """
        orgs = OrderedDict()  # no dictionary comprehensions, so have to loop
        for org in self.user.organization_set.all().order_by("name"):  # add in order queries (alphabetical?)
            orgs[org.pk] = org

        # Add a headless organization for superusers, containing
        #   any headless zones.
        # Make sure this is at the END of the list, so it is clearly special.
        if self.user.is_superuser:
            headless_org = Organization.get_or_create_headless_organization(refresh_zones=True)
            orgs[headless_org.pk] = headless_org

        return orgs

    def has_permission_for_object(self, object):

        # super users have access to every object
        if self.user.is_superuser:
            return True

        # we can only grant permissions for syncable models (might be good to raise an exception here instead)
        if not hasattr(object, "get_zone"):
            return False

        # allow access if the object's zone belongs to an org of which the user is a member
        if isinstance(object, Zone):
            zone = object
        else:
            zone = object.get_zone()
        for org in Organization.from_zone(zone):
            if org.is_member(self.user):
                return True

        # if we didn't find any reason to grant access -- don't!
        return False


class OrganizationInvitation(ExtendedModel):
    email_to_invite = models.EmailField(verbose_name="Email of invitee", max_length=75)
    invited_by = models.ForeignKey(User)
    organization = models.ForeignKey(Organization, related_name="invitations")

    class Meta:
        unique_together = ('email_to_invite', 'organization')

    def save(self, *args, **kwargs):
        if self.invited_by and self.organization not in self.invited_by.organization_set.all():
            raise PermissionDenied("User %s does not have permissions to invite people on this organization." % self.invited_by)
        super(OrganizationInvitation, self).save(*args, **kwargs)

    def send(self, request):
        to_email = self.email_to_invite
        sender = settings.CENTRAL_FROM_EMAIL
        cdict = {
            'invited_email': to_email,
            'organization': self.organization,
            'invited_by': self.invited_by,
            'central_server_host': request.get_host(),  # for central server actions, determine DYNAMICALLY to be safe
        }
        # Invite an existing user
        if User.objects.filter(email=to_email).count() > 0:
            subject = render_to_string('central/org_invite_email_subject.txt', cdict, context_instance=RequestContext(request))
            body = render_to_string('central/org_invite_email.txt', cdict, context_instance=RequestContext(request))
        # Invite an unregistered user
        else:
            subject = render_to_string('central/central_invite_email_subject.txt', cdict, context_instance=RequestContext(request))
            body = render_to_string('central/central_invite_email.txt', cdict, context_instance=RequestContext(request))
        send_mail(subject, body, sender, [to_email], fail_silently=False)


class DeletionRecord(ExtendedModel):
    organization = models.ForeignKey(Organization)
    deleter = models.ForeignKey(User, related_name="deletion_actor")
    deleted_user = models.ForeignKey(User, related_name="deletion_recipient", blank=True, null=True)
    deleted_invite = models.ForeignKey(OrganizationInvitation, blank=True, null=True)


class ExportJob(models.Model):

    organization = models.ForeignKey(Organization)
    zone = models.ForeignKey(Zone, null=True, blank=True)
    facility = models.ForeignKey(Facility, null=True, blank=True)
    facility_group = models.ForeignKey(FacilityGroup, null=True, blank=True)
    resource = models.CharField(
        choices=[
            ('user_logs', "User logs"),
            ('attempt_logs', "Attempt logs"),
            ('exercise_logs', "Exercise logs"),
            ('ratings', "Ratings"),
            ('device_logs', "Device logs"),
        ],
        null=False,
        blank=False,
        max_length=32,
    )
    
    requested = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)

    def get_file_path(self):
        root = os.path.join(
            settings.CSV_EXPORT_ROOT,
            str(self.organization.id),
        )
        ensure_dir(root)
        return os.path.join(
            root,
            "{type}-{dtm}-{id}.csv".format(
                type=self.resource,
                dtm=str(self.requested.strftime("%Y%m%d")),
                id=self.id,
            )
        )

    def run(self):
        csv_file = open(self.get_file_path(), 'wb')
        if self.resource == 'user_logs':
            data = self.get_user_logs()
        if self.resource == 'attempt_logs':
            data = self.get_attempt_logs()
        if self.resource == 'exercise_logs':
            data = self.get_exercise_logs()
        if self.resource == 'ratings':
            data = self.get_content_rating()
        if self.resource == 'device_logs':
            data = self.get_device_logs()
        if not data:
            csv_file.write("")
            return
        writer = csv.DictWriter(
            csv_file,
            fieldnames=data[0].keys()
        )
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    def get_user_logs(self):
        """
        Returns a list of dicts for CSV export
        """
        # They must have a zone_id, and may have a facility_id and group_id.
        # Try to filter from most specific, to least
        if self.facility_group:
            queryset = FacilityUser.objects.filter(group=self.facility_group)
        elif self.facility:
            queryset = FacilityUser.objects.filter(facility=self.facility)
        elif self.zone:
            # We could have used this queryset method, but in order to be clear
            # and precise, we use the extracted actual query
            # queryset = FacilityUser.objects.by_zone(self.zone)
            queryset = FacilityUser.objects.filter(
                Q(signed_by__devicezone__zone=self.zone, signed_by__devicezone__revoked=False) | \
                Q(signed_by__devicemetadata__is_trusted=True, zone_fallback=self.zone)
            )

        else:
            queryset = FacilityUser.objects.filter(
                Q(signed_by__devicezone__zone__organization=self.organization, signed_by__devicezone__revoked=False) | \
                Q(signed_by__devicemetadata__is_trusted=True, zone_fallback__organization=self.organization)
            )

        # Prefetch the facility relation
        queryset = queryset.select_related('facility')

        data = []
        
        for user in queryset:
            data.append({
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "facility_name": user.facility.name,
                "default_language": user.default_language,
                "is_teacher": user.is_teacher,
                "facility_id": user.facility.id,
                "id": user.id,
            })
        
        return data
        
    def get_exercise_logs(self):

        if self.facility_group:
            queryset = ExerciseLog.objects.filter(user__group=self.facility_group)
        elif self.facility:
            queryset = ExerciseLog.objects.filter(user__facility=self.facility)
        elif self.zone:
            queryset = ExerciseLog.objects.filter(
                Q(user__signed_by__devicezone__zone=self.zone, user__signed_by__devicezone__revoked=False) | \
                Q(user__signed_by__devicemetadata__is_trusted=True, user__zone_fallback=self.zone)
            )
        else:
            queryset = ExerciseLog.objects.filter(
                Q(user__signed_by__devicezone__zone__organization=self.organization, user__signed_by__devicezone__revoked=False) | \
                Q(user__signed_by__devicemetadata__is_trusted=True, user__zone_fallback__organization=self.organization)
            )

        # Prefetch the user relation
        queryset = queryset.select_related('user')
        # Prefetch the facility relation
        queryset = queryset.select_related('user__facility')
        
        columns = [
            "user",
            "exercise_id",
            "streak_progress",
            "attempts",
            "points",
            "language",
            "complete",
            "struggling",
            "attempts_before_completion",
            "completion_timestamp",
            "completion_counter",
            "latest_activity_timestamp",
        ]

        data = []
        for log in queryset:
            dct = {}
            for key in columns:
                dct[key] = getattr(log, key)
            user = dct['user']
            
            # Here is a bunch of insane and very costly lookups
            attempt_logs = AttemptLog.objects.filter(user=user, exercise_id=log.exercise_id, context_type__in=["playlist", "exercise"])
            dct["timestamp_first"] = attempt_logs.count() and attempt_logs.aggregate(Min('timestamp'))['timestamp__min'] or None
            dct["timestamp_last"] = attempt_logs.count() and attempt_logs.aggregate(Max('timestamp'))['timestamp__max'] or None
            dct["part1_answered"] = AttemptLog.objects.filter(user=user, exercise_id=log.exercise_id, context_type__in=["playlist", "exercise"]).count()
            dct["part1_correct"] = AttemptLog.objects.filter(user=user, exercise_id=log.exercise_id, correct=True, context_type__in=["playlist", "exercise"]).count()
            dct["part2_attempted"] = AttemptLog.objects.filter(user=user, exercise_id=log.exercise_id, context_type__in=["exercise_fixedblock", "playlist_fixedblock"]).count()
            dct["part2_correct"] = AttemptLog.objects.filter(user=user, exercise_id=log.exercise_id, correct=True, context_type__in=["exercise_fixedblock", "playlist_fixedblock"]).count()
            data.append(dct)
        data = self.annotate_users(data)
        
        logger.info("Created exercises log of {} rows".format(len(data)))
        
        return data

    def get_content_rating(self):

        if self.facility_group:
            queryset = ContentRating.objects.filter(user__group=self.facility_group)
        elif self.facility:
            queryset = ContentRating.objects.filter(user__facility=self.facility)
        elif self.zone:
            queryset = ContentRating.objects.filter(
                Q(user__signed_by__devicezone__zone=self.zone, user__signed_by__devicezone__revoked=False) | \
                Q(user__signed_by__devicemetadata__is_trusted=True, user__zone_fallback=self.zone)
            )
        else:
            queryset = ContentRating.objects.filter(
                Q(user__signed_by__devicezone__zone__organization=self.organization, user__signed_by__devicezone__revoked=False) | \
                Q(user__signed_by__devicemetadata__is_trusted=True, user__zone_fallback__organization=self.organization)
            )

        # Prefetch the user relation
        queryset = queryset.select_related('user')
        # Prefetch the facility relation
        queryset = queryset.select_related('user__facility')

        columns = [
            "user",
            "content_kind",
            "content_id",
            "content_source",
            "quality",
            "difficulty",
            "text",
        ]

        data = []
        for log in queryset:
            dct = {}
            for key in columns:
                dct[key] = getattr(log, key)
            
            # Do a lookup of the title
            content = get_content_item(content_id=log.content_id)
            dct["content_title"] = content.get("title", "Missing title") if content else "Unknown content"

            data.append(dct)

        data = self.annotate_users(data)
        
        logger.info("Exported ratings of {} rows".format(len(data)))
        
        return data

    def get_device_logs(self):
        # Facility and FacilityGroup are a bit unsure in the export since the
        # mapping from facility to zone to device is unsure. We use the
        # Facility.fallback_zone
        zone = None
        if self.zone:
            zone = self.zone
        if self.facility or self.facility_group:
            facility = self.facility or self.facility_group.facility
            zone = facility.fallback_zone

        if zone:
            queryset = Device.objects.filter(
                devicezone__zone=self.zone, devicezone__revoked=False
            )
        else:
            queryset = Device.objects.filter(
                devicezone__zone__organization=self.organization, devicezone__revoked=False
            )

        columns = [
            "name",
            "description",
            "public_key",
            "version",
        ]
        
        data = []

        for log in queryset:
            dct = {}
            for key in columns:
                dct[key] = getattr(log, key)
                all_sessions = SyncSession.objects.filter(client_device__id=log.id)
                last_sync = "Never" if not all_sessions else all_sessions.order_by("-timestamp")[0].timestamp
                dct["last_sync"] = last_sync
                dct["total_sync_sessions"] = len(all_sessions)

            data.append(dct)

        logger.info("Exported devices of {} rows".format(len(data)))
        
        return data

    def get_attempt_logs(self):
        """
        Fetches all attempt log rows
        """
        if self.facility_group:
            queryset = AttemptLog.objects.filter(user__group=self.facility_group)
        elif self.facility:
            queryset = AttemptLog.objects.filter(user__facility=self.facility)
        elif self.zone:
            queryset = AttemptLog.objects.filter(
                Q(user__signed_by__devicezone__zone=self.zone, user__signed_by__devicezone__revoked=False) | \
                Q(user__signed_by__devicemetadata__is_trusted=True, user__zone_fallback=self.zone)
            )
        else:
            queryset = AttemptLog.objects.filter(
                Q(user__signed_by__devicezone__zone__organization=self.organization, user__signed_by__devicezone__revoked=False) | \
                Q(user__signed_by__devicemetadata__is_trusted=True, user__zone_fallback__organization=self.organization)
            )

        # Prefetch the user relation
        queryset = queryset.select_related('user')
        # Prefetch the facility relation
        queryset = queryset.select_related('user__facility')

        columns = [
            "user",
            "exercise_id",
            "seed",
            "answer_given",
            "points",
            "correct",
            "complete",
            "context_type",
            "context_id",
            "language",
            "timestamp",
            "time_taken",
            "assessment_item_id",
        ]
        data = []
        for log in queryset:
            dct = {}
            for key in columns:
                dct[key] = getattr(log, key)
            data.append(dct)
        data = self.annotate_users(data)

        logger.info("Exported attempt logs of {} rows".format(len(data)))

        return data

    def annotate_users(self, rows):
        for row in rows:
            user = row.pop('user', None)
            if not user:
                continue
            row["username"] = user.username
            row["user_id"] = user.id
            row["facility_name"] = user.facility.name
            row["facility_id"] = user.facility.id
            row["is_teacher"] = user.is_teacher
        return rows

    class Meta:
        verbose_name = "Export Job"
        verbose_name_plural = "Export Jobs"
