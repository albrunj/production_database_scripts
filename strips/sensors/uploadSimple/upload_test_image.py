#!/usr/bin/python
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import upload_testrun

#----------------------------------------------------
# A script for testing the image upload
# Version 1, 2021-07-19, by VF
#
#----------------------------------------------------

# the file to write the JSON data if the upload is not successful
bad_dump = "dump_bad_upload.json"

# The test version we use now
testType = "TEST_IMAGE"
ParamType = "THEIMAGE"
myInst = "UCSC_STRIP_SENSORS"
runNo = "10"
myDate = "2021-07-20T01:59:13.773Z"

# Make the structure for the test run upload
def make_json_dict( SN, Comment ):

    retJSON = {
        "component": SN,
        "testType": testType,
        "institution": myInst,
        "runNumber": runNo,
        "date": myDate,
        "passed": True,
        "problems": False,
        "properties": {
            "COMMENTS": Comment
        },
        "results": {
            "THEIMAGE": None #""
        }
    }

    return retJSON


# Upload individual image for a relevant test run parameter
def add_image_to_test( c, testID, Image ):

    f = open( Image, "rb")
    c.post( "createBinaryTestRunParameter", 
            data = { "testRun": testID,
                     "parameter": ParamType },
            files = dict(data=f)
    )
    # files = { "data": ( Image, f, Image.split(".")[-1] ) }
    f.close()

    # The code from PB software:
    #
    # client.post("uploadTestRunResults", json={'component': powerboard.code, 'runNumber': runNumber, 'passed': passed, 'date': str(datetime.now().strftime('%d.%m.%Y %H:%M')), 'institution':'LBNL_STRIP_POWERBOARDS', 'testType': "PICTURE", 'results': {"PICTURE": "undefined", "COMMENT": comment}})
    # testRun = pwbdbtools.getLatestTestRunByComponent(client, component=powerboard.code, testType=["PICTURE"], stage=[powerboard.currentStage])
    # print("Uploading image to testRun: "+testRun['id'])
    # client.post("createBinaryTestRunParameter", data=dict(testRun=testRun['id'], parameter="PICTURE"), files={'data': (filename, open(filename, mode='rb'), filename.split(".")[-1])})
    # print("Image uploaded, check it here: https://itkpd-test.unicorncollege.cz/testRunView?id="+testRun['id'])


    return 


def main(args):
    # -o- Handle the input ---------------------------------------------------
    mySN        = args.SN
    myImage     = args.Image
    myComment   = args.Comment
    print(" Got input: ")
    print("    SN       = " +  mySN       )
    print("    Image    = " +  myImage    )
    print("    Comment  = " +  myComment  )


    fAbsPath = Path(myImage)
    if not fAbsPath.is_file():
        print(" don't really see the input file, exiting..." )
        return

    if not checkSN_basic( mySN ):
        print(" wrong SN format, exiting...")
        return

    # -o- DB interactions  ---------------------------------------------------
    oFile = "test_dump.log"
    oLog = open( oFile, 'w' )

    # Should have enough information to send off
    c = itkdb.Client()


    sensorJ = make_json_dict( mySN, myComment )
    # DBG
    #print( sensorJ["component"])
    #with open( bad_dump, 'w') as dF:
    #    json.dump( sensorJ, dF, indent=2 )
    #return
    # Act 1: test run upload
    uSuccess, respJ = upload_testrun( c, sensorJ )

    if uSuccess:
        wwwString = "https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/"
        wwwString += (respJ['testRun']['awid'] + "/testRunView?id=" + respJ['testRun']['id'] )
        oLog.write( mySN + " : " + wwwString )
        print(" uploaded SN = " + mySN )
    else:
        print("Upload of a test run failed. The prepared JSON file is written to <" + bad_dump + "> . Exiting.")
        with open( bad_dump, 'w') as dF:
            json.dump( sensorJ, dF, indent=2 )

        oLog.close()
        return

    # print(json.dumps(respJ, indent=2))

    # Act 2: to create the binary image for this test run
    add_image_to_test( c, respJ['testRun']['id'], myImage )

    oLog.close()
    print(" Done! The URL links for the tests are written to <" + oFile + ">" )

    return




if __name__ == '__main__':
    import argparse
    strDescription = " To check the image upload footwork \n"
    strDescription += "\n"

    parser = argparse.ArgumentParser(
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = strDescription )
    parser.add_argument('-s', '--SN'     , dest = 'SN', type = str, default = '', help = 'A serial number')
    parser.add_argument('-i', '--Image'  , dest = 'Image', type = str, default = '', help = 'Image File')
    parser.add_argument('-c', '--Comment', dest = 'Comment', type = str, default = '', help = 'Comment')
    args = parser.parse_args()

    main(args)
