import numpy as np
import sqlite3
import sys
import os
import time
from colors import bcolors

def createClusters(seq):
    clusters = []
    current_cluster = []
    for ind in range(len(seq)):
        #add to the current cluster if nothing is in it
        if len(current_cluster) == 0:
            current_cluster.append(seq[ind])
        
        #end the current cluster if it's the last element in the sequence
        if ind == len(seq) - 1:
            current_cluster.append(seq[ind])
            clusters.append(current_cluster)
        else:
            if seq[ind + 1] - seq[ind] != 1:
                current_cluster.append(seq[ind])
                clusters.append(current_cluster)
                current_cluster = []

    return clusters

SCAN = sys.argv[1]
obsdir = "./obs/" + SCAN + "/"
DBNAME = "rfisources.db"

MIN_DEV = 1
THRESH = 3
PREC = 3

datafiles = [el for el in os.listdir(obsdir) if "datafile" in el]

for datafile in datafiles:
    print(bcolors.HEADER + datafile + bcolors.ENDC)
    info = datafile.replace(".txt", "").replace("datafile_", "").replace("FCEN_", "").replace("EL_", "").replace("ANTLO_", "")
    info = info.split("_")
    
    FCEN = float(info[0])
    ELEV = float(info[1])
    ANTLO = info[2]

    arr = np.loadtxt(obsdir + datafile)
    std = max(arr.std(), MIN_DEV)
    mean = arr.mean()
    nsamps = arr.shape[0]
    exceeds = np.where(arr > mean + std * THRESH)[0]

    clusters = createClusters(exceeds)
    #clusters = [[round(360 * el[0] / nsamps, PREC), round(360 * el[1] / nsamps, PREC)] for el in clusters]

    for cluster in clusters:
        start = round(360 * cluster[0] / nsamps, PREC)
        end = round(360 * cluster[1] / nsamps, PREC)
        exceed = round(arr[cluster[0]:cluster[1] + 1].mean() - mean, 4)
        avg = round(0.5 * (cluster[0] + cluster[1]), PREC)
        print("\t" + bcolors.OKCYAN + str(avg) + " (" + str(start) + " -> " + str(end) + ")" + bcolors.ENDC)
        db = sqlite3.connect(DBNAME)
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO rfisources VALUES ('" + SCAN + "', " + str(start) + ", " + str(end) + ", " + str(ELEV) + ", " + str(FCEN) + ", " + str(exceed) + ", '" + ANTLO + "')")
        except sqlite3.IntegrityError:
            print("\t" + bcolors.WARNING + "HIT ALREADY IN SQL DATABASE" + bcolors.ENDC)
        db.commit()
        db.close()

    if len(clusters) == 0:
        print("\t" + bcolors.OKGREEN + "NO RFI DETECTED" + bcolors.ENDC)
