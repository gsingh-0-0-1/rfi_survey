import os
import sys
import glob
import datetime
from utils.dateutils import string2date, date2string

def checkObs(s):
    if "2021-00-00" in s:
        return False
    if "obs.finished" not in os.listdir(s):
        return False
    return True

OBSDIR = "/mnt/buf0/obs/"

SCAN = sys.argv[1]#f.read()

ants = os.listdir("./obs/" + SCAN + "/ephems/")

Q1_LATEST_DT = datetime.datetime(2022, 3, 13)
Q1_OBS_DATA = "/mnt/datax-netStorage-40G/rfi_survey_Q1_2022/data/"

def fetchListing(dt):
    delta = dt - Q1_LATEST_DT
    print(delta)
    #if delta > 0, then this is part of the ongoing scans
    if delta > datetime.timedelta(0):
        return glob.glob(OBSDIR + "*-*-*-*:*:*/")
    else:
        l = []
        for directory in glob.glob(Q1_OBS_DATA + "*"):
            l = l + [el for el in glob.glob(directory + "/*-*-*-*:*:*/")]
        
        return l


for ant in ants:
    f = open("./obs/" + SCAN + "/ephems/" + ant + "/matches.txt", "w")
    #if ":" not in ephem:
    #    continue
    ephems = os.listdir("./obs/" + SCAN + "/ephems/" + ant + "/")
    for ephem in ephems:
        if ":" not in ephem:
            continue

        ephem_dt = string2date(ephem.replace(".txt", ""))

        spl = ephem.split(":")
        options = []
        
        for mod in range(-1, 2):
            base = spl[0]
            val = int(spl[1]) + mod
            val = '0'*(2 - len(str(val))) + str(val)
            options.append(base + ":" + val)

        full_glob = fetchListing(ephem_dt)#glob.glob(OBSDIR + "*-*-*-*:*:*/")

        strdatelist = [el for el in full_glob if checkObs(el)]
        datelist = [string2date(el.split("/")[-2]) for el in full_glob if checkObs(el)]

        matched_obs = min(datelist, key = lambda d : abs(d - ephem_dt))

        ind = datelist.index(matched_obs)
        match = strdatelist[ind]

        f.write(ephem + "," + match + "\n")

    f.close()

