from django.conf.urls import patterns, include, url

import centralserver.i18n.api_urls
import centralserver.khanload.api_urls
import kalite.coachreports.api_urls
import kalite.control_panel.api_urls 

from .api_resources import ZoneResource

urlpatterns = patterns(__package__ + '.api_views',
    url(r'^organization/(?P<org_id>\w+)/delete$', 'delete_organization', {}, 'delete_organization'),
    url(r'zone/(?P<zone_id>\w+)/delete$', 'delete_zone', {}, 'delete_zone'),

    url(r'^version$', 'get_kalite_version', {}, 'get_kalite_version'),
    url(r'^download/kalite/$', 'get_download_urls', {}, 'get_download_urls'),

    # Zone TastyPie endpoint
    url(r'^export/', include(ZoneResource().urls)),
)
urlpatterns += patterns('kalite.coachreports.api_views',
    url(r'^coachreports/', include(kalite.coachreports.api_urls)),
)
urlpatterns += patterns('centralserver.i18n.api_views',
    url(r'^i18n/', include(centralserver.i18n.api_urls)),
)
urlpatterns += patterns('centralserver.khanload.api_views',
    url(r'^khanload/', include(centralserver.khanload.api_urls)),
)
# Control panel data export endpoints
urlpatterns += patterns('kalite.control_panel.api_views',
    url(r'^control_panel/', include(kalite.control_panel.api_urls)),
)


# APIs exposed for version compatibility with the previous versions
# (ARON) to other devs: put in the version you're maintaining compatibility for
#
# NOTE: This has been superceded by the same call within the 'stats' app,
#   but this call remains so that if the stats app is removed,
#   this app still functions.
urlpatterns += patterns('centralserver.i18n.api_views',
    # note: this will also be the canonical endpoint for this, since only old versions need get_subtitle_counts anyway
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}), # v0.10.0: fetching subtitles.
)
