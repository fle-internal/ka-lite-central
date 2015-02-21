from django.conf import settings
from django.template import Library

if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
    from django.contrib.staticfiles.templatetags.staticfiles import static as static_lib
else:
    from django.templatetags.static import static as static_lib

register = Library()


@register.simple_tag
def static(path, with_build=False):
    """
    This is a dummy/passthrough template tag to make templates (such as coach reports) from the
    distributed server work on the central server.
    """
    return static_lib(path)
