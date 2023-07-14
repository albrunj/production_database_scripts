#!/usr/bin/python
import json
from pathlib import Path

import itkdb

#from __path__ import updatePath
#updatePath()




# VF, 2021-06-24: To dump an test structure for a known {object,test} combination

def set_test_json(c, aJSON ):
    anErr = False
    Resp = {}
    try:
        Resp = c.post( 'importTestType', json = aJSON )
    except Exception as e:
        anErr = True
        print(" Could not set up the test structure" )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <set_test_json>")
        print(e)

    return anErr, Resp


def main(args):
    iFile = args.iFile
    print(" Got input: ")
    print("   iFile = " + iFile )

    # check the existence
    fAbsPath = Path(iFile)
    if not fAbsPath.is_file():
        print(" don't really see the file, exiting..." )
        return

    # read it in
    with open(iFile,'r') as iF:
        data=iF.read()

    # parse it
    anObj = json.loads(data)

    client = itkdb.Client()# expires_after=dict(days=1) )
    (err, Resp) = set_test_json(client, anObj)

    if err:
        print(" got a weird error, exiting...")
        return
    else:
        print(" got response:")
        print( json.dumps(Resp,indent=2) )

    print(" Done!")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'to set up a DB test structure')
    parser.add_argument('-j', '--inputJSONfile', dest = 'iFile', type = str, default = '', help = 'input JSON file with the structure to upload/set up')

    args = parser.parse_args()

    main(args)
