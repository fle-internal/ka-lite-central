import datetime
import os
from annoying.decorators import render_to
from collections_local_copy import Counter, OrderedDict
from datetime import timedelta  # this is OK; central server code can be 2.7+

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Max, Count, F, Q, Min
from django.utils.translation import ugettext as _

from centralserver.central.models import Organization
from fle_utils.django_utils.paginate import pages_to_show, paginate_data
from kalite.facility.models import Facility
from kalite.shared.decorators import require_authorized_admin
from securesync.models import DeviceZone


@require_authorized_admin
@render_to("deployment/cms.html")
def show_deployment_cms(request):
    """
    This does 3 queries:
    * Facilities, organized by organization.
    * Devices, organized by organization.
    * Organizations, organized by organization.

    It then combines results from these 3 queries to create a list of:
    * All Users that have facilities, have devices but no facilities, and have no devices.
    """

    # Query 1: Organizations
    deployment_data = OrderedDict([(org["id"], {
        "org_name": org["name"],
        "owner": org["owner__username"],
        "total_users": 0,
        "sync_sessions": 0,
        "models_synced": 0,
    }) for org in list(Organization.objects.values("id", "name", "owner__username"))])

    # Query 2: Organizations with users
    for org in list(Organization.objects.values("id", "users__username", "users__first_name", "users__last_name")):
        org_id = org["id"]
        deployment_data[org_id]["users"] = deployment_data[org_id].get("users", {})
        deployment_data[org_id]["users"][org["users__username"]] = {
            "first_name": org["users__first_name"],
            "last_name": org["users__last_name"],
            "email": org["users__username"],
        }

    # Query 3: Organizations with devices
    device_data = DeviceZone.objects \
        .annotate( \
            n_sessions=Count("device__client_sessions"), \
            n_models=Sum("device__client_sessions__models_uploaded")) \
        .values("n_sessions", "n_models", "device__id", "device__name", "zone__id", "zone__name", "zone__organization__id") \
        .order_by("zone__name", "-n_models", "-n_sessions")

    for devzone in list(device_data):
        org_id = devzone["zone__organization__id"]
        if not org_id:
            continue
        deployment_data[org_id]["devices"] = deployment_data[org_id].get("devices", {})
        deployment_data[org_id]["devices"][devzone["device__id"]] = {
            "id": devzone["device__id"],
            "name": devzone["device__name"],
            "zone_name": devzone["zone__name"],
            "zone_id": devzone["zone__id"],
            "models_synced": devzone["n_models"],
            "sync_sessions": devzone["n_sessions"],
        }
        deployment_data[org_id]["models_synced"] += devzone["n_models"] or 0
        deployment_data[org_id]["sync_sessions"] += devzone["n_sessions"] or 0

    # Query 4: Organizations with facilities
    facilities_by_org = list(Facility.objects \
        .filter(signed_by__devicemetadata__is_demo_device=False) \
        .annotate( \
            n_actual_users=Count("facilityuser")) \
        .values( \
            "n_actual_users", \
            "name", "address", \
            "latitude", "longitude", \
            "contact_email", "contact_name", \
            "user_count", \
            "zone_fallback__organization__id", \
            "signed_by__devicezone__zone__organization__id",) \
        .order_by("-n_actual_users"))

    for fac in list(facilities_by_org):
        org_id = fac["signed_by__devicezone__zone__organization__id"] or fac["zone_fallback__organization__id"]
        deployment_data[org_id]["facilities"] = deployment_data[org_id].get("facilities", {})
        deployment_data[org_id]["facilities"][fac["name"]] = fac
        deployment_data[org_id]["total_users"] += fac["n_actual_users"] or 0

    # Combine all data into a single data store.
    paged_data, page_urls = paginate_data(request, deployment_data.values(), page=int(request.GET.get("page", 1)), per_page=int(request.GET.get("per_page", 25)))

    return {
        "pages": sorted(paged_data, key=lambda dep: (dep["total_users"], dep["models_synced"], dep["sync_sessions"]), reverse=True),
        "page_urls": page_urls,
        "title": _("Deployments CMS"),
    }
