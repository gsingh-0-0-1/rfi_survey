import os
import sys
import glob
import datetime

dtformat = '%Y-%m-%d-%H:%M:%S'

def string2date(s):
    return datetime.datetime.strptime(s, dtformat)

def date2string(d):
    return d.strftime(dtformat)

def checkObs(s):
    if "2021-00-00" in s:
        return False
    if "obs.finished" not in os.listdir(s):
        return False
    return True

OBSDIR = "/mnt/buf0/obs/"

SCAN = sys.argv[1]#f.read()

ants = os.listdir("./obs/" + SCAN + "/ephems/")

for ant in ants:
    f = open("./obs/" + SCAN + "/ephems/" + ant + "/matches.txt", "w")
    #if ":" not in ephem:
    #    continue
    ephems = os.listdir("./obs/" + SCAN + "/ephems/" + ant + "/")
    for ephem in ephems:
        if ":" not in ephem:
            continue

        ephem_dt = datetime.datetime.strptime(ephem.replace(".txt", ""), dtformat) 

        spl = ephem.split(":")
        options = []
        
        for mod in range(-1, 2):
            base = spl[0]
            val = int(spl[1]) + mod
            val = '0'*(2 - len(str(val))) + str(val)
            options.append(base + ":" + val)

        full_glob = glob.glob(OBSDIR + "*-*-*-*:*:*/")
        datelist = [string2date(el.replace(OBSDIR, "").replace("/", "")) for el in full_glob if checkObs(el)]

        matched_obs = date2string(min(datelist, key = lambda d : abs(d - ephem_dt)))

        f.write(ephem + "," + OBSDIR + matched_obs + "\n")

f.close()

