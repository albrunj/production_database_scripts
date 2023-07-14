#!/usr/bin/python
import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import get_code



def update_component_property(c, SN, check_var, nVal):
    global bad_connection

    # step 1: to get object code reference
    err, objCode = get_code(c, SN)
    if err: 
        print(" in update_component_property: did not get the component code => cannot communicate ")
        return

    # We don't need no education
    try:
        Resp = c.post('setComponentProperty', json = 
                      {'component' : objCode,
                       'code'      : check_var,
                       'value'     : nVal }  )
    except Exception as e:
        print("post operation failed: " + SN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <update_component_property>")

        print(" in update_component_property: could not post the new value ")
        return

    # Check the output
    respVal = ""
    for aProp in Resp['properties']:
        if aProp['code'] == check_var:
            respVal = aProp['value']

    if respVal == nVal:
        print(" successfully updated (SN/property/value) : " + str(SN) + "/" + str(check_var) + "/" + str(nVal) )
    else:
        print(" tried     to update  (SN/property/value) : " + str(SN) + "/" + str(check_var) + "/" + str(nVal) + ", got " + respVal )



def main(args):
    SN    = args.SN
    var   = args.var_code
    nVal  = args.nVal
    print(" Got input: ")
    print("   SN        = " + SN   )
    print("   var_code  = " + var  )
    print("   nVal      = " + nVal )

    # TO-DO: strip/int/bool/float thing

    client = itkdb.Client()# expires_after=dict(days=1) )

    update_component_property(client, SN, var, nVal)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple parameter update for an object in DB')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '20USESX0000599', help = 'Serial Number to use')
    parser.add_argument('-v', '--var_code', dest = 'var_code', type = str, default = 'SUBSTRATE_LOT_NUMBER', help = 'Variable handle/code')
    parser.add_argument('-n', '--new_val', dest = 'nVal', type = str, default = '', help = 'New value')

    args = parser.parse_args()

    main(args)
