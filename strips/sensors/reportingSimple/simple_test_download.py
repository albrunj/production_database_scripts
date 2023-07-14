#!/usr/bin/python
import json

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import get_code
from strips.sensors.SensorSNUtils import get_testdata
from strips.sensors.SensorSNUtils import get_testruns_4_comp

#------------------------------------------------------
# Purpose: A simple download and storage (as JSON file) the test data
# V1, 2021-07-14: VF
#------------------------------------------------------


def get_test_list(c,test_response,check_testrun_code):
    # to fill in this list with the specified test run data for this test type
    retVal = []
    # to track if have an issue downloading the test data
    gotTests = True
    # find the correct test type
    for testrun in test_response:
        testrun_code = testrun['testType']['code']
        if testrun_code == check_testrun_code:
            # get data for the correct test type
            testID = testrun['id']
            success, testData = get_testdata(c,testID)
            if not success or testData == None :
                print(" did not find data for testID = <" + testID + ">, returning ")
                gotTests = False
                break

            retVal.append( testData )

    return gotTests, retVal


def check_test_type(c, SN, testType):

    # step 1: to get object code reference
    err, objCode = get_code(c, SN)
    if err: 
        print(" Did not get the code for this SN = <" + SN + ">, exiting...")
        return
    print(" got object code = <" + objCode + ">")
    
    # step 2: to get testruns for this object
    found_testruns, testruns_resp = get_testruns_4_comp(c, objCode)
    if not found_testruns:
        print(" test runs not found for this object, code = ", objCode)
        return
        
    # step 3: to pase the test runs and get the dictionaries we want
    gotResps,listResps = get_test_list(c, testruns_resp, testType )
    if not gotResps:
        print(" could not extract all the test run responses, exiting.")
        return

    # step 4: to store the JSON files
    print(" For SN = " + SN + 
          ", testType = " + testType + 
          " will write " + str( len(listResps) ) + " files.")
    for k, aResp in enumerate(listResps):
        fileName = SN + "__" + testType + "__" + str(k) + ".json"
        with open( fileName, 'w') as oF:
            json.dump( aResp, oF, indent=2 )

    print(" Done! ")


def main(args):
    SN        = args.SN
    testType  = args.test_code
    print(" Got input: ")
    print("   SN        = " + SN       )
    print("   test_code = " + testType )

    if not checkSN_basic(SN):
        print(" bad SN = <" + SN + ">, exiting...")
        return

    client = itkdb.Client() # expires_after=dict(days=1) )

    check_test_type(client, SN, testType)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple download and storage of a test JSON file from DB')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '20USESX0000599', help = 'object/component\'s Serial Number to check')
    parser.add_argument('-t', '--test_code', dest = 'test_code', type = str, default = 'MANUFACTURING18', help = 'Test handle/code')

    args = parser.parse_args()

    main(args)
