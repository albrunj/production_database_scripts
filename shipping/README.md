Shipping
========

For managing shipments, run:

```bash
python ship.py
````
And the script itself should be self-guided. For now, this script may be used to create shipments, but we would also like to add the ability to list all the outgoing/incoming shipments at institution, receive shipments and add comments, etc.

**Note**: When creating a shipment, when the script asks about adding components to a shipment from an input file, the filepath entered (no tab-completion) must be *relative* to the where ship.py is run from, e.g., if you run `python shipping/ship.py` from the top level of `production_database_scripts` and you have a file shipment.txt in shipping/ with the component codes and/or serial numbers to add, then you would enter `./shipping/shipment.txt` (on Linux or Mac) or `.\shipping\shipment.txt` (on Windows) when prompted to.

The excel_shipments.py script can be used to build a shipment from
rows in a spreadsheet.
