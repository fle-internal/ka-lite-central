"""
"""
from annoying.decorators import render_to

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from .forms import OrganizationForm, OrganizationInvitationForm, ExportForm
from .models import Organization, OrganizationInvitation, DeletionRecord, get_or_create_user_profile
from fle_utils.feeds.models import FeedListing
from fle_utils.internet.classes import JsonResponseMessageError
from fle_utils.internet.functions import set_query_params
from kalite.control_panel import views as kalite_control_panel_views
from kalite.shared.decorators.auth import require_authorized_admin
from securesync.engine.api_client import SyncClient
from securesync.models import Zone
from centralserver.central.models import ExportJob
from django.http.response import StreamingHttpResponse


@render_to("central/homepage.html")
def homepage(request):
    if getattr(request, "is_logged_in", False):
        return HttpResponseRedirect(reverse("org_management"))
    feed = FeedListing.objects.order_by('-posted_date')[:5]
    return {
        "feed": feed,
    }

@login_required
@render_to("central/org_management.html")
def org_management(request, org_id=None):
    """Management of all organizations for the given user"""

    # get a list of all the organizations this user helps administer
    organizations = get_or_create_user_profile(request.user).get_organizations()

    # add invitation forms to each of the organizations
    for org in organizations.values():
        org.form = OrganizationInvitationForm(initial={"invited_by": request.user})

    # handle a submitted invitation form
    if request.method == "POST":
        form = OrganizationInvitationForm(data=request.POST)
        if form.is_valid():
            # ensure that the current user is a member of the organization to which someone is being invited
            if not form.instance.organization.is_member(request.user):
                raise PermissionDenied(_("Unfortunately for you, you do not have permission to do that."))
            # send the invitation email, and save the invitation record
            form.instance.send(request)
            form.save()
            return HttpResponseRedirect(reverse("org_management"))
        else: # we need to inject the form into the correct organization, so errors are displayed inline
            for __, org in organizations.items():
                if org.pk == int(request.POST.get("organization")):
                    org.form = form

    zones = {}
    
    zones_qs = org.get_zones()
    zones_paginator = Paginator(zones_qs, 20)
    
    page_query = request.GET.get("zones_page", "1")
    
    # Only numeric
    if unicode(page_query).isnumeric():
        page_no = int(page_query)
    else:
        page_no = 1
    
    zone_page = page_no
    
    for org in organizations.values():
        zones[org.pk] = []
        for zone in list(zones_paginator.page(zone_page)):
            zones[org.pk].append({
                "id": zone.id,
                "name": zone.name,
            })
    return {
        "title": _("Account administration"),
        "organizations": organizations,
        "zones": zones,
        "zones_paginator": zones_paginator,
        "zones_page": page_no,
        "HEADLESS_ORG_NAME": Organization.HEADLESS_ORG_NAME,
        "my_invitations": list(OrganizationInvitation.objects \
            .filter(email_to_invite=request.user.email)
            .order_by("organization__name")),
    }


@login_required
def org_invite_action(request, invite_id):
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    org = invite.organization
    if request.user.email != invite.email_to_invite:
        raise PermissionDenied(_("It's not nice to force your way into groups."))
    if request.method == "POST":
        data = request.POST
        if data.get("join"):
            messages.success(request, _("You have joined ") + org.name + _(" as an admin."))
            org.add_member(request.user)
        if data.get("decline"):
            messages.warning(request, _("You have declined to join ") + org.name + _(" as an admin."))
        invite.delete()
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
def delete_admin(request, org_id, user_id):
    org = Organization.objects.get(pk=org_id)
    admin = org.users.get(pk=user_id)
    if org.owner == admin:
        raise PermissionDenied(_("The owner of an organization cannot be removed."))
    if request.user == admin:
        raise PermissionDenied(_("Your personal views are your own, but in this case you are not allowed to delete yourself."))
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_user=admin)
    deletion.save()
    org.users.remove(admin)
    messages.success(request, _("You have successfully removed %(username)s as an administrator for %(org_name)s") % {
         "username": admin.username,
         "org_name": org.name,
    })
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
def delete_invite(request, org_id, invite_id):
    org = Organization.objects.get(pk=org_id)
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_invite=invite)
    deletion.save()
    invite.delete()
    messages.success(request, _("You have successfully revoked the invitation for %(email)s.") % {"email": invite.email_to_invite})
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
@render_to("central/organization_form.html")
def organization_form(request, org_id):
    if org_id != "new":
        org = get_object_or_404(Organization, pk=org_id)
    else:
        org = None
    if request.method == 'POST':
        form = OrganizationForm(data=request.POST, instance=org)
        if form.is_valid():
            # form.instance.owner = form.instance.owner or request.user
            old_org = bool(form.instance.pk)
            form.instance.save(owner=request.user)
            form.instance.users.add(request.user)
            # form.instance.save()
            if old_org:
                return HttpResponseRedirect(reverse("org_management"))
            else:
                return HttpResponseRedirect(reverse("zone_add_to_org", kwargs={"zone_id": "new", "org_id": form.instance.pk}) )
    else:
        form = OrganizationForm(instance=org)
    return {
        'form': form
    }


@require_authorized_admin
@render_to("control_panel/zone_form.html")
def zone_add_to_org(request, zone_id, org_id=None, **kwargs):
    """Add a zone, then add that zone to an organization."""
    org = get_object_or_404(Organization, id=org_id)
    context = kalite_control_panel_views.process_zone_form(request, zone_id=zone_id, **kwargs)

    if request.method == "POST" and context["form"].is_valid():
        zone = context["form"].instance
        if zone not in org.zones.all():
            org.zones.add(zone)

        if zone_id == 'new':
            messages.success(request, _("To connect a KA Lite installation to this new sharing network, visit the server's 'registration' page."))
        return HttpResponseRedirect(reverse("zone_management", kwargs={ "zone_id": zone.id }))

    return context


def get_request_var(request, var_name, default_val="__empty__"):
    """
    Allow getting parameters from the POST object (from submitting a HTML form),
    or on the querystring.

    This isn't very RESTful, but it makes a lot of sense to me!
    """
    return  request.POST.get(var_name, request.GET.get(var_name, default_val))


@login_required
def crypto_login(request):
    """
    Remote admin endpoint, for login to a distributed server (given its IP address; see also securesync/views.py:crypto_login)

    An admin login is negotiated using the nonce system inside SyncSession
    """
    if not request.user.is_superuser:
        raise PermissionDenied()
    ip = request.GET.get("ip", "")
    if not ip:
        return HttpResponseNotFound(_("Please specify an IP (as a GET param)."))
    host = "http://%s/" % ip
    client = SyncClient(host=host, require_trusted=False)
    if client.test_connection() != "success":
        return HttpResponse(_("Unable to connect to a KA Lite server at %s") % host)
    client.start_session()
    if not client.session or not client.session.client_nonce:
        return HttpResponse(_("Unable to establish a session with KA Lite server at %s") % host)
    return HttpResponseRedirect("%ssecuresync/cryptologin/?client_nonce=%s" % (host, client.session.client_nonce))


@require_authorized_admin
@render_to("central/export.html")
def export(request):
    """
    2019-11-25
    This overwrites the previously central+distributed view function in
    kalite.control_panel.views where the same view function was parameterized
    by settings.CENTRAL_SERVER.
    """

    zone_id = request.GET.get("zone_id", "")
    facility_id = request.GET.get("facility_id", "")
    group_id = request.GET.get("group_id", "")

    if 'facility_user' in request.session:
        facility_id = request.session['facility_user'].facility.id

    if zone_id:
        zone = Zone.objects.get(id=zone_id)
    else:
        zone = ""

    all_zones_url = reverse("api_dispatch_list", kwargs={"resource_name": "zone"})
    if zone_id:
        org = Zone.objects.get(id=zone_id).get_org()
        org_id = org.id
    else:
        org_id = request.GET.get("org_id", "")
        if not org_id:
            return HttpResponseNotFound()
        else:
            org = Organization.objects.get(id=org_id)

    if request.method == 'POST':
        form = ExportForm(org, data=request.POST)
        if form.is_valid() and form.cleaned_data['submitted'] > 0:
            job = form.save()
            messages.success(request, _(
                "Job ID {id} was created and will run after {cnt} other jobs "
                "are completed. Please refresh this page to download the CSV data "
                "and expect up to 5-10 minutes before the file is generated."
            ).format(
                id=job.id,
                cnt=ExportJob.objects.exclude(id=job.id).filter(completed=None).count(),
            ))
            # This is not pretty, but the usage of querystring stuff for
            # maintaining state ain't pretty neither. Some old school PHP
            # patterns :)
            return HttpResponseRedirect(
                request.path_info + '?' + request.META['QUERY_STRING']
            )
    else:
        form = ExportForm(org)

    jobs = ExportJob.objects.filter(organization=org)

    context = {
        "form": form,
        "jobs": jobs,
        "org": org,
        "zone": zone,
        "org_id": org_id,
        "zone_id": zone_id,
        "facility_id": facility_id,
        "group_id": group_id,
        "all_zones_url": all_zones_url,
        "is_facility_user": "true" if "facility_user" in request.session else "false",
    }

    return context


@require_authorized_admin
def export_csv(request, jobid=0):
    org_id = request.GET.get("org_id", "")
    job = get_object_or_404(
        ExportJob.objects.filter(organization__id=org_id),
        id=jobid,
    )
    f = open(job.get_file_path(), "r")
    response = StreamingHttpResponse(
        f,
        content_type="text/csv",
    )
    response['Content-Disposition'] = 'attachment; filename="{org}_{type}_{dtm}.csv"'.format(
        org=job.organization.name,
        type=job.resource,
        dtm=job.completed.strftime("%Y%m%d")
    )
    return response

def handler_403(request, *args, **kwargs):
    if request.is_ajax():
        return JsonResponseMessageError(_("You must be logged in with an account authorized to view this page (API)."), status=403)
    else:
        messages.error(request, mark_safe(_("You must be logged in with an account authorized to view this page.")))
        return HttpResponseRedirect(set_query_params(reverse("auth_login"), {"next": request.get_full_path()}))


def test500(request):
    raise RuntimeError("This is a test. The canary is alive.")


def handler_404(request):
    return HttpResponseNotFound(render_to_string("central/404.html", {}, context_instance=RequestContext(request)))


def handler_500(request):
    return HttpResponseServerError(render_to_string("central/500.html", {}, context_instance=RequestContext(request)))
