"""
This file implements both the central and distributed server sides of
a handshake to download KA data.

Why does the central server have to be involved?
  - because we have exactly one API Key for KA, and we don't want to share it
  with distributed server accounts.
  - because we don't trust KA to keep their API static; by putting the central
  server in the middle, we can easily update, and distributed servers don't break.

Here's how it works:
* On the distributed server, there is a button on the facility user's "account" page with a button"Download data from KA".
* That button has a link to a distributed server url.  The user clicks it.
* That distributed server view sets up a proper URL/request to the central server, then redirects that central server URL.
* The central server tries to authenticate to KA (forwarding users to KA), with a call-back URL when that succeeds.
* The user authenticates with KA, and KA oauth is returned to the central server.
* The central server then uses the KA API to get the user data, interpret it, massage it, and compute (our) relevant quantities.
* The central server then uses a distributed server call-back URL to POST the downloaded user data.
* The distributed server gets that data, loads it, saves it, and then redirects the user--to their account page.
* The account page shows again, this time including the imported KA data
"""
import datetime
import json
import oauth
import os
import requests
import sys
import time
from khanacademy.test_oauth_client import TestOAuthClient
from oauth import OAuthToken

from django.conf import settings; logging = settings.LOG
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

from fle_utils.internet import JsonResponse, JsonResponseMessageError, set_query_params
from kalite.i18n import get_video_id
from kalite.main.models import ExerciseLog, VideoLog
from kalite.shared.decorators import require_login
from kalite.topic_tools import get_node_cache

KHAN_SERVER_URL = "http://www.khanacademy.org"


def start_auth(request):
    """
    Step 1 of oauth authentication: get the REQUEST_TOKEN
    """

    # Redirect to KA, for auth.  They will return to central, and we'll be able to continue
    #   using data from the session
    central_callback_url = request.build_absolute_uri(reverse('update_all_central_callback'))
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    return HttpResponseRedirect(client.start_fetch_request_token(central_callback_url))


def finish_auth(request):
    """
    Step 2 of the oauth authentication: use the REQUEST_TOKEN to get an ACCESS_TOKEN
    """
    params = request.GET
    try:
        request.session["REQUEST_TOKEN"] = OAuthToken(params['oauth_token'], params['oauth_token_secret'])
        request.session["REQUEST_TOKEN"].set_verifier(params['oauth_verifier'])
    except MultiValueDictKeyError as e:
        # we just want to generate a 500 anyway;
        #   nothing we could do here except give a slightly more meaningful error
        raise e

    logging.debug("Getting access token.")
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    request.session["ACCESS_TOKEN"] = client.fetch_access_token(request.session["REQUEST_TOKEN"])
    if not request.session["ACCESS_TOKEN"]:
        raise Exception("Did not get access token.")

    return request.session["ACCESS_TOKEN"]


def get_api_resource(request, resource_url):
    """
    Step 3 of the api process:
    Get the data.
    """
    logging.info("Getting data from khan academy (%s)." % resource_url)
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    start = time.time()
    response = client.access_resource(resource_url, request.session["ACCESS_TOKEN"])
    end = time.time()

    logging.debug("API (%s) time: %s" % (resource_url, end - start))
    data = json.loads(response)
    logging.info("Got %d items from khan academy (%s)." % (len(data), resource_url))

    return data


def update_all_central(request):
    """
    Update can't proceed without authentication.
    Start that process here.
    """

    # TODO-BLOCKER(jamalex): oauth not working right now, so direct the user back with an error
    dest = request.META.get("HTTP_REFERER", "").split("?")[0] or "/"
    dest += "?message=Khan%20Academy%20export%20feature%20not%20currently%20available.%20Please%20try%20later.&message_type=error&message_id=id_khanload"
    return HttpResponseRedirect(dest)

    # Store information in a session
    request.session["distributed_user_id"] = request.GET["user_id"]
    request.session["distributed_callback_url"] = request.GET["callback"]
    request.session["distributed_redirect_url"] = request.next or request.META.get("HTTP_REFERER", "") or "/"
    request.session["distributed_csrf_token"] = request._cookies.get("csrftoken")

    # TODO(bcipolli)
    # Disabled oauth caching, as we don't have a good way
    #   to expire the credentials when a user on the distributed
    #   server logs out.

    #if not "ACCESS_TOKEN" in request.session:
    # Will enter the callback, when it completes.
    logging.debug("starting new authorization handshake")
    return start_auth(request)
    #else:
    #logging.debug("using cached authorization handshake")
    #return update_all_central_callback(request)



def convert_ka_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

def update_all_central_callback(request):
    """
    Callback after authentication.

    Parses out the request token verification.
    Then finishes the request by getting an auth token.
    """
    if not "ACCESS_TOKEN" in request.session:
        finish_auth(request)

    exercises = get_api_resource(request, "/api/v1/user/exercises")
    videos = get_api_resource(request, "/api/v1/user/videos")
    node_cache = get_node_cache()

    # Collate videos
    video_logs = []
    for video in videos:
        # Assume that KA videos are all english-language, not dubbed (for now)
        youtube_id = video.get('video', {}).get('youtube_id', "")
        video_id = get_video_id(youtube_id)  # map from youtube_id to video_id (across all languages)

        # Only save videos with progress
        if not video.get('seconds_watched', None):
            continue

        # Only save video logs for videos that we recognize.
        if video_id not in node_cache["Video"]:
            logging.warn("Skipping unknown video %s" % video_id)
            continue

        try:
            video_logs.append({
                "video_id": video_id,
                "youtube_id": youtube_id,
                "total_seconds_watched": video['seconds_watched'],
                "points": VideoLog.calc_points(video['seconds_watched'], video['duration']),
                "complete": video['completed'],
                "completion_timestamp": convert_ka_date(video['last_watched']) if video['completed'] else None,
            })
            logging.debug("Got video log for %s: %s" % (video_id, video_logs[-1]))
        except KeyError:  #
            logging.error("Could not save video log for data with missing values: %s" % video)

    # Collate exercises
    exercise_logs = []
    for exercise in exercises:
        # Only save exercises that have any progress.
        if not exercise.get('last_done', None):
            continue

        # Only save video logs for videos that we recognize.
        slug = exercise.get('exercise', "")
        if slug not in node_cache['Exercise']:
            logging.warn("Skipping unknown video %s" % slug)
            continue

        try:
            completed = exercise['streak'] >= 10
            basepoints = node_cache['Exercise'][slug][0]['basepoints']
            exercise_logs.append({
                "exercise_id": slug,
                "streak_progress": min(100, 100 * exercise['streak']/10),  # duplicates logic elsewhere
                "attempts": exercise['total_done'],
                "points": ExerciseLog.calc_points(basepoints, ncorrect=exercise['streak'], add_randomness=False),  # no randomness when importing from KA
                "complete": completed,
                "attempts_before_completion": exercise['total_done'] if not exercise['practiced'] else None,  #can't figure this out if they practiced after mastery.
                "completion_timestamp": convert_ka_date(exercise['proficient_date']) if completed else None,
            })
            logging.debug("Got exercise log for %s: %s" % (slug, exercise_logs[-1]))
        except KeyError:
            logging.error("Could not save exercise log for data with missing values: %s" % exercise)

    # POST the data back to the distributed server
    try:

        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        logging.debug("POST'ing to %s" % request.session["distributed_callback_url"])
        response = requests.post(
            request.session["distributed_callback_url"],
            cookies={ "csrftoken": request.session["distributed_csrf_token"] },
            data = {
                "csrfmiddlewaretoken": request.session["distributed_csrf_token"],
                "video_logs": json.dumps(video_logs, default=dthandler),
                "exercise_logs": json.dumps(exercise_logs, default=dthandler),
                "user_id": request.session["distributed_user_id"],
            }
        )
        logging.debug("Response (%d): %s" % (response.status_code, response.content))
    except requests.exceptions.ConnectionError as e:
        return HttpResponseRedirect(set_query_params(request.session["distributed_redirect_url"], {
            "message_type": "error",
            "message": _("Could not connect to your KA Lite installation to share Khan Academy data."),
            "message_id": "id_khanload",
        }))
    except Exception as e:
        return HttpResponseRedirect(set_query_params(request.session["distributed_redirect_url"], {
            "message_type": "error",
            "message": _("Failure to send data to your KA Lite installation: %s") % e,
            "message_id": "id_khanload",
        }))


    try:
        json_response = json.loads(response.content)
        if not isinstance(json_response, dict) or len(json_response) != 1:
            # Could not validate the message is a single key-value pair
            raise Exception(_("Unexpected response format from your KA Lite installation."))
        message_type = json_response.keys()[0]
        message = json_response.values()[0]
    except ValueError as e:
        message_type = "error"
        message = unicode(e)
    except Exception as e:
        message_type = "error"
        message = _("Loading json object: %s") % e

    # If something broke on the distributed server, we have no way to recover.
    #   For now, just show the error to users.
    #
    # Ultimately, we have a message, would like to share with the distributed server.
#    if response.status_code != 200:
#        return HttpResponseServerError(response.content)

    return HttpResponseRedirect(set_query_params(request.session["distributed_redirect_url"], {
        "message_type": message_type,
        "message": message,
        "message_id": "id_khanload",
    }))
