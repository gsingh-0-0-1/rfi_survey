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
from shutil import copyfile

ATA_FREQ_LOW = 3000
ATA_FREQ_HIGH = 8000

def maketimestamp():
    tnow = list(datetime.datetime.now().timetuple())[:6]
    tnow = [str(el) for el in tnow]
    tnow = ['0'*(2 - len(el)) + el for el in tnow]
    tnow = tnow[0] + "-" + tnow[1] + "-" + tnow[2] + "-" + tnow[3] + ":" + tnow[4] + ":" + tnow[5]
    return tnow

BW = 672

EL_START = 20
EL_END = 30
EL_RES = 1

ELEVS = list(np.arange(EL_START, EL_END + EL_RES, EL_RES))

def main():
    t = time.time()

    THIS_SCAN_TIME = maketimestamp()
    os.mkdir("./obs/" + THIS_SCAN_TIME)
    os.mkdir("./obs/" + THIS_SCAN_TIME + "/ephems/")

    logger = logger_defaults.getProgramLogger("observe", loglevel=logging.INFO)

    #full frequency list of the RFI survey, in MHz
    freq_list = list(np.arange(ATA_FREQ_LOW + BW / 2, ATA_FREQ_HIGH, BW))

    ant_list = ['1f']

    lo = 'A'
    antlo_list = [ant + lo for ant in ant_list]

    ofile = open("./obs/" + THIS_SCAN_TIME + "/obsinfo.txt", "w")
    for ant in antlo_list:
        os.mkdir("./obs/" + THIS_SCAN_TIME + "/" + ant)
        ofile.write(ant + ",")
    ofile.write("\n")
    ofile.close()

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    #so long as this isn't a satellite, just make it very small (10**-5)
    invr = 2.55e-5

    count = 1


    ELEVS = [20, 25, 30]

    for freq in freq_list:
        ata_control.autotune(ant_list)
        for this_el in ELEVS:
            os.system("killall ata_udpdb")

            #setting the frequency
            ata_control.set_freq([freq]*len(ant_list), ant_list, lo='a')

            print(count % 2)
            #setting start position based on count
            if count % 2 == 1:
                    az_start = 0 #degrees
                    az_end = 360 #degrees
            if count % 2 == 0:
                    az_start = 360 #degrees
                    az_end = 0 #degrees
            print(az_start)
            el_start = this_el #degrees
            #ata_control.set_az_el(ant_list, az_start, el_start)

            n_tries = 3
            n = 0
            while True:
                try:
                    ata_control.set_az_el(ant_list, az_start, el_start)
                    break #no exception, so we break while loop
                except ATATools.ata_rest.ATARestException as e:
                    print("Exception happened... trying again in a bit")
                    time.sleep(5) #Sleep 5 seconds, and restart again
                    if n > n_tries:
                        # we've tried 3 times, let's just bail out
                        raise e
                n += 1

            #tuning
            snap_if.tune_if_antslo(antlo_list)

            #give some time between now and the antenna actually moving - necessary for FRB mode
            grace_time = 20 # seconds

            t_start = time.time()
            t_start += 37 #leap seconds
            t_start += grace_time #let's start this in X seconds into the future

            t_span = 360 * np.cos(this_el * np.pi / 180) #seconds, aka 6 minutes for the entire pirhouette
            obs_time = int(t_span + 1*grace_time)

            steps = 60 #6 seconds per step - just want this to be >~5 seconds, so the control boxes don't struggle

            ephem = ata_ephem.generate_ephem_az_swivel(az_start, az_end, el_start, t_start, t_span, steps, invr)
            #print(ephem)
           
            tnow = maketimestamp()

            ephem_name = "./obs/" + THIS_SCAN_TIME + "/ephems/" + tnow + ".txt"
            ata_ephem.ephem_to_txt(ephem_name, ephem)
            
            print("ephem file saved to disk")

            ephemid = ata_control.upload_ephemeris(ephem_name)
            ata_control.track_ephemeris(ephemid, ant_list)

            #blocking call - start recording!
            for rep in range(3):
                try:
                    print("-"*50)
                    print("OBS\tEL ", this_el, "\tFREQ\t", freq) 
                    print("-"*50)
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

if __name__ == "__main__":
    main()
