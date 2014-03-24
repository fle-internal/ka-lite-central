from django.conf.urls.defaults import patterns, include, url

import coachreports.api_urls
import i18n_central.api_urls
import khanload_central.api_urls


urlpatterns = patterns('central.api_views',
    url(r'^version$', 'get_kalite_version', {}, 'get_kalite_version'),
    url(r'^download/kalite/$', 'get_download_urls', {}, 'get_download_urls'),
)
urlpatterns += patterns('coachreports.api_views',
    url(r'^coachreports/', include(coachreports.api_urls)),
)
urlpatterns += patterns('i18n_central.api_views',
    url(r'^i18n/', include(i18n_central.api_urls)),
)
urlpatterns += patterns('khanload_central.api_views',
    url(r'^khanload/', include(khanload_central.api_urls)),
)


# APIs exposed for version compatibility with the previous versions
# (ARON) to other devs: put in the version you're maintaining compatibility for
#
# NOTE: This has been superceded by the same call within the 'stats' app,
#   but this call remains so that if the stats app is removed,
#   this app still functions.
urlpatterns += patterns('i18n_central.api_views',
    # note: this will also be the canonical endpoint for this, since only old versions need get_subtitle_counts anyway
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}), # v0.10.0: fetching subtitles.
)
