"""
"""
import json
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import Http404

from annoying.decorators import render_to

from kalite.version import SHORTVERSION

from fle_utils.general import sort_version_list
from . import get_language_pack_availability_filepath


logging = settings.LOG


@render_to('i18n/language_dashboard.html')
def language_dashboard(request):
    """
        Return context for language dashboard, organized by version

        context = {
            'lang_pack_by_version': [
                '0.12.0': {
                    meta data here....
                }
            ]
        }
    """
    try:
        with open(get_language_pack_availability_filepath()) as f:
            lang_availability = json.load(f)
        ordered_versions = sort_version_list([pack["software_version"] for code, pack in lang_availability.items()], reverse=True)
        lang_pack_by_version = OrderedDict((version, []) for version in ordered_versions)

        for code, pack in lang_availability.items():
            # add a url to download the language pack
            language_code = pack["code"]
            try:
                url = reverse("download_language_pack", kwargs={"version": SHORTVERSION, "lang_code": language_code})
            except NoReverseMatch:
                url = ""
            pack["download_language_url"] = url

            software_version = pack["software_version"]
            del pack["software_version"]  # won't be used other than to sort
            lang_pack_by_version[software_version].append(pack)
        context = {
            "lang_pack_by_version": lang_pack_by_version,
            "crowdin_base_url": "https://crowdin.com/project/ka-lite/"
        }
    except Exception:
        raise Http404
    return context
