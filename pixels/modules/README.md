# Pixel Modules

This README is for getting set up with uploading pixel module data. 

## Set Up 

Before we start, you will need to have some ITk Production Database passcodes to access the site. 
Try logging in here: https://itkpd-test.unicorncollege.cz
If you cannot log in you will need to sign up at the link about and get the Access Codes from Plus4U before you can get started. 

In your shell in the production_database_scripts folder run the following commands. The first will set up a token that will be valid for a few hours. 
```bash
$(python get_token.py)
```

## Registering a Component
To register a component run the following script and follow the commands. At the end you will need to give your module a name, this is just for human readable tracking as it already has a serial number, e.g. SLAC03. 
```bash
python registerComponent.py
```
Check within the ITk production database under "My Components" to see if your registration was successful. The serial number at the top of the component card will be used for upload via the API. 

<img src="img/serial_number.png" width="240">

## Upload Test Results via the Web User Interface
There are two options for uploading test results. The first is through the User Interface (UI) on the ITk production database website https://itkpd-test.unicorncollege.cz. If you click on the component, scroll down, and  click on the plus sign beside test results you will be guided through the steps to upload a test result. If you are having to upload tests for many modules at once this might be a bit cumbersome and uploading the tests through the API will probably be faster. 

![alt text](img/test_results.png "Image of Test Results" )

## Upload Test Results via the API
The API relies on you formatting your data in a way that the database will accept. Once you have formatted your data correctly you can upload it using python scripts in a bash shell. 

### Download Test Formats
The first step is to download some prototype formats. From within the itk_production_database scripts folder run: 
```bash
python2 test_prototype.py --project P --component-type MODULE --verbose
```
This will create a number of new files named prototype_ *TESTNAME*.json. If you open this file in a text editor you will see the json format for the data you will want to upload. 

### Format Your Test Results
In your text editor you will need to change the following items to be able to upload a prototype test result:

- Component (this is the serial number associated wiht your component)
- Institution (this is the code for your institute, if you can't remember it, check register_component.py)

You may want to rename the file so that it does not get overwritten if you run test_prototype.py again. You can also change the inputs for the test results, but make sure that you retain the correct formatting. If you are unsure about the formatting, you can double check by looking at the ITk Production Database and clicking "Test Types" -> "Modules" and the test you want to upload. 

### Upload Test Results

Now that your data has been formatted correctly, you can try to upload it! Run the following command, but make sure to change the file name to the file that you have edited. 
```bash
python2 upload_test_results.py --test-file prototype_*TESTNAME*.json --verbose
```
If this upload succeeded you will see the output "method POST". You can now check the upload on the ITk Production Database. 

### Example Wirebond Pull Test Uploads 

As each institute has different machines with differently formatted output files, different institutes may need to upload their own results. This is an example of a script that could be used for reading and formatting test results. 

The script upload_wirebond_results.py includes an example of reading in a DAGE wirebond pull test csv file (sample_wirebond_data.csv). The script parses the csv file and then creates a json file which can be uploaded through the upload test results script. 

```bash
cd pixel_modules
python2 upload_wirebond_results.py
python2 ../upload_test_results.py --test-file prototype_WIREBOND_DAGE.json --verbose
```
You can edit the inputs in the upload wirebond results file to account for your machine/operator/institute/component etc and potentially uplaod many results at once. 
