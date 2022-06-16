import os
import sys
import glob

OBSDIR = "/mnt/buf0/obs/"

SCAN = sys.argv[1]

ephems = os.listdir("./obs/" + SCAN + "/ephems/")

f = open("./obs/" + SCAN + "/ephems/matches.txt", "w")

for ephem in ephems:
    if ":" not in ephem:
        continue
    
    spl = ephem.split(":")
    options = []

    for mod in range(-1, 2):
        base = spl[0]
        val = int(spl[1]) + mod
        val = '0'*(2 - len(str(val))) + str(val)
        options.append(base + ":" + val)

    full_glob = []

    for option in options:
        full_glob = full_glob + glob.glob(OBSDIR + option + "*")

    matched_obs = full_glob[0]

    f.write(ephem + "," + matched_obs + "\n")

f.close()

