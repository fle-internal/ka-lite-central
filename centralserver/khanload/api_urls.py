"""
"""
from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns(__package__ + '.api_views',
    # Central server urls
    url(r'^update/central/$', 'update_all_central', {}, 'update_all_central'),
    url(r'^oauth/$', 'update_all_central_callback', {}, 'update_all_central_callback'),
)
