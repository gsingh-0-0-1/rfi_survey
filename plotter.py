import numpy as np
import matplotlib.pyplot as plt
import os
import sys

SCAN = sys.argv[1]

scandir = "./obs/" + SCAN + "/"

infofile = open(scandir + "obsinfo.txt")
antlist = [el for el in infofile.read().split(",") if el != "\n" and el != '']
infofile.close()

for ant in antlist:
    thisantdir = scandir + ant + "/"

    l = [el for el in os.listdir(thisantdir) if "datafile" in el]

    info = [el.replace("datafile_", "").replace(".txt", "").replace("FCEN_", "").replace("EL_", "").split("_") for el in l]

    freqs = []
    dummy = [freqs.append(float(el[0])) for el in info if float(el[0]) not in freqs]
    freqs.sort()
    freqs = [str(freq) for freq in freqs]

    els = []
    dummy = [els.append(float(el[1])) for el in info if float(el[1]) not in els]
    els.sort()
    els = [str(el) for el in els]
    print(els)
    spacing = abs(float(els[1]) - float(els[0])) / 2

    for freq in freqs:
        plt.subplot(projection = 'polar')
        plt.ylim([90, 0])
        for el in els:
            thisname = "datafile_FCEN_" + freq + "_EL_" + el
            ts = np.loadtxt(thisantdir + thisname + ".txt")
            z = np.array([ts, ts]).T

            rad = [float(el) - spacing, float(el) + spacing]
            print(rad)

            a = np.linspace(0, 2 * np.pi, ts.shape[0])

            r, th = np.meshgrid(rad, a)

            plt.pcolormesh(th, r, z)
        plt.grid()
        plt.colorbar()
        plt.savefig(thisantdir + "FCEN_" + freq + ".png")
        plt.clf()
    
    
