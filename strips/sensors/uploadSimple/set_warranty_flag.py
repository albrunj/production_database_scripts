#!/usr/bin/python
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import get_code


#------------------------------------------
# A script to assert a (warranty) flag for an object in DB
# Version1, 2021-07-27 by VF
#
#
# Seems like a generic enough functionality => won't do the sensor-related checks
#



def get_response(c,SN):

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

    return (foundObject, Resp)


def set_flags(c, aCode, list_flags):

    # need to find the damn object revision now
    aRev = 1
    # the code should work instead of SN for this function
    (foundIt, objJSON) = get_response(c, aCode)
    if not foundIt:
        print("Error: in <set_flags>, could not get properties of " + aCode + ", exiting.")
        return (True,)
    aRev = objJSON['sys']['rev']
    #print(" found the object revision = " + str(aRev) )

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

    return (interError, Resp)



def work_flags(c, aSN, list_flags, bDBG):

    # let's strip the SN from the trailing stuff
    lSN = aSN.rstrip()

    # check the input SN formatting
    if not checkSN_basic(lSN) :
        print("Error: SN = <" + lSN + "> is illegal!")
        return False

    (error, objCode) = get_code(c, lSN, bDBG )

    if error :
        print("Error: Object not found! SN = " + lSN + ", returning")
        return False
    if bDBG:
        print(" debugging output in work_flags:")
        print(objCode)

    (intErr, aResp) = set_flags(c, objCode, list_flags)

    if intErr:
        print("Error: setting flags failed! SN = " + lSN + ", returning")
        return False

    #print("//---------------------------------------------------")
    print(" SN = " + lSN + " processed" )
    if bDBG:
        print( json.dumps(aResp['flags'], indent=2) )

    return True


def main(args):
    SNs    = args.SNs
    iFile  = args.iFile
    iFlags = args.iFlags
    DBG    = args.DBG
    print(" Got input: ")
    print("   SNs     = " + SNs    )
    print("   iFile   = " + iFile )
    #print("   iFlags = " + iFlags )
    print("   DBG     = " + str(DBG) )

    list_flags = iFlags.split(',')
    #print(list_flags)

    # print(" length(SN) = " + str(len(SN)) + ", length(iFile) = " + str(len(iFile)) )
    # need the "expires" flag for the cache longevity

    # get SNs from the command-line input
    listSN = []
    if len(SNs) > 0 :
        listSN = SNs.split(",")
        #work_flags(client, SN, list_flags, DBG)

    # process the input file with SNs, if available
    lAbsPath = Path(iFile)
    if lAbsPath.is_file():
        with open(iFile,'r') as iF:
            lines = iF.readlines()

        for lineind in range(len(lines)) :
            newSN = lines[lineind]
            listSN.append(newSN)


    client = itkdb.Client()  # expires_after=dict(days=1) )

    for anSN in listSN:
        goodWork = work_flags(client, anSN, list_flags, DBG)
        if not goodWork:
            print(" Got error. Last attempted SN = " + anSN + ", exiting.")
            return

    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Script for asserting (warranty) flags')
    parser.add_argument('-s', '--SNs', dest = 'SNs', type = str, default = '', help = 'Serial Number to check')
    parser.add_argument('-f', '--File', dest = 'iFile', type = str, default = '', help = 'File with serial numbers')
    parser.add_argument('-l', '--Flags', dest = 'iFlags', type = str, default = 'WARRANTY_WAFER', help = 'A list of flag codes')
    parser.add_argument('-d', '--debug', dest = 'DBG',action="store_true", help = 'To print the extra/debugging info')

    args = parser.parse_args()

    main(args)
