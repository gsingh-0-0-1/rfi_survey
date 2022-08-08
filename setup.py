import os
import shutil

dirs_to_make = ['TLEdata', 'backups', 'followups', 'logs', 'obs']
files_to_write = ['TLEpass.txt', 'adminkeys.txt']

for d in dirs_to_make:
    os.mkdir(d)

for f in files_to_write:
    open(f, "w")
