#coding=utf-8
"""
based on: http://www.djangosnippets.org/snippets/1926/
"""
import cgi
from math import floor
from math import copysign; sign = lambda x: copysign(1, x)

from django import template
from django.conf import settings
from django.db.models.query import QuerySet
from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import floatformat
from django.utils import simplejson
from django.utils.safestring import mark_safe

from fle_utils.django_utils.serializers import serialize
from fle_utils.internet.classes import _dthandler


register = template.Library()
@register.simple_tag
def gpsfrac2coord(lat=None, long=None):
    """
    From http://geography.about.com/library/howto/htdegrees.htm

    1. The whole units of degrees will remain the same (i.e. in 121.135° longitude, start with 121°).
    2. Multiply the decimal by 60 (i.e. .135 * 60 = 8.1).
    3. The whole number becomes the minutes (8').
    4. Take the remaining decimal and multiply by 60. (i.e. .1 * 60 = 6).
    5. The resulting number becomes the seconds (6"). Seconds can remain as a decimal.
    6. Take your three sets of numbers and put them together, using the symbols for degrees (°), minutes (‘), and seconds (") (i.e. 121°8'6" longitude)
    """
    assert bool(lat) + bool(long) == 1, "Only specify lat or long"
    dec = float(lat or long)
    direc = ("NS" if lat else "EW")[int((sign(dec) - 1.)/2.)]
    dec = abs(dec)

    dec = abs(dec)
    ndeg = floor(dec)

    dec = max(0., dec - ndeg)
    nmin = floor(dec * 60.)

    dec = max(0., dec - nmin)
    nsec = floor(dec * 60.)

    return cgi.escape("""%d°%d'%d"%s""" % (ndeg, nmin, nsec, direc)).replace("'", "&#39;").replace('"', '&quot;')  # hack to deal with having ' AND " in text