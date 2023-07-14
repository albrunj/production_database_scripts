Software for "global" reporting of the sensors properties and test results
==========================================================================



create_local_sensorDB.py
----------------------------------------
*Written by Derek Hamersly. For any questions or help, contact derek@coho.org*

```bash 
python create_local_sensorDB.py [-d LOCALDBNAME]
```

This script retrieves all sensors and dummy sensors from the itk production database into a local json file from which one can quickly create global summary spreadsheets (with write_summary_to_xlsx.py). The itkstrips.ucsc.edu server hosts a Redis cache of this data, so it shouldn't take very long.

postprocess_localDB.py
----------------------------------------
*Written by Derek Hamersly. For any questions or help, contact derek@coho.org*

NOT FOR STANDALONE USE. Used as module at the end of create_local_sensorDB.py. For each sampling QC test (fullstrip and current stability), if at least 4 sensors fail in a batch, mark all sensors in that batch as failed. Future post-processing should be implemented in this script.

write_summary_to_xlsx.py
----------------------------------------
*Written by Derek Hamersly. For any questions or help, contact derek@coho.org*

```bash 
python write_sensor_summary_to_xlsx.py [-h] -g {sensor,shipment,batch} [-f [FILTERS [FILTERS ...]]] [-o OUTFILE] [-d LOCALDBNAME] [-s {ingot,ShipmentDate*,ShipmentName*,arrivalDate,batch,currentLocation,origLocation}]
```

Specialized inventory summary to local XLSX. Before using, you must have a local copy of the LOCALDBNAME that was created by create_local_sensorDB.py. 

Use `-g batch` to group the spreadsheet by sensor batches. Each row will have either a full batch or part of one. By default, rows are sorted by arrivalDate, but one can use `-s` to specify which attribute to sort rows by. 

Use `-g shipment` to group the spreadsheet by shipments. Each row will have either a full shipment or part of one. 

Use `-g sensor` to group the spreadsheet by sensor. This gives a very detailed look at all sensors in the database.


json_to_xlsx.py
----------------------------------------
*Written by Derek Hamersly. For any questions or help, contact derek@coho.org*

```bash 
python json_to_xlsx.py [-o OUTFILE] [-t SUMMARYTYPE] [-s SORTBY]
```

This is used as a module in write_summary_to_xlsx.py, and shouldn't be used as a standalone script (though it can be). It looks for "tmpvalues.json" and "tmpformatting.json" which are outputted by write_summary_to_xlsx.py, and writes these data into an XLSX file with XlsxWriter. The `-t` argument is the same as the `-g` argument in write_summary_to_xlsx.py.

