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
The querying mechanism on the catalog page is relatively self-explanatory; the raw querying functionality may be useful for those who wish to do more data analysis with the results from the database, as it returns JSON-formatted data.

### Observation Scheduler
#### Sky Scan
Sky scans are explained in the [Observation Details](#observation-details) section.

#### Follow-Ups
Follow-ups allow for users to image a specific area on the sky to get a better idea of what an RFI source might be. This will be used in the near future to automatically follow-up on newly-detected sources of RFI. The images are generated by calculating the pointing direction of the antenna(s) from the generated ephemeris files, extracting the appropriate slice (both in the time and frequency domains) of the filterbank file, and adding it to an array representing an image. The array is finally element-wise divided by the number of times a power value was added to any one element, and so we obtain the average power at each point in the image.

##### Raster
Raster scans create images by generating an ephemeris file from a center azimuth and elevation, the plus/minus "interval" for azimuth and elevation, and the gap (or spacing) between each "row" in the raster scan. The raster scan scans through the entire azimuthal range at each elevation (rather than scanning through the entire elevation range at each azimuth) due to the fact that the azimuth rotation drives at the ATA can operate at 3 times the speed of the elevation drives.

##### Flower
Flower scans differ in that they provide a better view of the central region. This can be especially useful for studying the radial extent of geostationary sources and satellites, since they will not move much over the time of the scan, unlike astronomical sources (especially those near the equator). Instead of azimuthal and elevation extent and the spacing gap, flower scans take in a number of petals (which will be rounded to the nearest multiple of 4) and a radial extent.

### Spectral Occupancy
Spectral occupancy is a metric that lets us estimate how often a specific set of frequencies are active at a certain location. The spectral occupancy map provides a user interface to visualize spectral occupancy and query the RFI catalog at the selected locations and frequencies. Changes in spectral occupancy are what will guide the automatic follow-up observations that will be conducted. The completion of this functionality will fully eliminate the human need to manually search for sources of interference at the ATA, and relegate the extent of human involvement to the inspection of follow-up observations to ensure that the observed sources are either transient or avoidable.

### NRDZ Scan Data
The National Radio Dynamic Zone has various sensors around Hat Creek Radio Observatory (HCRO) which scan through a number of frequencies in a periodic fashion. Images are generated from these data, and those images can be seen in the NRDZ Scan Observation Portal.
