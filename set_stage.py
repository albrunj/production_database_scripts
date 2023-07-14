#!/usr/bin/env python
import argparse
import os
import sys

import itk_pdb.dbAccess as dbAccess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set stage of an item in the production database")

    parser.add_argument("--component-id", help="Component code (required)")

    parser.add_argument("--component-stage", help="Component stage (required)")

    parser.add_argument("--test", action="store_true",
                        help="Test, don't send to DB")

    args = parser.parse_args()

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    component_code = None
    if args.component_id:
        component_code = args.component_id
    else:
        print("--component-id is required")
        sys.exit(0)

    component_stage = None
    if args.component_stage:
        component_stage = args.component_stage
    else:
        print("--component-stage is required")
        sys.exit(0)



    if args.test:
        print("Test: would send data:\n")
        print("uploadTestRunResults", component_code, component_stage)
        
        sys.exit(0)

    dbAccess.doSomething("setComponentStage", 
                         data ={'component': component_code,
                                'stage'    : component_stage} )
