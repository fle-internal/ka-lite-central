"""
"""
from django.conf import settings
from django.conf.urls import patterns, include, url

from kalite.version import VERSION


urlpatterns = patterns(__package__ + '.views',
    url(r'^dashboard$', 'lanuguage_dashboard', {}, 'lanuguage_dashboard'),
)
