#!/usr/bin/python
import json

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import get_code
from strips.sensors.SensorSNUtils import checkSN_basic


def update_component_SN(c, SN, nVal, bDBG):
    # did we get a semi-correct value?
    if not checkSN_basic( nVal ) :
        print(" ERROR: got bad SN = " + SN + ", ...exiting!" )
        return

    # step 1: to get object code reference
    err, objCode = get_code(c, SN)
    if err: 
        print(" in update_component_property: did not get the component code => cannot communicate ")
        return

    # We don't need no education
    try:
        Resp = c.post('updateComponentSN', json = 
                      {'component'   : objCode,
                       'serialNumber': nVal }  )
    except Exception as e:
        print("post operation failed: " + SN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <update_component_property>")

        print(" in update_component_SN: could not post the new value ")
        print(e)
        return

    # Check the output
    if bDBG:
        print( json.dumps(Resp, indent=2) )

    # get the new SN number and compare with what we wanted
    respVal = Resp['component']['serialNumber']

    if respVal == nVal:
        print(" successfully updated (SN/property/value) : " + str(SN) + "/" + str(nVal) )
    else:
        print(" tried     to update  (SN/property/value) : " + str(SN) + "/" + str(nVal) + ", got " + respVal )



def main(args):
    SN    = args.SN
    nVal  = args.nVal
    fDBG  = args.debug
    print(" Got input: ")
    print("   SN        = " + SN   )
    print("   nVal      = " + nVal )
    print("   fDBG      = " + fDBG )

    bDBG = False
    if fDBG == 'no':
        bDBG = False
    elif fDBG == 'yes':
        bDBG = True
    else:
        print(" wrong input option for the debugging flag, exiting...")
        return

    # TO-DO: strip/int/bool/float thing

    client = itkdb.Client()# expires_after=dict(days=1) )

    update_component_SN(client, SN, nVal, bDBG)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple parameter update for an object in DB')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '20USESX0000599', help = 'Serial Number to use')
    parser.add_argument('-n', '--new_val', dest = 'nVal', type = str, default = '', help = 'New value')
    parser.add_argument('-d', '--debug', dest = 'debug', type = str, default = 'no', help = 'debugging printout')

    args = parser.parse_args()

    main(args)
