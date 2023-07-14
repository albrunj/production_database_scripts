#!/usr/bin/python
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import get_code



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


def set_flags(c, aCode, list_flags):
    global bad_connection
    # don't bang the head against the wall
    if bad_connection :
        return (True,)

    # need to find the damn object revision now
    aRev = 1
    # the code should work instead of SN for this function
    (foundIt, objJSON) = get_response(c, aCode)
    if not foundIt:
        print("Error: in <set_flags>, could not get properties of " + aCode + ", exiting.")
        return (True,)
    aRev = objJSON['sys']['rev']
    print(" found the object revision = " + str(aRev) )

    # the actual query
    interError = False
    Resp = {}
    try:
        Resp = c.post('setComponentFlags', 
                      json = {'component': aCode,
                              'flags'    : list_flags,
                              'revision' : aRev } )
    except Exception as e:
        interError = True
        print("Error: object not found: " + aCode )
        print(e)
        if e.__class__.__name__ == 'Forbidden' :
            print("Error: got bad connection in <set_flags>")
            bad_connection = True

    return (interError, Resp)



def work_flags(c, aSN, list_flags, bDBG):
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

    (error, objCode) = get_code(c, lSN, bDBG )

    if error :
        print("Error: Object not found! SN = " + lSN + ", returning")
        return
    if bDBG:
        print(" debugging output in work_flags:")
        print(objCode)

    (intErr, aResp) = set_flags(c, objCode, list_flags)

    if intErr:
        print("Error: setting flags failed! SN = " + lSN + ", returning")
        return

    print("//---------------------------------------------------")
    print(" SN = " + lSN + " processed" )
    if bDBG:
        print( json.dumps(aResp['flags'], indent=2) )


def main(args):
    SN    = args.SN
    iFile = args.iFile
    iFlags = args.iFlags
    fDBG  = args.debug
    print(" Got input: ")
    print("   SN        = " + SN    )
    print("   iFile     = " + iFile )
    print("   iFlags    = " + iFlags )
    print("   fDBG      = " + fDBG )

    bDBG = False
    if fDBG == 'no':
        bDBG = False
    elif fDBG == 'yes':
        bDBG = True
    else:
        print(" wrong input option for the debugging flag, exiting...")
        return

    list_flags = iFlags.split(',')
    print(list_flags)

    # print(" length(SN) = " + str(len(SN)) + ", length(iFile) = " + str(len(iFile)) )
    # need the "expires" flag for the cache longevity
    client = itkdb.Client()  # expires_after=dict(days=1) )
    if len(SN) > 0 :
        work_flags(client, SN, list_flags, bDBG)

    lAbsPath = Path(iFile)
    if lAbsPath.is_file():
        with open(iFile,'r') as iF:
            lines = iF.readlines()
    else:
        return

    for lineind in range(len(lines)) :
        aSN = lines[lineind]
        work_flags(client, aSN, list_flags, bDBG)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple info download')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '', help = 'Serial Number to check')
    parser.add_argument('-f', '--File', dest = 'iFile', type = str, default = '', help = 'File with serial numbers')
    parser.add_argument('-l', '--Flags', dest = 'iFlags', type = str, default = '', help = 'A list of flag codes')
    parser.add_argument('-d', '--debug', dest = 'debug', type = str, default = 'no', help = 'debugging printout')

    args = parser.parse_args()

    main(args)
