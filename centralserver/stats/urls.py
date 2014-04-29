from django.conf.urls import patterns, include, url


urlpatterns = patterns(__package__ + '.views',
    url(r'^logs/$', 'show_logs', {}, 'show_logs'),
    url(r'^syncing/$', 'recent_syncing', {}, 'recent_syncing'),
    url(r'^timelines/$', 'timelines', {}, 'timelines'),
)
