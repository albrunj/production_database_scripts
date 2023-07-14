#!/usr/bin/python
import datetime
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import upload_testrun

#----------------------------------------------------
# A script for uploading the sensor "Special Use" information
# Version 1, 2021-07-27, by VF
# update, 2021-10-19, by VF: to skip empty lines
#
# Actions:
# - to open a file with a header and a list of the test results
# - to parse the header and the lines
# - to perform the data integrity checks on the lines
#    -o- + header check
#    -o- + have the necessary info
#    -o- + Batch-wafer number format
#    -o- + consistency of the SN and the batch-wafer number, SN format
#    -o- + length of data line for each sensor (at least the 4 essentials, no more than the key list)
# - if there are no issues, to upload the information for every sensor on the list
#
#
# The file structure example:
#
#Institute: CA
#RunNumber: 3
# BatchWaferNo; SN; Description; Date; Time; Comments
#VPX90001-W326; 20USBSX0000326; Design verification with early modules; 14 Feb 2021; ; Sent to Freiburg for module building
#VPX90001-W327; 20USBSX0000327; Design verification with early modules; 15 Feb 2021; ; Sent to Freiburg for module building
#VPX90001-W328; 20USBSX0000328; Design verification with early modules; 16 Feb 2021; ; Sent to Freiburg for module building
# 
# Data formats expected:
#  1) Date in the form of DD Mon YYYY
#  2) Time in the form of HH:MM:SS (but it could be omitted)
#
#----------------------------------------------------

standardKeys = ["BatchWaferNo", "SN", "Description", "Date",  # The alwasy necessary info
                "Time", "Comments"]                           # helpful info

# the file to write the JSON data if the upload is not successful
bad_dump = "dump_bad_upload.json"

# The test version we use now
testType = "ATLAS18_SPECIAL_USE_V1"

def get_header_info( listLines ):

    # initialize
    tInst = ""
    tRunN = ""
    for aLine in listLines[:2] :
        mArr = aLine.split(":")
        # assign the key and its value
        rawKey = mArr[0]
        rawVal = mArr[1]
        # remove spaces
        aKey = rawKey.strip()
        aVal = rawVal.strip()
        if aKey == "Institute":
            tInst = aVal
            # print(" Instutute = <" + aVal + ">")
        if aKey == "RunNumber":
            tRunN = aVal
            # print(" RunNumber = <" + aVal + ">")

    if len(tInst) == 0 :
        print("  could not find <Institute> information in the header")
        return False,tInst,tRunN
    if len(tRunN) == 0 :
        print("  could not find <RunNumber> information in the header")
        return False,tInst,tRunN

    print(" Got the header info ")

    return True,tInst,tRunN


def verify_keywords(aLine):

    listKeys = aLine.split(";")
    cleanKeys = []
    for aKey in listKeys:
        rawKey = aKey.strip()
        cleanKeys.append(rawKey)

    if cleanKeys != standardKeys :
        print(" the keys in the data file don't match the expected list")
        print("")
        print(" the keys in the data files are:")
        print(cleanKeys)
        print("")
        print(" the keys in the standard set are:")
        print(standardKeys) 
        print("")
        return False

    return True


def empty_dict():
    aDict = {}
    for aKey in standardKeys:
        aDict[aKey] = ""   # the default N/A for the strings

    return aDict


def process_data_line(aLine):

    aDict = empty_dict()
    
    # now process the line and fill in the values
    Vals = aLine.split(";")
    cleanVals = []
    for aVal in Vals:
        cleanV = aVal.strip()
        cleanVals.append(cleanV)

    print(cleanVals)
    
    if len(Vals) > len(aDict) :
        print(" got too many values in the following line")
        print("<" + aLine.rstrip() + ">")
        print("returning error")
        return False, aDict

    # loop over the standard keys
    #   and fill in the dictionary value for the key from the array of values
    for k,aKey in enumerate(standardKeys):
        if k+1 > len(cleanVals):
            break
        # print(" k = " + str(k) + ", Key = " + aKey + ", value = " + cleanVals[k])
        if len(cleanVals[k]) > 0 :
            aDict[aKey] = cleanVals[k]
        else:
            aDict[aKey] = ""

    # ....
    return True, aDict


# Make the structure for the test run upload
def get_json_from_dict( tInst, tRunN, sData ):

    # will use <null> instead of empty strings for the values
    minData = {}
    for aKey in sData:
        minData[aKey] = sData[aKey] if len(sData[aKey]) > 0 else None

    tPass = True
    tFail = False

    retJSON = {
        "component": sData["SN"],
        "testType": testType,
        "institution": tInst,
        "runNumber": tRunN,
        "date": sData["timeStamp"],
        "passed": tPass,
        "problems": tFail,
        "properties": {
            "COMMENTS": minData["Comments"],
            "RUNNUMBER": int(tRunN)
        },
        "results": {
            "DESCRIPTION" : minData["Description"]
        }
    }

    return retJSON


def simple_data_integrity_checks(aLine, aDict):
    # error checks...
    # 1) empty strings
    if ( len(aDict["BatchWaferNo"]) == 0 or
         len(aDict["SN"          ]) == 0 or
         len(aDict["Description" ]) == 0 or
         len(aDict["Date"        ]) == 0 ) :
        print(" Missing the necessary information in the line")
        print("<" + aLine.rstrip() + ">")
        print(" exiting...")
        return False
       
    # 2) check the input SN formatting
    anSN = aDict["SN"]
    if not checkSN_basic(anSN) :
        print("Error: SN = <" + anSN + "> is illegal!")
        return False

      
    # Check the consistency between the BatchWaferNo and SN:
    #   compare the last 5 characters
    bwNo = aDict["BatchWaferNo"]
    # print(" anSN = <" + anSN + ">")
    last5SN = anSN[-5:]
    lastNBW = bwNo.split("W")[1]
    # print(" anSN = <" + anSN + ">, last5SN = <" + last5SN + ">, lastNBW = <" + lastNBW + ">")
    wSN = int(last5SN)
    wBW = int(lastNBW)
    if wSN != wBW :
        print(" The BatchWaferNo and SN are not compatible:")
        print(" BatchWaferNo = <" + bwNo + ">, SN = <" + anSN + ">")
        print(" The extracted wafer numbers are <" + str(wBW) + "> and <" + str(wSN) + ">")
        print(" ...exiting")
        return False

    # Check the batch-wafer number format
    if ( ( bwNo[:3] != "VPX" and bwNo[:3] != "VPA" ) or
         bwNo[8]  != "-"   or
         bwNo[9]  != "W"   or
         ( len(bwNo) != 15 and len(bwNo) != 13 ) ) :
        print(" The BatchWaferNo seems misformatted:")
        print(" BatchWaferNo = <" + bwNo + ">, expect <VP(X|A)nnnnn-Wkkkkk>")
        #print(" VPX = <" + bwNo[:3] + ">")
        #print(" - = <" + bwNo[8] + ">")
        #print(" W = <" + bwNo[9] + ">")
        print(" ...exiting")
        return False

    # to check the Description (only presense)
    myDescription = aDict["Description"]
    if len(myDescription) == 0:
        print("Do not see the Recovery Method listed, will exit")
        return False
 
    # Must be good if got here (or not caught yet)
    return True


# Make the time stamp (This will check the date format as well) and return the modified dictionary.
def make_add_timestamp( aDict ):

    tDate = aDict["Date"]
    tTime = aDict["Time"]
    maDate = datetime.datetime.strptime(tDate,"%d %b %Y")
    maTime = "12:00:00.000Z"
    if len(tTime) > 0:
        readTime = datetime.datetime.strptime(tTime, "%H:%M:%S")
        maTime = readTime.strftime("%H:%M:%S") + ".000Z"
    timeStamp = maDate.isoformat().split('T')[0] + "T" + maTime
    # print("Got timeStamp = <" + timeStamp + ">")
    aDict["timeStamp"] = timeStamp

    return


# def write_individual_files( dictData, nRunN, tInst ):
#     # each dictionary corresponds to a data file
#     for myDict in dictData:
#         run3digi = str(nRunN).zfill(3)
#         fileName = myDict["BatchWaferNo"] + "_VisInspectionV2_" + run3digi + ".dat"
#         print(fileName + " :", end='')
#         mySN = myDict["SN"]
#         bwNo = myDict["BatchWaferNo"]
#         with open(fileName,'w') as oF:
#             oF.write(fileName + "\n")
#             oF.write("Type: "      + type_from_SN(mySN) + "\n")
#             oF.write("Batch: "     + bwNo[:8]           + "\n")
#             oF.write("Wafer: "     + bwNo.split("W")[1] + "\n")
#             oF.write("Component: " + mySN               + "\n")
#             oF.write("Date: "      + myDict["Date"]     + "\n")
#             oF.write("Time: "      + myDict["Time"]     + "\n")
#             oF.write("Institute: " + tInst              + "\n")
#             oF.write("TestType: "  + testType           + "\n")
#             oF.write("RunNumber: " + str(nRunN)         + "\n")
#             oF.write("Result: "    + myDict["Result"]   + "\n")
#             oF.write("Comments: "  + myDict["Comments"] + "\n")
#             # now, optional stuff, if present
#             for aKey in standardKeys:
#                 if ( aKey.startswith("Scratch") or 
#                      aKey.startswith("Location") or
#                      aKey.startswith("Damage") or
#                      aKey.startswith("Image") ) and len(myDict[aKey]) > 0 :
#                     oF.write( aKey + ": " + myDict[aKey] + "\n")
#         print(" written!")

#     return


# To upload the test data 
def upload_test_to_DB( c, inputSpecialUseFile, dictData, tInst, tRunN ):
    oFile = inputSpecialUseFile + ".log"
    oLog = open( oFile, 'w' )

    for sData in dictData:
        print(" SN = " + sData["SN"] + ": ", end='')
        sensorJ = get_json_from_dict( tInst, tRunN, sData )
        # DBG
        #print( sensorJ["component"])
        #with open( bad_dump, 'w') as dF:
        #    json.dump( sensorJ, dF, indent=2 )
        #return
        uSuccess, respJ = upload_testrun( c, sensorJ )
        if uSuccess:

            wwwString = "https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/"
            wwwString += (respJ['testRun']['awid'] + "/testRunView?id=" + respJ['testRun']['id'] )
            oLog.write( sData["SN"] + " : " + wwwString + "\n" )

            print(" Done!" )

        else:
            print(" Upload of a test run failed. The prepared JSON file is written to <" + bad_dump + "> . Exiting.")
            with open( bad_dump, 'w') as dF:
                json.dump( sensorJ, dF, indent=2 )
            oLog.close()
            return False

    # the inter-actions must've got well
    oLog.close()
    print(" Done! The URL links for the tests are written to <" + oFile + ">" )

    return True


def main(args,aTemplate):
    # -o- Handle the input ---------------------------------------------------
    inputSpecialUseFile = args.inputSpecialUseFile
    printTemplate       = args.printTemplate
#    writeSeparateFiles = args.writeSeparateFiles
    print(" Got input: ")
    print("   inputSpecialUseFile = " + inputSpecialUseFile       )
    print("   printTemplate       = " + str(printTemplate     ) )
#    print("   writeSeparateFiles = " + str(writeSeparateFiles) )

    if printTemplate:
        oFile = "template_SpecialUse.txt"
        print("\nWill write the Control File template to file <" + oFile + "> and exit.\n")
        with open(oFile,'w') as oF:
            oF.write(aTemplate)
        return

    # check the existence of the input
    if len(inputSpecialUseFile) == 0 :
        print(" wrong input file description, exiting...")
        return

    fAbsPath = Path(inputSpecialUseFile)
    if not fAbsPath.is_file():
        print(" don't really see the input file, exiting..." )
        return


    # -o- To process the input file
    # read the input
    with open(inputSpecialUseFile,'r') as iFile:
        myLines = iFile.readlines()

    nHeader = 2
    nMin = nHeader + 1 + 1 # 1 line for the keyword list, and another one for the 1st data line

    # -o- Get the header information ---------------------------------------------------
    if len(myLines) < nMin :
        print(" not enough lines in the input file. Expect 4-line header, 1-line keyword title, and >= 1 line with data")
        print(" Exiting.")
        return

    Succ, tInst, tRunN = get_header_info(myLines)
    if not Succ:
        print(" Could not parse the input file header, exiting...")
        return

    # Check the integer
    nRunN = int(tRunN)
    if nRunN < 1 :
        print(" got RunNumber = " + str(nRunN) + "; this is illegal; exiting.")
        return

    # -o- read it all in ---------------------------------------------------
    print(" Will process the lines ")
    gotKeys = False
    dictData = [] # This is an array of dictionaries
    nTotalLines = 0
    for aLine in myLines[nHeader:] :
        # remove the comment lines, which start with "#" symbol
        if aLine.startswith("#") or len(aLine.strip())==0:
            continue

        # remove comments
        useLine = aLine.split("#")[0]

        # process the line with the keywords
        if not gotKeys:
            good_keys = verify_keywords(useLine)
            if not good_keys :
                print(" the line with keywords is misformatted:")
                print("<" + useLine + ">")
                print(" ...exiting")
                return

            gotKeys = True # finish the signleton
            continue

        # Past the keyword line should only have the real data
        nTotalLines += 1

        # now process the actual lines with data!
        goodLine, aDict = process_data_line(useLine)
        if not goodLine:
            print(" the line is bad, exiting...")
            return

        # to perform the data integrity checks
        goodData = simple_data_integrity_checks( aLine, aDict)
        if not goodData:
            print(" Failed the data integrity checks, exiting...")
            return

        # make/add the time stamp
        make_add_timestamp(aDict)

        # add the dictionary to the list, if it's not there already
        if aDict in dictData:
            print(" see duplicate data, won't process the data from the line")
            print("<" + aLine.rstrip() + ">")
            continue

        dictData.append( aDict )


    # check that we did get the data
    print(" Saw the total of " + str(nTotalLines) + " data lines")
    print(" Found useful information for " + str(len(dictData)) + " sensors ")
    if len(dictData) == 0 :
        print(" did not get the data to upload, exiting")
        return

    # If asked to write the separate input files for each sensor, will do just that and exit
    # if writeSeparateFiles:
    #     write_individual_files( dictData, nRunN, tInst )
    #     return

    # -o- DB interactions  ---------------------------------------------------
    # Should have enough information to send off
    c = itkdb.Client()
    
    goodUpload = upload_test_to_DB( c, inputSpecialUseFile, dictData, tInst, tRunN )
    if not goodUpload:
        print(" Upload error. Something must've gone wrong. ")

    return


if __name__ == '__main__':
    import argparse
    aTemplate =  " Institute: <Institute handle in DB> \n"
    aTemplate += " RunNumber: <Number> \n"
    aTemplate += "# \n"
    aTemplate += "# lines starting with \"#\" are comments. They can be present after 1st 4 lines of the header.\n"
    aTemplate += "# \n"
    aTemplate += "# \n"
    aTemplate += "# Only 1st 4 fields are necessary for every line (time can be an empty string).\n"
    aTemplate += "# Multiple images can be comma(,)-separated for a given field.\n"
    aTemplate += "# \n"
    aTemplate += "# Data formats expected:\n"
    aTemplate += "#  1) Date in the form of DD Mon YYYY\n"
    aTemplate += "#  2) Time in the form of HH:MM:SS (but it could be omitted)\n"
    aTemplate += "# \n"
    aTemplate += "# \n"
    aTemplate += " BatchWaferNo; SN; Description; Date; Time; Comments\n"
    aTemplate += "# \n"
    aTemplate += "# \n"
    aTemplate += "<semicolon-separated information for these fields> # only 1st 4 are necessary \n"
    aTemplate += "# \n"

    strDescription = "Processing an input File (ASCII) to upload the Visual Inspection data to DB\n\n"
    strDescription += " A template/example content is between \"-------\" lines:\n\n"
    strDescription += " ----------------------------------------\n"
    strDescription += aTemplate
    strDescription += " ----------------------------------------\n"
    strDescription += "\n"

    parser = argparse.ArgumentParser(
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = strDescription )
    parser.add_argument('-i', '--inputFile',     dest = 'inputSpecialUseFile', type = str, default = '', help = 'A text file with the handling damage information')
    parser.add_argument('-t', '--printTemplate', dest = 'printTemplate',action="store_true", help = 'To print the Input File template and exit')
#    parser.add_argument('-w', '--writeSeparateFiles', dest = 'writeSeparateFiles',action="store_true", help = 'To write separate files for each sensors for the standard QC software and exit')
    args = parser.parse_args()

    main(args,aTemplate)
