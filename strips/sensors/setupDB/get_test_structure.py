#!/usr/bin/python
import json

import itkdb

#from __path__ import updatePath
#updatePath()




# VF, 2021-06-24: To dump an test structure for a known {object,test} combination

def get_test_structure(c, compType, testType):
    anErr = False
    Resp = {}
    try:
        Resp = c.get( 'exportTestType', 
                      json = { 'project'       : "S",
                               'componentType' : compType,
                               'testType'      : testType } )
    except Exception as e:
        anErr = True
        print(" Could not get the test structure" )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_test_structure>")
        print(e)

    return anErr, Resp


def main(args):
    compType   = args.compType
    testType   = args.testType
    outputFile = args.outputFile
    print(" Got input: ")
    print("   compType   = " + compType   )
    print("   testType   = " + testType   )
    print("   outputFile = " + outputFile )

    if compType == "" or testType == "":
        print(" Did not get the intput expected.")
        print(" The handle/code cannot be of zero length.")
        print("    Exiting.")
        return

    client = itkdb.Client()# expires_after=dict(days=1) )
    (err, Resp) = get_test_structure(client, compType, testType)

    if err:
        print(" got a weird error, exiting...")
        return
    else:
        print(" got response:")
        # write it all out
        if len(outputFile) > 0 :
            with open( outputFile, 'w') as oF:
                json.dump( Resp['testType'], oF, indent=2 )
        else:
            # write to std output
            print( json.dumps(Resp['testType'],indent=2) )

    print(" Done!")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple query of DB test structure')
    parser.add_argument('-c', '--componentType', dest = 'compType', type = str, default = 'SENSOR_TEST_COMPONENT', help = 'component type (handle/code in DB)')
    parser.add_argument('-t', '--testType', dest = 'testType', type = str, default = 'TMP_IMAGE_TEST_1', help = 'test type (handle/code in DB)')
    parser.add_argument('-o', '--outputFile', dest = 'outputFile', type = str, default = '', help = 'output file for the test structure (JSON)')

    args = parser.parse_args()

    main(args)
