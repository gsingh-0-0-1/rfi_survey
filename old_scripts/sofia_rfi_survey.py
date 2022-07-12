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

import argparse
import logging

import os
from shutil import copyfile

def main():
    t = time.time()
    logger = logger_defaults.getProgramLogger("observe", loglevel=logging.INFO)

    #full frequency list of the RFI survey, in MHz
    #freq_list = [736, 1408, 2080, 2752, 3424, 4096, 4768, 5440, 6112, 6784, 7456, 8128, 8800, 9472, 10144, 10816]

    #truncated frequency list for 5c test
    freq_list = [4096]

    #ant_list = ['1a', '1f', '5c', '1h', '2b', '4j']
    #ant_list = ['1a', '1f', '5c']
    # 3 old feeds, 3 new feeds, all with SNAPs
    #ant_list = ['1a', '1f', '1h', '3d', '4j', '5c']

    #just a 3d test today
    ant_list = ['3d']

    lo = 'A'
    antlo_list = [ant+lo for ant in ant_list]

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    #so long as this isn't a satellite, just make it very small (10**-5)
    invr = 2.55e-5

    count = 1

    for freq in freq_list:
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
        el_start = 20 #degrees
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
        ata_control.autotune(ant_list)
        snap_if.tune_if_antslo(antlo_list)

    	#give some time between now and the antenna actually moving - necessary for FRB mode
        grace_time = 15 # seconds

        t_start = time.time()
        t_start += 37 #leap seconds
        t_start += grace_time #let's start this in X seconds into the future

        t_span = 360 #seconds, aka 6 minutes for the entire pirhouette
        obs_time = int(t_span + 1*grace_time)

        steps = 60 #6 seconds per step - just want this to be >~5 seconds, so the control boxes don't struggle

        ephem = ata_ephem.generate_ephem_az_swivel(az_start, az_end, el_start, t_start, t_span, steps, invr)
        print(ephem)
        ephem_name = "/mnt/buf0/2022-03-31_3d_TEST/ephem_rfi_survey_az_%.3f_t_%f.txt" %(az_start, t_start)
        ata_ephem.ephem_to_txt(ephem_name, ephem)
        print("ephem file saved to disk")

        id = ata_control.upload_ephemeris(ephem_name)
        ata_control.track_ephemeris(id, ant_list)

        #blocking call - start recording!
        utc = snap_dada.start_recording(antlo_list, obs_time, acclen=120*40, disable_rfi=True, npolout=1)

        count += 1
    tt = time.time()

    time.sleep(10)
    print(tt-t)

if __name__ == "__main__":
    main()
