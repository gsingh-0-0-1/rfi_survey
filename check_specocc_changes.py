import numpy as np
import requests
import sys
import datetime
from utils.dateutils import string2date, date2string
import matplotlib.pyplot as plt
from matplotlib import cm

CLUSTER_PREC = 1
EPSILON_1 = 0.0
EPSILON_2 = 0.1
EPSILON_3 = 0.1

def processData(response_data):
    '''
    This function takes the raw response data returned by the web server and 
    processes it -- mainly through location-based clustering -- so that
    we can check for locations on the sky to perform follow-ups.
    '''

    split = response_data.split("|")
    N_OBS = int(split[0])
    raw_data = split[1].split("\n")
    raw_data = [el.split(",") for el in raw_data if el != ""]

    clustered_data = {}

    for el in raw_data:
        az_r = round(float(el[0]))
        el_r = round(float(el[1]))
        key = str(az_r) + "," + str(el_r)
        try:
            clustered_data[key] += 1
        except KeyError:
            clustered_data[key] = 1 

    array_data = np.zeros((int(360 / CLUSTER_PREC), int(90 / CLUSTER_PREC)))
    for key in clustered_data:
        clustered_data[key] = min(1.0, round(clustered_data[key] / N_OBS, 4))
        coords = [int(el) for el in key.split(",")]
        array_data[int((coords[0] - 1) / CLUSTER_PREC), int((coords[1] - 1) / CLUSTER_PREC)] = clustered_data[key]

    return array_data


def fetchData(cfreq, bw, d_start, d_end):
    '''
    This function fetches the raw spectral occupancy data for a given
    frequency, bandwidth, start date, and end date.
    '''

    req_url = "http://frb-node6.hcro.org:9000/specoccdata/" + cfreq + "/" + bw + "/" + date2string(d_start).replace(":", "").replace("-", "") + "/" + date2string(d_end).replace(":", "").replace("-", "")

    print("\tGET " + req_url + "...")

    req = requests.get(req_url) 

    return req.text

def runSearch(CFREQ, BW):
    '''
    This function queries spectral occupancy data for the recent and benchmark periods.
    '''

    REC_DAYS = 1
    BEN_DAYS = 7

    #datetimes for the "recent" period
    D_END_REC = datetime.datetime.now()
    D_BEG_REC = D_END_REC - datetime.timedelta(days = REC_DAYS)

    #datetimes for the "benchmark" period
    D_END_BEN = D_BEG_REC
    D_BEG_BEN = D_END_BEN - datetime.timedelta(days = BEN_DAYS)

    print("Beginning search for recent period:")
    print("\t" + date2string(D_BEG_REC) + " -> " + date2string(D_END_REC))

    REC_DATA = fetchData(CFREQ, BW, D_BEG_REC, D_END_REC)
    REC_DATA = processData(REC_DATA)

    print("Beginning search for benchmark period:")
    print("\t" + date2string(D_BEG_BEN) + " -> " + date2string(D_END_BEN))

    BEN_DATA = fetchData(CFREQ, BW, D_BEG_BEN, D_END_BEN)
    BEN_DATA = processData(BEN_DATA)

    DIFF = REC_DATA - BEN_DATA
    DIFF[np.where(DIFF < 0)] = 0

    BENCHMARK_CROWDEDNESS = np.mean(BEN_DATA[np.where(BEN_DATA > EPSILON_1)])#np.mean(BEN_DATA)

    DIFF_FLAGS = np.where(DIFF > EPSILON_2)
    DIFF_FLAGS = np.concatenate((DIFF_FLAGS[0][:, np.newaxis], DIFF_FLAGS[1][:, np.newaxis]), axis = 1)

    CROWD_FLAGS = np.where(REC_DATA > EPSILON_3 + BENCHMARK_CROWDEDNESS)
    CROWD_FLAGS = np.concatenate((CROWD_FLAGS[0][:, np.newaxis], CROWD_FLAGS[1][:, np.newaxis]), axis = 1)

    FLAGS = [el for el in DIFF_FLAGS if el in CROWD_FLAGS]

    print("BENCHMARK CROWDEDNESS", BENCHMARK_CROWDEDNESS)

    print(FLAGS)

    FLAGS = [[el[0] / CLUSTER_PREC, el[1] / CLUSTER_PREC] for el in FLAGS]

    print(FLAGS)

    colormap = cm.viridis

    plt.subplot(1, 3, 1)
    plt.title("Recent Data")
    plt.imshow(REC_DATA, aspect = 1/4, cmap = colormap, vmin = 0.0, vmax = 1.0)
    plt.colorbar()

    plt.subplot(1, 3, 2)
    plt.title("Benchmark Data")
    plt.imshow(BEN_DATA, aspect = 1/4, cmap = colormap, vmin = 0.0, vmax = 1.0)
    plt.colorbar()

    plt.subplot(1, 3, 3)
    plt.title("Recent - Benchmark")
    plt.imshow(DIFF, aspect = 1/4, cmap = colormap)
    plt.colorbar()

    plt.show()


if __name__ == "__main__":
    CLUSTER_PREC = round(3500 / float(sys.argv[1]), 2)
    runSearch((sys.argv[1]), (sys.argv[2]))

