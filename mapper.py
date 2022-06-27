import numpy as np
from sigpyproc.readers import FilReader
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import pandas as pd

fig = plt.figure()
ax = Axes3D(fig)

MJD_UNIX_DAYS = 40587

#f = open("./obs/lastscan.txt")
SCAN = sys.argv[1]
#f.close()

obsdatadir = '/mnt/buf0/obs/'

obsdir = "./obs/" + SCAN + "/"

matchfile = open(obsdir + "/ephems/matches.txt")
matchdata = matchfile.read().split("\n")
matchfile.close()

matchdata = [el.split(",") for el in matchdata if el != '']

ofile = open(obsdir + "/obsinfo.txt")
obsinfo = ofile.read().split(",")
ofile.close()
antlist = [el for el in obsinfo if el != '' and el != '\n']

data = {}

split = 1

bw = open(obsdir + "df_bw.txt", "w")
bw.write(str(672 / split))
bw.close()

for matchpair in matchdata:
    ephemdata = np.loadtxt(obsdir + "/ephems/" + matchpair[0], dtype = float)

    for ant in antlist:
        this_ant_dir = obsdir + "/" + ant + "/"
        this_ant_data_dir = matchpair[1] + "/" + ant + "/"
        
        l = [el for el in os.listdir(this_ant_data_dir) if '.fil' in el]
        filfilename = l[0]

        filfile = FilReader(this_ant_data_dir + filfilename)
        header = filfile.header

        NSAMPS = header.nsamples_files[0]
        MJDSTART = header.tstart_files[0]
        FCH1 = header.fch1

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

                print(elev_samples[ELEV])

                np.savetxt(obsdir + "datafile_FCEN_" + str(FCENTER) + "_EL_" + str(ELEV) + ".txt", this_ts)


