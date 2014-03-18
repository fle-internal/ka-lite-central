from django.conf.urls.defaults import patterns, include, url

import i18n_central.api_urls
import kalite.coachreports.api_urls
import khanload.api_urls  # change to khanload_central


urlpatterns = patterns('central.api_views',
    url(r'^version$', 'get_kalite_version', {}, 'get_kalite_version'),
    url(r'^download/kalite/$', 'get_download_urls', {}, 'get_download_urls'),
)


urlpatterns += patterns('khanload.api_views',  # change to khanload_central
    url(r'^khanload/', include(khanload.api_urls)),# change to khanload_central
)
urlpatterns += patterns('kalite.coachreports.api_views',
    url(r'^coachreports/', include(kalite.coachreports.api_urls)),
)
urlpatterns += patterns('i18n_central.api_views',
    url(r'^i18n/', include(i18n_central.api_urls)),

    # APIs exposed for version compatibility with the previous versions
    # (ARON) to other devs: put in the version you're maintaining compatibility for
    # note: this will also be the canonical endpoint for this, since only old versions need get_subtitle_counts anyway
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}), # v0.10.0: fetching subtitles.
)