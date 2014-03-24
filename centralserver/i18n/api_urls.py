"""
"""
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url

from centralserver.version import VERSION


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^language_packs/available$', 'get_available_language_packs', {"version": VERSION}),
    url(r'^language_packs/available/(?P<version>.*)$', 'get_available_language_packs', {}, 'get_available_language_packs'),

    url(r'^videos/dubbed_video_map$', 'get_dubbed_video_mappings', {}, 'get_dubbed_video_mappings'),
)
