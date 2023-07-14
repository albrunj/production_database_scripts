#!/usr/bin/env python3

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import argparse
import itk_pdb.dbAccess as dbAccess


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Determines the number of components of a given type with some filtering options")

    parser.add_argument("component", help="Code of component.")
    parser.add_argument("type", help="Code for component subtype.")
    parser.add_argument("-sp", "--subproject", help="Subproject, either SB, SE, or SG.")
    parser.add_argument("-s", "--stage", help="Stage of the component.")
    parser.add_argument("-i", "--institution", help="Owner institution.")
    parser.add_argument("-l", "--location", help="Current location.")
    parser.add_argument("-v", "--version", help="Powerboard version.")

    args = parser.parse_args()

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")
	
    comp_list = dbAccess.doSomething("listComponents", {'project':'S', 'subproject':args.subproject, 'componentType':args.component, 'type':args.type, 'institution':args.institution, 'currentLocation':args.location,'currentStage':args.stage, 'pageInfo':{'pageIndex': 0, 'pageSize':1}}, method='GET')
	
    print(comp_list['pageInfo']['total'])
