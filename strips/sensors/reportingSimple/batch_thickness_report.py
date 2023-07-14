#!/usr/bin/python
import json

import itkdb
from __path__ import updatePath
#from pprint import PrettyPrinter
updatePath()

from strips.sensors.SensorSNUtils import get_batch_byNumber

###
# 2021-06-20, VF: a code for checking the thickness test results for a given batch
#             There are 3 steps:
#             1) Getting the batch components and retaining MAINs + halfmoons
#             2) Getting the bulk component info for the comopnents -> test list
#             3) Getting the bulk tests from DB -> actual values
#             4) making a summary
#
#----------------------------


comptype_MAINs = ['SENSOR','SENSOR_S_TEST']
comptype_HMs   = ['SENSOR_HALFMOONS','SENSOR_H_TEST']


def find_bulk_test_values(c,lCode,iDBG,test_code,var_code):
    # The input list has codes, but not the test data
    # Want to obtain the data with the bulk call
    error = False
    aResp = {}
    try:
        aResp = c.get( 'getComponentBulk', 
                       json = {'component'  : lCode,
                               'outputType' : "full",
                               'force' : True } )
    except Exception as e:
        error = True
        print("Bulk Components not found..." )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <find_bulk_test_values>")
        if iDBG:
            print(e)
        return (error,aResp)

    outputLength = len(aResp)
    print(" got the component list of size = " + str(outputLength) )

    # This is a full list of components and properties
    # Let's count the SNs and proper tests
    lTstIDs = []
    dCompTst = {}
    for aComp in aResp:
        aSN = aComp['serialNumber']
        dCompTst[aSN] = []
        # check the tests
        for aTst in aComp['tests']:
            # find the right type
            if aTst['code'] == test_code:
                for aRun in aTst['testRuns']:
                    anID = aRun['id']
                    lTstIDs.append(anID)
    if iDBG:
        for anID in lTstIDs:
            print(" id = " + anID )
    print(" got dictionary of size = " + str(len(dCompTst)) )
    print(" got thickness test list of size = " + str(len(lTstIDs)) )

    # don't waste time on the call, if got no data
    if len(lTstIDs) == 0 :
        return (error, dCompTst)

    # Now let's find the test runs
    tResp = {}
    try:
        tResp = c.get( 'getTestRunBulk', 
                       json = {'testRun'  : lTstIDs} )
    except Exception as e:
        error = True
        print("Bulk TestRuns not found..." )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <find_thicknesses>")
        if iDBG:
            print(e)
        return (error,tResp)

    # Let's browse and fill in the lists in the dictionary
    # print( json.dumps(tResp, indent=2) )
    print(" got thickness test data of size = " + str(len(lTstIDs)) )
    aVal = -999.0
    for aTst in tResp:
        if aTst['state'] != "ready":
            continue # must've been deleted

        foundVal = False
        for aResult in aTst['results']:
            if aResult['code'] == var_code:
                foundVal = True
                aVal = aResult['value']
        if not foundVal:
            continue

        lComp = aTst['components']
        nComp = len(lComp)
        if nComp != 1:
            print(" strange number of components in a test," + str(nComp) + ", exiting...")
        aSN = lComp[0]['serialNumber']
        print(" SN = " + aSN + ", value = " + str(aVal))
        # should be setup to augment the list of thicknesses
        if aSN not in dCompTst:
            print(" found a stray test with un-matched SN")
            print( json.dumps(aTst, indent=2) )
            print(" exiting...")
            return error, dCompTst
        print(" ")
        #print(json.dumps(dCompTst))
        dCompTst[aSN].append(aVal)
        # print(" SN = " + aSN )
        # print(dCompTst[aSN])
        #print(json.dumps(dCompTst))
            

    return error, dCompTst


def report_batch_thickness(c,bDBG,iBatch):

    (err, aResp) = get_batch_byNumber(c,iBatch,bDBG)
    if err:
        print("in <report_batch_thickness>, got error , exiting...")
        return {},{}
    # print( json.dumps(aResp,indent=2) )


    # Let's loop over the components that belong to the batch
    lCodeMAINs = []
    lCodeHMs   = []
    nComp  = 0
    nMAINs = 0
    nHMs   = 0
    for aComp in aResp['components']:
        aState   = aComp['state']
        # don't pay attention to the deleted things
        if aState !='ready':
            continue

        # Counting the total number of components
        nComp += 1

        # count the MAINs and Halfmoons
        compType = aComp['componentType']['code']
        aSN      = aComp['serialNumber']
        aCode    = aComp['code']
        if bDBG:
            print(" SN = " + aSN + ", component_type = " + compType ) #+ ", state = " + aState )

        if compType not in comptype_MAINs and compType not in comptype_HMs:
            continue

        if compType in comptype_MAINs:
            nMAINs += 1
            lCodeMAINs.append(aCode)
        elif compType in comptype_HMs:
            nHMs += 1
            lCodeHMs.append(aCode)
        else:
            # should never get here
            print(" IMPOSSIBLE Error in <report_batch_thickness>, compType = " + compType + ", exiting...")
            return {}, {}

    # A quick counting report
    print(" Batch Components:")
    print("   N(Total) = " + str(nComp ) )
    print("   N(MAIN ) = " + str(nMAINs) )
    print("   N(HMs  ) = " + str(nHMs  ) )

    # find the thickness tests for MAINs
    print(" want MAIN thicknesses ")
    (err,dThickMAIN) = find_bulk_test_values(c,lCodeMAINs,bDBG,
                                             "ATLAS18_MAIN_THICKNESS_V1","AVTHICKNESS")
    if err:
        print(" got an error during the call! will exit")
        return {}, {}
    print(" got MAIN thicknesses ")
    if bDBG:
        print( json.dumps(dThickMAIN,indent=2) )

    # find the thickness tests for Halfmoons
    print(" want HM thicknesses ")
    (err,dThickHM) = find_bulk_test_values(c,lCodeHMs,bDBG,
                                           "ATLAS18_HM_THICKNESS_V1","AVTHICKNESS")
    if err:
        print(" got an error during the call! will exit")
        return {}, {}
    print(" got HM thicknesses ")
    if bDBG:
        print( json.dumps(dThickHM,indent=2) )


    return dThickMAIN, dThickHM



def main(args):
    iBatch = args.iBatch
    fDBG  = args.debug
    print(" Got input: ")
    print("   iBatch = " + iBatch )
    print("   fDBG   = " + fDBG )

    bDBG = False
    if fDBG == 'no':
        bDBG = False
    elif fDBG == 'yes':
        bDBG = True
    else:
        print(" wrong input option for the debugging flag, exiting...")
        return

    # do some checks on the input
    if len(iBatch) == 0:
        print(" input batch ID is not specified, exiting...")
        return

    # establish a DB client
    c = itkdb.Client()# expires_after=dict(days=1) )


    ThMAIN, ThHM   = report_batch_thickness(c,bDBG,iBatch)

    # Assume at least the MAIN sensor size is non-zero
    if len(ThMAIN) == 0:
        print(" Something is wrong, got zero MAIN sensors in this batch")

    # Now, print the table
    print("\n\n\n")
    print(" Final table: ")
    print(" SN(MAIN); List(Thick.MAIN); SN(HM); List(Thick.HM)")
    for snMAIN in ThMAIN:
        snPrint = ""
        lHM = []
        # the HM serial number, as it should be
        snHM = snMAIN[:8] + "9" + snMAIN[9:]
        # check if the HM object exists
        if snHM in ThHM:
            snPrint = snHM
            lHM = ThHM[snHM]
        pMAIN = ", ".join( str(x) for x in ThMAIN[snMAIN] )
        pHM   = ", ".join( str(x) for x in lHM            )
        print(snMAIN + "; " + pMAIN + "; " + snPrint + "; " + pHM)

    # There can be halfmoons without the MAIN sensors though => find such exceptions
    for snHM in ThHM:
        # the MAIN serial number, as it should be
        snMAIN = snHM[:8] + "0" + snHM[9:]
        # check if the HM object exists
        if snMAIN in ThMAIN:
            continue
        pHM = ", ".join( str(x) for x in ThHM[snHM] )
        print("; ; " + snHM + "; " + pHM)




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'to report the thickness test results for MAINs and Halfmoons from a batch')
    parser.add_argument('-b', '--batch ID', dest = 'iBatch', type = str, default = '', help = 'input batch ID')
    parser.add_argument('-d', '--debug', dest = 'debug', type = str, default = 'no', help = 'debugging printout')

    args = parser.parse_args()

    main(args)
