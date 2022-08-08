# ATA RFI Database

## Setup
### Server
Begin by running the `setup.py` script. Then, run `node main.js` to start the database server. The server assumes a given directory structure that is present on the ATA computers for observational data.

### Satellites
You will have to setup up a Space-Track account (https://www.space-track.org/), and place your password in a file called `TLEpass.txt`. (Make sure to remove the trailing newline.)

### Observation Scheduler
Observation scheduling requires the setup of authorization keys. Create a file called `adminkeys.txt`, and format it as such:
```
<authorization key #1>,<observer name #1>
<authorization key #2>,<observer name #2>
```
and so on and so forth.

In order to use the `system_obs.*` scripts, you should set up at least one key/name pair with the name `SYSTEM_OBS`.

## Usage
