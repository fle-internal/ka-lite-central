from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns(__package__ + '.views',
    url(r'^cms/?$', 'show_deployment_cms', {}, 'show_deployment_cms'),
)
