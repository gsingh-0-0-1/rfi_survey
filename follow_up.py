#!/home/obsuser/miniconda3/envs/ATAobs/bin/python

import ATATools
from ATATools import ata_control, logger_defaults, ata_ephem
import atexit
from SNAPobs import snap_dada, snap_if, snap_config
import numpy as np
import sys
import time
import datetime

import argparse
import logging

import os
import shutil
import subprocess
import sqlite3

from utils import ephemgen

def maketimestamp():
    tnow = list(datetime.datetime.now().timetuple())[:6]
    tnow = [str(el) for el in tnow]
    tnow = ['0'*(2 - len(el)) + el for el in tnow]
    tnow = tnow[0] + "-" + tnow[1] + "-" + tnow[2] + "-" + tnow[3] + ":" + tnow[4] + ":" + tnow[5]
    return tnow

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

ATA_FREQ_LOW = 3000
ATA_FREQ_HIGH = 8000

BW = 672

EL_START = 20
EL_END = 30
EL_RES = 1

invr = 2.55e-5
count = 1

ant_list = ['1a']
N_ANTS = len(ant_list)
lo = 'A'
antlo_list = [ant + lo for ant in ant_list]

paramstring = ','.join(sys.argv[1:-2])

freq_list = [float(sys.argv[1])]

SCANTYPE = sys.argv[2]

if SCANTYPE.lower() == 'flower' or SCANTYPE.lower() == 'raster':
    center_az = float(sys.argv[3])
    center_el = float(sys.argv[4])

if SCANTYPE.lower() == 'flower':
    n_petals = int(sys.argv[5])
    theta_max = 2 * np.pi

    ANT_FOV = 3500 / freq_list[0]

    PATTERN_RADIUS = float(sys.argv[6])#max(ANT_FOV, 1)

    n_petals = int(4 * (round(n_petals / 4) + 1))
    assert n_petals % 4 == 0
    k = int(n_petals / 2)

    ephem = ephemgen.flower_petal(center_az, center_el, n_petals, PATTERN_RADIUS)
elif SCANTYPE.lower() == 'raster':
    az_radius = float(sys.argv[5])
    el_radius = float(sys.argv[6])
    interval = float(sys.argv[7])
    ephem = ephemgen.raster_scan(center_az, center_el, az_radius, el_radius, interval = interval)
elif SCANTYPE.lower() == 'line':
    start_az = float(sys.argv[3])
    start_el = float(sys.argv[4])
    end_az = float(sys.argv[5])
    end_el = float(sys.argv[6])
    center_az = start_az
    center_el = start_el
    ephem = ephemgen.linescan(start_az, start_el, end_az, end_el)

OBSERVER_NAME = sys.argv[-2]
INTENDED_TARGET = sys.argv[-1]


SAVEDIR = "./followups/"

t = time.time()

THIS_SCAN_TIME = maketimestamp()

print(THIS_SCAN_TIME)

os.mkdir(SAVEDIR + THIS_SCAN_TIME)
os.mkdir(SAVEDIR + THIS_SCAN_TIME + "/ephems/")

logger = logger_defaults.getProgramLogger("observe", loglevel=logging.INFO)

with open(SAVEDIR + THIS_SCAN_TIME + "/specs.txt", "w") as f:
    f.write(",".join(sys.argv))

ofile = open(SAVEDIR + THIS_SCAN_TIME + "/obsinfo.txt", "w")
for ant in antlo_list:
    os.mkdir(SAVEDIR + THIS_SCAN_TIME + "/" + ant)
    ofile.write(ant + ",")
ofile.write("\n")
ofile.close()

ata_control.reserve_antennas(ant_list)
atexit.register(ata_control.release_antennas, ant_list, True)

for freq in freq_list:
    os.system("killall ata_udpdb")

    n_tries = 3
    n = 0
    while True:
        try:
            ata_control.set_az_el(ant_list, center_az, center_el)
            break #no exception, so we break while loop
        except ATATools.ata_rest.ATARestException as e:
            print("Exception happened... trying again in a bit")
            time.sleep(5) #Sleep 5 seconds, and restart again
            if n > n_tries:
                # we've tried 3 times, let's just bail out
                raise e
        n += 1

    ata_control.autotune(ant_list)
    #setting the frequency
    ata_control.set_freq([freq]*len(ant_list), ant_list, lo='a')


    #tuning
    snap_if.tune_if_antslo(antlo_list)

    grace_time = 20

    obs_time = ephem[-1][0] + grace_time

    print("Obs for", obs_time)

    ephem[:, 0] = ephem[:, 0] + time.time() + grace_time + 37
    ephem[:, 0] = ephem[:, 0] * (10 ** 9)

    tnow = maketimestamp()
    ephem_names = {}
    for ant in ant_list:
        os.mkdir(SAVEDIR + THIS_SCAN_TIME + "/ephems/" + ant + lo + "/")

        ephem_names[ant] = SAVEDIR + THIS_SCAN_TIME + "/ephems/" + ant + lo + "/" + tnow + ".txt"
        ata_ephem.ephem_to_txt(ephem_names[ant], ephem)

    print("ephem files saved to disk")

    for ant in ant_list:
        ephemid = ata_control.upload_ephemeris(ephem_names[ant])
        ata_control.track_ephemeris(ephemid, [ant])

    #blocking call - start recording!
    for rep in range(3):
        try:
            utcstr = snap_dada.start_recording(antlo_list, obs_time, acclen=120*40, disable_rfi=True, npolout=1)
            break
        except Exception as e:
            print("-"*50)
            print(e)
            print("Ran into an error, going to try again in 5 seconds...")
            print("-"*50)
            time.sleep(5)

    #make the time more accurate
    THIS_SCAN_TIME_n = utcstr
    shutil.move(SAVEDIR + THIS_SCAN_TIME, SAVEDIR + THIS_SCAN_TIME_n)
    THIS_SCAN_TIME = THIS_SCAN_TIME_n

    count += 1
tt = time.time()

db = sqlite3.connect("followups.db")
cur = db.cursor()
cur.execute("insert into followups (datetime, name, params, source) values ('" + THIS_SCAN_TIME + "', '" + OBSERVER_NAME + "', '" + paramstring + "', '" + INTENDED_TARGET +"')")
db.commit()
db.close()

time.sleep(10)
print(tt-t)

ls = open(SAVEDIR + "lastscan.txt", "w")
ls.write(THIS_SCAN_TIME)
ls.close()

ata_control.release_antennas(ant_list, True) 

subprocess.Popen(["python", "proc_followup.py", str(THIS_SCAN_TIME)])

print("Obs and processing finished.")
