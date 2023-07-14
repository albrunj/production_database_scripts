Sensor Codes
============

Scripts for interfacing content related to silicon strip sensors (e.g., IV scans) with the ITk Production Database (ITkPD).

Due to the multiple functionalities required, most of the software/information is in sub-directories:
 - "approvals" is for the steps associated with the sensor approval (either CERN reception after testing, or release to the module sites)
 - [bysite_plots](bysite_plots/README.md) is for the parts flow plots
 - [registration](registration/README.md)" is for the sensor registrations and HPK data summaries upload (for *CERN and KEK* only)
 - [reportingGlobal](reportingGlobal/README.md) is for the summaries of sensor tests and properties
 - "reportingIV" is the software for plotting and viewing IV curves
 - [reporingSimple](reporingSimple/README.md) is for extracting simple values/scripts from DB
 - [sensor_tests_interfacing_functions](sensor_tests_interfacing_functions/README.md)" is D&D software for the sensor QC tests: summary from DB, summary of the new tests, test upload to DB
 - [setupDB](setupDB/README.md)" is for setting up DB tests (for sensor AC's use)
 - [shipments](shipments/README.md)" is for an (easier) shipments of items in DB
 - [upload_legacy](upload_legacy/README.md)" is the legacy code for the sensor tests
 - [uploadSimple](uploadSimple/README.md)" is for the simple upload of test results for select tests (mostly Visual Inspection)

SensorSNUtils.py
----------------------------------------
*Written by Matt Basso. For any questions or help, contact mjbasso2012@gmail.com*

Used as a module. If using this module, only use this method:
```python
makeSN(component_type,sensor_type,wafer_number, dummy=False,subproject=None,qa_piece=False)
```  
Can be used with only the first three args in most situations. If creating a SN for a QA piece, use ```qa_piece=True```.
 If creating a SN for a dummy, use ```dummy=True``` and specify subproject. Subproject must be specified when making SN's for dummys because it can't be extracted from the sensor_type as with non-dummy components.

Installation
============

Some scripts in this directory use the itkdb module for DB communication.

This can be installed using:

```bash
python -m pip install --user itkdb
```
