#!/usr/bin/env python
import argparse
import json
import os
import sys

import itk_pdb.dbAccess as dbAccess

def read_file(fname, componentCode = None, institution = None):
    d = open(fname).read()
    data = json.loads(d)

    if componentCode is not None:
        data["component"] = componentCode

    if institution is not None:
        data["institution"] = institution

    # Do some validation

    if "component" not in data:
        print("Need reference to component, hex string")
        sys.exit(1)

    if "testType" not in data:
        print("Need to know test type, short code")
        sys.exit(1)

    if "institution" not in data or data["institution"] is None:
        print("Need to know institution, short code")
        sys.exit(1)

    if "runNumber" not in data:
        print("Need runNumber field in json file (string)")
        sys.exit(1)

    if "passed" not in data:
        print("Need passed field (bool) in json file")
        sys.exit(1)

    if "results" not in data:
        print("Need some test results")
        sys.exit(1)

    if "properties" in data:
        for k,v in data["properties"].items():
            if v == "some_string":
                print("This looks like a prototype file, property: %s" % k)
                sys.exit(1)

    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload test data to production database")

    parser.add_argument("--test-file", help="Name of json file with test data")

    parser.add_argument("--component-id", help="Override component code")

    parser.add_argument("--institution", help="Institution this test was run at")

    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    parser.add_argument("--test", action="store_true",
                        help="Test, don't send to DB")

    args = parser.parse_args()

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    component_code = None
    if args.component_id:
        component_code = args.component_id

    if not args.test_file:
        print("Need test file to upload, see test_prototype.py'")
        sys.exit(1)

    f = read_file(args.test_file, component_code, args.institution)

    if args.test:
        print("Test: would send data:\n")
        print(json.dumps(f, indent=4))
        
        sys.exit(0)

    dbAccess.doSomething("uploadTestRunResults", f)
