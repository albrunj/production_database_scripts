# Introduction

This was developed by David Rousso (david.rousso@cern.ch) and Dominic Jones (dominic.matthew.jones@cern.ch). 

Hello, this is the script library for analyzing QC Tests and uploading QC tests to the central CERN ITK database system.

Note that you will need to have an ITK database account and know your 2 access codes in order to run this code. You will have to enter these codes at the start of each Python session. 

Please let us know if there are any issues/bugs. 

If you haven't already cloned this repository, see the [top level](/README.md) guide for installation instructions.

You must then navigate to the `strips/sensors/sensor_tests_interfacing_functions` folder. There is a jupyter notebook tutorial there called `Brief Tutorial.ipynb` to help you get started.

In order to install jupyter notebook, use Anaconda. See `https://test-jupyter.readthedocs.io/en/latest/install.html`

In case you are unable to use jupyter, the markdown of the tutorial has been copied below as documentation. 

Note that you may require to `pip3 install` some libraries if you do not have them, such as `requests`

Also note that python needs to be able to see the scripts in this folder in order to run them, so if you are not running in this folder, you may need to add this folder to your python path. 

```
import sys
sys.path.append('??/production_database_scripts/strips/sensors/sensor_tests_interfacing_functions')
```

# Brief Tutorial

Welcome to the tutorial. We will first go over some of the basics in explaining the example files and the general setup of the scripts.

As a note, in general, you should never need to modify any of the python files in normal use except for the `CommonConfig.py` in which you would only ever need to make some minimal changes depending on how you would like things set up. 

After this we will go over the **primary use cases**, namely, if you have just run a QC test and you want to generate an analysis report for it to extract the parameters and see how it compares to all the ITK DB data in its batch, and also if you want to have the option to subsequently upload this test to the ITK DB. We will also go over the case of generating a report for a batch even if you don't have a local file at hand. All of these primary use cases **can also be done via the command line directly** without the need for going through interactive python, and so we will show how to do this. 

After this we will go over the more detailed nitty gritty things you can do to play with your data directly and interactively in python, like trying to make queries on your local or the ITK DB data.

After this we will go through some more advanced stuff that most people should not need to deal with unless they are doing something advanced, like rewriting your local tests into a standard format, manually analysing and uploading a test, viewing a special stability report to see the non-temperature-compensated curves and a humidity-current histogram, or manually creating a comparison report. 

If you cannot run this as a jupyter notebook, you can simply open python interactive and copy and paste the commands as we go. Do this by typing `python3 -i` in the command line. Again, note that you only need the interactive to help you learn and if you are doing more detailed queries, and that for the major use cases, you do should not need to do anything interactively if you do not want to and you can run them directly from the command line as we will go over later. In the case that you are not running in the folder, you will need to add the `/production_database_scripts/strips/sensors/sensor_tests_interfacing_functions/` folder to path so that the script are accessible and change the `querypath` and `outputpath` accordingly. 

Note: you will need to run these following few cells in this short "introduction" section for the rest of the tutorial to work.

## An important note about test file formats:

The templates for the various file formats that are recognized by the scripts are in the `DataFormats` folder.

If you have a test file that you would like to deal with that is not in one of the provided template formats, you can make your own.

Look at the existing examples to get an idea of what to do. In general, for the header, replace the value of the field with "$$$TAG&&&" where "TAG" is the corresponding tag of that field. Check the `datafields` variable in Section 6 of `CommonConfig.py` for the full list of recognized tags.

Replace the entire table including the headers with "$$$TABLE&&&". If there are any unrecognized header names, add them to `alternatecolumnnames` in Section 2 of `CommonConfig.py`.

Ensure that any spaces or carriage returns stay as is an only the field values are replaced by the tags. 

**However I strongly suggest you don't try this until you have played with the Example Files first**

### The Example Test Files and Your Query Path

The `querypath` variable is a path/folder/ or list of paths/folders of local tests (i.e. on your local disk) that you want to import into python to analyze/upload/do anything with. The scripts will comb through recursively through everything in the `querypath` to find every .dat or .txt file and try to import it as a test file. 

Some example test files have been provided in the `Example Files/Example Wafer Test Files` folder, one for each test type that the scripts can deal with, so that you can start playing with the scripts directly out of the box.

Note that out of the box, the scripts are set to deal with dummy sensors so that you can play around and learn how to use things without fearing breaking anything. We will go through how to check whether or not the scripts are set to dummy sensors or real sensors later. 

For the dummy sensors, your site should have been sent a few dummy sensors (from batches VPX90001 and VPX90002).

Note that the example files given have a set wafer/batch/serial, and that you will not be able to upload a test to a wafer if the ITK DB thinks your site does not have it. This means that before you can upload things, **you will need to manually change the wafer/batch/serial in all the example files to those of a wafer that has been given to your site.** You may get errors if the wafer you are trying to upload is not in the correct stage or institution on the ITK DB so be sure that this is done correctly. 

Additionally, the scripts **ideally** should not allow you to upload duplicate tests, meaning that if you are still playing around with uploading these example files and wish to upload them again, you may need to manually change a couple of numbers here and there to make the scripts think that you are not uploading a duplicate test. 


```python
### querypath for the built-in example files:
querypath=r"Example Files\Example Wafer Test Files"

### Example querypath's from Cambridge's local file system:
#All Test Files on Cambridge Local Disk
#querypath=["/var/clus/pc_backup/Cleanroom/data/sisensors/","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2020"]

#Just VPX30816 on Cambridge Local Disk
#querypath=["/var/clus/pc_backup/Cleanroom/data/sisensors/VPX30816/","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019/CMM/VPX30816","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019/Long Strip/VPX30816","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019/Testing/CMM/VPX30816"]

#Latest Stuff:
#querypath="/pchome/cleanrm/LabView/QC_test_dat/ATLAS18S/VPX32409/"

#Dummy Sensors:
#querypath="/var/clus/pc_backup/Cleanroom/data/sisensors/VPX90002/"
#querypath="/var/clus/pc_backup/Cleanroom/data/sisensors/VPX90001/"
```

### The Output File Path for the Analysis Report

For many of the primary use cases, an HTML interactive analysis report will be created. In general you can actually ignore this argument if you wish as the scripts will put it in a default filepath and open it for you in a browser automatically if it can, but it is still useful to define where it is so you know where to find it if you need to. 


```python
### Example outputfile path:
outputfile="Example Files/Example HTML Reports/TestHTMLReport.html"
```

### Checking the Configuration of the Scripts

Run the following to check to make sure that the scripts are set to deal with the correct project, the dummy sensors or real sensors, and that the test types are correct (by default these should be the dummy sensors, but this is a good place to check that things are sensible in case you are already at the point where you are changing the configuration to deal with the real sensors.

I am also making you input your credentials here so you don't need to bother doing so in the rest of the tutorial, and also you can fix issues regarding that now if need be.

Note that when you are ready to change to deal with real sensors, go to `CommonConfig.py` and change the `ITK_COMPONENTTYPE` accordingly near the top of the file. 

If you are making any changes to any python files you will need to restart this notebook. 

`ITK_PROJECT` should be `S`
`ITK_COMPONENTTYPE` should be `SENSOR_S_TEST` for dummy sensors, and `SENSOR` for real sensors. 

**NOTE: IF WHENEVER YOU ARE RUNNING THINGS YOU START TO GET WEIRD TOKEN RELATED ERRORS THIS MEANS YOUR TOKEN HAS EXPIRED AND YOU NEED TO REAUTHENTICATE. IF YOU ARE UNABLE TO REAUTHENTICATE, CLEAR THE `production_database_scripts/strips/sensors/sensor_tests_interfacing_functions/.env` file to reset the state!**

(If in the case you leave the notebook open for too long and your token expires and you need to reset it, run this:)
```
import __path__
import dbAccess
dbAccess.token=None
```


```python
from CommonConfig import ITK_PROJECT,ITK_COMPONENTTYPE,TestType_IV,TestType_CV,TestType_Metrology,TestType_Strip,TestType_Stability,TestType_Manufacturing,TestType_IV_Hammamatsu

print('The current settings are:')
print('')
print('ITK_PROJECT="'+ITK_PROJECT+'"')
print('ITK_COMPONENTTYPE="'+ITK_COMPONENTTYPE+'"')
print('')
print('TestType_IV="'+TestType_IV+'"')
print('TestType_CV="'+TestType_CV+'"')
print('TestType_Metrology="'+TestType_Metrology+'"')
print('TestType_Strip="'+TestType_Strip+'"')
print('TestType_Stability="'+TestType_Stability+'"')
print('TestType_Manufacturing="'+TestType_Manufacturing+'"')
print('TestType_IV_Hammamatsu="'+TestType_IV_Hammamatsu+'"')
```


```python

```

## Primary Use Cases: Analyzing and Uploading Tests!

We will go through all of the primary use cases. For these, you have the choice of running them either interactively or via the command line directly. I will first give a cell to run interactively, then a cell to print out what command you would need to copy to your command line if you wish to run it via the command line. (We cannot run via the command line directly from the notebook if you need to authenticate, so I will provide the exact line needed for the example files, as well as a cell that will print out the command needed in case you changed the querypath or the outputfile. 

### Just Generating an Analysis Report for a QC Test(s) You Did

Let's say you just ran a QC Test(s) and you want to analyze it (i.e. have the scripts extract the relevant parameters and then put it on interactive plots to compare it to the rest of the tests in the batch that are already on the ITK DB). 

Run the following. This will produce an HTML report. Note that Green is Pass, Yellow is So-So, Red is Fail, Blue is suspected Measurement Error, Grey means there is something weird with the test like there is no data, and **bright** colours are for the local test you put in `querypath`, and **dark** colours are for tests already on the ITK DB. 

**To run interactively:**


```python
import RUNME_GenerateBatchReport
TESTCOMPARISONDATA=RUNME_GenerateBatchReport.MAIN(querypath,outputfile)
```

**To run directly via command line:**

For the default example files:

`python3 RUNME_GenerateBatchReport.py "Example Files/Example Wafer Test Files" "Example Files/Example HTML Reports/TestHTMLReport.html"`

If you changed anything, you can see what command to run by running the following cell:


```python
print('python3 RUNME_GenerateBatchReport.py "'+str(querypath)+'" "'+str(outputfile)+'"')
```

### Doing the Same as Above, But With the Option to Upload the Test to the ITK DB Afterwards

If you not only want to see the analysis report, but also have the option to upload the test afterwards, do the following. Note that the scripts will prompt you to confirm the upload, and will give you the option to choose to upload/not upload tests and change decisions if needed, as well as give you the option to just quit. By default, only tests that passed have their "Upload?" flag set to True. 

**You may have noticed in the report that the CV and IV Example Tests have a "Measurement Error" flag.** If you read the entries in the report, you will notice that this is due to the fact that the humidity was exceeded and so the data is not actually valid. By default, these will not be uploaded, but you as the technician can judge whether or not it is still good and manually change it to "Pass" or "Fail", and if you wish to upload it, manually set "Upload" to "True" in the upload UI below.

**To run interactively:**


```python
import RUNME_GenerateReportAndUploadTests
FlattenedTestList=RUNME_GenerateReportAndUploadTests.MAIN(querypath,outputfile)
```

**To run directly via command line:**

For the default example files:

`python3 RUNME_GenerateReportAndUploadTests.py "Example Files/Example Wafer Test Files" "Example Files/Example HTML Reports/TestHTMLReport.html"`


If you changed anything, you can see what command to run by running the following cell:


```python
print('python3 RUNME_GenerateReportAndUploadTests.py "'+str(querypath)+'" "'+str(outputfile)+'"')
```

### Creating an Analysis Report for ITK DB Data Only for a Given Batch w/o a Given Local Test File

If you don't need to analyse any local test files and you just want to generate the report for everything on the ITK DB for a given batch, simply run the following:

**NOTE:** There is the optional `wafers` parameter here that can be introduced which is a list of only which wafers you want to show in the report. This is optional and if it is not included it will show all the wafers. This has been added below because of the issue arising that there are hundreds wafers in the dummy batch which may make the report slow. You would add something like `wafers=[141,161]` to the arguments.

**To run interactively:**


```python
batch="VPX90001"
wafers=[164, 175]

import RUNME_GenerateBatchReport
TESTCOMPARISONDATA=RUNME_GenerateBatchReport.MAIN([],outputfile,batch,wafers)
```

**To run directly via command line:**

For the default example files:

`python3 RUNME_GenerateBatchReport.py "[]" "Example Files/Example HTML Reports/TestHTMLReport.html" "VPX90001" "[164, 175]"`

If you changed anything, you can see what command to run by running the following cell:


```python
print('python3 RUNME_GenerateBatchReport.py "'+str('[]')+'" "'+str(outputfile)+'" "'+str(batch)+'" "'+str(wafers)+'"')
```

### Directly Uploading Tests Without Analysis (with Automatic Pass)

This is for directly uploading tests that are not the standard IV/CV/STAB/STRIP/BOW

If you would like to create your own user defined test, take a test file, and replace all the fields with `$$$NAME&&&` where `NAME` is the **SMALL GREY LETTERS** name of the parameter in the test type definition on the ITK DB. (Your TestType name must also match that in the ITK DB)

**However**, for things to work better, try to use the following key names for their relevant fields:
```
$$$Date&&&
$$$Time&&&
$$$TestType&&&
$$$Filename&&&
$$$Type&&& #(For the sensor type, like ATLAS17LS)
$$$Batch&&&
$$$Wafer&&&
$$$Component&&& #(For the serial number, like 20US#####)
$$$RunNumber&&&
```

If you have a table, replace the entire table including the headers with a single `$$$TABLE&&&`. If your header names are different than the small grey letters on the ITK DB, you will need to add them in the `alternatecolumnnames` and `APIAlternateNamesTABLES` variables in `CommonConfig.py`, where the key is `TABLE_`+some name for the column, the list in `alternatecolumnnames` contains what the column name exactly appears as in the test file, and the list in `APIAlternateNamesTABLES` contains what the little grey letter name is in the ITK DB if not already there.

Then take this file and save it under the `DataFormats` folder.

**To run interactively:**


```python
querypath=["Example Files/Example Wafer Test Files/VPX90002-W0161_KEKtestOLD_segment1_001.dat",
           "Example Files/Example Wafer Test Files/VPX90002-W0161_KEKtestNEW_segment1_001.dat"]

import RUNME_DirectImportAndUploadOfOtherTests
UPLOADEDDATA=RUNME_DirectImportAndUploadOfOtherTests.MAIN(querypath)
```


```python
UPLOADEDDATA
```

**To run directly via command line:**

For the default example files:

`python3 RUNME_DirectImportAndUploadOfOtherTests.py "['Example Files/Example Wafer Test Files/VPX90002-W0161_KEKtestOLD_segment1_001.dat', 'Example Files/Example Wafer Test Files/VPX90002-W0161_KEKtestNEW_segment1_001.dat']"
` 

If you changed anything, you can see what command to run by running the following cell:


```python
print('python3 RUNME_DirectImportAndUploadOfOtherTests.py "'+str(querypath)+'"')
```

## More In Depth Use Cases

Here we will cover some more in depth interactive use cases you want to manually import some local or ITK DB test data into interactive python to play around with and make basic queries like "which wafers have had tests done since the new year?" or "which wafers have had an IV test done on them?"

In general, if you are just beginning and just want to upload and analyze tests you should not need to do any of the stuff below yet. All the primary use cases are above this cell. 

Note that the way we deal with tests in python is as a test dictionary list object, e.g. TESTDICTLIST, which most of the scripts work with. E.g. if you run `ImportData.py` it will return such an object.  

In these types of Object: 
Every test is represented by a dictionary with common keys like "Voltage\[V\]" or "Wafer".
The test dictionary list is a list of these dictionaries

The reason for this is to make simple queries one-liners as we will see below.

Note that the final object that is passed out will only include test files which could have been read properly and have actual data in them (i.e. this will ignore any tests whose table fields are all 0). 

If there are multiple tests which have the exact same data and timestamp, the object passed out will only have one of those tests.

Note that Wafer numbers in these TESTDICTLISTs have the "W" and any leading zeros stripped and converted into integers if possible, or are left as is if it is not possible.

### Manually Importing Local Test Data to Python to Play Around With:

Now let's say that you just want to look at the local files you have in the `querypath` and play around with them. Let's import them so we can run some queries on them.


```python
import ImportData
LOCALTESTDICTLIST=ImportData.ImportData(querypath)
```

Now that we have the tests stored in a python object let's play with it!

**First let's get an idea of what keys exist in this test data representation:**


```python
list(LOCALTESTDICTLIST[0].keys())
```

Now let's do some example queries!

**Get all the batch, wafer, and filepaths:**


```python
set([(i['Batch'],i['Wafer'],i['Filepath']) for i in LOCALTESTDICTLIST if i['TestType']])
```

**Get all wafer numbers of wafers who have had an IV test done on them:**


```python
set([i['Wafer'] for i in LOCALTESTDICTLIST if i['TestType'] in [TestType_IV,TestType_IV_Hammamatsu]])
```

**See all wafer serial numbers of wafers who have had tests after the new year:**


```python
set([i['Component'] for i in LOCALTESTDICTLIST if i['Timestamp']>"2020-01-01T00:00:00.000Z"])
```

**See all Test Types that have been done on a particular Wafer for a particular Batch:**


```python
set([i['TestType'] for i in LOCALTESTDICTLIST if i['Wafer'] == 161 and i['Batch'] == 'VPX90002'])
```

**See what TestTypes have been done overall:**


```python
set([i['TestType'] for i in LOCALTESTDICTLIST])
```

**List all sensor types in your local test files:**


```python
set(i['Type'] for i in LOCALTESTDICTLIST)
```

**List out selected fields for all tests:**


```python
sorted([(str(i['Wafer']),i['Component'],i['TestType'],i['Filepath'],i['Timestamp']) for i in LOCALTESTDICTLIST])
```

### Manually Importing all Data From the ITK DB to Python Play Around With:

Now let's do the exact same but with the tests on the ITK DB instead!


```python
import ImportDataFromDatabase
ITKDBTESTDICTLIST=ImportDataFromDatabase.ImportDataFromDatabase()
```

Now that we have the tests stored in a python object let's play with it!

**First let's get an idea of what keys exist in this test data representation:**


```python
list(ITKDBTESTDICTLIST[0].keys())
```

**See all wafer serial numbers of wafers who have had tests after the new year:**


```python
set([i['Component'] for i in ITKDBTESTDICTLIST if i['Timestamp']>"2020-01-01T00:00:00.000Z"])
```

**List out selected fields for all tests:**


```python
sorted([(str(i['Wafer']),i['Component'],i['TestType'],i['Filepath'],i['Timestamp']) for i in ITKDBTESTDICTLIST])
```


```python

```

## Very Advanced Use Cases

If you are a beginner with a script trying to do something simple and common and you are down here you are probably doing something incorrect... 

The following are very very specific advanced use cases mainly for debugging and manually doing things for special cases. You really should not need to be down here unless you really know what you are doing and are experienced. Consequently, most things down here are interactive only as they are more complicated. 

### Creating a Special Detailed Stability Report

The plots shown in the normal analysis report for stability tests are temperature-compensated. If there is something fishy and you want to look at things at more detail, namely seeing the raw data, as well as a histogram of the humidity vs the temperature-compensated traces to see the effects of humidity, run the following:

**First of all, let us set an output path for this special stability report:**


```python
stablityoutputfile="Example Files/Example HTML Reports/TestHTMLSpecialStabilityReport.html"
```

**To run interactively:**


```python
import RUNME_GenerateSpecialStabilityReport
RUNME_GenerateSpecialStabilityReport.MAIN(querypath,stablityoutputfile)
```

**To run directly via command line:**

For the default example files:

`python3 RUNME_GenerateSpecialStabilityReport.py "Example Files" "Example Files/TestHTMLSpecialStabilityReport.html"`

If you changed anything, you can see what command to run by running the following cell:


```python
print('python3 RUNME_GenerateSpecialStabilityReport.py "'+str(querypath)+'" "'+str(stablityoutputfile)+'"')
```

### Convert Local Tests to a Standard Data Format and Writing BACK IN THE EXISTING DIRECTORIES (with a filename prefix):

If you have a bunch of local tests in historical formats that you wish to rewrite into the current standard format, run the following. In this section, the new standard tests will be written out into the same directories as their respective original tests, with a prefix "STD_" in front of them to differentiate them.

**First let's import some local tests that are in an old format:**


```python
oldformatquerypath="Example Files/OLD Example Wafer Test Files"
import ImportData
LOCALTESTDICTLIST=ImportData.ImportData(oldformatquerypath)
```

**(Just for the example to keep things simple and easily undoable I just want to convert only one of the tests:)**


```python
index=-1
TOSTDTESTDICTLIST=[LOCALTESTDICTLIST[index]]
```

**Let's convert all the tests in `TOSTDTESTDICTLIST` to a standard format:**


```python
import WriteToStandardFormat
WriteToStandardFormat.WriteToStandardFormat(TOSTDTESTDICTLIST)
```

**Let's verify it has been converted correctly by checking the folder. Theres should be a test with a "STD_" prefix now:**


```python
import os 
folder=os.path.dirname(TOSTDTESTDICTLIST[index]['Filepath'])
!ls "{folder}"
```

**(Just for the example, let's just show what the original test looked like:)**


```python
##SHOW ORIGINAL
with open(os.path.join(folder,TOSTDTESTDICTLIST[index]['Filename']),"r") as f:
    print(f.read())
```

**(Just for the example, let's just show what the new converted test looks like:)**


```python
##SHOW STANDARD
with open(os.path.join(folder,"STD_"+TOSTDTESTDICTLIST[index]['Filename']),"r") as f:
    print(f.read())
```

**(Just for the example, let's now delete the standard test you just created to get everything back to normal:)**


```python
stdfilename=os.path.join(folder,"STD_"+TOSTDTESTDICTLIST[index]['Filename'])
!rm "{stdfilename}"
```

### Convert Local Tests to a Standard Data Format and Writing TO A MIRROR DIRECTORY:

If you have a bunch of local tests in historical formats that you wish to rewrite into the current standard format, run the following. In this section, the new standard tests will be written out into a directory mirroring the structure of the input directory.

**First, let's define the directory we want to convert and the mirror directory we want to output the files in:**


```python
querypathformirror="Example Files/OLD Example Wafer Test Files"
mirrorpath="Example Files/STD Converted Example Wafer Test Files"
```

**Now let's import the local test files in that directory and convert them:**


```python
import ImportData
LOCALTESTDICTLISTFORMIRROR=ImportData.ImportData(querypathformirror)

import WriteToStandardFormat
WriteToStandardFormat.WriteToStandardFormat(LOCALTESTDICTLISTFORMIRROR,(querypathformirror,mirrorpath))
```

**Let's try to import the converted tests just to check that it worked:**


```python
import ImportData
LOCALTESTDICTLISTMIRRORED=ImportData.ImportData(mirrorpath)
```

**(Just as a sanity check, let's look at the files from the original and mirrored directories):**


```python
### Let's see which files are different, and ensure that those are just already STD_ files in the original directory:
List1=[i['Filename'] for i in LOCALTESTDICTLISTFORMIRROR]
List2=[i['Filename'] for i in LOCALTESTDICTLISTMIRRORED]

print(len(List1))
print(len(List2))

for i in List1:
    if 'STD_'+i not in List2:
        print(i)
```

**(Removing the converted directory to revert everything back to the original state):**


```python
!rm -rf "{mirrorpath}"
```

### Manually Creating Your Own HTML Report With Your Own Definitions of How Tests Are Split Up:

Here I am basically just as an example, manually creating a comparison analysis report, in this case just comparing all the tests on the ITK DB for the batch VPX90002. (Note this is just an example, if you actually want to do this there is an easier way to do this up in the "common use cases" section.


```python
import GenerateReport
import ImportDataFromDatabase

ITKDBTESTDICTLIST=ImportDataFromDatabase.ImportDataFromDatabase()

Batch='VPX90002'

CURRENTTESTBATCHLIST=[[]]
HISTORICALTESTBATCHLIST=[[i for i in ITKDBTESTDICTLIST if i['Batch']==Batch]]
TITLESLIST=[Batch]

GenerateReport.MAIN(CURRENTTESTBATCHLIST,HISTORICALTESTBATCHLIST,TITLESLIST,outputfile)
```

### Manually Analyzing and Uploading Tests in a TESTDICTLIST to the ITK DB:

You should almost never have to do this unless you are doing something incredible specific. If you are a beginner and down here you are doing something very wrong...

**First let's import some local tests:**


```python
import ImportData
LOCALTESTDICTLIST=ImportData.ImportData(querypath)
```

**For this example, I want to manually analyse and upload every CV test for wafer 161:**

**NOTE: IF YOU UPLOAD JUST LIKE THIS WITHOUT FIRST PASSING IT THROUGH THE ANALYSIS FUNCTIONS, THE DERIVED PARAMETERS AND PASS/FAIL DECISIONS WILL NOT BE UPLOADED!!**


```python
TOANALYZETESTDICTLIST=[Test for Test in LOCALTESTDICTLIST if Test['Wafer']==161 and Test['TestType']==TestType_CV]
```

**Manually analyze (i.e. extract the derived parameters and give a pass/fail decision) for just the CV Tests (just as an example) and store the analyzed tests in `UPLOADTESTDICTLIST`:**


```python
#First we need to run this through the corresponding analysis function to get the derived parameters!
import SENSOR_CV_Analysis
UPLOADTESTDICTLIST=[]
for Test in TOANALYZETESTDICTLIST:
    if Test['TestType']==TestType_CV:
        UPLOADTESTDICTLIST.append(SENSOR_CV_Analysis.Analyze_CV(Test))
```

**Manually upload all tests in `UPLOADTESTDICTLIST` to the ITK DB:**


```python
import UploadDataToDatabase
UploadDataToDatabase.UploadDataToDatabase(UPLOADTESTDICTLIST)
```


```python
#########################################################################################
```


```python
#########################################################################################
```









# Developer Notes on Individual Scripts (FOR DEVELOPERS ONLY)


## ImportData.py

This imports all test data from a local directory and spits it out in a TESTDICTLIST
The query path can be a single directory, single .dat or .txt file or a python list (i.e comma separated) of directories or files.

To run from Python3 Interactive do: 

```python
querypath="/var/clus/pc_backup/Cleanroom/data/sisensors/"
import ImportData
CAMDBDICTLIST=ImportData.ImportData(querypath)
```

## ImportDataFromDatabase.py

This 'downloads' all test data from the ITK Database and spits it out in a TESTDICTLIST
Note at the moment this only imports data which satifises: 

```python
ITK_PROJECT='S'
ITK_COMPONENTTYPE='SENSOR'
data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE}
```
where the above can be changed in CommonConfig if necessary

```python
import ImportDataFromDatabase
ITKDBTESTLIST=ImportDataFromDatabase.ImportDataFromDatabase()
```


## UploadDataToDatabase.py

This uploads all test data given in a TESTDICTLIST format to the ITK Database
This will not reupload tests that have already been uploaded. 

```python
import UploadDataToDatabase
UploadDataToDatabase.UploadDataToDatabase(UPLOADTESTLIST)
```

## WriteToStandardFormat.py

This writes all test data given in a TESTDICTLIST format to the standard data format per test and puts each test under the same directory as what is given as the filepath for that specific test in TESTDICTLIST (i.e. it writes a standard .dat format in the same place where the existing non standard format is). Alternatively, 

```python
#To use:

import WriteToStandardFormat
WriteToStandardFormat.WriteToStandardFormat(WAFERDICTLIST,MirrorDirectoryMap=None)

#where WAFERDICTLIST is obtained elsewhere, probably via ImportData
```


If `CreateMirrorDirectory==None`, then it will add the standard file in the same directory as the old file
If `CreateMirrorDirectory==(OriginalDirectory,MappedDirectory)`, then all standard files will be added to mapped directory in the same file substructure as the original directory


## GetComponentInfoFromDatabase.py

This downloads all component/wafer data (i.e. the correlation of the serial number, ITK Database Component Code, Batch, Wafer, and Type) from the ITK Database and spits it out in a dictionary list format (the keys are different than the TESTDICTLIST. Keys are shown in the CommonConfig file).

Note at the moment this gives a few error messages like "Could not split batch and wafer: W0128" if the name on the ITK DB cannot be split.

```python
import GetComponentInfoFromDatabase
COMPONENTIDDICTLIST=GetComponentInfoFromDatabase.GetComponentInfoFromDatabase()
```

To do queries for example get Serial Number given Batch and Wafer:

```python
[i['Component'] for i in COMPONENTIDDICTLIST if (i['Batch']=='VPX30816' and i['Wafer']== 164)]
```

## CommonConfig.py

This houses all common configuration variables and functions such as test variable names
