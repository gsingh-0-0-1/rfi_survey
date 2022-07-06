import numpy as np
from sigpyproc.readers import FilReader
import sys
from mpl_toolkits.mplot3d import Axes3D
import os
import pandas as pd
import scipy.signal
import sqlite3

def downsample(l, f):
    if f == 1:
        return l

    arrs = [l[i::f] for i in range(f)]
    target = max([el.shape[0] for el in arrs])
    updated = [np.concatenate((el, np.full(target - el.shape[0], [el[-1]]))) for el in arrs]
    ds = sum(updated) / f
    return ds

DOWNSAMPLE_FACTOR = 16

MJD_UNIX_DAYS = 40587

#f = open("./obs/lastscan.txt")
SCAN = sys.argv[1]
#f.close()

SCAN = SCAN.replace("\\", "")

obsdatadir = '/mnt/buf0/obs/'

obsdir = "./obs/" + SCAN + "/"
ephemdir = obsdir + "ephems/"

antlo_list = os.listdir(ephemdir)

data = {}

#~5 MHz bandwidth
split = 128

bw = open(obsdir + "df_bw.txt", "w")
bw.write(str(672 / split))
bw.close()

for ant in antlo_list:
    matchfile = open(ephemdir + ant + "/matches.txt")
    matchdata = [el.split(",") for el in matchfile.read().split("\n") if el != ""]
    matchfile.close()

    #print(matchdata)
    #continue

    for matchpair in matchdata:
        ephemdata = np.loadtxt(obsdir + "/ephems/" + ant + "/" + matchpair[0], dtype = float)
        
        this_ant_dir = obsdir + "/" + ant + "/"
        this_ant_data_dir = matchpair[1] + "/" + ant + "/"
        
        l = [el for el in os.listdir(this_ant_data_dir) if '.fil' in el]
        filfilename = l[0]

        filfile = FilReader(this_ant_data_dir + filfilename)
        header = filfile.header

        NSAMPS = header.nsamples_files[0]
        MJDSTART = header.tstart_files[0]
        FCH1 = header.fch1
        CFREQ = FCH1 - 512

        f = open(obsdir + "cfreq.txt", "w")
        f.write(str(CFREQ))
        f.close()

        db = sqlite3.connect("obsdata.db")
        cur = db.cursor()
        try:
            cur.execute(" INSERT INTO obsdata VALUES ('" + SCAN + "', " + str(CFREQ) + ") ")
        except sqlite3.IntegrityError:
            pass
        db.commit()
        db.close()

        if FCH1 not in data:
            data[FCH1] = {}

        MOD_UNIX_START = (MJDSTART - 40587) * 86400 + 37

        #the ephemeris time is going to be after the "official" start time
        #this delay is in seconds
        time_delay = ephemdata[0][0] / (10 ** 9) - MOD_UNIX_START
        
        tsamp = header.tsamp

        sample_delay = round(time_delay / tsamp)

        block = filfile.read_block(sample_delay, NSAMPS - sample_delay)

        ELEVS = np.unique(ephemdata[:, 2])
        elev_samples = {}
        for elev in ELEVS:
            this_ephem = ephemdata[np.where(ephemdata[:, 2] == elev)]
            start_sample = round(((this_ephem[0][0] - ephemdata[0][0]) / (10 ** 9)) / tsamp)
            end_sample = round(((this_ephem[-1][0] - ephemdata[0][0]) / (10 ** 9)) / tsamp)
            elev_samples[elev] = [start_sample, end_sample]

        #we can only really use the center 672 MHz
        #in a file where we have 4096 channels of 0.25 MHz width,
        #this corresponds to the indices:
        b_low = 704
        b_high = 3392
        block = block[b_low:b_high]

        NCHANS = block.shape[0]
        #redefine FCH1
        #176 here is (1024 - 672) / 2
        FCH1 = FCH1 - 176
        for spl in range(split):

            start = spl * NCHANS / split
            end = start + NCHANS / split


            start = int(start)
            end = int(end)

            ts = 10 * np.log10(block[start:end].mean(axis = 0))

            FCENTER = FCH1 - (0.25 * (start + end) / 2)
            #print(FCH1, FCENTER, FCH1 - FCENTER)
            #print()
            for ELEV in elev_samples.keys():
                START_AZ = round(ephemdata[np.where(ephemdata[:, 2] == ELEV)][0][1])
                
                this_ts = ts[elev_samples[ELEV][0]:elev_samples[ELEV][1]]

                if START_AZ == 360:
                    this_ts = this_ts[::-1]


                this_ts = downsample(this_ts, DOWNSAMPLE_FACTOR)

                np.savetxt(obsdir + "datafile_FCEN_" + str(FCENTER) + "_EL_" + str(ELEV) + "_ANTLO_" + ant + ".txt", this_ts)


