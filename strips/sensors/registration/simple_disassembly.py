#!/usr/bin/python
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic



# VF, 2021-05-10: to disassemble an object.
#
# Want to do:
#    - get a SN
#    - get it's component properties
#    - to loop over the official children
#      -- to disassemble the children from the parent
#
# Seems like a generic enough functionality => won't do the sensor-related checks
#



# VF, 2021-05-01: Will use a global variable to indicate the state of DB connection affairs
bad_connection = False # original goodness

def get_code(c,SN):
    global bad_connection
    # don't bang the head against the wall
    if bad_connection :
        return (False,)

    # the actual query
    foundObject = True
    try:
        Resp = c.get('getComponent', json = {'component':SN})
    except Exception as e:
        foundObject = False
        print("object not found: " + SN )
        if e.__class__.__name__ == 'Forbidden' :
            print("Error: got bad connection in <get_code>")
            bad_connection = True

    objCode = Resp['code']

    return (foundObject, objCode)


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


def dis_assemble(c, codeParent, codeChild):
    global bad_connection
    # don't bang the head against the wall
    if bad_connection :
        return (False,)

    # the actual query
    qSuccess = True
    Resp = {}
    try:
        Resp = c.post('disassembleComponent', 
                      json = {'parent':codeParent,
                              'child':codeChild, 
                              'trashed': False} ) # The default it to junk the stuff...
    except Exception as e:
        qSuccess = False
        print("Error: disassembly did not work: " + codeParent + " " + codeChild )
        print(e)
        if e.__class__.__name__ == 'Forbidden' :
            print("Error: got bad connection in <dis_assemble>")
            bad_connection = True

    return (qSuccess, Resp)



def disown_children(c, aSN):
    global bad_connection

    # let's strip the SN from the trailing stuff
    lSN = aSN.rstrip()

    # check the input SN formatting
    if not checkSN_basic(lSN) :
        print(" Error: SN = <" + lSN + "> is illegal!")
        return

    # check if the DB connection is active
    if bad_connection :
        print(" Error: bad connection, returning ")
        return

    (foundObj, objResp) = get_response(c, lSN)

    if not foundObj :
        print(" Error: Object not found! SN = " + lSN + ", returning")
        return
    #else:
    #    print(" Object found: SN = " + lSN + " , code = " + objResp['code'])

    #return
    
    objCode = objResp['code']
    objType = objResp['componentType']['code']

    # check if the object is childless
    n_child = len(objResp['children'])
    if n_child == 0:
        print(" Error: SN = <" + lSN + "> is childless, returning")
        return

    # iterate over children
    nTotal=0
    nFailed=0
    nDisowned=0
    for aChild in objResp['children']:
        #print("//------------------------------------------------------------")
        #print( json.dumps(aChild, indent=2) )

        # check if the child actually exists: some might already be dumped...
        childInfo = aChild['component']
        if childInfo is None:
            #print(" this child is gone! continuing ")
            continue
        # 

        nTotal += 1
        childCode = aChild['component']['code']
        childSN   = aChild['component']['serialNumber']
        childType = aChild['componentType']['code']

        # the query
        (got_done, aResp) = dis_assemble(c, objCode, childCode)

        outcome = 'Unclear'
        if not got_done:
            print(" Error: Failed to dis-assemble!")
            nFailed += 1
            outcome = 'Failed-to-disassemble'
            print("the query response is: ", json.dumps(aResp, indent=2) )
        else:
            print(" succeeded with the dis-assembly!")
            nDisowned += 1
            outcome = 'Disassembled'

        print( " see child: type = " + childType + 
               ", SN = " + childSN + 
               " : " + outcome )
        #, code = " + childCode ) 

        #break

    print( " SN = " + lSN +
           " type = " + objType +
           " nChild = " + str(nTotal) + 
           " nDisowned = " + str(nDisowned)
           + " nFailed = " + str(nFailed) )
    return



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
        disown_children(client, SN)

    lAbsPath = Path(iFile)
    if lAbsPath.is_file():
        with open(iFile,'r') as iF:
            lines = iF.readlines()
    else:
        return

    for lineind in range(len(lines)) :
        aSN = lines[lineind]
        disown_children(client, aSN)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple disassembly (disowning of the chilren)')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '', help = 'Serial Number to check')
    parser.add_argument('-f', '--File', dest = 'iFile', type = str, default = '', help = 'File with serial numbers')

    args = parser.parse_args()

    main(args)
