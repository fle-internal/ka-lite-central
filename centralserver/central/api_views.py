"""
"""
import datetime
import json
import os
from collections_local_copy import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

import kalite.version  # for kalite software version
from fle_utils.internet import allow_jsonp, api_handle_error_with_json, JsonResponse, JsonpResponse


@allow_jsonp
@api_handle_error_with_json
def get_kalite_version(request):
    assert kalite.version.VERSION in kalite.version.VERSION_INFO

    request_version = request.GET.get("current_version", "0.10.0")  # default to first version that can understand this.
    needed_updates = [v for v in sorted(kalite.version.VERSION_INFO.keys()) if request_version < v]    # versions are nice--they sort by string
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
