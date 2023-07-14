#!/usr/bin/env python
import argparse
from pathlib import Path

from __path__ import updatePath

updatePath()

import itkdb	

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import get_inst_code
from strips.sensors.SensorSNUtils import get_codes_bulk_filter
from strips.sensors.SensorSNUtils import get_batch_byNumber

#from pprint import PrettyPrinter
#pp = PrettyPrinter(indent = 1,width=200)

#-----------------------------------------
# VF, 2021-08-01: Created
# VF, 2021-08-11: Adjusted for working with dummy sensors
#-----------------------------------------



comptype_MAINs = ['SENSOR','SENSOR_S_TEST']


def check_list_SNs( listSNs ):
    for anSN in listSNs:
        if not checkSN_basic( anSN ) :
            print("Error: SN = <" + anSN + "> is illegal!")
            return False

    return True


def get_codes_from_batch(c, BatchID, rSite, dummy, bDBG):
    batch_code     = 'SENSORS_PROD_BATCH' if not dummy else 'BATCH_TEST_SENSOR'
    (err, aResp) = get_batch_byNumber(c,BatchID,bDBG, batch_code)
    if err:
        print("in <get_codes_from_batch>, got error , exiting...")
        return False,{}

    # Let's loop over the components that belong to the batch
    retDict = {}
    nComp  = 0
    nMAINs = 0
    nMAINuse = 0
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
        aLoc     = aComp['currentLocation']['code']
        if bDBG:
            print(" SN = " + aSN + ", component_type = " + compType ) #+ ", state = " + aState )

        if compType not in comptype_MAINs :
            continue

        nMAINs += 1
        # add if ok
        if len(rSite) == 0:
            retDict[aCode] = aSN
            nMAINuse += 1
        else:
            if aLoc == rSite:
                retDict[aCode] = aSN
                nMAINuse += 1

    print("processed batch <" + BatchID + ">" + 
          ", saw <"    + str(nComp) + "> components, " + 
          "of which <" + str(nMAINs) + "> are MAIN sensors, " + 
          "of which <" + str(nMAINuse) + "> satisfied the site requirement")

    return True, retDict


def move_to_stage( c, dCodes, theStage ):
    for aCode in dCodes:

        resp2 = c.post( 'setComponentStage', 
                        data = {'component': aCode,
                                'stage'    : theStage,
                                'comment': "moving for approval"} )
        # report the motion
        anSN = dCodes[aCode]
        if resp2 != None:
            print("Moved sensor <" + anSN + "> for <" + theStage + ">" )
        else:
            print("Error moving sensor <" + anSN + "> for <" + theStage + ">" )

    return


def main(args):
    BatchID  = args.BatchID
    SNs      = args.SNs
    fList    = args.fileList
    rSite    = args.restrictSite
    DBG      = args.debug
    theStage = args.stage
    dummy    = args.dummy
    print(" Got input: ")
    print("  BatchID  = " + BatchID )
    print("  SNs      = " + SNs     )
    print("  fList    = " + fList   )
    print("  rSite    = " + rSite   )
    print("  DBG      = " + str(DBG) )
    if DBG:
        print("  theStage = " + theStage   )
        print("  dummy    = " + str(dummy) )


    if( len(BatchID) == 0 and
        len(SNs    ) == 0 and
        len(fList  ) == 0 ):
        print(" Need either <BatchID>, or <SNs>, or <fList>. Got neither => exiting.")
        return

    # open a client to work with DB
    c = itkdb.Client()

    # List of codes for the sensors to be moved
    lCodes = {}
    # Process a batch if requested ---------------------------------------
    if len(BatchID) > 0 :
        goodCodes,batch_codes = get_codes_from_batch(c, BatchID, rSite, dummy, DBG) 
        if goodCodes:
            print(" got codes for <" + str( len(batch_codes) ) + "> sensors from batch <" + BatchID + ">")
            lCodes.update( batch_codes )
        else:
            print(" got an error processing the batch information, exitint..")
            return


    # list of SNs from the other sources ---------------------------------
    lSNs = []

    # SN(s) from the commant-line argument
    if len(SNs) > 0:
        listSN1 = SNs.split(",") # presume it could be a comma-separated list
        for anSN in listSN1:
            cleanSN = anSN.strip()
            lSNs.append(cleanSN)

    # SN(s) from the input file list
    if len(fList) > 0 :
        lAbsPath = Path(fList)
        if lAbsPath.is_file():
            with open(fList,'r') as iF:
                lines = iF.readlines()
        else:
            print(" Funny file name: <" + fList + ">" )
            print(" .... cannot process. Exiting. ")
            return

        for aLine in lines:
            # want to have commented out lines
            if aLine.startswith("#") : 
                continue

            # let's strip the SN from the trailing stuff
            cleanSN = aLine.strip()

            lSNs.append(cleanSN)

    # check the list
    goodSNs = check_list_SNs( lSNs )
    if not goodSNs:
        print(" Failed the SN formatting check, exiting...")
        return

    # get {code: SN} dictionary for these SNs
    if len(lSNs) > 0 :
        # need to get the damn institute's hash code
        instCode = ""
        if len(rSite) > 0:
            goodCall, gotCode = get_inst_code(c, rSite, DBG)
            if goodCall:
                instCode = gotCode
            else:
                print(" bad call finding the institute's hash code, from the supplied handle = <" + rSite + ">, exiting")
                return
        dbErr,SN_codes = get_codes_bulk_filter(c, lSNs, instCode, DBG) 
        if dbErr:
            print(" trouble converting SNs to codes, exiting.")
            return
        else:
            print(" got codes for <" + str( len(SN_codes) ) + "> sensors from SNs")
            lCodes.update( SN_codes )

    # and now, move! ----------------------------------------------
    move_to_stage( c, lCodes, theStage )

    return



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Move the sensors to the approval stage')
    parser.add_argument('-b', '--batchID',      dest = 'BatchID',      type = str, default = '', help = 'input batch ID')
    parser.add_argument('-s', '--sensorSN',     dest = 'SNs',          type = str, default = '', help = 'comma-separated serial numbers')
    parser.add_argument('-f', '--fileList',     dest = 'fileList',     type = str, default = '', help = 'file with SNs, 1 per row')
    parser.add_argument('-r', '--restrictSite', dest = 'restrictSite', type = str, default = '', help = 'site name for which the motion is relevant')
    parser.add_argument('-g', '--stage',        dest = 'stage',        type = str, default = 'BLESSING', help = 'approval stage name')

    parser.add_argument('-D', '--dummies',      dest = 'dummy', action="store_true", help = 'dummy sensor toggle')
    parser.add_argument('-d', '--debug',        dest = 'debug', action="store_true", help = 'debugging printout')
    args = parser.parse_args()

    main(args)
