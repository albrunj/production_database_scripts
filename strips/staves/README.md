Stave README
============

This is the code for dealing with the production database 
in relation to staves.

If you have any questions please contact Jiayi Chen jennyz@brandeis.edu

Load_a_Stave.py
===============

This script can register a new STAVE (initiate) and assemble MODULEs (update).

If you want to try to register a new STAVE and load a MODULE using this script, you need to prepare the following:

a)  use the stave folder in the git repo (/Stave-18-1/, it has one calibration folder of two module assembly info on stave side L)

b)  Register a short slim module through User Interface, give it a local name

c)  Put this local name into the modulesID_L.csv in 'Calibrations' at the correct module position.
    This csv is needed for supplying the unique ID (in this case, it’s the local name) to find the MODULE in PD.

d)  Now run in terminal:

```bash
python3 LoadedStave.py initiate --directory ./Calibrations/ --positions 9
```

follow the directions from prompt lines; it will first register a STAVE and then assemble the MODULE at position 9.

========   =========  ==========  ==========

If you want to assemble more MODULEs to the same STAVE:

a) repeat step b) above

b) save local name in modulesID.csv (say position 10)

c) run:

```bash
python3 LoadedStave.py update --directory ./Calibrations/ --positions 10
```

prompt lines will ask for the local name of the STAVE and assemble MODULE at position 10.

uploadModulePlacementAccuracy.py
================================  

This script is designed to upload the FINAL position survey of all modules loaded on one side of a stave. The current script is uploading the last survey conducted on each module (so technically not the FINAL survey).

If you want to upload such a test:

a) unzip 'ElectricalStaveFinalSurvey.zip' (this is a 'fake' final survey file of the US electrical stave prototype)

b) to upload test, run:
```bash
python3 uploadMPA.py upload --directory ./ElectricalStaveFinalSurvey/
```
 OR to just see what the DTOin look like or test the program:

```bash
python3 uploadMPA.py testing --directory ./ElectricalStaveFinalSurvey/
 ```

c) prompt line will ask for a registered STAVE's local name

SyncSTAVE_GUI.py
================

This script is the GUI version of Load_a_Stave.py. It is to synchronize a local loaded stave with the  corresponding STAVE component in the database:

(1) It can read a local directory (stave folder) that saves all stave loading logs and present the assembly status
(2) It can register a new STAVE
(3) It can upload each MODULE loading information to STAVE in the database
(4) It can check a STAVE’s assembly status in the database

To run this script, first repeat step (a)-(c) in Load_a_Stave.py, then:

```bash
python SyncSTAVE_GUI.py
```
