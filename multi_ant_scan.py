#!/home/obsuser/miniconda3/envs/ATAobs/bin/python


#######################
# This example script shows how to set up an observation using the
# SNAP boards with a swivel across azimuth.
# Trying antenna reservation, tuning, movement, data recording
# for new feed antennas.
#######################

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

ATA_FREQ_LOW = 3000
ATA_FREQ_HIGH = 8000

BW = 672

EL_START = 20
EL_END = 30
EL_RES = 1

#full frequency list of the RFI survey, in MHz
freq_list = [float(sys.argv[1])]#list(np.arange(ATA_FREQ_LOW + BW / 2, ATA_FREQ_HIGH, BW))

ant_list = ['1a', '1f', '5c']
N_ANTS = len(ant_list)
lo = 'A'
antlo_list = [ant + lo for ant in ant_list]

#so long as this isn't a satellite, just make it very small (10**-5)
invr = 2.55e-5

count = 1

swivel_tspan = 864 #seconds

def maketimestamp():
    tnow = list(datetime.datetime.now().timetuple())[:6]
    tnow = [str(el) for el in tnow]
    tnow = ['0'*(2 - len(el)) + el for el in tnow]
    tnow = tnow[0] + "-" + tnow[1] + "-" + tnow[2] + "-" + tnow[3] + ":" + tnow[4] + ":" + tnow[5]
    return tnow

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def calctime(seq):
    return sum(swivel_tspan * np.cos(np.pi * np.array(seq) / 180))


ELEVS = list(np.arange(EL_START, EL_END + EL_RES, EL_RES))

t = time.time()

THIS_SCAN_TIME = maketimestamp()
os.mkdir("./obs/" + THIS_SCAN_TIME)
os.mkdir("./obs/" + THIS_SCAN_TIME + "/ephems/")

logger = logger_defaults.getProgramLogger("observe", loglevel=logging.INFO)

ofile = open("./obs/" + THIS_SCAN_TIME + "/obsinfo.txt", "w")
for ant in antlo_list:
    os.mkdir("./obs/" + THIS_SCAN_TIME + "/" + ant)
    ofile.write(ant + ",")
ofile.write("\n")
ofile.close()


ELEVS = np.arange(20, 80.01, 2.5)
ant_elevs = {}
for ant in ant_list:
    ant_elevs[ant] = []
#we want to minimize the time that it takes for the scan
#swivels at higher elevations take less time, and so an
#even split in number of swivels / elevations doesn't 
#actually minimize observation time
total_time = calctime(ELEVS)
one_ant_maxtime = total_time / N_ANTS

ant_ind = 0
for elev in ELEVS[::-1]:
    if calctime(np.array(ant_elevs[ant_list[ant_ind]])) <= one_ant_maxtime or ant_ind + 1 == N_ANTS:
        pass
    else:
        ant_ind += 1

    ant_elevs[ant_list[ant_ind]].append(elev)

#override for now - every antenna should look at the entire sky
for ind in range(len(ant_list)):
    ant_elevs[ant_list[ind]] = ELEVS[ind::N_ANTS]#ant_elevs[ant][::-1]

ANT_INIT_ELEVS = [ant_elevs[ant][0] for ant in ant_list]

steps = 60

el_spacing = ant_elevs[ant_list[0]][1] - ant_elevs[ant_list[0]][0]

ata_control.reserve_antennas(ant_list)
atexit.register(ata_control.release_antennas, ant_list, False)

for freq in freq_list:
    os.system("killall ata_udpdb")

    n_tries = 3
    n = 0
    while True:
        try:
            for ind in range(len(ant_list)):
                ata_control.set_az_el(ant_list[ind], 0, ANT_INIT_ELEVS[ind])
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

    FULL_EPHEM = {}
    for ant in ant_list:
        FULL_EPHEM[ant] = None

    grace_time = 120
    spacing_time = el_spacing * 1.5
    
    t_start = time.time()
    t_start += 37
    t_start += grace_time

    elev_times = []

    for this_ant in ant_list:
        for ind in range(len(ant_elevs[this_ant])):
            this_el = ant_elevs[this_ant][ind]

            t_span = swivel_tspan * np.cos(this_el * np.pi / 180) #seconds, aka 6 minutes for the entire pirhouette

            if FULL_EPHEM[this_ant] is None:
                az_start = 0
                az_end = 360
                this_t_start = t_start
            else:
                az_start = int(FULL_EPHEM[this_ant][-1][1])
                az_end = 360 - az_start
                this_t_start = (FULL_EPHEM[this_ant][-1][0] / (10**9)) + spacing_time
            

            ephem = ata_ephem.generate_ephem_az_swivel(az_start, az_end, this_el, this_t_start, t_span, steps, invr)
            
            if FULL_EPHEM[this_ant] is not None:
                FULL_EPHEM[this_ant] = np.concatenate((FULL_EPHEM[this_ant], ephem))
            else:
                FULL_EPHEM[this_ant] = ephem
    
    tnow = maketimestamp()
    ephem_names = {}
    for ant in ant_list:
        os.mkdir("./obs/" + THIS_SCAN_TIME + "/ephems/" + ant + lo + "/")

        ephem_names[ant] = "./obs/" + THIS_SCAN_TIME + "/ephems/" + ant + lo + "/" + tnow + ".txt"
        ata_ephem.ephem_to_txt(ephem_names[ant], FULL_EPHEM[ant])

    print("ephem files saved to disk")

    obs_times = [(FULL_EPHEM[key][-1][0] - FULL_EPHEM[key][0][0]) / (10 ** 9) for key in FULL_EPHEM.keys()]
    obs_time = int(max(obs_times) + grace_time) #int(((FULL_EPHEM[-1][0] - FULL_EPHEM[0][0]) / (10**9)) + 1*grace_time)
    
    print("Starting sky scan from elevation\t", ELEVS[0], " to\t", ELEVS[-1])
    print("\tELEV RES", ELEVS[1] - ELEVS[0])
    print("CFREQ\t", freq)
    print("ANTS\t", ','.join(antlo_list))
    print("OBS TIME\t", obs_time)



    for ant in ant_list:
        ephemid = ata_control.upload_ephemeris(ephem_names[ant])
        ata_control.track_ephemeris(ephemid, [ant])

    #make the time more accurate
    THIS_SCAN_TIME_n = maketimestamp()
    shutil.move("./obs/" + THIS_SCAN_TIME, "./obs/" + THIS_SCAN_TIME_n)
    THIS_SCAN_TIME = THIS_SCAN_TIME_n

    #blocking call - start recording!
    for rep in range(3):
        try:
            utc = snap_dada.start_recording(antlo_list, obs_time, acclen=120*40, disable_rfi=True, npolout=1)
            break
        except Exception as e:
            print("-"*50)
            print(e)
            print("Ran into an error, going to try again in 5 seconds...")
            print("-"*50)
            time.sleep(5)

    count += 1
tt = time.time()

time.sleep(10)
print(tt-t)

ls = open("./obs/lastscan.txt", "w")
ls.write(THIS_SCAN_TIME)
ls.close()

ata_control.release_antennas(ant_list, False) 

subprocess.Popen(["python",  "scanproc.py", str(THIS_SCAN_TIME)], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
#os.system("python catalogsources.py " + str(THIS_SCAN_TIME))
#print("Starting satellite search process...")
#subprocess.Popen(["python", "satellitesearch.py", str(THIS_SCAN_TIME)], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
print("Obs and processing finished.")
