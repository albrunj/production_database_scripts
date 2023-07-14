Software for DB shipments of objects
==================================================

easy_ship.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python easy_ship.py [-c ControlFile [-p printTemplate] ]
```

This script does the DB footwork for entering information about a shipment and sending if off. The information is taken from the <ControlFile>. The option *-p* only prints the Control File template, as an example.

The more detailed description is available on TWiki: https://twiki.cern.ch/twiki/pub/Atlas/StripsDatabase/DB-shipping_instructions_2021-06-27.pdf .


makeSNlists.py
*Written by Derek Hamersly. For any comments, please contact derek@coho.org*

```bash 
python makeSNlists.py [-i inputDir -o outputFile [-b BatchNumber]]
```

This script takes in a directory with HPK data files, then writes an output file with SNs for the sensors and halfmoons. The optional *-b* parameter restricts the list to the ones from the specified batch number.

