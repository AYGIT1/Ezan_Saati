#!/usr/local/bin/python3
# <bitbar.title>Prayer Times BitBar</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Aykut ALADAG</bitbar.author>
# <bitbar.author.github>AYGIT1</bitbar.author.github>
# <bitbar.desc>Prayer times are based on Presidency of Religious Affairs, Turkey.</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <bitbar.image></bitbar.image>
# <bitbar.abouturl>https://github.com/AYGIT1/Ezan_Saati</bitbar.abouturl>

import datetime
import json
import sys
import requests
import os

# Redirect stderr to null by default
sys.stderr = open(os.devnull, "w")

# Get script fullpath
SCRIPT_PATH = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"

# For printing to stderr
def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_prayer_times():
    country = "TURKEY"  # Ülke
    province = "ANKARA"  # Şehir
    district = "ANKARA"  # İlçe
    url = "https://ezanvakti.herokuapp.com"

    countries, provinces, districts, prayer = ("",)*4
    try:
        # Find country ID
        countries = requests.get(url + "/ulkeler")
        for data_country in countries.json():
            if data_country["UlkeAdiEn"] == country.upper():
                country_id = data_country["UlkeID"]

        # Find province ID
        provinces = requests.get(url + f"/sehirler?ulke={country_id}")
        for data_province in provinces.json():
            if data_province["SehirAdiEn"] == province.upper():
                province_id = data_province["SehirID"]

        # Find district ID
        districts = requests.get(url + f"/ilceler?sehir={province_id}")
        for data_district in districts.json():
            if data_district["IlceAdiEn"] == district.upper():
                district_id = data_district["IlceID"]

        # Get prayer times for the district
        prayer = requests.get(url + f"/vakitler?ilce={district_id}")
        return prayer.json()

    except:
        if "<Response [429]>" in {str(countries), str(provinces), str(districts), str(prayer)}:
            errprint("HTTP error 429 (Too Many Requests)")
        else:
            errprint("No network")

        raise SystemExit(0)


# Dump JSON formatted data to file
def write_to_file(data):
    with open(f"{SCRIPT_PATH}.ptimes.json", "w") as json_file:
        json.dump(data, json_file)


def rerun(error_text):
    errprint(error_text)
    write_to_file(get_prayer_times())
    convert_datetime(f"{SCRIPT_PATH}.ptimes.json")


# Convert JSON formatted file to datetime object
def convert_datetime(filename):
    data = []

    try:
        with open(filename, mode="r", encoding="utf-8") as json_file:
            data = json.loads(json_file.read())
    except json.decoder.JSONDecodeError:
        rerun("Cache file corrupted, downloading file...")
    except FileNotFoundError:
        rerun("Cache file not found, downloading file...")
        return
    
    present_time = datetime.datetime.now()
    present_time = present_time - datetime.timedelta(microseconds=present_time.microsecond)

    for ptimes in data:
        try:
            gregorian_date = ptimes["MiladiTarihKisa"]
            if gregorian_date == present_time.strftime("%d.%m.%Y"):
                index_nextday = data.index(ptimes) + 1
                date_format = "%d.%m.%Y%H:%M"
                
                maghrib = datetime.datetime.strptime(gregorian_date + ptimes["Aksam"],  date_format)
                sunrise = datetime.datetime.strptime(gregorian_date + ptimes["Gunes"],  date_format)
                asr     = datetime.datetime.strptime(gregorian_date + ptimes["Ikindi"], date_format)
                fajr    = datetime.datetime.strptime(gregorian_date + ptimes["Imsak"],  date_format)
                dhuhr   = datetime.datetime.strptime(gregorian_date + ptimes["Ogle"],   date_format)
                isha    = datetime.datetime.strptime(gregorian_date + ptimes["Yatsi"],  date_format)

                try:
                    fajr_next = datetime.datetime.strptime(
                        data[index_nextday]["MiladiTarihKisa"] + data[index_nextday]["Imsak"], date_format)
                except IndexError:
                    rerun("Cache is outdated, updating...")

                ptimeslist = [fajr, sunrise, dhuhr, asr, maghrib, isha, fajr_next]
                pnameslist = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
                max_name_length = len(max(pnameslist))

                counter_a = 0
                counter_b = 1
                for ptime in ptimeslist:
                    counter_a += 1
                    if present_time < ptime:
                        if (ptime - present_time) < datetime.timedelta(minutes=16):
                            remtime = str(ptime - present_time)
                            remtime = ":".join(remtime.split(":")[0:2])
                            print(remtime, "| color=red\n---")
                            break
                        remtime = str(ptime - present_time)
                        remtime = ":".join(remtime.split(":")[0:2])
                        if len(remtime) < 5:
                            remtime = "0" + remtime
                        print(remtime, "\n---")
                        break
                for ptime, pname in zip(ptimeslist, pnameslist):
                    counter_b += 1
                    padding = max_name_length - len(pname)
                    if counter_a == counter_b :
                        print(pname + padding * " " + "\t\t:", datetime.datetime.strftime(ptime, "%H:%M"),
                              "| color = green font = Menlo size = 12")
                    else:
                        print(pname + padding*" " + "\t\t:", datetime.datetime.strftime(ptime, "%H:%M"),
                              "| font = Menlo size = 12")
                return
        except KeyError:
            rerun("Unidentified JSON file, downloading file from server: https://ezanvakti.herokuapp.com  ...")
    rerun("Cache is outdated, updating...")


convert_datetime(f"{SCRIPT_PATH}.ptimes.json")
