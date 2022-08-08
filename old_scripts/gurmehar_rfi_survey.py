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

    ls = open("./obs/lastscan.txt", "w")
    ls.write(THIS_SCAN_TIME)
    ls.close()

    logger = logger_defaults.getProgramLogger("observe", loglevel=logging.INFO)

    #full frequency list of the RFI survey, in MHz
    freq_list = [2500]#list(np.arange(ATA_FREQ_LOW + BW / 2, ATA_FREQ_HIGH, BW))

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


    #ELEVS = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
    ELEVS = [20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]

    steps = 60

    for freq in freq_list:
        os.system("killall ata_udpdb")

        n_tries = 3
        n = 0
        while True:
            try:
                ata_control.set_az_el(ant_list, 0, ELEVS[0])
                break #no exception, so we break while loop
            except ATATools.ata_rest.ATARestException as e:
                print("Exception happened... trying again in a bit")
                time.sleep(5) #Sleep 5 seconds, and restart again
                if n > n_tries:
                    # we've tried 3 times, let's just bail out
                    raise e
            n += 1

        FULL_EPHEM = None
        grace_time = 60
        spacing_time = 6
        
        t_start = time.time()
        t_start += 37
        t_start += grace_time

        elev_times = []

        for this_el in ELEVS:
            
            t_span = 360 * np.cos(this_el * np.pi / 180) #seconds, aka 6 minutes for the entire pirhouette

            if FULL_EPHEM is None:
                az_start = 0
                az_end = 360
            else:
                az_start = int(FULL_EPHEM[-1][1])
                az_end = 360 - az_start
                t_start = (FULL_EPHEM[-1][0] / (10**9)) + spacing_time
            
            print(t_start, t_span)

            ephem = ata_ephem.generate_ephem_az_swivel(az_start, az_end, this_el, t_start, t_span, steps, invr)
            
            if FULL_EPHEM is not None:
                FULL_EPHEM = np.concatenate((FULL_EPHEM, ephem))
            else:
                FULL_EPHEM = ephem
        
        tnow = maketimestamp()
        ephem_name = "./obs/" + THIS_SCAN_TIME + "/ephems/" + tnow + ".txt"
        ata_ephem.ephem_to_txt(ephem_name, FULL_EPHEM)

        print("ephem file saved to disk")

        
        obs_time = int(((FULL_EPHEM[-1][0] - FULL_EPHEM[0][0]) / (10**9)) + 1*grace_time)
        
        print(obs_time)

        ata_control.autotune(ant_list)
        #setting the frequency
        ata_control.set_freq([freq]*len(ant_list), ant_list, lo='a')


        #tuning
        snap_if.tune_if_antslo(antlo_list)
            



        ephemid = ata_control.upload_ephemeris(ephem_name)
        ata_control.track_ephemeris(ephemid, ant_list)

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

if __name__ == "__main__":
    main()
