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

SCAN = sys.argv[1]

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

split = 16

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


        sample_delay = round(time_delay / header.tsamp)

        block = filfile.read_block(sample_delay, NSAMPS - sample_delay)

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

            print(start, end)

            start = int(start)
            end = int(end)

            ts = 10 * np.log10(block[start:end].mean(axis = 0))

            FCENTER = FCH1 - (0.25 * (start + end) / 2)
            #print(FCH1, FCENTER, FCH1 - FCENTER)
            #print()
            ELEV = ephemdata[0][2]
            START_AZ = round(ephemdata[0][1])
            if START_AZ == 360:
                ts = ts[::-1]

            np.savetxt(obsdir + "datafile_FCEN_" + str(FCENTER) + "_EL_" + str(ELEV) + ".txt", ts)


