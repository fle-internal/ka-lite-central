"""

"""
import os

from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import BaseCommand

from django.db.models import Count
from django.db import connection

from ...models import RegistrationProfile

from securesync.models import Zone, SyncSession


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
    
    for registration in regs_per_day:

        while True and all_days:
            day = all_days.pop()
            if day < registration["date"]:
                csv_file.write(
                    "{},{},{},{}\n".format(day, day.strftime("%Y %B"), 0))
            else:
                break
        
        csv_file.write("{},{},{},{}\n".format(registration["date"], registration["date"].strftime("%B %Y"), registration["date"].strftime("%Y-%m"), registration["regs"]))

    csv_file.close()


def top_sync_networks(csv_file):
    """
    Creates a CSV file with registrations per day. It's intended for creating a
    graph from a pivot table in a spreadsheet.
    
    <network name>,<devices>,<syncs>,<avg-syncs-per-device>
    """
    print("Now going through zones...")
    zones = Zone.objects.all().annotate(
        sessions=Count('devicezone_set__client__client_sessions'),
        devices=Count('devicezone_set__id'),
    ).values("id", "name", "sessions", "devices").order_by('-sessions')
    print("Total zones: {}".format(zones.count()))
    print("Just doing the first 100...")
    for zone in zones[:100]:
        csv_file.write(
            "{},{},{},{}\n".format(zone["name"], zone["devices"], zone["sessions"], zone["sessions"] / zone["devices"]))
    
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
    )

    def handle(self, *args, **options):

        root_folder = os.path.abspath(options["folder"])
        
        now_prefix = datetime.now().strftime("%Y%m%d")
        
        f = open(
            os.path.join(root_folder, "{}_registrations_per_day.csv".format(now_prefix)),
            "w"
        )
        registrations_per_day(f)

        f = open(
            os.path.join(root_folder, "{}_top_sync_networks.csv".format(now_prefix)),
            "w"
        )
        top_sync_networks(f)
