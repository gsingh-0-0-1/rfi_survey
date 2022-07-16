import os
import subprocess
import sys
import time
import requests
import datetime
from utils.dateutils import date2string, string2date
import atexit

OBS_ID = sys.argv[1]

CFREQ = sys.argv[2]

def endObservation(o_id):
    req = requests.get("http://frb-node6.hcro.org:9000/endobs/" + str(o_id))

atexit.register(endObservation, OBS_ID)

f = open("errlog.txt", "w")
f.write("*"*50 + "\n")
f.write("*" + "-"*48 + "*" + "\n")
f.write("*"*50 + "\n")
f.write("STARTING OBS AT TIME " + date2string(datetime.datetime.now()) + "\n")

subprocess.call(["nohup", "python", "multi_ant_scan.py", str(CFREQ)], stdout = f, stderr = f )

f.close()



