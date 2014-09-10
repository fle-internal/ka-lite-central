"""
"""
import json
from collections import OrderedDict

from annoying.decorators import render_to

from fle_utils.general import sort_version_list
from . import get_language_pack_availability_filepath


@render_to('i18n/language_dashboard.html')
def lanuguage_dashboard(request):
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
    lang_availability = json.load(open(get_language_pack_availability_filepath()))
    ordered_versions = sort_version_list([lang_pack["software_version"] for lang_pack in lang_availability], reverse=True)
    lang_pack_by_version = OrderedDict((version, []) for version in ordered_versions)

    for lang_pack in lang_availability:
        software_version = lang_pack["software_version"]
        del lang_pack["software_version"] # won't be used other than to sort
        lang_pack_by_version[software_version].append(lang_pack)
    context = {
        "lang_pack_by_version": lang_pack_by_version,
        "crowdin_base_url": "https://crowdin.com/project/ka-lite/",
    }
    return context

