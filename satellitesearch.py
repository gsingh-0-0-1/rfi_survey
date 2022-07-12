import numpy as np
import pandas as pd
import sgp4
from sgp4.api import Satrec
import datetime
import os
import sys
import shutil
from fetchTLE import fetchTLE
from utils.dateutils import string2date, date2string
from skyfield.api import EarthSatellite
from skyfield.api import load, wgs84
import sqlite3
from utils.colors import bcolors

TLEdir = "./TLEdata/"
JULIAN_0_IN_UNIX = 2440587.5
UNIX_0 = datetime.datetime(1970, 1, 1)
ATA = wgs84.latlon(40.8178049, -121.4695413)
AZ_TOL = EL_TOL = 1
DIST_CUTOFF = 50000


IGNORE_LIST = [
        ]

def generateUpdateCommand(obs, start_az, end_az, elev, antlo, source, source_az, source_el):
    if source != "NULL":
        source = "'" + source + "'"
    command = "update rfisources set source = " + source + ",source_az = " + str(source_az) + ", source_el = " + str(source_el) + " where obs='" + obs + "' and start_az=" + str(start_az) + " and end_az=" + str(end_az) + " and elev=" + str(elev) + " and antlo='" + antlo + "'"
    return command

def checkIgnoreSatellite(name):
    if "DEB" in name or "R/B" in name:
        return True
    if name in IGNORE_LIST:
        return True
    

def checkForAcceptableTLE(timestamp):
    dt = string2date(timestamp)
    listing = [string2date(el.replace(".txt", "")) for el in os.listdir(TLEdir)]
    if len(listing) == 0:
        return False
    bestmatch = min(listing, key = lambda x : abs(x - dt))
    delta = abs(bestmatch - dt)
    if abs(delta.days) < 1:
        return date2string(bestmatch) + ".txt"
    else:
        return False

def generateSatelliteData(timestamp):
    dt = string2date(timestamp)
    ts = load.timescale()
    TLE = checkForAcceptableTLE(timestamp)
    if TLE:
        pass
    else:
        fetchTLE(timestamp)
        TLE = timestamp + ".txt"

    datafile = open(TLEdir + TLE, "r")
    data = datafile.read()
    datafile.close()

    data = [el for el in data.split("\n") if el != ""]
    if len(data) == 0:
        print(bcolors.FAIL + "TLE file contains no data. If this file was just downloaded, it is possible this observation is too old and the TLE failed to properly generate." + bcolors.ENDC)
        sys.exit()
    nsats = len(data) / 3
    #len(data) should be a multiple of 3 since there are three lines per satellite
    assert nsats == int(nsats)

    nsats = int(nsats)
    
    tledata = []
    for i in range(nsats):
        tledata.append(data[i * 3:(i * 3) + 3])

    #satellite_data = {'name' : [], 'alt' : [], 'az' : []}
    satellite_list = []
    n = 0
    for sat in tledata:
        name = sat[0][2:]
        #if checkIgnoreSatellite(name):
        #    print("EXCLUDING", name)
        #    continue
        satellite = EarthSatellite(sat[1], sat[2], name, ts)

        geo = satellite.at(ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))

        #topocentric = diff.at(ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))

        #alt, az, d = topocentric.altaz()

        #alt = alt.degrees
        #az = az.degrees
        #d = d.km
        d = np.linalg.norm(geo.position.km)
        if d > DIST_CUTOFF:
            print("EXCLUDING", name, "@ DIST", d)
            continue
        

        diff = satellite - ATA
        satellite_list.append([name, diff])
    
    #satellite_data = pd.DataFrame(satellite_data)

    return satellite_list


def crossCheckRFIHits(timestamp):
    print("Fetching catalogued RFI for obs", timestamp + "...")
    db = sqlite3.connect("rfisources.db")
    cur = db.cursor()
    res = cur.execute("SELECT DISTINCT obs, start_az, end_az, elev, antlo FROM rfisources where obs='" + timestamp + "'")
    res = [el for el in res]
    db.close()

    print("Generating satellite data for obs", timestamp + "...")
    satellite_data = generateSatelliteData(timestamp)

    EPHEMERIDES = {}

    with open("./obs/" + timestamp + "/obsinfo.txt") as f:
        antlos = [el for el in f.read().split(",") if el.isalnum()]

    for antlo in antlos:
        directory = "./obs/" + timestamp + "/ephems/" + antlo + "/"

        with open(directory + "matches.txt") as f:
            matchdata = f.read()

        ephemname = matchdata.split(",")[0]

        EPHEMERIDES[antlo] = np.loadtxt("./obs/" + timestamp + "/ephems/" + antlo + "/" + ephemname)        


    for hit in res:
        obs = hit[0]
        start_az = hit[1]
        end_az = hit[2]
        elev = hit[3]
        #cfreq = hit[4]
        #exceed = hit[5]
        antlo = hit[4]
      
        if (end_az - start_az) == 0:
            continue

        #if not ((1200 < cfreq < 1800) or (2200 < cfreq < 2400) or (3700 < cfreq < 4200) or (8000 < cfreq < 9000)):
        #    continue

        center_az = round(0.5 * (hit[2] + hit[1]), 3)
        center_el = hit[3]

        az_range = [center_az - AZ_TOL, center_az + AZ_TOL]
        el_range = [center_el - EL_TOL, center_el + EL_TOL]

        print(bcolors.OKCYAN + "Matching satellites to RFI hit @ AZ", center_az, "\tEL", center_el, "w/ ANTLO\t", antlo, "\tWIDTH\t", end_az - start_az, bcolors.ENDC)

        ephem = EPHEMERIDES[antlo]
        ephem = ephem[np.where(ephem[:, 2] == center_el)]

        #now we find the part of the ephemeris file closest to our given azimuth
        ephem[:, 1] = ephem[:, 1] - center_az
        ephem = abs(ephem)
        row = ephem[ephem[:, 1].argsort()][0]
        t = row[0]
        #remove the 37 leap seconds
        t = t - 37

        dt = datetime.datetime.utcfromtimestamp(t / (10 ** 9))
        ts = load.timescale()
        best_guess = None
        t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        for sat in satellite_data:
            name = sat[0]
            diff = sat[1]
            topocentric = diff.at(t)

            el, az, d = topocentric.altaz()
            
            if el.degrees < 20:
                continue

            el = round(el.degrees, 3)
            az = round(az.degrees, 3)
            d = d.km

            if el > el_range[0] and el < el_range[1] and az > az_range[0] and az < az_range[1]:
                d = (180 / np.pi) * np.arccos(np.cos(np.pi * (center_el - el) / 180) * np.cos(np.pi * (center_az - az) / 180))
                if best_guess is None or d < best_guess[3]:
                    best_guess = [name, az, el, d]
                print(bcolors.HEADER + "\tGuessing ", name, "@ AZ", az, "\tEL", el, "\tD_ARC", d, bcolors.ENDC)

        db = sqlite3.connect("rfisources.db")
        cur = db.cursor()
        if best_guess is not None:

            #cur.execute("replace into rfisources (obs, start_az, end_az, elev, cfreq, exceed, antlo, source, source_az, source_el) VALUES " + modhit)
            command = generateUpdateCommand(obs, start_az, end_az, elev, antlo, best_guess[0], best_guess[1], best_guess[2])
            print(bcolors.OKGREEN + "\tBest guess was", best_guess[0], " @ AZEL\t", best_guess[1], best_guess[2], bcolors.ENDC)
        else:
            command = generateUpdateCommand(obs, start_az, end_az, elev, antlo, "NULL", "NULL", "NULL")
            print(bcolors.FAIL + "\tNO GUESSES FOUND" + bcolors.ENDC)

        print("\t" + bcolors.WARNING, command, bcolors.ENDC)
        cur.execute(command)
        db.commit()
        db.close()

if __name__ == "__main__":
    SCAN = sys.argv[1]

    crossCheckRFIHits(SCAN)

