"""
Utility functions for i18n related tasks on the distributed server
"""
import bisect
import glob
import json
import os
import re
import requests
import shutil
from collections_local_copy import OrderedDict, defaultdict

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.http import HttpRequest
from django.utils import translation
from django.views.i18n import javascript_catalog

################################################
###                                          ###
###   NOTE TO US:                            ###
###   main migrations import this file, so   ###
###   we CANNOT import main.models in here.  ###
###                                          ###
################################################
from centralserver.version import VERSION
from fle_utils.general import ensure_dir, softload_json
from kalite.i18n import lcode_to_django_lang, lcode_to_django_dir, lcode_to_ietf, get_language_name, get_langcode_map, get_code2lang_map

AMARA_HEADERS = {
    "X-api-username": getattr(settings, "AMARA_USERNAME", None),
    "X-apikey": getattr(settings, "AMARA_API_KEY", None),
}

SUBTITLES_DATA_ROOT = os.path.join(settings.ROOT_DATA_PATH, "subtitles")
LANGUAGE_PACK_ROOT = os.path.join(settings.MEDIA_ROOT, "language_packs")

LANGUAGE_SRT_SUFFIX = "_download_status.json"
SRTS_JSON_FILEPATH = os.path.join(SUBTITLES_DATA_ROOT, "srts_remote_availability.json")
DUBBED_VIDEOS_MAPPING_FILEPATH = os.path.join(settings.I18N_CENTRAL_DATA_PATH, "dubbed_video_mappings.json")
SUBTITLE_COUNTS_FILEPATH = os.path.join(SUBTITLES_DATA_ROOT, "subtitle_counts.json")
SUPPORTED_LANGUAGES_FILEPATH = os.path.join(settings.I18N_CENTRAL_DATA_PATH, "supported_languages.json")
CROWDIN_CACHE_DIR = os.path.join(settings.PROJECT_PATH, "..", "_crowdin_cache")
LANGUAGE_PACK_BUILD_DIR = os.path.join(settings.ROOT_DATA_PATH, "i18n", "build")

LOCALE_ROOT = settings.LOCALE_PATHS[0]


def get_lang_map_filepath(lang_code):
    return os.path.join(SUBTITLES_DATA_ROOT, "languages", lang_code + LANGUAGE_SRT_SUFFIX)


def get_language_pack_availability_filepath(version=VERSION):
    return os.path.join(LANGUAGE_PACK_ROOT, version, "language_pack_availability.json")


def get_localized_exercise_dirpath(lang_code):
    ka_lang_code = lang_code.lower()
    return os.path.join(get_lp_build_dir(ka_lang_code), "exercises")


def get_localized_exercise_count(lang_code):
    # Used by update_language_packs
    exercise_dir = get_localized_exercise_dirpath(lang_code)
    all_exercises = glob.glob(os.path.join(exercise_dir, "*.html"))
    return len(all_exercises)


def get_lp_build_dir(lang_code=None, version=None):
    global LANGUAGE_PACK_BUILD_DIR
    build_dir = LANGUAGE_PACK_BUILD_DIR
    if lang_code:
        build_dir = os.path.join(build_dir, lang_code)
    if version:
        if not lang_code:
            raise Exception("Must specify lang_code with version")
        build_dir = os.path.join(build_dir, version)

    return build_dir


def get_language_pack_filepath(lang_code, version=VERSION):
    """Returns location on disk of a language pack.

    Args:
        lang_code: string code, ietf format (will be converted)
        version: string (e.g. 0.10.3)

    Returns:
        string: absolute (local) filepath to the requested language pack.
    """
    return os.path.join(LANGUAGE_PACK_ROOT, version, "%s.zip" % lcode_to_ietf(lang_code))


def get_language_pack_metadata_filepath(lang_code, version=VERSION):
    """Returns the location on disk of the metadata associated with a to-be-built language pack.

    Args:
        lang_code: string, ietf format (will be converted)
        version: string (e.g. 0.10.3)

    Returns:
        string: absolute (local) filepath to the requested metadata file.
    """
    lang_code = lcode_to_ietf(lang_code)
    metadata_filename = "%s_metadata.json" % lang_code

    return os.path.join(get_lp_build_dir(lang_code, version=version), metadata_filename)


SUPPORTED_LANGUAGE_MAP = None
def get_supported_language_map(lang_code=None):
    lang_code = lcode_to_ietf(lang_code)
    global SUPPORTED_LANGUAGE_MAP
    if not SUPPORTED_LANGUAGE_MAP:
        with open(SUPPORTED_LANGUAGES_FILEPATH) as f:
            SUPPORTED_LANGUAGE_MAP = json.loads(f.read())

    if not lang_code:
        return SUPPORTED_LANGUAGE_MAP
    else:
        lang_map = defaultdict(lambda: lang_code)
        lang_map.update(SUPPORTED_LANGUAGE_MAP.get(lang_code) or {})
        return lang_map


def get_supported_languages():
    """This function returns all languages manually chosen for i18n support.

    Returns:
        list of language codes (ietf format)
    """
    return get_supported_language_map().keys()


DUBBED_VIDEO_MAP_RAW = None
DUBBED_VIDEO_MAP = None
def get_dubbed_video_map(lang_code=None, force=False):
    """
    Stores a key per language.  Value is a dictionary between video_id and (dubbed) youtube_id
    """
    global DUBBED_VIDEO_MAP, DUBBED_VIDEO_MAP_RAW, DUBBED_VIDEOS_MAPPING_FILEPATH

    if DUBBED_VIDEO_MAP is None or force:
        try:
            if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH) or force:
                try:
                    # Never call commands that could fail from the distributed server.
                    #   Always create a central server API to abstract things (see below)
                    logging.debug("Generating dubbed video mappings.")
                    call_command("generate_dubbed_video_mappings", force=force)
                except Exception as e:
                    if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH):
                        # Unrecoverable error, so raise
                        raise
                    elif DUBBED_VIDEO_MAP:
                        # No need to recover--allow the downstream dude to catch the error.
                        raise
                    else:
                        # We can recover by NOT forcing reload.
                        logging.warn("%s" % e)

            DUBBED_VIDEO_MAP_RAW = softload_json(DUBBED_VIDEOS_MAPPING_FILEPATH, raises=True)
        except Exception as e:
            logging.info("Failed to get dubbed video mappings; defaulting to empty.")
            DUBBED_VIDEO_MAP_RAW = {}  # setting this will avoid triggering reload on every call

        DUBBED_VIDEO_MAP = {}
        for lang_name, video_map in DUBBED_VIDEO_MAP_RAW.iteritems():
            logging.debug("Adding dubbed video map entry for %s (name=%s)" % (get_langcode_map(lang_name), lang_name))
            DUBBED_VIDEO_MAP[get_langcode_map(lang_name)] = video_map

    return DUBBED_VIDEO_MAP.get(lang_code, {}) if lang_code else DUBBED_VIDEO_MAP


def get_srt_url(youtube_id, code):
    return settings.STATIC_URL + "srt/%s/subtitles/%s.srt" % (code, youtube_id)


def get_srt_path(lang_code=None, youtube_id=None):
    """Central server must make srts available at a web-accessible location.

    Now, they share that location, which was published in 0.10.2, and so cannot be changed
    (at least, not from the central-server side)

    Note also that it must use the django-version language code.
    """
    srt_path = os.path.join(settings.STATIC_ROOT, "srt")
    if lang_code:
        srt_path = os.path.join(srt_path, lcode_to_django_dir(lang_code), "subtitles")
    if youtube_id:
        srt_path = os.path.join(srt_path, youtube_id + ".srt")

    return srt_path


def get_subtitle_count(lang_code):
    # Used in API and update_language_packs
    all_srts = glob.glob(os.path.join(get_srt_path(lang_code=lang_code), "*.srt"))
    return len(all_srts)


def get_langs_with_subtitles():
    # Used in cache_subtitles
    subtitles_path = get_srt_path()
    if os.path.exists(subtitles_path):
        return os.listdir(subtitles_path)
    else:
        return []


def scrub_locale_paths():
    # Used in update_language_packs
    for locale_root in settings.LOCALE_PATHS:
        if not os.path.exists(locale_root):
            continue
        for lang in os.listdir(locale_root):
            # Skips if not a directory
            if not os.path.isdir(os.path.join(locale_root, lang)):
                continue
            # If it isn't crowdin/django format, keeeeeeellllllll
            if lang != lcode_to_django_dir(lang):
                logging.info("Deleting %s directory because it does not fit our language code format standards" % lang)
                shutil.rmtree(os.path.join(locale_root, lang))
