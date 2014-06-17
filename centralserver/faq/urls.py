from django.conf.urls.defaults import *
from . import views as faq_views

urlpatterns = patterns('',
    url(regex = r'^(?P<topic_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
        view  = faq_views.redirect_to_fle_faq,
        name  = 'faq_redirect',
    ),
)