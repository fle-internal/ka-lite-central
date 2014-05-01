"""
"""
import csv
import json
import os
import pygeoip
import re

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from securesync.models import SyncSession

GEOIPDAT = os.path.join(settings.ROOT_DATA_PATH, "GeoLiteCity.dat")
gic = pygeoip.GeoIP(GEOIPDAT)

class Command(BaseCommand):
    help = "Generate IP address list."

    option_list = BaseCommand.option_list + (
        make_option("-i", "--ips",
                    action="store",
                    dest="ip_file",
                    default="",
                    metavar="FILE",
                    help="Output filename for IP list"),
        make_option("-l", "--locations",
                    action="store",
                    dest="location_file",
                    default="",
                    metavar="FILE",
                    help="Output filename for location list"),
        make_option("-q", "--locations_csv",
                    action="store",
                    dest="location_csv_file",
                    default="",
                    metavar="FILE",
                    help="Output filename for location list CSV file"),
        make_option("-c", "--countries",
                    action="store",
                    dest="country_file",
                    default="",
                    metavar="FILE",
                    help="Output filename for country list"),
    )

    def handle(self, *args, **options):

        ip_set = set(["", "127.0.0.1"])

        ips = []

        for ip in SyncSession.objects.order_by("timestamp").values("ip"):
            for addr in ip["ip"].split(","):
                addr = addr.strip()
                if addr not in ip_set:
                    ips.append(addr)
                    ip_set.add(addr)

        locations = ips_to_locations(ips)

        if options.get("ip_file"):
            with open(options["ip_file"], "w") as f:
                self.stdout.write("Writing list of IPs to %s!\n" % options["ip_file"])
                f.write("\n".join(ips))

        if options.get("location_file"):
            with open(options["location_file"], "w") as f:
                self.stdout.write("Writing locations of IPs as JSONP data to %s!\n" % options["location_file"])
                jsonp = "display_locations(%s);" % json.dumps(locations)
                f.write(jsonp)

        if options.get("location_file"):
            with open(options["location_csv_file"], "w") as f:
                self.stdout.write("Writing locations of IPs as CSV data to %s!\n" % options["location_csv_file"])
                cf = csv.writer(f)
                cf.writerow(["name", "latitude", "longitude", "description"])
                cf.writerows([[r["name"], r["latitude"], r["longitude"], ""] for r in locations])

        if options.get("country_file"):
            with open(options["country_file"], "w") as f:
                self.stdout.write("Writing list of countries as JSONP data to %s!\n" % options["country_file"])
                countries = get_countries(locations)
                jsonp = "display_countries(%s);" % json.dumps(countries)
                f.write(jsonp)
                states = get_states(locations)
                print "Countries (%d):" % len(countries)
                print "\n".join(sorted(country.replace("United States", "U.S.A. (%d+ states)" % len(states)) for country in countries))


def ips_to_locations(ips):
    records = [gic.record_by_addr(item.strip()) for item in ips if item]
    locations = []
    existing_locations = set([(0, 0)])
    for record in records:
        if record:
            if (record["latitude"], record["longitude"]) not in existing_locations:
                record["city"] = record.get("city") or ""
                record["region_name"] = record.get("region_name") or ""
                record["country_name"] = record.get("country_name") or ""
                name = [record["city"], record["region_name"], record["country_name"]]
                name = filter(lambda x: not re.match("^\d*$", x), name)
                record["name"] = ", ".join(name)
                locations.append(record)
                existing_locations.add((record["latitude"], record["longitude"]))
    
    return locations

def get_countries(locations, continent=None):
    countries = set([])
    for record in locations:
        if record:
            if continent and continent != record["continent"]:
                continue
            countries.add(record['country_name'].replace(", Republic of", "").replace(", United Republic of", ""))
    return list(countries.union(["Bhutan", "Central African Republic"]) - set(['Anonymous Proxy', 'Satellite Provider', 'Asia/Pacific Region', 'Virgin Islands, U.S.']))

def get_states(locations, country="United States"):
    states = set([])
    for record in locations:
        if record and record["country_name"] == country and record["region_name"]:
            states.add(record["region_name"])
    return states
