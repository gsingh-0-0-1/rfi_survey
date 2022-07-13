import os
import subprocess
import sys
import time
import requests

OBS_ID = sys.argv[1]

CFREQ = sys.argv[2]

def endObservation(o_id):
    req = requests.get("http://frb-node6.hcro.org:9000/endobs/" + str(o_id))

os.system("python multi_ant_scan.py " + CFREQ)

endObservation(OBS_ID)

