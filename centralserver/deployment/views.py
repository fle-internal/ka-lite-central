import datetime
import os
from annoying.decorators import render_to
from collections_local_copy import Counter, OrderedDict
from datetime import timedelta  # this is OK; central server code can be 2.7+

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Max, Count, F, Q, Min
from django.utils.translation import ugettext as _

from fle_utils.django_utils.paginate import pages_to_show
from kalite.facility.models import Facility
from kalite.shared.decorators import require_authorized_admin


@require_authorized_admin
@render_to("deployment/cms.html")
def show_deployment_cms(request):

    logins_with_facilities = Facility.objects \
        .filter(signed_by__devicemetadata__is_trusted=False, signed_by__devicemetadata__is_demo_device=False) \
        .annotate( \
            n_actual_users=Count("facilityuser")) \
        .values( \
            "n_actual_users", \
            "name", "address", \
            "latitude", "longitude", \
            "contact_email", "contact_name", \
            "user_count",
            "signed_by__devicezone__zone__id", \
            "signed_by__devicezone__zone__organization__users__username", \
            "signed_by__devicezone__zone__organization__users__first_name", \
            "signed_by__devicezone__zone__organization__users__last_name", \
            "signed_by__devicezone__zone__organization__name",) \
        .order_by("-n_actual_users")

        #.extra (select={ \
        #    "facility_name": "name", \
        #    "zone_id": "signed_by__devicezone__zone__id", \
        #    "email": "signed_by__devicezone__zone__organization__users__email", \
        #    "org_name": "signed_by__devicezone__zone__organization__name", })

    def paginate_users(user_list, per_page=25, page=1):
        """
        Create pagination for users
        """
        if not user_list:
            users = []
            page_urls = {}

        else:
            #Create a Django Pagintor from QuerySet
            paginator = Paginator(user_list, per_page)
            try:
                #Try to render the page with the passed 'page' number
                users = paginator.page(page)
                #Call pages_to_show function that selects a subset of pages to link to
                listed_pages = pages_to_show(paginator, page)
            except PageNotAnInteger:
                #If not a proper page number, render page 1
                users = paginator.page(1)
                #Call pages_to_show function that selects a subset of pages to link to
                listed_pages = pages_to_show(paginator, 1)
            except EmptyPage:
                #If past the end of the page range, render last page
                users = paginator.page(paginator.num_pages)
                #Call pages_to_show function that selects a subset of pages to link to
                listed_pages = pages_to_show(paginator, paginator.num_pages)

        if users:
            #Generate URLs for pagination links
            if not users.has_previous():
                previous_page_url = ""
            else:
                #If there are pages before the current page, generate a link for 'previous page'
                prevGETParam = request.GET.copy()
                prevGETParam["page"] = users.previous_page_number()
                previous_page_url = "?" + prevGETParam.urlencode()

            if not users.has_next():
                next_page_url = ""
            else:
                #If there are pages after the current page, generate a link for 'next page'
                nextGETParam = request.GET.copy()
                nextGETParam["page"] = users.next_page_number()
                next_page_url = "?" + nextGETParam.urlencode()

            page_urls = {"next_page": next_page_url, "prev_page": previous_page_url}

            if listed_pages:
                #Generate URLs for other linked to pages
                for listed_page in listed_pages:
                    if listed_page != -1:
                        GETParam = request.GET.copy()
                        GETParam["page"] = listed_page
                        page_urls.update({listed_page: "?" + GETParam.urlencode()})
                users.listed_pages = listed_pages
                users.num_listed_pages = len(listed_pages)

        return users, page_urls

    user_pages, page_urls = paginate_users(logins_with_facilities, page=int(request.GET.get("page", 1)), per_page=int(request.GET.get("per_page", 25)))

    return {
        "user_pages": user_pages,
        "page_urls": page_urls,
        "title": _("Deployments CMS"),
    }
