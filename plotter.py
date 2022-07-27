import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import matplotlib

colormap = matplotlib.cm.viridis

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
if len(els) == 1:
    spacing = 2.5
else:
    spacing = abs(float(els[1]) - float(els[0])) / 2

antlos = []
dummy = [antlos.append(el[2]) for el in info if el[2] not in antlos]

ffile = open(scandir + "obsfreqs.txt", "w")
for freq in freqs:
    ffile.write(freq)
    ffile.write(",")
ffile.close()

efile = open(scandir + "obsels.txt", "w")
for el in els:
    efile.write(str(el) + ",")
efile.close()


bw = open(scandir + "df_bw.txt")
IMG_BW = bw.read()
bw.close()

NGRAPHS = len(antlos)# + 1

layouts = {1 : [1, 1],
        2 : [1, 2],
        3 : [2, 2],
        4 : [2, 2],
        5 : [3, 2],
        6 : [3, 2],
        }

NROWS = layouts[NGRAPHS][0]
NCOLS = layouts[NGRAPHS][1]

TITLE_FSIZE = 18

MIN_POWER = -80
MAX_POWER = -30

def initPlot():
    plt.figure(figsize = (9 * NCOLS, 9 * NROWS))

    plt.rcParams.update({'text.color': "white",
                     'axes.labelcolor': "white",
                     "axes.edgecolor" : "w",
                     "xtick.color" : "w",
                     "ytick.color" : "w"})

plt.clf()


for freq in freqs:
    plt.close()
    initPlot()
    combTS = []
    for i in range(len(antlos)):
        plt.subplot(NROWS, NCOLS, i + 1, projection = 'polar')
        plt.ylim([90, 0])
    #plt.subplot(NROWS, NCOLS, NROWS * NCOLS, projection = 'polar')
    #plt.ylim([90, 0])
    print("Plotting at", freq)
    antlo_meshes = {}
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
                #print(thisname)
                continue

            TS = TS + ts
            N += 1
            z = np.array([ts, ts]).T
            
            rad = [float(el) - spacing / 2, float(el) + spacing / 2]
            a = np.linspace(0, 2 * np.pi, ts.shape[0])

            r, th = np.meshgrid(rad, a)
            
            #sys.exit()
            ax = plt.subplot(NROWS, NCOLS, ind + 1, projection = 'polar')
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            mesh = ax.pcolormesh(th, r, z, vmin = MIN_POWER, vmax = MAX_POWER, cmap = colormap)
            antlo_meshes[antlo] = mesh
        
        TS = TS / N
        Z = np.array([TS, TS]).T
        combTS.append(Z)
        #plt.subplot(NROWS, NCOLS, NROWS * NCOLS, projection = 'polar')
        #plt.pcolormesh(th, r, Z, vmin = -80, vmax=-30)


    for ind in range(len(antlos)):
        antlo = antlos[ind]
        ax = plt.subplot(NROWS, NCOLS, ind + 1, projection = 'polar')
        ax.set_title("CFREQ " + str(freq) + " | BW " + str(IMG_BW) + " | MHz, AntLO " + antlo, fontsize = TITLE_FSIZE)

        ax.grid()
        plt.colorbar(antlo_meshes[antlo])
    
    #plt.subplot(NROWS, NCOLS, NROWS * NCOLS, projection = 'polar')
    #plt.title("CFREQ " + str(freq) + " | BW " + str(IMG_BW) + " | MHz, Combined", fontsize = TITLE_FSIZE)

    #plt.grid()
    #plt.colorbar()
    #plt.tight_layout(pad = 5)
    plt.savefig(scandir + "FCEN_" + freq + ".png", transparent = True)
    plt.close()

    ax = plt.subplot(1, 1, 1, projection = 'polar')
    ax.set_ylim([90, 0])
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    for ind in range(len(els)):
        el = els[ind]
        ts = combTS[ind]

        rad = [float(el) - spacing / 2, float(el) + spacing / 2]
        a = np.linspace(0, 2 * np.pi, ts.shape[0])

        r, th = np.meshgrid(rad, a)

        mesh = ax.pcolormesh(th, r, ts, vmin = MIN_POWER, vmax = MAX_POWER, cmap = colormap)
    

    ax.set_title("CFREQ " + str(freq) + " | BW " + str(IMG_BW) + " | MHz, Combined")
    ax.grid()
    plt.colorbar(mesh)
    plt.tight_layout()
    plt.savefig(scandir + "FCEN_" + freq + "_combined.png", transparent = True)
    
    plt.close()
