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

        ts = 10 * np.log10(block.mean(axis = 0))

        FCENTER = FCH1 - (0.25 * 2048)
        ELEV = ephemdata[0][2]
        START_AZ = round(ephemdata[0][1])
        if START_AZ == 360:
            ts = ts[::-1]

        np.savetxt(this_ant_dir + "datafile_FCEN_" + str(FCENTER) + "_EL_" + str(ELEV) + ".txt", ts)

        '''print(ts.shape)

        n = ts.shape[0]#12
        rad = [20]#[20 for i in range(n)]#np.linspace(0)
        a = np.linspace(ephemdata[0][1] * np.pi / 180, ephemdata[-1][1] * np.pi / 180, n)
        r, th = np.meshgrid(rad, a)
        
        np.savetxt(filfilename + ".txt", ts)

        z = ts#[ts, ts]#np.random.uniform(-1, 1, (n,m))
        #z = np.array(z).T
        plt.subplot(projection="polar")
        
        #th = np.squeeze(th)
        #r = np.squeeze(r)
        #z = np.squeeze(z)

        plt.pcolormesh(r, th, z, cmap = 'Blues')
        #plt.plot(rad, a)

        plt.grid()
        plt.colorbar()
        plt.savefig("test" + filfilename + ".png")
        plt.clf()'''
