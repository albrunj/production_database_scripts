#!/usr/bin/python
import json
import logging

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import setup_logging
from strips.sensors.SensorSNUtils import get_batch_byNumber
from strips.sensors.SensorSNUtils import set_batch_prop


def main(args):

    log_base_file = "junk_"
    logFile = setup_logging(log_base_file)

    logMAIN = logging.getLogger('LOG-MAIN')
    logMAIN.info(" starting the log file for DB : " + logFile )
    logMAIN.info('\n *** change_batch_property.py ***')

    batchName  = args.batchName 
    propHandle = args.propHandle
    bType      = args.bType
    datumI     = args.datumI
    datumS     = args.datumS
    if args.datumL == "True":
        datumL = True
    elif args.datumL == "False":
        datumL = False
    else:
        datumL = None
    logMAIN.info(" Got input: ")
    logMAIN.info("   batchName  = " + batchName   )
    logMAIN.info("   propHandle = " + propHandle  )
    logMAIN.info("   bType      = " + str(bType ) )
    logMAIN.info("   datumI     = " + str(datumI) )
    logMAIN.info("   datumL     = " + str(datumL) )
    logMAIN.info("   datumS     = " + str(datumS) )

    # count the number of input options
    theVal = None
    nOpt = 0
    if datumI is not None:
        theVal = datumI
        nOpt += 1
    if datumL is not None:
        theVal = datumL
        nOpt += 1
    if datumS is not None:
        theVal = datumS
        nOpt += 1

    if nOpt != 1 :
        logMAIN.error(" need exactly 1 of the following option: <i>, <l>, <s>")
        logMAIN.error(" returning ")
        return

    
    c = itkdb.Client()# expires_after=dict(days=1) )

    # get the batch info with the descendant nodes
    if bType is not None:
        (err, aResp) = get_batch_byNumber(c,batchName,False,bType)
    else:
        (err, aResp) = get_batch_byNumber(c,batchName,False)
        
    if err:
        logMAIN.error(" got error accessing batch <" + batchName + ">, exiting...")
        return

    with open("structure_batch-std-info.json","w") as oF:
        json.dump( aResp, oF, indent=2 )

    batchID = aResp['id']
    
    (succ, jResp) = set_batch_prop(c,batchID,propHandle,theVal,logMAIN)

    if not succ:
        logMAIN.error("could not set the batch property, exiting.")
        return
    else:
        logMAIN.info(" success! Set the batch property!")
    
    with open("structure_batch-update-response.json","w") as oF:
        json.dump( jResp, oF, indent=2 )
    return

    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'to update a batch property in DB')
    parser.add_argument('-b', '--batchName', dest = 'batchName', type = str, required=True, help = 'The batch name to use')
    parser.add_argument('-p', '--propHandle', dest = 'propHandle', type = str, required=True, help = 'The property handle to change.')
    parser.add_argument('-t', '--bType',  dest = 'bType',  type = str, help = 'The batch type.')
    parser.add_argument('-i', '--datumI', dest = 'datumI', type = int, help = 'The Integer type of input datum.')
    parser.add_argument('-l', '--datumL', dest = 'datumL', type = str, help = 'The Boolean type of input datum.')
    parser.add_argument('-s', '--datumS', dest = 'datumS', type = str, help = 'The Boolean type of input datum.')
    # TODO: to set several versions

    args = parser.parse_args()

    main(args)
