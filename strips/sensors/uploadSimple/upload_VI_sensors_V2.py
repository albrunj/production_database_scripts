#!/usr/bin/python
import datetime
import json
import os
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import type_from_SN
from strips.sensors.SensorSNUtils import upload_testrun
from strips.sensors.SensorSNUtils import add_image_to_test

#----------------------------------------------------
# A script for uploading the visual inspection information
# Version 1, 2021-07-09, by VF
# Version 1.1, 2021-08-16, by VF: allow 4-digit wafer number
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
#    -o- + image file extension, image number per defect (no more than 4)
#    -o- + image existence, total size
# - if there are no issues, to upload the information for every sensor on the list
#
#
# The file structure example:
#
#Institute: CA
#RunNumber: 3
#BatchWaferNo; SN; Date; Time; Result; Comments; ScratchPadImage; Location1; DamageType1; Images1; Location2; DamageType2; Images2; Location3; DamageType3; Images3; Location4; DamageType4; Images4; Location5; DamageType5; Images5; Location6; DamageType6; Images6 # 1st line with keywords
#VPX32409-W00147; 20USBSS0000147; 07 Jan 2020; 01:12:00; Pass
#VPX32409-W00148; 20USBSS0000148; 10 Feb 2020; 23:15:00; Fail; deep scratch ; ; Guard Ring; scratch; SS_W00148_GR1.jpg,SS_W00148_GR2.jpg,SS_W00148_GR3.jpg,SS_W00148_GR4.jpg
#VPX32409-W00149; 20USBSS0000149; 01 Dec 2021; ; Pass; Goo on strips ; SS_W00149.png; Segment 2, strips 850-870; Debris; SS_W00149_seg2_1.png,SS_W00149_seg2_2.png,SS_W00149_seg2_3.png,SS_W00149_seg2_4.png; Segment 1, strips 860-870; Debris; SS_W00149_seg1_1.png
# 
# Data formats expected:
#  1) Date in the form of DD Mon YYYY
#  2) Time in the form of HH:MM:SS (but it could be omitted)
#  3) The damage classifications:  mark / debris / scuffing / suction cup mark / blotch / pit / deposit / scratch / deep scratch / chip / mismatched serial number / metal short / metal break
#  4) The target location descriptions (not checked): corner / edge / guard ring / segment No, strip(s) Numbers
#
#----------------------------------------------------


standardKeys = ["BatchWaferNo", "SN", "Result", "Date",  # The alwasy necessary info
                "Time", "Comments",                      # helpful info
                "ScratchPadImage",                       # the scratch pad image
                "Location1", "DamageType1", "Images1",   # the 1st damage location
                "Location2", "DamageType2", "Images2",   # the 2nd damage location
                "Location3", "DamageType3", "Images3",   # the 3rd damage location
                "Location4", "DamageType4", "Images4",   # the 4th damage location
                "Location5", "DamageType5", "Images5",   # the 5th damage location
                "Location6", "DamageType6", "Images6"]   # the 6th damage location

standardDamages = ["mark", "debris", "scuffing", "suction cup mark", "blotch", "pit", "deposit", "scratch", "deep scratch", "chip", "mismatched serial number", "metal short", "metal break"]         # the standard classification of damages

# the file to write the JSON data if the upload is not successful
bad_dump = "dump_bad_upload.json"

# The test version we use now
testType = "ATLAS18_VIS_INSPECTION_V2"
maxIMG = 4
maxDEFECT = 6
maxSIZE = 10_000_000

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
        print(" (Expect exact keywords as in the template, before the data lines.)")
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
        # if aKey[:3] == "IMS" :
        #     aDict[aKey] = null # the default N/A for the images
        # else:
        #     aDict[aKey] = ""   # the default N/A for the strings

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
        # print(" k = " + str(k) + ", Key = " + aKey)
        aDict[aKey] = cleanVals[k]

    # ....
    return True, aDict


# Make the structure for the test run upload
def get_json_from_dict( tInst, tRunN, sData ):

    tPass = False
    tFail = False
    if sData["Result"] == "Pass":
        tPass = True
        tFail = False
    elif sData["Result"] == "Fail":
        tPass = False
        tFail = True
    else:
        # should never get here
        tPass = "Test results are unclear"
        tFail = "Test results are unclear"

    # Example from the PB software
    # client.post("uploadTestRunResults", json={'component': powerboard.code, 'runNumber': runNumber, 'passed': passed, 'date': str(datetime.now().strftime('%d.%m.%Y %H:%M')), 'institution':'LBNL_STRIP_POWERBOARDS', 'testType': "PICTURE", 'results': {"PICTURE": "undefined", "COMMENT": comment}})
    # testRun = pwbdbtools.getLatestTestRunByComponent(client, component=powerboard.code, testType=["PICTURE"], stage=[powerboard.currentStage])
    # print("Uploading image to testRun: "+testRun['id'])
    # client.post("createBinaryTestRunParameter", data=dict(testRun=testRun['id'], parameter="PICTURE"), files={'data': (filename, open(filename, mode='rb'), filename.split(".")[-1])})
    # print("Image uploaded, check it here: https://itkpd-test.unicorncollege.cz/testRunView?id="+testRun['id'])

    retJSON = {
        "component": sData["SN"],
        "testType": testType,
        "institution": tInst,
        "runNumber": tRunN,
        "date": sData["timeStamp"],
        "passed": tPass,
        "problems": tFail,
        "properties": {
            "COMMENTS": sData["Comments"],
            "RUNNUMBER": int(tRunN)
        },
        "results": {
            "IMSCRATCHPAD": None, #sData["ScratchPadImage"],
            "LOCATION1"   : sData["Location1"],
            "DAMAGE_TYPE1": sData["DamageType1"],
            "IMS1_1"      : None, # sData["IMS1_1"],
            "IMS1_2"      : None, # sData["IMS1_2"],
            "IMS1_3"      : None, # sData["IMS1_3"],
            "IMS1_4"      : None, # sData["IMS1_4"],
            "LOCATION2"   : sData["Location2"],
            "DAMAGE_TYPE2": sData["DamageType2"],
            "IMS2_1"      : None, # sData["IMS2_1"],
            "IMS2_2"      : None, # sData["IMS2_2"],
            "IMS2_3"      : None, # sData["IMS2_3"],
            "IMS2_4"      : None, # sData["IMS2_4"],
            "LOCATION3"   : sData["Location3"],
            "DAMAGE_TYPE3": sData["DamageType3"],
            "IMS3_1"      : None, # sData["IMS3_1"],
            "IMS3_2"      : None, # sData["IMS3_2"],
            "IMS3_3"      : None, # sData["IMS3_3"],
            "IMS3_4"      : None, # sData["IMS3_4"],
            "LOCATION4"   : sData["Location4"],
            "DAMAGE_TYPE4": sData["DamageType4"],
            "IMS4_1"      : None, # sData["IMS4_1"],
            "IMS4_2"      : None, # sData["IMS4_2"],
            "IMS4_3"      : None, # sData["IMS4_3"],
            "IMS4_4"      : None, # sData["IMS4_4"],
            "LOCATION5"   : sData["Location5"],
            "DAMAGE_TYPE5": sData["DamageType5"],
            "IMS5_1"      : None, # sData["IMS5_1"],
            "IMS5_2"      : None, # sData["IMS5_2"],
            "IMS5_3"      : None, # sData["IMS5_3"],
            "IMS5_4"      : None, # sData["IMS5_4"],
            "LOCATION6"   : sData["Location6"],
            "DAMAGE_TYPE6": sData["DamageType6"],
            "IMS6_1"      : None, # sData["IMS6_1"],
            "IMS6_2"      : None, # sData["IMS6_2"],
            "IMS6_3"      : None, # sData["IMS6_3"],
            "IMS6_4"      : None  # sData["IMS6_4"]
        }
    }

    return retJSON


def simple_data_integrity_checks(aLine, aDict):
    # error checks...
    # 1) empty strings
    if ( len(aDict["BatchWaferNo"]) == 0 or
         len(aDict["SN"          ]) == 0 or
         len(aDict["Result"      ]) == 0 or
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
         ( len(bwNo) != 15 and len(bwNo) != 14 and len(bwNo) != 13 ) ) :
        print(" The BatchWaferNo seems misformatted:")
        print(" BatchWaferNo = <" + bwNo + ">, expect <VP(X|A)nnnnn-Wkkkkk>")
        #print(" VPX = <" + bwNo[:3] + ">")
        #print(" - = <" + bwNo[8] + ">")
        #print(" W = <" + bwNo[9] + ">")
        print(" ...exiting")
        return False

    # Check that the Result is correct
    maResult = aDict["Result"]
    if ( maResult != "Pass" and
         maResult != "Fail" ):
        print(" See a wrote value in the result field: <" + maResult + ">, should be either <Pass> or <Fail> ")
        return False

    # to check the DamageType classification
    for maDamage in [aDict["DamageType1"],
                     aDict["DamageType2"],
                     aDict["DamageType3"],
                     aDict["DamageType4"],
                     aDict["DamageType5"],
                     aDict["DamageType6"]] :
        if len(maDamage) > 0 :
            cmpDamage = maDamage.lower()
            if cmpDamage not in standardDamages:
                print(" Got new/unknown damage type = <" + maDamage + ">")
                print(" The authorized types are:")
                print(standardDamages)
                print(" Exiting.")
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


def check_add_images( aDict ):
    # to check the images
    totalSize = 0.0
        
    # To initialize with nothing
    for k in range(1,maxDEFECT+1):
        for n in range(1,maxIMG+1):
            newKey = "IMS" + str(k) + "_" + str(n)
            aDict[newKey] = None

    for k in range(1,maxDEFECT+1):
        aKey = "Images" + str(k)
        mImages = aDict[aKey]
        if len(mImages) > 0 :
            # check the number of them
            listImages = mImages.split(",")
            cleanImages = []
            for anImage in listImages:
                clImage = anImage.strip()
                cleanImages.append(clImage)
            if len(cleanImages) > maxIMG:
                print(" see more than " + str(maxIMG) + " images for a defect:")
                print(cleanImages)
                print("Only up to " + str(maxIMG) + " are supported, exiting...")
                return False
            # Check their existence and size
            for n,anImage in enumerate(cleanImages):
                aPath = Path(anImage)
                if not aPath.is_file():
                    print(" file <" + anImage + "> does not exist, exiting")
                    return
                chkName = anImage.lower()
                if not ( chkName.endswith('.png' ) or
                         chkName.endswith('.jpg' ) or
                         chkName.endswith('.jpeg') or
                         chkName.endswith('.bmp' ) or
                         chkName.endswith('.png' ) ) :
                    print(" incorrect file extension for <" + anImage + ">")
                    print(" expected png/jpg/jpeg/bmp/png, exiting...")
                    return
                totalSize += os.path.getsize(anImage)
                # Since we already parsed this, add the new key to the dict, to use in the JSON file
                newKey = "IMS" + str(k) + "_" + str(n+1)
                aDict[newKey] = anImage
    if totalSize >= maxSIZE :
        print(" the input images are too large, expect maximum of 10 MB in total, exiting ")
        return False

    # Images must be good, if got here.
    return True


def write_individual_files( dictData, nRunN, tInst ):
    # each dictionary corresponds to a data file
    for myDict in dictData:
        run3digi = str(nRunN).zfill(3)
        fileName = myDict["BatchWaferNo"] + "_VisInspectionV2_" + run3digi + ".dat"
        print(fileName + " :", end='')
        mySN = myDict["SN"]
        bwNo = myDict["BatchWaferNo"]
        with open(fileName,'w') as oF:
            oF.write(fileName + "\n")
            oF.write("Type: "      + type_from_SN(mySN) + "\n")
            oF.write("Batch: "     + bwNo[:8]           + "\n")
            oF.write("Wafer: "     + bwNo.split("W")[1] + "\n")
            oF.write("Component: " + mySN               + "\n")
            oF.write("Date: "      + myDict["Date"]     + "\n")
            oF.write("Time: "      + myDict["Time"]     + "\n")
            oF.write("Institute: " + tInst              + "\n")
            oF.write("TestType: "  + testType           + "\n")
            oF.write("RunNumber: " + str(nRunN)         + "\n")
            oF.write("Result: "    + myDict["Result"]   + "\n")
            oF.write("Comments: "  + myDict["Comments"] + "\n")
            # now, optional stuff, if present
            for aKey in standardKeys:
                if ( aKey.startswith("Scratch") or 
                     aKey.startswith("Location") or
                     aKey.startswith("Damage") or
                     aKey.startswith("Image") ) and len(myDict[aKey]) > 0 :
                    oF.write( aKey + ": " + myDict[aKey] + "\n")
        print(" written!")

    return


# To upload the test data and to attach the images
def upload_data_images( c, inputVisualInspectionFile, dictData, tInst, tRunN ):
    oFile = inputVisualInspectionFile + ".log"
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

            # now, add the images
            # 1) get the test ID
            testID = respJ['testRun']['id']

            # 2) loop over the keywords that may have image data and call the binary parameter upload
            for aKey in sData:
                if ( aKey.startswith("ScratchPad") or
                     aKey.startswith("IMS"       ) ) :
                    imageFile = sData[aKey]
                    if imageFile is not None:
                        if len(imageFile) > 0:
                            add_image_to_test( c, testID, aKey, imageFile )

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
    inputVisualInspectionFile = args.inputVisualInspectionFile
    printTemplate             = args.printTemplate
    writeSeparateFiles        = args.writeSeparateFiles
    print(" Got input: ")
    print("   inputVisualInspectionFile = " + inputVisualInspectionFile )
    print("   printTemplate             = " + str(printTemplate     ) )
    print("   writeSeparateFiles        = " + str(writeSeparateFiles) )

    if printTemplate:
        oFile = "template_VisualInspection.txt"
        print("\nWill write the Control File template to file <" + oFile + "> and exit.\n")
        with open(oFile,'w') as oF:
            oF.write(aTemplate)
        return

    # check the existence of the input
    if len(inputVisualInspectionFile) == 0 :
        print(" wrong input file description, exiting...")
        return

    fAbsPath = Path(inputVisualInspectionFile)
    if not fAbsPath.is_file():
        print(" don't really see the input file, exiting..." )
        return


    # -o- To process the input file
    # read the input
    with open(inputVisualInspectionFile,'r') as iFile:
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
        if aLine.startswith("#") :
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

        # check/add images
        goodImages = check_add_images(aDict)
        if not goodImages:
            print(" Images no good, exiting...")
            return

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
    if writeSeparateFiles:
        write_individual_files( dictData, nRunN, tInst )
        return

    # -o- DB interactions  ---------------------------------------------------
    # Should have enough information to send off
    c = itkdb.Client()
    
    goodUpload = upload_data_images( c, inputVisualInspectionFile, dictData, tInst, tRunN )
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
    aTemplate += "#  3) The damage classifications:  mark / debris / scuffing / suction cup mark / blotch / pit / deposit / scratch / deep scratch / chip / mismatched serial number / metal short / metal break \n"
    aTemplate += "#  4) The target location descriptions (not checked): corner / edge / guard ring / segment No, strip(s) Numbers\n"
    aTemplate += "# \n"
    aTemplate += "# \n"
    aTemplate += " BatchWaferNo; SN; Result; Date; Time; Comments; ScratchPadImage; Location1; DamageType1; Images1; Location2; DamageType2; Images2; Location3; DamageType3; Images3; Location4; DamageType4; Images4; Location5; DamageType5; Images5; Location6; DamageType6; Images6 # 1st line with keywords \n"
    aTemplate += "# \n"
    aTemplate += "# \n"
    aTemplate += "<semicolon-separated information for these fields> # only 1st 4 are necessary; multiple images can be comma-separated for a given field\n"
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
    parser.add_argument('-i', '--inputFile',          dest = 'inputVisualInspectionFile', type = str, default = '', help = 'A text file with the visual inspection information (identifications, comments, classification, images)')
#    parser.add_argument('-o', '--outputJSONFile',   dest = 'outputJSONFile',   type = str, default = '', help = 'output JSON file name/path')
    parser.add_argument('-t', '--printTemplate',      dest = 'printTemplate',action="store_true", help = 'To print the Input File template and exit')
    parser.add_argument('-w', '--writeSeparateFiles', dest = 'writeSeparateFiles',action="store_true", help = 'To write separate files for each sensors for the standard QC software and exit')
    args = parser.parse_args()

    main(args,aTemplate)
