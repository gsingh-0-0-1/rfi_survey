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

def maketimestamp():
    tnow = list(datetime.datetime.now().timetuple())[:6]
    tnow = [str(el) for el in tnow]
    tnow = ['0'*(2 - len(el)) + el for el in tnow]
    tnow = tnow[0] + "-" + tnow[1] + "-" + tnow[2] + "-" + tnow[3] + ":" + tnow[4] + ":" + tnow[5]
    return tnow

logger = logger_defaults.getProgramLogger("observe", loglevel=logging.INFO)

configfile = open(sys.argv[1])
OBS_CONFIG_DATA = configfile.read().split("\n")
configfile.close()

#config file should be formatted as such:
#az
#el
#obs time in seconds
#antennae
#CFREQ
#LO

OBS_AZ = float(OBS_CONFIG_DATA[0])
OBS_EL = float(OBS_CONFIG_DATA[1])
OBS_LEN = float(OBS_CONFIG_DATA[2])
ANT_LIST = OBS_CONFIG_DATA[3].split(",")
CFREQ = float(OBS_CONFIG_DATA[4])
LO = OBS_CONFIG_DATA[5]

ANTLO_LIST = [ant + LO for ant in ANT_LIST]

print("Observation Details:" + "-"*30)
print("Target:\t AZ ", OBS_AZ, "\tEL ", OBS_EL)
print("T\t", OBS_LEN, "s")
print("CFREQ\t", CFREQ, "MHz\tLO ", LO)
print("ANTLO\t", " ".join(ANTLO_LIST))



os.system("killall ata_udpdb")

ata_control.reserve_antennas(ANT_LIST)
atexit.register(ata_control.release_antennas, ANT_LIST, False)

ntries = 3

for i in range(ntries):
    try:
        ata_control.set_az_el(ANT_LIST, OBS_AZ, OBS_EL)
        break
    except ATATools.ata_rest.ATARestException as e:
        print("Exception happened... trying again in a bit")
        time.sleep(5)
        if i == ntries - 1:
            raise e


ata_control.autotune(ANT_LIST)
ata_control.set_freq([CFREQ]*len(ANT_LIST), ANT_LIST, lo='a')
snap_if.tune_if_antslo(ANTLO_LIST)

t = maketimestamp()
os.mkdir("obs/" + t + "/")
f = open("obs/" + t + "/info.txt", "w")
f.write(sys.argv[1] + "\n")
f.close()

utc = snap_dada.start_recording(ANTLO_LIST, OBS_LEN, acclen=120*40, disable_rfi=True, npolout=1)



