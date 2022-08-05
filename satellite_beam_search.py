import numpy as np
import pandas as pd

import sgp4
from sgp4.api import Satrec

import datetime
import os
import sys
import shutil

from utils.dateutils import string2date, date2string
from skyfield.api import EarthSatellite
from skyfield.api import load, wgs84
import sqlite3

from utils.colors import bcolors
from utils.dateutils import date2string, string2date

import satellitesearch
from fetchTLE import fetchTLE

def checkEphemerisIntersections(ephemname, freq):
    ephem = np.loadtxt(ephemname)

    FOV = 3500 / freq
    TOL = FOV / 2

    timescale = load.timescale()

    t = ephem[0][0] / (10 ** 9) - 37
    dt = datetime.datetime.utcfromtimestamp(t)
    dt_s = date2string(dt)

    satellite_data = satellitesearch.generateSatelliteData(dt_s)
    
    for pointing in ephem:
        pointing_az = pointing[1]
        pointing_el = pointing[2]
       
        print(bcolors.WARNING + "Checking satellite matches at ephem pointing", round(pointing_az, 3), "\t", round(pointing_el, 3), bcolors.ENDC)

        TOL_corrected = TOL / np.cos(pointing_el * np.pi / 180)

        az_range = [pointing_az - TOL, pointing_az + TOL]
        el_range = [pointing_el - TOL_corrected, pointing_el + TOL_corrected]

        for item in satellite_data:
            name = item[0]
            satellite = item[1]

            satellite_time = timescale.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

            topocentric = satellite.at(satellite_time)

            sat_el, sat_az, radial_d = topocentric.altaz()

            sat_el = sat_el.degrees
            sat_az = sat_az.degrees
            radial_d = radial_d.km

            if sat_el < 20:
                continue

            az_check = (sat_az >= az_range[0]) and (sat_az <= az_range[1])
            el_check = (sat_el >= el_range[0]) and (sat_el <= el_range[1])

            if az_check and el_check:
                print("\t" + bcolors.OKCYAN + "Potential intersection at ephem pointing" + bcolors.OKGREEN, round(pointing_az, 3), "\t", round(pointing_el, 3), bcolors.OKCYAN + "with satellite" + bcolors.FAIL, name, bcolors.OKCYAN + "at" + bcolors.OKGREEN, round(sat_az, 3), "\t", round(sat_el, 3), bcolors.ENDC)



