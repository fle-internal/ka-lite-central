"""
"""
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

import centralserver.contact.urls
import centralserver.deployment.urls
import centralserver.faq.urls
import centralserver.registration.urls
import centralserver.stats.api_urls
import centralserver.stats.urls
import fle_utils.feeds.urls
import kalite.coachreports.urls
import kalite.control_panel.urls
import kalite.facility.urls
import securesync.urls
from .import api_urls
from fle_utils.videos import OUTSIDE_DOWNLOAD_BASE_URL  # for video download redirects


admin.autodiscover()

def redirect_to(self, base_url, path=""):
    return HttpResponseRedirect(base_url + path)

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
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^content/(?P<page>\w+)/', 'content_page', {}, 'content_page'), # Example of a new landing page
    url(r'^wiki/(?P<path>.*)$', 'content_page', {"page": "wiki_page", "wiki_site": settings.CENTRAL_WIKI_URL}, 'wiki'),

    url(r'^glossary/$', 'glossary', {}, 'glossary'),

    # The install wizard app has two views: both options available (here)
    #   or an "edition" selected (to get more info, or redirect to download, below)
    #url(r'^download/wizard/$', 'download_wizard', {}, 'download_wizard'),
    #url(r'^download/wizard/(?P<edition>[\w-]+)/$', 'download_wizard', {}, 'download_wizard'),
    #url(r'^download/thankyou/$', 'download_thankyou', {}, 'download_thankyou'),

    # Downloads: public
    url(r'^download/kalite/(?P<version>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    # Downloads: private
    url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/(?P<zone_id>[^\/]+)/$', 'download_kalite_private', {}, 'download_kalite_private'),
    url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/(?P<zone_id>[^\/]+)/(?P<include_data>[^\/]+)/$', 'download_kalite_private', {}, 'download_kalite_private'),

    # The following has been superceded by the stats app, but we
    #   keep it here so that things will function even if that app is removed.
    url(r'^download/videos/(.*)$', lambda request, vpath: HttpResponseRedirect(OUTSIDE_DOWNLOAD_BASE_URL + vpath)),

    url(r'^wiki/installation/$', 'content_page', {"page": "wiki_page", "wiki_site": settings.CENTRAL_WIKI_URL, "path": "/installation/"}, 'install'),

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

urlpatterns += patterns('kalite.control_panel.views',
    # Zone, facility, device
    url(r'^', include(kalite.control_panel.urls)),
)

urlpatterns += patterns('',
    # Reporting
    url(r'^coachreports/', include(kalite.coachreports.urls)),
)

urlpatterns += patterns('',
    url(r'^contact/', include(centralserver.contact.urls)),
    url(r'^faq/', include(centralserver.faq.urls)),
    url(r'^accounts/', include(centralserver.registration.urls)),
)

urlpatterns += patterns('',
    url(r'^stats/', include(centralserver.stats.urls)),
    url(r'^deployments/', include(centralserver.deployment.urls)),
)

handler403 = __package__ + '.views.handler_403'
handler404 = __package__ + '.views.handler_404'
handler500 = __package__ + '.views.handler_500'
