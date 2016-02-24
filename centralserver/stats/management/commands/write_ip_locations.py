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
from django.core.paginator import Paginator

from securesync.models import SyncSession

GEOIPDAT = os.path.join(settings.ROOT_DATA_PATH, "GeoLiteCity.dat")

COUNTRIES = set(["Andorra","United Arab Emirates","Afghanistan","Antigua and Barbuda","Albania","Armenia","Angola","Argentina","Austria","Australia","Azerbaijan","Bosnia and Herzegovina","Barbados","Bangladesh","Belgium","Burkina Faso","Bulgaria","Bahrain","Burundi","Benin","Brunei Darussalam","Bolivia","Brazil","Bahamas","Bhutan","Botswana","Belarus","Belize","Canada","Congo, The Democratic Republic of the","Central African Republic","Congo","Switzerland","Cote D'Ivoire","Chile","Cameroon","China","Colombia","Costa Rica","Cuba","Cape Verde","Cyprus","Czech Republic","Germany","Djibouti","Denmark","Dominica","Dominican Republic","Algeria","Ecuador","Estonia","Egypt","Eritrea","Spain","Ethiopia","Finland","Fiji","Micronesia, Federated States of","France","Gabon","United Kingdom","Grenada","Georgia","Ghana","Gambia","Guinea","Equatorial Guinea","Greece","Guatemala","Guinea-Bissau","Guyana","Honduras","Croatia","Haiti","Hungary","Indonesia","Ireland","Israel","India","Iraq","Iran, Islamic Republic of","Iceland","Italy","Jamaica","Jordan","Japan","Kenya","Kyrgyzstan","Cambodia","Kiribati","Comoros","Saint Kitts and Nevis","Korea, Democratic People's Republic of","Korea, Republic of","Kuwait","Kazakhstan","Lao People's Democratic Republic","Lebanon","Saint Lucia","Liechtenstein","Sri Lanka","Liberia","Lesotho","Lithuania","Luxembourg","Latvia","Libya","Morocco","Monaco","Moldova, Republic of","Montenegro","Madagascar","Marshall Islands","Macedonia","Mali","Myanmar","Mongolia","Mauritania","Malta","Mauritius","Maldives","Malawi","Mexico","Malaysia","Mozambique","Namibia","Niger","Nigeria","Nicaragua","Netherlands","Norway","Nepal","Nauru","New Zealand","Oman","Panama","Peru","Papua New Guinea","Philippines","Pakistan","Poland","Portugal","Palau","Paraguay","Qatar","Romania","Serbia","Russian Federation","Rwanda","Saudi Arabia","Solomon Islands","Seychelles","Sudan","Sweden","Singapore","Slovenia","Slovakia","Sierra Leone","San Marino","Senegal","Somalia","Suriname","South Sudan","Sao Tome and Principe","El Salvador","Syrian Arab Republic","Swaziland","Chad","Togo","Thailand","Tajikistan","Timor-Leste","Turkmenistan","Tunisia","Tonga","Turkey","Trinidad and Tobago","Tuvalu","Taiwan","Tanzania, United Republic of","Ukraine","Uganda","United States","Uruguay","Uzbekistan","Holy See (Vatican City State)","Saint Vincent and the Grenadines","Venezuela","Vietnam","Vanuatu","Samoa","Yemen","South Africa","Zambia","Zimbabwe"])
TERRITORIES = set(["Anguilla","Antarctica","American Samoa","Aruba","Aland Islands","Saint Bartelemey","Bermuda","Bonaire, Saint Eustatius and Saba","Bouvet Island","Cocos (Keeling) Islands","Cook Islands","Curacao","Christmas Island","Western Sahara","Falkland Islands (Malvinas)","Faroe Islands","French Guiana","Guernsey","Gibraltar","Greenland","Guadeloupe","South Georgia and the South Sandwich Islands","Guam","Hong Kong","Heard Island and McDonald Islands","Isle of Man","British Indian Ocean Territory","Jersey","Cayman Islands","Saint Martin","Macao","Northern Mariana Islands","Martinique","Montserrat","New Caledonia","Norfolk Island","Niue","French Polynesia","Saint Pierre and Miquelon","Pitcairn","Puerto Rico","Palestinian Territory","Reunion","Saint Helena","Svalbard and Jan Mayen","Sint Maarten","French Southern Territories","Tokelau","Turks and Caicos Islands","United States Minor Outlying Islands","Virgin Islands, British","Virgin Islands, U.S.","Wallis and Futuna","Mayotte","Macau"])

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

        # We paginate to keep memory usage low while loading large chunks of the queryset at once
        pages = Paginator(SyncSession.objects.order_by("timestamp").values("ip", "client_device_id"), 50000)
        for page in range(1, pages.num_pages + 1):
            print "Page", page, "of", pages.num_pages
            for session in pages.page(page).object_list:
                for addr in session["ip"].split(","):
                    addr = addr.strip()

                    if addr not in BLACKLIST:

                        # update the ip_metadata
                        ip_metadata[addr] = ip_metadata.get(addr, {"devices": set([]), "location": None})
                        ip_metadata[addr]["devices"].add(session["client_device_id"])

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
                countries, territories = get_countries_and_territories(locations)
                jsonp = "display_countries(%s); display_territories(%s);" % (json.dumps(list(countries)), json.dumps(list(territories)))
                f.write(jsonp)
                states = get_states(locations)
                missing_countries, missing_territories = get_missing_countries_and_territories(locations)
                print "\nCountries (%d):" % len(countries)
                print "\n".join(sorted(country for country in countries))
                print "\nTerritories (%d):" % len(territories)
                print "\n".join(sorted(territory for territory in territories))
                print ""
                print "\nMissing countries (%d):" % len(missing_countries)
                print "\n".join(sorted(country for country in missing_countries))
                print "\nMissing territories (%d):" % len(missing_territories)
                print "\n".join(sorted(territory for territory in missing_territories))

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
        gic = pygeoip.GeoIP(GEOIPDAT)
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

def get_countries_and_territories(locations, continent=None):
    items = set([])
    for record in locations:
        if record:
            if continent and continent != record["continent"]:
                continue
            item_name = record['country_name']
            items.add(item_name)
    items.add("Bhutan") # We know it!
    print "MISSING", items - COUNTRIES.union(TERRITORIES)
    return items.intersection(COUNTRIES), items.intersection(TERRITORIES)

def get_missing_countries_and_territories(locations, continent=None):
    countries, territories = get_countries_and_territories(locations, continent=continent)
    return COUNTRIES - countries, TERRITORIES - territories

def get_states(locations, country=["United States", "U.S.A."]):
    if isinstance(country, basestring):
        country = [country]
    states = set([])
    for record in locations:
        if record and record["country_name"] in country and record["region_name"]:
            states.add(record["region_name"])
    return states
