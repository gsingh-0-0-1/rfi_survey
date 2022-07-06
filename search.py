import numpy as np
import os
import sys
import shutil
import sqlite3
from colors import bcolors

OBSDIR = "./obs/"

BW = 672
EL_SPACING = 2.5
AZ_TOL = 2
THRESH = 3

EL = float(sys.argv[1])
AZ = float(sys.argv[2])
CFREQ = float(sys.argv[3])

#keep things away from the edge
if abs(360 - AZ) < AZ_TOL:
    AZ = 360 - AZ_TOL

if AZ < AZ_TOL:
    AZ = AZ_TOL

LO = CFREQ - BW / 2
HI = CFREQ + BW / 2

db = sqlite3.connect("obsdata.db")
cur = db.cursor()
data = cur.execute("SELECT * from obsdata WHERE cfreq > " + str(LO) + " AND cfreq < " + str(HI))
data = [el for el in data]
db.close()

HITS = []
DIFF = {}
for pair in data:
    obs = pair[0]

    thisobsdir = OBSDIR + obs + "/"

    f = open(thisobsdir + "obsels.txt", "r")
    ELEVS = f.read()
    f.close()
    ELEVS = [float(el) for el in ELEVS.split(",") if el != ""]

    f = open(thisobsdir + "obsfreqs.txt", "r")
    FREQS = f.read()
    f.close()
    FREQS = [float(fr) for fr in FREQS.split(",") if fr != ""]

    target_elev = min(ELEVS, key = lambda x : abs(x - EL))
    target_freq = min(FREQS, key = lambda x : abs(x - CFREQ))
    

    print(bcolors.HEADER + "Searching observation\t", obs, "at \tEL", target_elev, "\tFREQ", target_freq, bcolors.ENDC)

    datafiles = [el for el in os.listdir(thisobsdir) if "datafile" in el and "EL_" + str(target_elev) in el and "FCEN_" + str(target_freq) in el]
    for f in datafiles:
        print("\t", bcolors.OKCYAN, f, bcolors.ENDC)
        data = np.loadtxt(thisobsdir + f)
        nsamps = data.shape[0]
        indlo = int(nsamps * (AZ - AZ_TOL) / 360)
        indhi = int(nsamps * (AZ + AZ_TOL) / 360)
        dataslice = data[indlo:indhi + 1]
        mean = data.mean()
        #the std of most data is going to be extremely low
        #and so we might get hits from weird deviations
        #we want "hits" to be meaningful, so we make sure the
        #std stays above 1
        std = max(data.std(), 1)
        exceed_inds = np.where(dataslice > mean + THRESH * std)[0]
        if exceed_inds.shape[0] == 0:
            print(bcolors.FAIL, "\t\tNO HITS")
        else:
            print(bcolors.OKGREEN, "\t\tFOUND", exceed_inds.shape[0], "HITS NEAR AZ", round(360 * (np.mean(exceed_inds) + indlo) / nsamps, 3))
            hit = "http://obs-node1:9001/main?obs=" + obs + "&freq=" + str(target_freq)
            HITS.append(hit)
            DIFF[hit] = np.mean(dataslice[exceed_inds] - dataslice.mean())   
        print(bcolors.ENDC)
    print()

print()
HITS.sort(key = lambda x : DIFF[x])
HITS = HITS[::-1]
print("-"*20, "ALL HITS", "-"*20)
print("RANK\tURL")
for i in range(len(HITS)):
    print(bcolors.ENDC + str(i + 1) + "\t" + bcolors.UNDERLINE + HITS[i])


