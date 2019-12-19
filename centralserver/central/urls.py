"""
"""
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.http import HttpResponseRedirect

import centralserver.deployment.urls
import centralserver.i18n.urls
import centralserver.registration.urls
import centralserver.stats.api_urls
import fle_utils.feeds.urls
import kalite.coachreports.urls
import kalite.control_panel.urls
import kalite.dynamic_assets.urls
import kalite.facility.urls
import securesync.urls
from . import api_urls
from fle_utils.videos import OUTSIDE_DOWNLOAD_BASE_URL  # for video download redirects


admin.autodiscover()


# This must be prioritized, to make sure stats are recorded for all necessary urls.
#   If removed, all apps should still function, as appropriate URL confs for each
#   app still exist
urlpatterns = patterns('',
    url(r'^', include(centralserver.stats.api_urls)),  # add at root
)

urlpatterns += patterns('',
    url('r^' ,include(fle_utils.feeds.urls)),
)

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^securesync/', include(securesync.urls)),
    url(r'^securesync/', include(kalite.facility.urls)),
)

# Dynamic assets
urlpatterns += patterns('',
    url(r'^_generated/', include(kalite.dynamic_assets.urls)),
)

urlpatterns += patterns('',
    url(r'^favicon.ico/?$', lambda request: HttpResponseRedirect(settings.STATIC_URL + "images" + request.path)),
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'django.views.static.serve', {
        'document_root': settings.STATIC_ROOT,
    }),
)

urlpatterns += patterns(__package__ + '.views',
    url(r'^test/500/$', 'test500', {}, 'test500'),  # Test for error handling
    url(r'^$', 'homepage', {}, 'homepage'),

    # The following has been superceded by the stats app, but we
    #   keep it here so that things will function even if that app is removed.
    url(r'^download/videos/(.*)$', lambda request, vpath: HttpResponseRedirect(OUTSIDE_DOWNLOAD_BASE_URL + vpath)),

    url(r'^about/$', lambda request: HttpResponseRedirect('http://learningequality.org/'), {}, 'about'),

    # Endpoint for remote admin
    url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'),
)

urlpatterns += patterns(__package__ + '.views',
    # Organization-related stuff.
    url(r'^delete_admin/(?P<org_id>\w+)/(?P<user_id>\w+)/$', 'delete_admin', {}, 'delete_admin'),
    url(r'^delete_invite/(?P<org_id>\w+)/(?P<invite_id>\w+)/$', 'delete_invite', {}, 'delete_invite'),

    url(r'^organization/$', 'org_management', {}, 'org_management'),
    url(r'^organization/(?P<org_id>\w+)/$', 'organization_form', {}, 'organization_form'),
    url(r'^organization/invite_action/(?P<invite_id>\w+)/$', 'org_invite_action', {}, 'org_invite_action'),

    url(r'organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)$', 'zone_add_to_org', {}, 'zone_add_to_org'),
)

urlpatterns += patterns(__package__ + '.api_views',
    url(r'^api/', include(api_urls)),
)

urlpatterns += patterns('centralserver.central.views',
    url(r'^export/$', 'export', {}, 'data_export'),
    url(r'^export/job/(?P<jobid>\d+)/csv/$', 'export_csv', {}, 'data_export_csv'),
)

urlpatterns += patterns('kalite.control_panel.views',
    # Zone, facility, device
    url(r'^', include(kalite.control_panel.urls)),
)

urlpatterns += patterns('',
    # Reporting
    url(r'^coachreports/', include(kalite.coachreports.urls)),
)

urlpatterns += patterns('',
    url(r'^contact/', lambda request: HttpResponseRedirect("https://learningequality.org/ka-lite/map/add/#contact")),
    url(r'^accounts/', include(centralserver.registration.urls)),
)

urlpatterns += patterns('',
    url(r'^deployments/', include(centralserver.deployment.urls)),
    url(r'^languages/', include(centralserver.i18n.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^jsreverse/$', 'django_js_reverse.views.urls_js', name='js_reverse'),
    )

# Dummy URL patterns, to avoid Javascript errors for code coming from the distributed server
urlpatterns += patterns('',
    url(r'^dummy/search/$', lambda request: HttpResponseRedirect("/"), {}, 'search'),
    url(r'^dummy/search_api/(?P<channel>\w+)/$', lambda request: HttpResponseRedirect("/"), {}, 'search_api'),
    url(r'^dummy/learn/$', lambda request: HttpResponseRedirect("/"), {}, 'learn'),
    url(r'^dummy/zone_redirect/$', lambda request: HttpResponseRedirect("/"), {}, 'zone_redirect'),
)

handler403 = __package__ + '.views.handler_403'
handler404 = __package__ + '.views.handler_404'
handler500 = __package__ + '.views.handler_500'
