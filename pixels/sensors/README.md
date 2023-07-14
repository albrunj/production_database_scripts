# ITK Production Database, Pixel side GUI

Itk production database GUI for component registration and test run uploads.

## Required packages:

Requirements are listed in [requirements.txt](requirements.txt)

```
pip install -r requirements.txt
```

## Authentication

For authentication:

- export ITKDB_ACCESS_CODE1=(your itkdb password1)
- export ITKDB_ACCESS_CODE2=(your itkdb password2)
- type `itkdb authenticate` in the terminal

You should get a response that you are authenticated as you and NOT as anonymous. If you experience being logged in as `anonymous` try to remove the `.auth` file via `rm .auth` and try again.

## How to use the GUIs:

In order to run either of the two GUIs
simply cd into /GUI and run either RegisterComponent.py or UploadTestResult.py.


### Register components:

For registration of new modules run the script "RegisterComponent.py" a window should appear with several drop down menus.
Choose the desired project, subproject, component type and flavor, and add an attachment if desired.

Hit the "Set Parameters of component" button to change the .json dictionary that will be uploaded.
A preview of this json will appear on the right side in the window.

To register the component, after the parameters has been set, click the "Register component" button, and the terminal will (hopefully) give you a feedback that the componet has been registered!


### Wafer maps:
Wafer Maps are .json files that can be found in the directory "WaferMap". These files contains the positions and types of all the sensor tiles connected to a wafer from a given vendor. The code will run trough wafer map file in a for loop and register and attach all the sensor tiles to the (parent) wafer. This method was specially meant for institutes that had ~20-30 dices on their wafer and would save time by not having to register the sensor tiles manually one by one.

This method, however, is just an optional shortcut for registering all the sensors tiles on a wafer right after registering the wafer itself. But you also need to know which vendor number (V1-V6 in the new SN schema) this wafer map should be connected too.

You can add or change your wafer map in inside the "Wafermap" directory. However, the position number of the sensor tile is standardized (changing this would also mean to change the for loop in the "RegisterComponent.py" script.

- Example for Vendor6.json Wafer map:
  Here the script will first register 3 single RD53a sensors with position (1-3), 5 quads position (4-8) and then 3 singles again with position (9-11) in the database and attach them to the wafer. The number inside the 2D array element (NR: 1-6) decides the sensor type. More information on the sensor type numbers can be found in the SN schema.


### Upload test results:

- In order to upload test results to an already registered module start the script "UploadTestResult.py".

- A window should appear. Here you choose what test you want to upload from the dropdown menu at the top.

- Below the dropdown menu you can find a "browse"-button in order to browse for datafiles associated to the selected test type.
  You can browse and add more than one datafile, and they will be appended in a list in the same order as you selected them.

- Below the browse button you find an entry-field, this entryfield is activated by clicking the button next to it.
  The purpose of this field is to enter the depletion voltages for the IV test uploads. The entered values are appended to a list in the order they are typed by clicking the button next to the entry-field once more.

NB! The inter-pixel capacitance and resistance results can be easily added via. the Web App by going to My components -> Choose Component -> Click + sign at the bottom of the page under test. 

### Notebooks:
Skeleton scripts for specific database tasks. Scripts are in [Jupyter](https://jupyter.org) (.ipynb) and other interactive coding environment (.py) formats.
**NB** Useful library for Jupyter conversion [here](https://pypi.org/project/ipynb-py-convert/)

* *FindComponent*: find specific component(s)

* *FindTest*: find/change test information for specific components

* *CreateBareModule*: create a bare quad digital module, and check expected tests

* *FindComponentVoila*: find specific component(s) in a [Viola](https://github.com/voila-dashboards/voila) friendly notebook - using ipywidgets functionality

**NB** to run any notebook be sure to set environment variables in *setEnv.py*

### Other:
In the folder Analyses you can find the analysis scripts for IV, CV and IT measurements

## References
- [Qualification task report by Simon Huiberts](https://cds.cern.ch/record/2808669)
