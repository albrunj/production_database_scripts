Legacy Code for uploading Strip Sensors data to DB, developed before D&D's main software suite
=================================================================================================


# uploadDataGUI.py

*Written by Nashad Rahman. For any questions or help, contact rahman.176@osu.edu*

## **Requirements:**

Before running the program, please ensure you are running Python 3 and you have the PyQT5 module installed. To do this, ensure you have pip installed on your machine and then in a terminal run:

```bash
pip3 install "PyQt5"
```

This program may work in Python 2 as well, but has not been as thoroughly tested.

## Usage:
**First**: the prompt to enter your access code appears:

**After Login:** A screen appears with two tabs. The first tab has a button on the right side which allows users to select a file or directory. Click this to select a file which contains your data. To select a folder, you may have to select a file and then delete the name of the file from the text box in the first tab.

**Click “Upload”** to gather data from the file and upload it to the database.

**If Successful** It will show a status bar at the bottom of the screen

**Issues and Blanks**
If any issues or blanks are found, the program will notify the user, ask if they want to continue, and then ask if they would like to manually input a value. If the information is not required by the database, the user has the option to ignore the blank.

**Batch Upload**
For Batch upload, simply enter in a folder name **insead of a file**
Confirms and uploads all files in the directory, prompts with any errors or blanks same as before

## **Options**

**Ignore Blanks** will not prompt the user if any data is missing from the data files. Unchecked by default

**Save a copy of .JSON file** will save a json file with the same data and in the same place with the same name as the original file, just with .JSON at the end

**Do not upload, but check values** will still interact with the database and check validity, but does not upload data

**Delimiters** allows users to add in any additional delimiters in order to match the format in which their data is saved, including tabs. By default it has ‘: ‘ and ‘= ‘ (spaces are important). Reusing characters within delimiters is fine, but if one contains the other (ei ‘: ‘ and ‘:’ ) the larger delimiter string must come after the smaller. (ei  `[‘:‘ ,‘: ’,’ : ‘]` )

**Data Header** options allow users to customize how the program searches for the data titles. In the example above, the data header would be expected to look like:

    %%Title1/%  %%Title2/%  %%Title3/%

**Default Values** Allows users to set a default value if no others are found (Blank by default)

**Override Values** Allows users to set an override value even if another is found (Blank by default)

## **File Formatting and Acceptable Inputs**

The program can upload single files or full directories. To upload a folder, simply change the name from a file to the directory and the program will attempt to upload all files in the directory.

By default, the program checks if the file is a .json file. If it is, then it just uploads all the information in the file as is, only modifying if there are values present in “Override Values”. If users choose to save in the .json format, they must

However, the .json format may not always be very human readable, and users may want to save data in different, more accessible means. Additionally, the database has strict requirements for exactly how to pass in information and what is required. For these reasons, this program allows flexibility in how users can save their data.

Any program that does not have the .json extension should be formatted like so:

The project, component type, and test type are required to get a sample of what the database expects to receive. These must be given explicitly in the file or typed into the override or default values. The value and the key must be separated by one of the delimiters (by default is “: “ and “= “ but users can customize). The rest of the values required by the database (as described by the sample) are expected to be formatted in the same way. All keys must match the DTo sample exactly, including capitalization. Any additional lines that do not have a delimiter or do not match the data sample, will be ignored. Note: the date must be in the format dd.mm.yyyy.

Before results, a _data header_ is required. This must start with a “%” and have the keys to each data list between “%%” and “/%” as shown above. Each header must be separated by a space or a tab. Units can be placed outside but will not be recorded as the database will not accept them.

Until the data header, the parameters could have any order. After the data header, there can only be results data present. These must be in columns respective to the data header, separated by a space or a tab.
