import os
import shutil
import sqlite3

dirs_to_make = ['TLEdata', 'backups', 'followups', 'logs', 'obs']
files_to_write = ['TLEpass.txt', 'adminkeys.txt']

for d in dirs_to_make:
    os.mkdir(d)

for f in files_to_write:
    open(f, "w")


python_libs = ['numpy', 'matplotlib', 'bs4', 'requests_html', 'scipy', 'sgp4', 'skyfield']
for lib in python_libs:
    os.system('pip install ' + lib)


node_libs = ['express', 'sqlite3', 'better-sqlite3', 'socket.io', 'serve-index']
for lib in node_libs:
    os.system('npm install ' + lib)


sql_setup = {
        "obsdata.db" : ['CREATE TABLE obsdata (obs text, cfreq real, flagged bit, name text, UNIQUE(obs, cfreq))'],
        "rfisources.db" : ['CREATE TABLE "rfisources" (obs text, start_az real, end_az real, elev real, cfreq real, exceed real, antlo text, source_sat text, source_sat_az real, source_sat_el real, UNIQUE(obs, start_az, end_az, elev, cfreq, exceed, antlo))'],
        "followups.db" : ['CREATE TABLE followups (datetime text primary key, name text, params text, source text)']
        }

for dbname in sql_setup.keys():
    db = sqlite3.connect(dbname)
    cur = db.cursor()
    for command in sql_setup[dbname]:
        cur.execute(command)
    db.commit()
    db.close()

print("Make sure you have sigpyproc installed (https://github.com/ewanbarr/sigpyproc)")



