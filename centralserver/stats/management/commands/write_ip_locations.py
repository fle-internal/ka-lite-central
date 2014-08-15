"""
"""
import csv
import json
import os
import pygeoip
import re
import simplekml

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
        make_option("-k", "--kml",
                    action="store",
                    dest="kml_file",
                    default="",
                    metavar="FILE",
                    help="Output filename for KML file"),
        make_option("-u", "--country_csv",
                    action="store",
                    dest="country_csv",
                    default="",
                    metavar="FILE",
                    help="Output filename for country CSV file"),
        make_option("-o", "--continent_csv",
                    action="store",
                    dest="continent_csv",
                    default="",
                    metavar="FILE",
                    help="Output filename for continent CSV file"),
    )

    def handle(self, *args, **options):

        BLACKLIST = ["", "127.0.0.1"]

        ip_set = set([])

        ips = []

        ip_metadata = {}

        for session in SyncSession.objects.order_by("timestamp"):
            for addr in session.ip.split(","):
                addr = addr.strip()

                if addr not in BLACKLIST:

                    # update the ip_metadata
                    ip_metadata[addr] = ip_metadata.get(addr, {"devices": set([]), "location": None})
                    ip_metadata[addr]["devices"].add(session.client_device.id)

                    # update the list of ips
                    if addr not in ip_set:
                        ips.append(addr)
                        ip_set.add(addr)

        locations, all_locations = ips_to_locations(ips)

        for ip in ips:
            ip_metadata[ip]["location"] = all_locations[ip]

        if options.get("ip_file"):
            with open(options["ip_file"], "w") as f:
                self.stdout.write("Writing list of IPs to %s!\n" % options["ip_file"])
                f.write("\n".join(ips))

        if options.get("location_file"):
            with open(options["location_file"], "w") as f:
                self.stdout.write("Writing locations of IPs as JSONP data to %s!\n" % options["location_file"])
                jsonp = "display_locations(%s);" % json.dumps(locations)
                f.write(jsonp)

        if options.get("location_csv_file"):
            with open(options["location_csv_file"], "w") as f:
                self.stdout.write("Writing locations of IPs as CSV data to %s!\n" % options["location_csv_file"])
                cf = csv.writer(f)
                cf.writerow(["name", "latitude", "longitude", "description"])
                cf.writerows([[r["name"], r["latitude"], r["longitude"], ""] for r in locations])

        if options.get("kml_file"):
            kml = simplekml.Kml()
            for r in locations:
                pnt = kml.newpoint(name=r["name"].split(",")[0], coords=[(r["longitude"], r["latitude"])])
                pnt.style.iconstyle.scale = 5
                pnt.style.iconstyle.color = "ff0000ff"
            kml.save(options["kml_file"])

        if options.get("country_file"):
            with open(options["country_file"], "w") as f:
                self.stdout.write("Writing list of countries as JSONP data to %s!\n" % options["country_file"])
                countries = get_countries(locations)
                jsonp = "display_countries(%s);" % json.dumps(countries)
                f.write(jsonp)
                states = get_states(locations)
                print "Countries (%d):" % len(countries)
                # print "\n".join(sorted(country.replace("United States", "U.S.A. (%d+ states)" % len(states)) for country in countries))
                print "\n".join(sorted(country for country in countries))

        if options.get("country_csv"):
            with open(options["country_csv"], "w") as f:
                counts = count_devices_by_region(ip_metadata, "country_name")
                rows = sorted(counts.items(), key=lambda x: -x[1])
                cc = csv.writer(f)
                cc.writerow(["country", "registered_devices"])
                cc.writerows(rows)

        if options.get("continent_csv"):
            with open(options["continent_csv"], "w") as f:
                counts = count_devices_by_region(ip_metadata, "continent")
                rows = sorted(counts.items(), key=lambda x: -x[1])
                cc = csv.writer(f)
                cc.writerow(["continent", "registered_devices"])
                cc.writerows(rows)

def ips_to_locations(ips):
    locations = []
    all_locations = {}
    existing_locations = set([(0, 0), (None, None)])
    for ip in ips:
        ip = ip.strip()
        record = gic.record_by_addr(ip) or {}
        record["city"] = record.get("city") or ""
        record["region_name"] = record.get("region_name") or ""
        record["country_name"] = record.get("country_name") or ""
        name = [record["city"], record["region_name"], record["country_name"]]
        name = filter(lambda x: not re.match("^\d*$", x), name)
        record["name"] = ", ".join(name)
        all_locations[ip] = record
        if (record.get("latitude"), record.get("longitude")) not in existing_locations:
            locations.append(record)
            existing_locations.add((record["latitude"], record["longitude"]))
    
    return locations, all_locations


COUNTRY_STRINGS_TO_REMOVE = [", Republic of", ", United Republic of", ", Islamic Republic of"]


def count_devices_by_region(ip_metadata, region_field):
    regions = {}
    for ip, data in ip_metadata.items():
        region = data["location"].get(region_field)
        if region and region != "--":
            regions[region] = regions.get(region, set([]))
            regions[region].update(data["devices"])
    for region in regions:
        regions[region] = len(regions[region])
    return regions

def get_countries(locations, continent=None):
    countries = set([])
    for record in locations:
        if record:
            if continent and continent != record["continent"]:
                continue
            country_name = record['country_name']
            for substring in COUNTRY_STRINGS_TO_REMOVE:
                country_name = country_name.replace(substring, "")
            countries.add(country_name)
    return list(countries.union(["Bhutan", "Central African Republic"]) - set(['Anonymous Proxy', 'Satellite Provider', 'Asia/Pacific Region', 'Virgin Islands, U.S.']))

def get_states(locations, country=["United States", "U.S.A."]):
    if isinstance(country, basestring):
        country = [country]
    states = set([])
    for record in locations:
        if record and record["country_name"] in country and record["region_name"]:
            states.add(record["region_name"])
    return states
