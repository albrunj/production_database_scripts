#!/usr/bin/env python3

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()
    
import os

import json
import itk_pdb.dbAccess as dbAccess
import argparse

tests={
    "LV_ENABLE":
        ["LVENABLE",
         "VOUT",
         "IIN",
         "IOUT",
         "VIN"],
    "HV_ENABLE":
        ["HVENABLE",
         "HVIIN",
         "HVVIN"],
    "DCDCEFFICIENCY":
        ["IOUT",
         "EFFICIENCY",
         "AMACPTAT",
         "AMACVDCDC",
         "IINOFFSET",
         "VIN",
         "IIN"],
    "HVSENSE":
        ["AMACGAIN0",
         "AMACGAIN1",
         "AMACGAIN2",
         "AMACGAIN4",
         "AMACGAIN8",
         "HVI",
         "HVV",
         "ILEAK"],
    "STATUS":
        ["VIN",
         "IIN",
         "VOUT",
         "IOUT",
         "AMACVDCDC",
         "AMACVDDLR",
         "AAMCDCDCIN",
         "AMACVDDREG",
         "AMAC900BG",
         "AMAC600BG",
         "AMACCAL",
         "AMACNTCPB",
         "AMACCUR10V",
         "AMACCUR1V",
         "AMACHVRET",
         "AMACPTAT",
         "HVVIN",
         "HVIIN"],
    "BER":
        ["RELIABILITY"],
    "VIN":
        ["VINSET",
         "VIN",
         "IIN",
         "AMACDCDCIN"],
    "OF":
        ["OF",
         "VIN",
         "IIN",
         "linPOLV"],
    "CUR10V":
        ["DCDCiP",
         "DCDCiN",
         "AMACCUR10V",
         "DCDCiOffset"],
    "CUR1V":
        ["DCDCiP",
         "DCDCiN",
         "AMACCUR10V",
         "DCDCiOffset"]
}

def getResults(version, ids, runs, resultDict):
    for boards in version:
        testsByComp = session.doSomething(action = "listTestRunsByComponent", data = {'component':boards['code'], 'testType':list(tests.keys())}, method = 'GET')
        for testTypes in testsByComp:
            for types in list(tests.keys()):
                if(testTypes["testType"]["code"] == types):
                    ids[types].append(testTypes["id"])

    for testTypes in ids:
        for runId in ids[testTypes]:
            runs[testTypes].append(session.doSomething(action = "getTestRun", data = {'testRun':runId}, method = 'GET'))

    for testTypes in list(tests.keys()):
        for testrun in runs[testTypes]:
            for results in testrun["results"]:
                for subtests in tests[testTypes]:
                    if(results["code"]==subtests):
                        resultDict[testTypes][subtests].append(results["value"])

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description = "Gets powerboard data for HTML display.")
    parser.add_argument("pass1", help="First ITk database password.")
    parser.add_argument("pass2", help="Second ITk database password.")
    parser.add_argument("saveLocation", help="Location in which to store json files.")
        
    args = parser.parse_args()
        
    os.environ["ITK_DB_AUTH"] = dbAccess.authenticate(args.pass1, args.pass2)
        
    from itk_pdb.dbAccess import ITkPDSession
    global session
    session = ITkPDSession()
    session.authenticate()
        
        
    testIDs = {}
    testRuns = {}
    testResults = {}
        
    testIDs_v3a = {}
    testRuns_v3a = {}
    testResults_v3a = {}
        
    testIDs_v3b = {}
    testRuns_v3b = {}
    testResults_v3b = {}
        
    for test in list(tests.keys()):
        testIDs[test] = []
        testRuns[test] = []
        testResults[test] = {}
        for subtests in tests[test]:
            testResults[test][subtests] = []
        
    for test in list(tests.keys()):
        testIDs_v3a[test] = []
        testRuns_v3a[test] = []
        testResults_v3a[test] = {}
        for subtests in tests[test]:
            testResults_v3a[test][subtests] = []
        
    for test in list(tests.keys()):
        testIDs_v3b[test] = []
        testRuns_v3b[test] = []
        testResults_v3b[test] = {}
        for subtests in tests[test]:
            testResults_v3b[test][subtests] = []
        
    pwb = session.doSomething(action = "listComponents", data = {'project':'S', 'subproject':['SB'], 'componentType':['PWB'], 'type':['B3']}, method = 'GET')
    pwb_v3a = []
    pwb_v3b = []
        
    for items in pwb:
        for props in items['properties']:
            if props['code'] == 'VERSION' and (props['value'] == 'v3.0' or props['value'] == 'v3.0a' or props['value'] == '0' or props['value']=='1'):
                pwb_v3a.append(items)
            if props['code'] == 'VERSION' and (props['value'] == 'v3.0b' or props['value']=='2'):
                pwb_v3b.append(items)
        
    getResults(pwb, testIDs, testRuns, testResults)
    getResults(pwb_v3a, testIDs_v3a, testRuns_v3a, testResults_v3a)
    getResults(pwb_v3b, testIDs_v3b, testRuns_v3b, testResults_v3b)
        
    json_all_v = json.dumps(testResults)
    f = open(args.saveLocation + "/testResults.json", "w")
    f.write(json_all_v)
    f.close()
        
    json_v3a = json.dumps(testResults_v3a)
    g = open(args.saveLocation + "/testResults_v3a.json", "w")
    g.write(json_v3a)
    g.close()
        
    json_v3b = json.dumps(testResults_v3b)
    h = open(args.saveLocation + "/testResults_v3b.json", "w")
    h.write(json_v3b)
    h.close()
