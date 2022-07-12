import numpy as np
import datetime
from utils.dateutils import string2date, date2string
import os
import sys

ORIG_DATA_DIR = "/mnt/datax-netStorage-40G/rfi_survey_Q1_2022/data/"

SUBDIR_LIST = os.listdir(ORIG_DATA_DIR)

OBS_DIR = "./obs/"


for d in SUBDIR_LIST:
    print(d)
    l = os.listdir(ORIG_DATA_DIR + d + "/")
    dirs = [el for el in l if "ephem" not in el]
    ephs = [el for el in l if "ephem" in el]    
    
    for di in dirs:
        print("\t" + di)
        targetpath = OBS_DIR + di + "/"
        if not os.path.exists(targetpath):
            os.mkdir(targetpath)
    
    dir_tstamps = [string2date(el) for el in dirs]

    for ep in ephs:
        print("\t" + ep)
        ephemfile = np.loadtxt(ORIG_DATA_DIR + d + "/" + ep)
        tstamp = ep.split("_")[-1].replace(".txt", "")
        tstamp = datetime.datetime.utcfromtimestamp(float(tstamp) - 37)
        print("\t\t" + date2string(tstamp), end = '')
        match = min(dir_tstamps, key = lambda x : abs(x - tstamp))
        strmatch = date2string(match)
        fullmatch = ORIG_DATA_DIR + d + "/" + strmatch
        print(" ->", fullmatch)

        ephem_dir_targetpath = OBS_DIR + strmatch + "/ephems/"
        if not os.path.exists(ephem_dir_targetpath):
            os.mkdir(ephem_dir_targetpath)


        antlos = ''
        for antlo in [el for el in os.listdir(fullmatch) if el != "obs.finished"]:
            print("\t\t" + antlo)
            targetpath = ephem_dir_targetpath + antlo
            if not os.path.exists(targetpath):
                os.mkdir(targetpath)
            
            with open(targetpath + "/matches.txt", "w") as f:
                f.write(strmatch + ".txt," + fullmatch)

            np.savetxt(targetpath + "/" + strmatch + ".txt", ephemfile)
            antlos = antlos + antlo + ","
        
        with open(OBS_DIR + strmatch + "/obsinfo.txt", "w") as f:
            f.write(antlos)


