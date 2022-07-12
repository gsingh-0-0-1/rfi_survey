import numpy as np
import os
import datetime
from utils.dateutils import date2string, string2date
import sys

def generateLink(timestamp):
    date = string2date(timestamp)
    delta = datetime.datetime.now() - date
    if delta.days < 0:
        raise Exception("Time delta is negative")
        sys.exit()
    
    delay = int(delta.total_seconds())
    print("Delay", delay)

    link = 'https://www.space-track.org/basicspacedata/query/class/gp/EPOCH/%3Enow-' + str(delay) + '/orderby/NORAD_CAT_ID,EPOCH/format/3le' 
    return link

def processTLE(timestamp):
    with open("TLEdata/" + timestamp + ".txt") as f:
        data = [el for el in f.read().split("\n") if el != ""]
    nsats = len(data) / 3
    final = ''
    satdata = []

    assert int(nsats) == nsats

    for i in range(int(nsats)):
        satdata.append(data[i * 3:(i * 3) + 3])
    
    for sat in satdata:
        name = sat[0]
        if "DEB" in name or "R/B" in name or "TO BE ASSIGNED" in name:
            continue
        else:
            final = final + name + "\n" + sat[1] + "\n" + sat[2] + "\n"

    with open("TLEdata/" + timestamp + ".txt", "w") as f:
        f.write(final)

def fetchTLE(timestamp):
    password = ''
    with open("TLEpass.txt", "r") as f:
        password = f.read()

    print("Logging into SPACE-TRACK...")
    os.system('curl -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=gurmehar@gmail.com&password=' + password + '"')
    print("Fetching TLE...")
    os.system('curl --limit-rate 100K --cookie cookies.txt ' + generateLink(timestamp) + ' > TLEdata/' + timestamp + '.txt')
    
    print("Processing TLE...")
    processTLE(timestamp)
