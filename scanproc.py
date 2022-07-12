import os
import sys
import subprocess

SCAN = ''

try:
    SCAN = sys.argv[1]
except Exception as e:
    SCAN = "$(cat obs/lastscan.txt)"

if "lastscan" in SCAN:
    sys.exit()

os.system("python matcher.py " + SCAN + "; python mapper.py " + SCAN + "; python plotter.py " + SCAN + "; python catalogsources.py " + SCAN)
subprocess.Popen(["python", "satellitesearch.py", str(SCAN)], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

