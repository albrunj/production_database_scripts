#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import itk_pdb.dbAccess as dbAccess
from itk_pdb.dbAccess import ITkPDSession

import os, sys
import glob
import argparse
import json

def read_file(fname):
    d = open(fname).read()
    data = json.loads(d)

    # Insert some more validation

    if "config" not in data:
        print("Missing the AMACv2 configuration used during testing")
        sys.exit(1)

    if "component" not in data["config"]:
        print("Missing component name (via config)")
        sys.exit(1)
        
    if "runNumber" not in data:
        print("Missing runNumber")
        sys.exit(1)

    if "tests" not in data:
        print("Missing test results")
        sys.exit(1)

    #
    # Copy common meta-data to the test results
    for test in data["tests"]:
        test["runNumber"]= data["runNumber"]
        test["institution"]= "LBL"
        test["component"]= data["config"]["component"]
        if 'properties' not in test: test["properties"]={}
        test["properties"]["CONFIG"]= data["runNumber"]

    return data

def parse_serial(snum):

    version = snum[7]
    bnum = int(snum[8:10])
    pnum = int(snum[10:14])

    if version == "0":
        subType = "B2"
    elif version == "1":
        subType = "B3"

    return [version, bnum, pnum, subType]

def getPWBFiles(panelPath):
    charFiles = []
    bfFiles = []
    pbFolders = glob.glob(panelPath + "/pb*")
    for i in range (0, len(pbFolders)):
        char_file = glob.glob(pbFolders[i] + "/*_pbv3-test.json")
        bf_file = glob.glob(pbFolders[i] + "/*_pbv3-diagnostic.json")
        if(len(char_file)==1):
            charFiles.append(char_file[0])
        if(len(bf_file)==1):
            bfFiles.append(bf_file[0])

    return charFiles, bfFiles

def uploadResults(testFile, uploadConfig):
    f = read_file(testFile)
    pb = f['config']['component']

    # Check if the requested component exists
    found = False
    componentList = session.doSomething(action = "listComponents", data = {'project':'S', 'subproject':'SB', 'institution':'LBL', 'componentType':'PWB'}, method='GET')
    for components in componentList:
        if pb == components['serialNumber']:
            found = True
            break
	
    if found == False:
        print('Powerboard ' + pb + ' not in database.')

    compinfo=session.doSomething(action = "getComponent", data = {'component':f['config']['component']}, method='GET')
    component=compinfo['code'] # needed for test runs list

    # Check if the config exists, if not upload
    testRuns=session.doSomething(action = "listTestRunsByComponent", data = {'component':component}, method='GET')

    found=False
    print('\nUploading for ' + pb)

    if(uploadConfig):
        for testRun in testRuns:
            if testRun['testType']['code']!='CONFIG': continue
            if testRun['runNumber']==f['config']['runNumber']:
                found=True
                break
        if not found:
            print('Uploading configuration {}'.format(f['config']['runNumber']))
            session.doSomething(action = "uploadTestRunResults", data = f['config'], method = 'POST')

        # Upload the test results
    for test in f['tests']:
        print('Uploading test {}'.format(test['testType']))
        session.doSomething(action = "uploadTestRunResults", data = test, method = 'POST')

def upload(test_date, QCRecep, pass1=None, pass2=None):
    global session
    session = ITkPDSession()
    session.authenticate()

    if pass1 == None and pass2 == None:
        if os.getenv("ITK_DB_AUTH"):
          dbAccess.token = os.getenv("ITK_DB_AUTH")

    else:
        os.environ["ITK_DB_AUTH"] = dbAccess.authenticate(pass1, pass2)

    charFiles, bfFiles = getPWBFiles(test_date)

    if QCRecep=='qc': 
        for testFile in bfFiles:
            uploadResults(testFile, False)
        for testFile in charFiles:
            uploadResults(testFile, True)
    else:
        for testFile in bfFiles:
            uploadResults(testFile, False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Powerboard test data to production database.")

    parser.add_argument("test_date", help="Path to the test date folder containing powerboard test data.")

    parser.add_argument("--verbose", action="store_true", help="Print what's being sent and received")    

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--reception", action='store_true')
    group.add_argument("-qc", "--quality_control", action='store_true')

    args = parser.parse_args()

    if args.verbose:
        dbAccess.verbose = True

    if args.quality_control == True:
        upload(args.test_date, 'qc')

    else:
        upload(args.test_date, 'r')
