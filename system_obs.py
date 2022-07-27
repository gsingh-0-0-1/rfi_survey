import requests
import time
import sys

CFREQ = sys.argv[1]

with open("adminkeys.txt") as f:
    data = f.read()
    spl = data.split("\n")
    row = [el for el in spl if "SYSTEM_OBS" in el][0]
    key = row.split(",")[0]

requests.get("http://frb-node6.hcro.org:9000/addobs/" + key + "/" + CFREQ)


