import requests
import time

with open("adminkeys.txt") as f:
    data = f.read()
    spl = data.split("\n")
    row = [el for el in spl if "SYSTEM_OBS" in el][0]
    key = row.split(",")[0]

SCAN_FREQS = [1600, 2300, 4200]

for freq in SCAN_FREQS:
    requests.get("http://frb-node6.hcro.org:9000/addobs/" + key + "/" + str(freq))
    time.sleep(1)


