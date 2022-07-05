import numpy as np
import matplotlib.pyplot as plt
import os
import sys

#f = open("./obs/lastscan.txt")
SCAN = sys.argv[1]
#f.close()

SCAN = SCAN.replace("\\", "")

scandir = "./obs/" + SCAN + "/"

#infofile = open(scandir + "obsinfo.txt")
#antlist = [el for el in infofile.read().split(",") if el != "\n" and el != '']
#infofile.close()

#for ant in antlist:
#thisantdir = scandir + ant + "/"

l = [el for el in os.listdir(scandir) if "datafile" in el]

info = [el.replace("datafile_", "").replace(".txt", "").replace("FCEN_", "").replace("EL_", "").replace("ANTLO_", "").split("_") for el in l]

freqs = []
dummy = [freqs.append(float(el[0])) for el in info if float(el[0]) not in freqs]
freqs.sort()
freqs = [str(freq) for freq in freqs]

els = []
dummy = [els.append(float(el[1])) for el in info if float(el[1]) not in els]
els.sort()
els = [str(el) for el in els]
spacing = abs(float(els[1]) - float(els[0])) / 2

antlos = []
dummy = [antlos.append(el[2]) for el in info if el[2] not in antlos]

ffile = open(scandir + "obsfreqs.txt", "w")
for freq in freqs:
    ffile.write(freq)
    ffile.write(",")
ffile.close()

bw = open(scandir + "df_bw.txt")
IMG_BW = bw.read()
bw.close()

NGRAPHS = len(antlos) + 1

layouts = {2 : [1, 2],
        3 : [2, 2],
        4 : [2, 2]
        }

NROWS = layouts[NGRAPHS][0]
NCOLS = layouts[NGRAPHS][1]

TITLE_FSIZE = 21

plt.figure(figsize = (9 * NCOLS, 9 * NROWS))

plt.rcParams.update({'text.color': "white",
                     'axes.labelcolor': "white",
                     "axes.edgecolor" : "w",
                     "xtick.color" : "w",
                     "ytick.color" : "w"})

plt.clf()

for freq in freqs:
    for i in range(len(antlos) + 1):
        plt.subplot(NROWS, NCOLS, i + 1, projection = 'polar')
        plt.ylim([90, 0])
    print("Plotting at", freq)
    for el in els:
        TS = 0
        r = 0
        th = 0
        N = 0
        for ind in range(len(antlos)):
            antlo = antlos[ind]

            thisname = "datafile_FCEN_" + freq + "_EL_" + el + "_ANTLO_" + antlo
            try:
                ts = np.loadtxt(scandir + thisname + ".txt")
            except Exception as e:
                print(thisname)
                continue

            TS = TS + ts
            N += 1
            z = np.array([ts, ts]).T

            rad = [float(el) - spacing / 2, float(el) + spacing / 2]
            a = np.linspace(0, 2 * np.pi, ts.shape[0])

            r, th = np.meshgrid(rad, a)
            
            #sys.exit()
            plt.subplot(NROWS, NCOLS, ind + 1, projection = 'polar')
            plt.pcolormesh(th, r, z, vmin = -80, vmax=-30)
        
        TS = TS / N
        Z = np.array([TS, TS]).T
        plt.subplot(NROWS, NCOLS, NGRAPHS, projection = 'polar')
        plt.pcolormesh(th, r, Z, vmin = -80, vmax=-30)


    for ind in range(len(antlos)):
        antlo = antlos[ind]
        plt.subplot(NROWS, NCOLS, ind + 1, projection = 'polar')
        plt.title("CFREQ " + str(freq) + " | BW " + str(IMG_BW) + " | MHz, AntLO " + antlo, fontsize = TITLE_FSIZE)

        plt.grid()
        plt.colorbar()
    
    plt.subplot(NROWS, NCOLS, NGRAPHS, projection = 'polar')
    plt.title("CFREQ " + str(freq) + " | BW " + str(IMG_BW) + " | MHz, Combined", fontsize = TITLE_FSIZE)

    plt.grid()
    plt.colorbar()
    plt.tight_layout(pad = 5)
    plt.savefig(scandir + "FCEN_" + freq + ".png", transparent = True)
    plt.clf()

