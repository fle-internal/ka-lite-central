"""
"""
from django.conf.urls import patterns, include, url

urlpatterns = patterns(__package__ + '.views',
    url(r'^dashboard$', 'language_dashboard', {}, 'language_dashboard'),
)
