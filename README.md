# ATA RFI Database

## Setup
This section is here for documentation; this is all set up already on the ATA computers (@ http://frb-node6.hcro.org:9000), and so if you are looking for information on how to use the database and website, skip to the [Usage](#usage) section.
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
All interaction with the database and related functionalities can and should be done through the front-end / webserver rather than the command line

### RFI Observation Portal
#### Observation Details
The full-sky (or if you're a stickler, almost-full-sky) scans from 20 to 80 degrees in elevation are processed into heatmaps with 5.25 MHz of bandwidth and waterfall plots for each elevation swivel. These observations are done by swiveling a given antenna around the full 360 degrees of azimuth at any given elevation, spacing elevation by 2.5 degrees -- and with multiple antennas, the antennas stagger their elevation swivels in order to cover the entire sky faster than if they were to all observe the entire sky. A waterfall plot is generated for each elevation swivel.

#### Data Rate / Sampling
The data that are stored are heavily downsampled from the original filterbank files. The filterbank files are downsampled by a factor of 32 in the time domain, and a factor of 11 in the frequency domain (0.25 MHz -> 5.25 MHz). This allows the storage of the relevant data for one scan (downsampled data, images, etc...) to be stored in roughly `80 MB` compared to the `12GB` of raw data, a reduction by a factor of about 150.

### RFI Catalog
#### Querying
