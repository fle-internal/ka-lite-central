"""

"""
import os

from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import BaseCommand

from django.db.models import Count
from django.db import connection

from ...models import RegistrationProfile


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
        
        registrations_per_day = open(
            os.path.join(root_folder, "{}_registrations_per_day.csv".format(now_prefix)),
            "w"
        )

        total_days = 365*5
        regs_per_day_from = datetime.now() - timedelta(days=total_days)

        truncate_date = connection.ops.date_trunc_sql('date', 'auth_user.date_joined')

        # Note the empty order_by(), that's on purpose to delete any ordering
        # specified on Models, such that we don't mess up GROUP BY.
        regs_per_day = RegistrationProfile.objects.filter(
            activation_key=RegistrationProfile.ACTIVATED,
            user__date_joined__gte=regs_per_day_from
        ).order_by()
        
        regs_per_day = regs_per_day.extra({'date': truncate_date}).values(
            'date'
        ).annotate(
            regs=Count("pk")
        ).values("date", "regs").order_by("date")

        all_days = [datetime.now()-timedelta(days=sub) for sub in range(0, total_days)]
        
        if not regs_per_day.exists():
            print("No registrations found for summary")
        
        for registration in regs_per_day:

            while True:
                day = all_days.pop()
                if day < registration["date"]:
                    registrations_per_day.write("{}, {}\n".format(day, 0))
                else:
                    break
            
            registrations_per_day.write("{}, {}\n".format(registration["date"], registration["regs"]))

        registrations_per_day.close()