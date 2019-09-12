"""
"""
import datetime
import json
import os
from collections import OrderedDict
from distutils.version import StrictVersion

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _

import kalite.version  # for kalite software version
from .models import Organization
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError, JsonResponseMessageSuccess
from fle_utils.internet.decorators import allow_jsonp, api_handle_error_with_json, api_response_causes_reload
from kalite.shared.decorators.auth import require_authorized_admin
from securesync.models import Zone


@require_authorized_admin
@api_response_causes_reload  # must go above @api_handle_error_with_json
def delete_organization(request, org_id):
    org = Organization.objects.get(pk=org_id)
    org.delete()
    return JsonResponseMessageSuccess(_("You have successfully deleted Organization %(org_name)s.") % {"org_name": org.name})


@require_authorized_admin
@api_response_causes_reload  # must go above @api_handle_error_with_json
def delete_zone(request, zone_id):
    zone = Zone.objects.get(id=zone_id)
    zone.soft_delete()
    return JsonResponseMessageSuccess(_("You have successfully deleted Zone %(zone_name)s") % {"zone_name": zone.name})


@allow_jsonp
@api_handle_error_with_json
def get_kalite_version(request):
    assert kalite.version.VERSION in kalite.version.VERSION_INFO

    def versionkey(v):
        '''sorts a version. For now, it sorts them by release date. It returns
        a number in the hundreds range to make space for subsorts, such as version
        number.
        '''
        version, vdata = v
        date = datetime.datetime.strptime(vdata['release_date'], "%Y/%m/%d")
        return date.toordinal() / 1000 # divide by 1000 to turn into 100s range

    request_version = request.GET.get("current_version", "0.10.0")  # default to first version that can understand this.
    needed_updates = [version for version,_ in sorted(kalite.version.VERSION_INFO.iteritems(), key=versionkey) if StrictVersion(request_version) < StrictVersion(version)]    # versions are nice--they sort by string
    return JsonResponse({
        "version": kalite.version.VERSION,
        "version_info": OrderedDict([(v, kalite.version.VERSION_INFO[v]) for v in needed_updates]),
    })
