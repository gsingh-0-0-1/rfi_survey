import numpy as np
from sigpyproc.readers import FilReader
import matplotlib.pyplot
import sys
import os
import matplotlib.pyplot as plt
import matplotlib

colormap = matplotlib.cm.jet

THIS_SCAN = sys.argv[1]

OBSDIR = "./followups/"
DATADIR = "/mnt/buf0/obs/"

THIS_SCAN_DIR = OBSDIR + THIS_SCAN + "/"
THIS_SCAN_DATA_DIR = DATADIR + THIS_SCAN + "/"

with open(THIS_SCAN_DIR + "obsinfo.txt", "r") as f:
    ANT_LIST = [el for el in f.read().split(",") if el != "" and el != "\n"]

flist = ''

for ant in ANT_LIST:
    l = [el for el in os.listdir(THIS_SCAN_DIR + "ephems/" + ant + "/") if ".txt" in el]
    ephem = np.loadtxt(THIS_SCAN_DIR + "ephems/" + ant + "/" + l[0])
    
    center_az = np.mean(ephem[:, 1])
    center_el = np.mean(ephem[:, 2])
    

    fil_name = [el for el in os.listdir(THIS_SCAN_DATA_DIR + ant) if ".fil" in el][0]
    
    fil_path = THIS_SCAN_DATA_DIR + ant + "/" + fil_name

    f = FilReader(fil_path)
    tsamp = f.header.tsamp
    NSAMPS = f.header.nsamples
    MJDSTART = f.header.tstart_files[0]

    MOD_UNIX_START = (MJDSTART - 40587) * 86400 + 37

    #the ephemeris time is going to be after the "official" start time
    #this delay is in seconds
    time_delay = ephem[0][0] / (10 ** 9) - MOD_UNIX_START
    sample_delay = int(time_delay / tsamp)

    block = 10 * np.log10(f.read_block(sample_delay, NSAMPS - sample_delay))

    #get the center 25 MHz
    block = block[176 * 4:(1024 - 176) * 4]
    FTOP = f.header.fch1 - 176

    splitnum = 128
    chans_per_split = int(block.shape[0] / splitnum)
    f_per_split = chans_per_split * abs(f.header.foff)

    for freq_n in range(splitnum):
        this_ftop = FTOP - (freq_n * f_per_split)
        this_fcen = this_ftop - (f_per_split / 2)
        flist += str(this_fcen) + ","

        with open(THIS_SCAN_DIR + "freqs.txt", "w") as f:
            f.write(flist)

    for freq_n in range(splitnum):
        this_ftop = FTOP - (freq_n * f_per_split)
        this_fcen = this_ftop - (f_per_split / 2)
        freq_block = block[freq_n * chans_per_split : (freq_n + 1) * chans_per_split]

        ANT_FOV = 3500 / this_fcen
        HALF_FOV = ANT_FOV / 2

        IMG_AZ_LEN = int(100 * (HALF_FOV + np.ptp(ephem[:, 1])))
        IMG_EL_LEN = int(100 * (HALF_FOV + np.ptp(ephem[:, 2])))

        ANT_FOV = int(100 * ANT_FOV)
        HALF_FOV = int(100 * HALF_FOV)

        IMG_AZ_CENTER = int(IMG_AZ_LEN / 2)
        IMG_EL_CENTER = int(IMG_EL_LEN / 2)

        #we will use these to create a circular mask so we can generate the image
        X = np.arange(0, IMG_EL_LEN)
        Y = np.arange(0, IMG_AZ_LEN)
        
        IMG_ARRAY = np.zeros((IMG_AZ_LEN, IMG_EL_LEN))
        DIV_ARRAY = np.copy(IMG_ARRAY)
        
        print(freq_n, this_ftop, this_fcen)
        for ind in range(0, len(ephem[:, 0]) - 1):
            #az_coord = int(100 * round(ephem[ind, 1] - center_az, 2)) + IMG_CENTER
            #el_coord = int(100 * round(ephem[ind, 2] - center_el, 2)) + IMG_CENTER
            sample_start = int(((ephem[ind, 0] - ephem[0, 0]) / (10 ** 9)) / tsamp)
            sample_end = int(((ephem[ind + 1, 0] - ephem[0, 0]) / (10 ** 9)) / tsamp)
            
            this_nsamps = sample_end - sample_start

            az_diff = ephem[ind + 1, 1] - ephem[ind, 1]
            el_diff = ephem[ind + 1, 2] - ephem[ind, 2]

            #for sample_ind in range(1):
            for sample_ind in range(this_nsamps):
                sub_block = freq_block[:, sample_start + sample_ind:sample_start + sample_ind + 1]
                #sub_block = freq_block[:, sample_start : sample_end]
                power = np.mean(sub_block)
                
                az_coord = int(100 * round(ephem[ind, 1] + (az_diff * sample_ind / this_nsamps) - center_az, 2)) + IMG_AZ_CENTER
                el_coord = int(100 * round(ephem[ind, 2] + (el_diff * sample_ind / this_nsamps) - center_el, 2)) + IMG_EL_CENTER
                
                if not np.isnan(power):
                    FOV_FILL = (X[np.newaxis, :] - el_coord) ** 2 + (Y[:, np.newaxis] - az_coord) ** 2 < HALF_FOV ** 2
                    
                    IMG_ARRAY[FOV_FILL] += power
                    DIV_ARRAY[FOV_FILL] += 1


        IMG_ARRAY = IMG_ARRAY / DIV_ARRAY
        
        IMG_ARRAY[np.where(DIV_ARRAY == 0)] = np.amin(IMG_ARRAY[np.where(DIV_ARRAY != 0)])
        plt.title("FCEN " + str(this_fcen) + " MHz, BW " + str(f_per_split) + " MHz")
        plt.imshow(IMG_ARRAY.T, cmap = colormap, extent=[center_az - IMG_AZ_LEN / 200, center_az + IMG_AZ_LEN / 200, center_el - IMG_EL_LEN / 200, center_el + IMG_EL_LEN / 200])
        plt.xlabel("Azimuth (deg)")
        plt.ylabel("Elevation (deg)")
        plt.colorbar()
        plt.savefig(THIS_SCAN_DIR + "FCEN_" + str(this_fcen) + ".png") 
        plt.clf()


