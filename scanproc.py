import os
import sys

SCAN = ''

try:
    SCAN = sys.argv[1]
except Exception as e:
    SCAN = "$(cat obs/lastscan.txt)"

if "lastscan" in SCAN:
    sys.exit()

os.system("python matcher.py " + SCAN + "; python mapper.py " + SCAN + "; python plotter.py " + SCAN)


