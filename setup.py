import os
import shutil

dirs_to_make = ['TLEdata', 'backups', 'followups', 'logs', 'obs']
files_to_write = ['TLEpass.txt', 'adminkeys.txt']

for d in dirs_to_make:
    os.mkdir(d)

for f in files_to_write:
    open(f, "w")

os.system('npm install express')
os.system('npm install sqlite3')
os.system('npm install better-sqlite3')
os.system('npm install socket.io')
os.system('npm install serve-index')
