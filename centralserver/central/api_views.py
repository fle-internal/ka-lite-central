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
from kalite.shared.decorators import require_authorized_admin
from securesync.models import Zone


@require_authorized_admin
@api_response_causes_reload  # must go above @api_handle_error_with_json
def delete_organization(request, org_id):
    org = Organization.objects.get(pk=org_id)
    num_zones = org.get_zones().count()
    if num_zones > 0:
        return JsonResponseMessageError(_("You cannot delete Organization '%(org_name)s' because it has %(num_zones)s sharing network(s) associated with it.") % {
            "org_name": org.name,
            "num_zones": num_zones,
        })
    else:
        org.delete()
        return JsonResponseMessageSuccess(_("You have successfully deleted Organization %(org_name)s.") % {"org_name": org.name})


@require_authorized_admin
@api_response_causes_reload  # must go above @api_handle_error_with_json
def delete_zone(request, zone_id):
    zone = Zone.objects.get(id=zone_id)
    if zone.has_dependencies(passable_classes=["Organization"]):
        return JsonResponseMessageError(_("You cannot delete Zone '%(zone_name)s' because it is syncing data with with %(num_devices)d device(s)") % {
            "zone_name": zone.name,
            "num_devices": zone.devicezone_set.count(),
        })
    else:
        zone.delete()
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


@allow_jsonp
@api_handle_error_with_json
def get_download_urls(request):
    base_url = "%s://%s" % ("https" if request.is_secure() else "http", request.get_host())

    # TODO: once Dylan makes all subtitle languages available,
    #   don't hard-code this.
    download_sizes = {
        "en": 19.8,
    }

    downloads = {}
    for locale, size in download_sizes.iteritems():
        urlargs = {
            "version": kalite.version.VERSION,
            "platform": "all",
            "locale": locale
        }
        downloads[locale] = {
            "display_name": "",  # Will fill in when language list from subtitles is available.
            "size": size,
            "url": "%s%s" % (base_url, reverse("download_kalite_public", kwargs=urlargs)),
        }

    return JsonResponse(downloads)
