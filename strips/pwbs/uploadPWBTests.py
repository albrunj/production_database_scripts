#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os, sys
import argparse
import json
import itk_pdb.dbAccess as dbAccess

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
        test["properties"]["CONFIG"]= data["config"]["runNumber"]

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Powerboard test data to production database.")

    parser.add_argument("test_file", help="Path to the json file with test data.")

    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    f = read_file(args.test_file)

    # Check if the requested component exists, if not register
    found = False
    componentList = dbAccess.doSomething("listComponents", {'project':'S', 'subproject':'SB', 'institution':'LBL', 'componentType':'PWB'}, method='GET')['pageItemList']
    for components in componentList:
        if f['config']['component'] == components['serialNumber']:
            found = True
            break

    if found == False:
        response = input(
            'Powerboard not in database. Would you like to register it? [y/n]: '
        )
    if response == 'y':
        nums = parse_serial(f['config']['component'])
        dbAccess.doSomething(
            "registerComponent",
            {
                'project': 'S',
                'subproject': 'SB',
                'institution': 'LBL',
                'componentType': 'PWB',
                'type': nums[3],
                'serialNumber': f['config']['component'],
            },
            method='POST',
        )
    else:
        sys.exit(1)

    compinfo=dbAccess.doSomething("getComponent", {'component':f['config']['component']}, method='GET')
    component=compinfo['code'] # needed for test runs list

    # Check if the config exists, if not upload
    testRuns=dbAccess.doSomething("listTestRunsByComponent", {'component':component}, method='GET')

    found=False
    for testRun in testRuns['pageItemList']:
        if testRun['testType']['code']!='CONFIG': continue
        if testRun['runNumber']==f['config']['runNumber']:
            found=True
            break
    if not found:
        print('Uploading configuration {}'.format(f['config']['runNumber']))
        dbAccess.doSomething("uploadTestRunResults", f['config'])

        # Upload the test results
    for test in f['tests']:
        print('Uploading test {}'.format(test['testType']))
        dbAccess.doSomething("uploadTestRunResults", test)
