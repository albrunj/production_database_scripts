Module Codes
============

Scripts for interfacing content related to strip modules (e.g., ITSDAQ tests) with the ITk Production Database (ITkPD).

uploadITSDAQTests.py
--------------------

A command line script for uploading ITSDAQ results from a local machine to the ITkPD. General use is:

```bash
python uploadITSDAQTests.py <$(SCTDAQ_VAR) location> [--getConfirm] [--uploadFiles] [--psPath <ps folder path>] [--cfgPath <config folder path>] [--recursionDepth <depth>]
```

Where `--getConfirm` will ask for a confirmation of each file to be uploaded, `--uploadFiles` will look for \*.pdf, \*.det, \*.trim, and \*.mask files associated with each test and upload them, `--psPath` denotes the location of the $(SCTDAQ_VAR)/ps/ location or equivalent (in case the location where the ps output is stored is not in the ITSDAQ installation directory, $(SCTDAQ_VAR)), `--cfgPath` denotes the location of the $(SCTDAQ_VAR)/config/ location or equivalent (for the same reason as ps; in these cases, <$(SCTDAQ_VAR) location> is assumed to point to $(SCTDAQ_VAR)/results/), and `--recursionDepth` denotes how deep you wish to search for files in any of the aformentioned directories (default = 0 := top level). Running `./uploadITSDAQTests.py --help` gives a print-out similar to the above.

ITSDAQUploadGui.py
------------------

A GUI interface for uploading ITSDAQ results from a local machine to the ITkPD. General use is:

```bash
python ITSDAQUploadGui.py
```

Where the arguments within the GUI match those as uploadITSDAQTests.py. For a tutorial on either script, please refer to this [talk](https://indico.cern.ch/event/808725/contributions/3385800/attachments/1828778/2997008/190410_Basso_ATLASUpgradeWeek_ITkPDQualificationTaskSummary_EDITED.pdf). Note: for ease of debugging the GUI, one should set `_DEBUG = True` at the top of ITSDAQUploadGui.py, which will provide a print-out of the functions the GUI is entering/exiting.

Module Inspection GUI
---------------------

Adam Azoulay has provided [code](https://gitlab.cern.ch/aazoulay/ITkTrackingGUI) for a hybrid/powerboard/module visual inspection. The project is archived; in the case the previous link becomes broken, Matt Basso has a fork of the project.

IVScanGUI.py
------------

GUI for comparing module IV scans of type "MODULE_IV_PS_V1" with those of their respective sensors. Modified from Seth Zenz's sensor IV GUI found [here](/strips/sensors/reportingIV)

User guide by Seth Zenz for the sensor GUI: https://twiki.cern.ch/twiki/pub/Atlas/StripsDatabase/Zenz-IVScanGUI-Documentation.pdf

The module GUI is very similar to that described in this document. The most notable exception is this GUI replaces the option to plot/select by batch with the option to plot/select by serial number. In addition, the code now searches for IV scans of type ATLAS18_IV_TEST_V1 in child sensors. There is currently no option to not plot the child sensor IVs if they exist. Future work may implement this capability.

Contact Emily Duden at emilyduden@brandeis.edu with questions.

getAsicConfig.py
----------------

Script for pulling the initializations used during the ABCStar wafer probing and writing the info to an ITSDAQ config.  It will iterate over each ABCStarV1 chip assembled to a STAR Hybrid Assembly, pull the "DAC_TEST" JSON, and write the relevant info to an ITSDAQ config.

Example usage:
```
python getAsicConfig.py --serial 20USBHX2000791
python getAsicConfig.py --local GPC1938_X_002_B_H2
```

You must provide either the serial number of the STAR Hybrid Assembly or the local name.  This script is tested for barrels, and feedback from the endcap community would be appreciated.

This script should have the same python version requirements as what's listed in the top-level [README](/README.md).

Contact Ian Dyckes at ian.dyckes@cern.ch with questions.
