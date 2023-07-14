Software for sensor registration in DB (by *CERN and KEK*)
==========================================================

Some parts of the software in this directory is for correcting the data structures, checking the registrations, and adding/correcting data. All of which is for *special cases* only.

In general, this software is *NOT* to be used by other sensor QC, sensor QA, module/stave/petal building sites. 


registerSensors__ATLAS18.py
---------------------------
*Written by Matt Basso. For any questions or help, contact mjbasso2012@gmail.com*
*Updated for production from Matt's version by Vitaliy Fadeyev, fadeyev@ucsc.edu*

A command line script for registering **pre-production and/or production (i.e., ATLAS18)** silicon strip sensors received from HPK in the ITkPD and uploading IV scan results provided by HPK for each sensor to the ITkPD. Closely based on the above script. General use is:

```bash
./registerSensors__ATLAS18.py -q -d <directory path containing HPK results files> -i <institution code to associate the sensors with> -r <arrival date = dd/mm/yyyy> [-D]
```

Where `-d (--inputDir)` points to the directory containing the identifying information for the sensors (e.g., serial numbers) and the IV scans as provided by HPK. The `-d (--institution)` flag indicates the institution code to associate the registered sensors and test results with. The `[-q]` is a flag to also register one mini QA piece and one chip QA piece. (This is the production scheme!) The `-r` argument specifies the date of the sensor arrival to the reception site in "dd/mm/yyyy" format.
The `[-D]` is a flag to let the program know that all scripts in the `--inputDir` are dummy files. Running `./registerSensors__ATLAS18.py -h (--help)` gives a print-out similar to the above. Note: the serial numbers are set manually for silicon strip sensors and come from HPK. However, the HPK-provided serial numbers follow the pattern set by ATLAS ITk.

Note: 


registerSensors__ATLAS18_noHM.py
---------------------------
*Cloned by Vitaliy Fadeyev *

A special case of the script above, in case of replacement/production reception weirdnesses. It does not register halfmoon sensors. The emphasis is on Wafer/Sensor registrations. It can optionally register the QA pieces along with them.


registerSensors__aux.py
---------------------------
* Written by Vitaliy Fadeyev, contact fadeyev@ucsc.edu *

A special case of the registerSensors_ATLAS18.py, in case of a wrong wafer reception. It also only registers the Wafer/Sensor. It does not upload any HPK data. It does not register halfmoon sensors or QA pieces. 


old_registerSensors__ATLAS18.py
---------------------------
*Written by Matt Basso. For any questions or help, contact mjbasso2012@gmail.com*

This is the original "ATLAS18" registration script. It was used for pre-production and kept here as a record.



registerQA.py
---------------------------
*Written by Derek Hamersly. For any questions or help, contact derek@coho.org*

A standalone script for registering a batch of QA pieces. 
```bash
python registerQA.py -fp/--fpath <path to file with list of QA pieces to register>
```

The input file must have a list of QA pieces. If dummies, the subproject line must be used as the second line of the file. If not dummies, ignore the subproject line.  
QAregistrationfile.txt:  
Line 1: `institution      <institution>`  
Line 2 (ONLY USE IF REGISTERING DUMMIES): `subproject       <subproject>`  
All subsequent lines: `<sensortype>,  VPX<batchnum>-W<wafernum>,  <QA comp name>,  <WaferPositionLabel>`  

Examples of the format of the QA piece lines are below:  
(dummy) `ATLASDUMMY18,    VPX12345-W54321,   Sensor QAchip test,   ATLAS test chip 3 - A4`  
(real) `ATLAS18R0,    VPX12345-W54321,   Sensor Testchip&MD8,   ATLAS test chip 1 - A2`  
If registering dummy QA pieces, don't include the subproject line.  
Cannot combine dummy and real QA pieces in same file!  


updateTestRuns.py
----------------------------------------
*Written by Derek Hamersly. For any questions or help, contact derek@coho.org*

```bash 
python updateTestRuns.py -d <directory path containing updated HPK results files> -i <institution> [-D]
```

This script should be used when corrected data is received. This will reupload all the testruns corresponding to the test files in the input directory.  


registerSensors__prototypes.py
------------------------------

A command line script for registering **prototype (i.e., ATLAS17)** silicon strip sensors received from HPK in the ITkPD and uploading IV scan results provided by HPK for each sensor to the ITkPD. Written by Martin Sykora from Charles University in Prague. General use is:

```bash
./registerSensors__prototypes.py --inputDir <directory path containing HPK results files> --institution <institution code to associate the sensors with>
```

Where `--inputDir` points to the directory containing the identifying information for the sensors (e.g., serial numbers) and the IV scans as provided by HPK and `--institution` indicate the institution code to associate the registered sensors and test results with. Running `./registerSensors__prototypes.py --help` gives a print-out similar to the above. Note: the serial numbers are set manually for silicon strip sensors and come from HPK. However, the HPK-provided serial numbers follow the pattern set by ATLAS ITk.


