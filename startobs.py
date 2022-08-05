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

TYPE = sys.argv[2]

PARAMS = sys.argv[3].split(",")

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

command = ['python']

if TYPE == "SCAN":
    command += ['multi_ant_scan.py']
if TYPE == "FOLLOWUP":
    command += ['follow_up.py']

command = command + PARAMS
print(command)

#time.sleep(5)
subprocess.call(command, stdout = f, stderr = f)

f.close()

