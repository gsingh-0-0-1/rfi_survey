import os
import subprocess
import sys
import time
import requests
import datetime
from utils.dateutils import date2string, string2date
import atexit
import shutil

OBS_ID = sys.argv[1]

CFREQ = sys.argv[2]

def endObservation(o_id):
    req = requests.get("http://frb-node6.hcro.org:9000/endobs/" + str(o_id))

atexit.register(endObservation, OBS_ID)

LOGNAME = "logs/errlog_" + date2string(datetime.datetime.now()) + ".txt"

f = open(LOGNAME, "w")
f.write("*"*50 + "\n")
f.write("*" + "-"*48 + "*" + "\n")
f.write("*"*50 + "\n")
f.write("STARTING OBS AT TIME " + date2string(datetime.datetime.now()) + "\n")

f.close()

f = open(LOGNAME, "w")

subprocess.call(["python", "multi_ant_scan.py", str(CFREQ)], stdout = f, stderr = f )

f.close()

