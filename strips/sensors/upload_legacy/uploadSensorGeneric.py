import argparse
import os
import re

from itk_pdb.dbAccess import ITkPDSession

parser = argparse.ArgumentParser()

parser.add_argument("inputLocation", help="Where data to upload is being stored, can be a file or directory. Must be in correct format")

parser.add_argument("--ignoreBlanks", action="store_true", help="Use if you would like to ignore blanks and upload data anyways. Note: May cause errors if value is required")

args = parser.parse_args()

ignoreBlanks = args.ignoreBlanks

inputLocation = args.inputLocation

# Ask yes or no question
def question(mesg):
    return input(mesg).upper()[0]

def search_notset(info, inputLocation):##Searches to see if any spaces have not been filled in, prompts user to manually input

    for key, value in info.items():

        if "notset" == info[key]:
            print("\nWARNING: No value for \"" + key + "\" found in " + inputLocation)
            dec = 0
            dec = question("Would you like to continue? (y/n) ")

            while dec != "Y" and dec != "N":
                dec = question("Invalid input, please try again. Would you like to continue? (y/n) ")
            if dec == "N":
                exit(0)
            elif dec == "Y":
                dec = 0
                dec = question("Would you like to manually input a value? (y/n) ")

                while dec != "Y" and dec != "N":
                    dec = question("Invalid input, please try again. Would you like to manually input a value? (y/n) ")

                if dec == "N":
                    continue
                elif dec == "Y":

                    manualInput = input("Enter value for " + key + ": ")

                    if str(manualInput).upper() == "TRUE":
                        manualInput = True
                    if str(manualInput).upper() == "FALSE":
                        manualInput = False

                    info[key] = manualInput


        elif isinstance(value, dict):
            search_notset(value, inputLocation)

def setInfo(dicti, gkey, ginfo): #Loops through an input dictionary, finding keys that match gkey, replacing its value with ginfo
    for key, value in dicti.items():

        if isinstance(value, dict):
            setInfo(value, gkey, ginfo)

        else:
            if key == gkey:
                dicti[key] = ginfo

def clearDict(dictionary): #Clear the Dto sample acquired from the database
    for key, value in dictionary.items():

        if isinstance(value, list):
            dictionary[key] = []

        elif isinstance(value, dict):
            clearDict(value)

        else:
            dictionary[key] = "notset"


class dataToPass:
    def __init__(self): ##Initializes data with empty dictionary
        self.py_dict = {}


    def getDto(self, session, code, componentType, project):

        dtoString = session.doSomething('generateTestTypeDtoSample', 'GET', {'code': code, 'componentType': componentType, 'project': project, 'requiredOnly': False})

        self.py_dict = dtoString["dtoSample"]

        clearDict(self.py_dict)


    ##Allow function to easily set values in dictionary, can be reused by other code
    def setBasic(self, pName, pValue):
        self.py_dict[pName] = pValue

    def setProperties(self, pName, pValue):
        self.py_dict["properties"][pName] = pValue

    def setResults(self, pName, pValue):
        self.py_dict["results"][pName] = pValue

    def addData(self, dName, dValue):
        self.py_dict["results"][dName].append(dValue)


    ##Uploads data to Itk DB
    def upload(self, session):

        session.doSomething('uploadTestRunResults', 'POST', data=self.py_dict)


def IVDataUpload(inputLocation):


    data = dataToPass()

    dat = open(inputLocation, "r")
    all = dat.readlines()

    for line in all:

        if "project: " in line:
            project = line[9:-1]
        if "componentType: " in line:
            componentType = line[15:-1]
        if "testType: " in line:
            testType = line[10:-1]

    try:
        print("Getting Dto for " + inputLocation + "\nPROJECT: " + project + "\tCOMPONENT TYPE: " + componentType + "\tTEST TYPE:" + testType)
    except:
        print("\nNot enough info to get Dto for " + inputLocation)

        dec = question("Would you like to manually input values? (y/n) ")

        while dec != "Y" and dec != "N":
            dec = question("Invalid input, please try again. Would you like to manually input values? (y/n) ")

        if dec == "N":
            exit(0)
        elif dec == "Y":
            try: print("PROJECT: " + project)
            except: project = input("Enter project (S or P): ")

            try: print("COMPONENT TYPE: " + componentType)
            except: componentType = input("Enter component type (e.g. SENSOR): ")

            try: print("TEST TYPE:" + testType)
            except: testType = input("Enter test type (e.g. SENSOR_STRIP_TEST): ")

    try:
        data.getDto(session, testType, componentType, project)
    except:
        print("Unable to get Dto form Itk PDB, please check that PROJECT, COMPONENT TYPE, and TEST TYPE math database exactly")
        exit(1)

    lineIsData = False #Changes to true once data is detected
    dataTitles = []

    for line in all:

        pos = line.find(": ")#Information will be extracted if a colon is present

        if (pos != -1) :

            info_desc = line[:(pos)]
            extracted = line[(pos + 2):-1]

            setInfo(data.py_dict, info_desc, extracted)

        if lineIsData:

            lineData = line.split()

            for m , title in enumerate(dataTitles):

               data.addData(str(title), lineData[m])

        if line[0] == "%": #Indicates that the following lines are data and the current one is data

            lineData = line.split()

            for string in lineData:

                try:
                    dataTitles.append((re.findall("%%(.*)/%", string)[0]))
                except AttributeError:
                    continue

            lineIsData = True

    dat.close()

    if not ignoreBlanks:
        search_notset(data.py_dict, inputLocation)

    data.upload(session)


#Start DB Session to be used by each upload
session = ITkPDSession()

session.authenticate()


if os.path.isdir(inputLocation):

    print("\nInput is a directory, please be sure only data files are present.")

    dec = 0
    dec = question("Would you like to continue? (y/n) ")

    while dec != "Y" and dec != "N":

        dec = question("Invalid input, please try again. Would you like to continue? (y/n) ")

    if dec == "N":
        exit(0)

    elif dec == "Y":

        for filename in os.listdir(inputLocation): ##Cycles through all files in the directory

            IVDataUpload(inputLocation+filename)

elif os.path.isfile(inputLocation):
    IVDataUpload(inputLocation)
else:
    print("\nInvalid input location")
    exit(1)
