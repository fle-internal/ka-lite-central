"""
"""
from django.conf.urls import patterns, include, url

urlpatterns = patterns(__package__ + '.views',
    url(r'^dashboard$', 'lanuguage_dashboard', {}, 'lanuguage_dashboard'),
)
