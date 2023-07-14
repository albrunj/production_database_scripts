#!/usr/bin/python
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic



# VF, 2021-05-12: to print an object properties/info from an object
#
#
# Seems like a generic enough functionality => won't do the sensor-related checks
#



# VF, 2021-05-01: Will use a global variable to indicate the state of DB connection affairs
bad_connection = False # original goodness

def get_response(c,SN):
    global bad_connection
    # don't bang the head against the wall
    if bad_connection :
        return (False,)

    # the actual query
    foundObject = True
    Resp = {}
    try:
        Resp = c.get('getComponent', json = {'component':SN})
    except Exception as e:
        foundObject = False
        print("Error: object not found: " + SN )
        print(e)
        if e.__class__.__name__ == 'Forbidden' :
            print("Error: got bad connection in <get_response>")
            bad_connection = True

    return (foundObject, Resp)



def get_info(c, aSN):
    global bad_connection

    # let's strip the SN from the trailing stuff
    lSN = aSN.rstrip()

    # check the input SN formatting
    if not checkSN_basic(lSN) :
        print("Error: SN = <" + lSN + "> is illegal!")
        return

    # check if the DB connection is active
    if bad_connection :
        print("Error: bad connection, returning ")
        return

    (foundObj, objResp) = get_response(c, lSN)

    if not foundObj :
        print("Error: Object not found! SN = " + lSN + ", returning")
        return

    print("//---------------------------------------------------")
    print(" SN = " + lSN )
    print("the query response is: ", json.dumps(objResp, indent=2) )



def main(args):
    SN    = args.SN
    iFile = args.iFile
    print(" Got input: ")
    print("   SN        = " + SN    )
    print("   iFile     = " + iFile )

    # print(" length(SN) = " + str(len(SN)) + ", length(iFile) = " + str(len(iFile)) )
    # need the "expires" flag for the cache longevity
    client = itkdb.Client()  # expires_after=dict(days=1) )
    if len(SN) > 0 :
        get_info(client, SN)

    lAbsPath = Path(iFile)
    if lAbsPath.is_file():
        with open(iFile,'r') as iF:
            lines = iF.readlines()
    else:
        return

    for lineind in range(len(lines)) :
        aSN = lines[lineind]
        get_info(client, aSN)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple info download')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '', help = 'Serial Number to check')
    parser.add_argument('-f', '--File', dest = 'iFile', type = str, default = '', help = 'File with serial numbers')

    args = parser.parse_args()

    main(args)
