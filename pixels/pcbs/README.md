# PCB code for PDB

Scripts of PCB registration and test uploads.
  * scripts written in *python3* notebook fashion
  * upload data example in csv format

---

## Data

Data provided in *csv* format for several *PCB_RECEPTION* and *PCB_QC* tests on ~250 *PCB_QUAD* components

In *data* folder:
  * Full dataset provided (~250 components): "RD53A Quad Hybrid QC register - Sheet1"
  * Test dataset (3 components): "TestSheet1"


## Scripts

In analysis folder
  * PDBinfrastructure - common authentication and DB access functions. Based on [*itkdb*](https://pypi.org/project/itkdb/) API client
  * myDetails_template - simple class template for holding authentication credentials. *to be updated by user*
  * scripts directory (in *jupyter* (*.ipynb*) and *hydrogen* (*.py*) notebook formats)
    * registration - read in CSV and register components using ASN
    * testUpload - read in CSV and update components in PDB with test data
    * deletionScript - check PDB and delete selected components
    * plottingCSV - (simple) plotting based in CSV
    * plottingPDB - (simple) plotting based on PDB queries

**NB** check paths before running: *jupyter* notebook is assumed in *scripts* directory; *hydrogen* notebooks assumed running from production_database_scripts (top) directory
