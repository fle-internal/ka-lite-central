"""

"""
import os

from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import BaseCommand

from django.db.models import Count, Max, Min
from django.db import connection

from ...models import RegistrationProfile

from securesync.models import Zone, Device, UnregisteredDevice
from centralserver.central.models import Organization
from securesync.engine.models import SyncSession


def registrations_per_day(csv_file):
    """
    Creates a CSV file with registrations per day. It's intended for creating a
    graph from a pivot table in a spreadsheet.
    
    <date>,<year-month-humanized>,<year-month-sorted>,<registrations>
    
    Example:
    
    2019-05-05,May 2019,2019-05,2
    2019-05-05,May 2019,2019-05,4
    2019-06-01,June 2019,2019-06,1
    """
    
    total_days = 365 * 5
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    regs_per_day_from = now - timedelta(days=total_days)

    truncate_date = connection.ops.date_trunc_sql('day', 'auth_user.date_joined')

    # Note the empty order_by(), that's on purpose to delete any ordering
    # specified on Models, such that we don't mess up GROUP BY.
    regs_per_day = RegistrationProfile.objects.filter(
        activation_key=RegistrationProfile.ACTIVATED,
        user__date_joined__gte=regs_per_day_from
    ).order_by()
    
    regs_per_day = regs_per_day.extra({'date': truncate_date}).values(
        'date'
    ).annotate(
        regs=Count("user")
    ).values("date", "regs").order_by("date")

    all_days = [now - timedelta(days=sub) for sub in range(0, total_days)]
    
    if not regs_per_day.exists():
        print("No registrations found for summary")
    
    print("Looking into registrations per day. Found {} days with registrations.".format(regs_per_day.count()))
    
    for registration in regs_per_day:

        while True and all_days:
            day = all_days.pop()
            if day < registration["date"]:
                csv_file.write(
                    "{},{},{},{}\n".format(day, day.strftime("%B %Y"), day.strftime("%Y-%m"), 0))
            else:
                break
        
        csv_file.write("{},{},{},{}\n".format(registration["date"], registration["date"].strftime("%B %Y"), registration["date"].strftime("%Y-%m"), registration["regs"]))

    csv_file.close()


def sessions_per_day(csv_file):
    """
    Creates a CSV file with registrations per day. It's intended for creating a
    graph from a pivot table in a spreadsheet.
    
    <date>,<year-month-humanized>,<year-month-sorted>,<registrations>
    
    Example:
    
    2019-05-05,May 2019,2019-05,2
    2019-05-05,May 2019,2019-05,4
    2019-06-01,June 2019,2019-06,1
    """
    
    total_days = 365 * 5
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    sessions_per_day_from = now - timedelta(days=total_days)

    truncate_date = connection.ops.date_trunc_sql('day', 'timestamp')

    # Note the empty order_by(), that's on purpose to delete any ordering
    # specified on Models, such that we don't mess up GROUP BY.
    syncs_per_day = SyncSession.objects.filter(
        timestamp__gte=sessions_per_day_from
    ).order_by()
    
    syncs_per_day = syncs_per_day.extra({'date': truncate_date}).values(
        'date'
    ).annotate(
        syncs=Count("pk")
    ).values("date", "syncs").order_by("date")

    all_days = [now - timedelta(days=sub) for sub in range(0, total_days)]
    
    if not syncs_per_day.exists():
        print("No syncs found for summary")
    
    print("Looking into registrations per day. Found {} days with registrations.".format(syncs_per_day.count()))
    
    for sync in syncs_per_day:

        while True and all_days:
            day = all_days.pop()
            if day < sync["date"]:
                csv_file.write(
                    "{},{},{},{}\n".format(day, day.strftime("%B %Y"), day.strftime("%Y-%m"), 0))
            else:
                break
        
        csv_file.write("{},{},{},{}\n".format(sync["date"], sync["date"].strftime("%B %Y"), sync["date"].strftime("%Y-%m"), sync["syncs"]))

    csv_file.close()


def top_sync_zones(csv_file, min_date=None, order_by="-sessions"):
    """
    Creates a CSV file with the top sync zones. It's intended for creating a
    graph from a pivot table in a spreadsheet.
    
    <network name>,<devices>,<sessions>,<avg-syncs-per-device>,<first_sync>,<last_sync>
    """
    print("Now going through zones...")
    zones = Zone.objects.all()
    
    if min_date:
        zones = zones.filter(devicezone__device__client_sessions__timestamp__gte=min_date)
    
    zones = zones.annotate(
        sessions=Count('devicezone__device__client_sessions__pk'),
        devices=Count('devicezone__pk', distinct=True),
        first_session=Min('devicezone__device__client_sessions__timestamp'),
        last_session=Max('devicezone__device__client_sessions__timestamp'),
    ).values("id", "name", "sessions", "devices", "first_session", "last_session").distinct().order_by(order_by)
    print("Total zones: {}".format(zones.count()))
    print("Just doing the first 100...")
    csv_file.write(
        "Network,Devices,Sessions,Sessions/device,First seen,Last seen,Sessions/day\n"
    )
    for zone in zones[:100]:
        csv_file.write(
            "{},{},{},{},{},{},{}\n".format(
                zone["name"],
                zone["devices"],
                zone["sessions"],
                float(zone["sessions"]) / zone["devices"],
                zone["first_session"].date() if zone["first_session"] else None,
                zone["last_session"].date() if zone["last_session"] else None,
                (zone["last_session"] - zone["first_session"]).days if zone["last_session"] and zone["first_session"] else None,
            )
        )
    
    csv_file.close()


def top_sync_organizations(csv_file, min_date=None, order_by="-sessions"):
    """
    Creates a CSV file with the top sync zones. It's intended for creating a
    graph from a pivot table in a spreadsheet.
    
    <org>,<devices>,<sessions>,<avg-syncs-per-device>,<first_sync>,<last_sync>
    """
    print("Now going through organizations...")
    orgs = Organization.objects.all()
    
    if min_date:
        orgs = orgs.filter(zones__devicezone__device__client_sessions__timestamp__gte=min_date)
    
    orgs = orgs.annotate(
        sessions=Count('zones__devicezone__device__client_sessions__pk'),
        devices=Count('zones__devicezone__pk', distinct=True),
        first_session=Min('zones__devicezone__device__client_sessions__timestamp'),
        last_session=Max('zones__devicezone__device__client_sessions__timestamp'),
    ).values("id", "name", "sessions", "devices", "first_session", "last_session").distinct().order_by(order_by)
    print("Total organizations: {}".format(orgs.count()))
    print("Just doing the first 100...")
    csv_file.write(
        "Network,Devices,Sessions,Sessions/device,First seen,Last seen,Sessions/day\n"
    )
    for org in orgs[:100]:
        csv_file.write(
            "{},{},{},{},{},{},{}\n".format(
                org["name"],
                org["devices"],
                org["sessions"],
                float(org["sessions"]) / org["devices"],
                org["first_session"].date() if org["first_session"] else None,
                org["last_session"].date() if org["last_session"] else None,
                (org["last_session"] - org["first_session"]).days if org["first_session"] and org["last_session"] else None,
            )
        )
    
    csv_file.close()

class Command(BaseCommand):
    help = """
    Exports key statistics in .csv files:
    
    <date>_registrations_per_day.csv
    <date>_top100_sync_networks.csv
    <date>_top100_sync_networks_recent.csv
    """

    option_list = BaseCommand.option_list + (
        make_option('-o', '--folder',
            action='store',
            dest='folder',
            default=".",
            help='Output folder for sync',
        ),
        make_option('-f', '--from-date',
            action='store',
            dest='min_date',
            default=None,
            help='Lower bound on dates',
        ),
    )

    def handle(self, *args, **options):

        root_folder = os.path.abspath(options["folder"])
        
        now_prefix = datetime.now().strftime("%Y%m%d")
        
        # Print out some general statistics
        
        total_organizations = Organization.objects.all().count()
        total_devices = Device.objects.exclude(devicezone__zone__organization=Organization.get_or_create_headless_organization()).values("id").distinct().count()
        total_zones = Zone.objects.all().count()
        unregistered_devices = UnregisteredDevice.objects.all().count()
        unclaimed_devices = Device.objects.filter(devicezone__zone__organization=Organization.get_or_create_headless_organization()).values("id").distinct().count()
        
        print(
            "Total organizations: {}\n".format(total_organizations) +
            "Total devices registered: {}\n".format(total_devices) +
            "Total devices one-click: {}\n".format(unclaimed_devices) +
            "Total devices unregistered: {}\n".format(unregistered_devices) +
            "Total zones: {}\n".format(total_zones)
        )
        
        f = open(
            os.path.join(root_folder, "{}_registrations_per_day.csv".format(now_prefix)),
            "w"
        )
        registrations_per_day(f)

        f = open(
            os.path.join(root_folder, "{}_sessions_per_day.csv".format(now_prefix)),
            "w"
        )
        sessions_per_day(f)

        min_date = options.get("min_date", None)
 
        f = open(
            os.path.join(root_folder, "{}_top_sync_networks_sessions.csv".format(now_prefix)),
            "w"
        )
        top_sync_zones(f, min_date=min_date, order_by="-sessions")
  
        f = open(
            os.path.join(root_folder, "{}_top_sync_networks_devices.csv".format(now_prefix)),
            "w"
        )
        top_sync_zones(f, min_date=min_date, order_by="-devices")

        f = open(
            os.path.join(root_folder, "{}_top_sync_organizations_sessions.csv".format(now_prefix)),
            "w"
        )
        top_sync_organizations(f, min_date=min_date, order_by="-sessions")

        f = open(
            os.path.join(root_folder, "{}_top_sync_organizations_devices.csv".format(now_prefix)),
            "w"
        )
        top_sync_organizations(f, min_date=min_date, order_by="-devices")
