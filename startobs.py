import os
import subprocess
import sys
import time
import requests

OBS_ID = sys.argv[1]

def endObservation(o_id):
    req = requests.get("http://frb-node6.hcro.org:9000/endobs/" + str(o_id))


time.sleep(10)

endObservation(OBS_ID)

