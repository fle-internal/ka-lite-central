"""
"""
import json
import os
import pygeoip

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from securesync.models import SyncSession

GEOIPDAT = os.path.join(settings.ROOT_DATA_PATH, "GeoLiteCity.dat")

class Command(BaseCommand):
    help = "Generate IP address list."

    option_list = BaseCommand.option_list + (
        make_option('-f', '--file',
                    action='store',
                    dest='file',
                    default="",
                    metavar="FILE",
                    help="Output filename"),
        make_option('-l', '--locations',
                    action='store_true',
                    dest='locations',
                    help="Turn IPs into geolocations"),
    )

    def handle(self, *args, **options):

        ips = [addr.strip() for ip in SyncSession.objects.values("ip").distinct() for addr in ip["ip"].split(",")]
        ips = list(set(ips) - set([""]))

        ips = sorted(ips)  # easier for human-readable reviewing for any issues

        filename = options["file"] or ("locations.jsonp" if options["locations"] else "ips.txt")
        with open(filename, "w") as f:
            if options["locations"]:
                self.stdout.write("Mapping IPs to locations and writing JSONP data to %s!\n" % filename)
                locations = ips_to_locations(ips)
                jsonp = "display_locations(%s);" % json.dumps(locations)
                f.write(jsonp)
            else:
                self.stdout.write("Writing list of IPs to %s!\n" % filename)
                f.write("\n".join(ips))

def ips_to_locations(ips):
    gic = pygeoip.GeoIP(GEOIPDAT)
    records = [gic.record_by_addr(item.strip()) for item in ips if item]
    locations = []
    existing_locations = set([(0, 0)])
    for record in records:
        if record:
            if (record['latitude'], record['longitude']) not in existing_locations:
                name = [record['city'], record['region_name'], record['country_name']]
                name = filter(lambda x: not re.match("^\d*$", x), name)
                name = ", ".join(name)
                locations.append({
                    "latitude": record['latitude'],
                    "longitude": record['longitude'],
                    "name": name,
                })
                existing_locations.add((record['latitude'], record['longitude']))
    
    return locations