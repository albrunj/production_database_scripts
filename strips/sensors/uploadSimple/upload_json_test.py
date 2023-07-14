#!/usr/bin/python
import json
from pathlib import Path

import itkdb



# VF, 2021-06-27: to upload a json file for a test run

def upload_testrun(c,test_data):
    try:
        Resp = c.post('uploadTestRunResults', json = test_data )
    except Exception as e:
        print("There was an issue with uploading the test results" )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_code>")
        print(e)
        return False, {}

    return True, Resp


def main(args):
    jasonFile    = args.jasonFile
    responseFile = args.responseFile
    print(" Got input: ")
    print("   jasonFile    = " + jasonFile    )
    print("   responseFile = " + responseFile )

    if len(jasonFile) == 0:
        print(" the intput file is not supplied. Please try -j option. Exiting.")
        return

    fAbsPath = Path(jasonFile)
    if not fAbsPath.is_file():
        print(" don't really see the input file <" + jasonFile + ">, exiting..." )
        return

    # read it in
    with open(jasonFile,'r') as iF:
        data=iF.read()

    # parse it
    anObj = json.loads(data)

    client = itkdb.Client()# expires_after=dict(days=1) )

    goodCall, aResp = upload_testrun(client, anObj)
    if goodCall:
        print(" Success!")
        print(" Can try to see the test run at the following URL:")
        print("")
        print("   https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/" + 
              aResp['testRun']['awid'] + 
              "/testRunView?id=" + 
              aResp['testRun']['id'] )
        print("")
    else:
        print(" got an error with the upload call.")

    # write it all out
    if len(responseFile) > 0 :
        with open( responseFile, 'w') as oF:
            json.dump( aResp, oF, indent=2 )
        print(" wrote the DB response to file <" + responseFile + ">")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple repeat query of DB')
    parser.add_argument('-j', '--jasonFile', dest = 'jasonFile', type = str, default = '', help = 'A JSON file to upload')
    parser.add_argument('-r', '--responseFile', dest = 'responseFile', type = str, default = '', help = 'A file to write the DB response to.')

    args = parser.parse_args()

    main(args)
