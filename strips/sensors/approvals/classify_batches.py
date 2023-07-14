#!/usr/bin/python
import argparse
import json
import logging
import numbers
import os
import time
from bisect import bisect
from datetime import datetime

import itkdb
from __path__ import updatePath
from dateutil import parser as dateparser
updatePath()

from strips.sensors.SensorSNUtils import get_batch_byNumber
from strips.sensors.SensorSNUtils import check_batch_name
from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import setup_logging
from strips.sensors.SensorSNUtils import isHalfmoon
from strips.sensors.SensorSNUtils import makeSN_sensor
from strips.sensors.SensorSNUtils import get_sensor_batches
from strips.sensors.SensorSNUtils import get_testdata_bulk
from strips.sensors.SensorSNUtils import get_components_bulk
from strips.sensors.SensorSNUtils import get_resp
from strips.sensors.SensorSNUtils import check_strips_bounds
from strips.sensors.SensorSNUtils import consecutive_strips
from strips.sensors.approvals.batch_sensor_tests import Batch
from strips.sensors.approvals.batch_sensor_tests import Wafer
from strips.sensors.approvals.batch_sensor_tests import MAIN
from strips.sensors.approvals.batch_sensor_tests import HM
from strips.sensors.approvals.batch_sensor_tests import QAchip
from strips.sensors.approvals.batch_sensor_tests import QAmini
from strips.sensors.approvals.summary_data import MON_TESTS
from strips.sensors.approvals.summary_data import STRIP_ATL_KEYS
from strips.sensors.approvals.summary_data import STRIP_KEK_KEYS
from strips.sensors.approvals.summary_data import MON_KEYS
from strips.sensors.approvals.summary_data import NICE_SITES
from strips.sensors.approvals.summary_data import NUM_KEYS
from strips.sensors.approvals.summary_data import PROD_MAIN_TYPES
from strips.sensors.approvals.summary_data import PROD_MAIN_STAGES
from strips.sensors.approvals.summary_data import FINAL_STATES
from strips.sensors.approvals.summary_data import DESIGN


###
# 2021-10-18, VF: a code for scnaning batch and sensor info in DB
#             There are several steps:
#             1) Getting the batch components and retaining MAINs + halfmoons
#             2) Getting the bulk component info for the components -> test list
#             3) Getting the bulk tests from DB -> actual values
#             4) making a summaries (html) and saving data (json)
#
#----------------------------


scriptVersion = DESIGN

comptype_WAFERs = ['SENSOR_WAFER','SENSOR_W_TEST']
comptype_MAINs  = ['SENSOR','SENSOR_S_TEST']
comptype_HMs    = ['SENSOR_HALFMOONS','SENSOR_H_TEST']
comptype_QAmini = ['SENSOR_MINI_MD8','SENSOR_QAMINI_TEST']
comptype_QAchip = ['SENSOR_TESTCHIP_MD8','SENSOR_QCHIP_TEST']


'''
            for aResult in aTst['results']:
                aVar = aResult['code']
                if aVar in Vars:
                    aVal = aResult['value']
                    myName = Vars[aVar]
                    dSNvals[theSN][myName] = aVal

WEIRDS = [
              "MANUFACTURING18",
              "ATLAS18_VIS_INSPECTION_V1",
              "ATLAS18_VIS_INSPECTION_V2",
              "ATLAS18_IV_TEST_V1",
              "ATLAS18_CV_TEST_V1",
#              "ATLAS18_CURRENT_STABILITY_V1",
              "ATLAS18_FULLSTRIP_STD_V1",
              "ATLAS18_SHAPE_METROLOGY_V1",
              "ATLAS18_MAIN_THICKNESS_V1",
              "ATLAS18_HM_THICKNESS_V1"  ,
              "ATLAS18_KEKTEST_NEW_V1"   ,
              "ATLAS18_KEKTEST_OLD_V1"   ,
              "ATLAS18_HANDLING_DAMAGE_V1", 
              "ATLAS18_RECOVERY_V1"      ,
              "ATLAS18_SPECIAL_USE_V1"   
]

'''
HEAVY = ["ATLAS18_CURRENT_STABILITY_V1"]


# to check if the new (1st) date/runNumber are the latest
def newLater(strD1,strD2,strN1,strN2):
    logNL_ = logging.getLogger('LOG-NL_')
    N1 = int(strN1)
    N2 = int(strN2)
    compN = N1 > N2
    dt1 = dateparser.parse(strD1)
    dt2 = dateparser.parse(strD2)
    stamp1 = datetime.combine(dt1.date(),dt1.time())
    stamp2 = datetime.combine(dt2.date(),dt2.time())
    compD = stamp1 > stamp2
    if compN != compD :
        # sometimes the timestamps are exactly equal, which is a false alarm
        if stamp1 != stamp2:
            logNL_.error(" Seeing incompatibility b/w the run numbers and time stamps:")
            logNL_.error(" " + strN1 + " > " + strN2 + " : " + str(compN))
            logNL_.error(" " + strD1 + " > " + strD2 + " : " + str(compD))
    # the runnumbers are deemed more reliable -- less likely to be a typo,
    # since they are in the file names for most tests
    return compN


# To parse the reponse from the 
def find_latest_runs(dbResp):
    # This is a full list of components and properties
    # Let's count the SNs and make a list of the proper tests
    lTstIDs = []
    listAll = [lTstIDs]
    for aComp in dbResp:
        # check the tests
        # a dictionary of the test types and dates: want to select the latest ones
        dictTCD = {}
        for aTst in aComp['tests']:
            # find the right type
            tCode = aTst['code']
            # a special consideration for the IV data: want all of them for now
            # (Since the stage info is not available here...)
            if tCode in ['ATLAS18_IV_TEST_V1','ATLAS18_FULLSTRIP_STD_V1',
                         'ATLAS18_KEKTEST_NEW_V1', 'ATLAS18_KEKTEST_OLD_V1']:
                for aRun in aTst['testRuns']:
                    tID = aRun['id']
                    lTstIDs.append( tID )
                continue

            # main code for the rest of the tests
            if tCode in MON_TESTS:
                for aRun in aTst['testRuns']:
                    runState = aRun['state']
                    # don't want to consider the deleted runs
                    if runState != "ready":
                        continue
                    tID = aRun['id']
                    #lTstIDs.append(tID)
                    tDate = aRun['date']
                    runN  = aRun['runNumber']
                    if tCode in dictTCD:
                        #pDate = dictTCD[tCode]['date']
                        if newLater(tDate,dictTCD[tCode]['date'],runN,dictTCD[tCode]['runN']):
                            #if tDate >= pDate: # picking up the latest is safer
                            dictTCD[tCode]['date'] = tDate
                            dictTCD[tCode]['id'  ] = tID
                            dictTCD[tCode]['runN'] = runN
                    else:
                        dictTCD[tCode] = {}
                        dictTCD[tCode]['id'  ] = tID
                        dictTCD[tCode]['date'] = tDate
                        dictTCD[tCode]['runN'] = runN
        # now, for a given component, collect the ids for these unique and latest runs
        for tCode in dictTCD:
            if tCode in HEAVY:
                # this is a special case of large data
                newList = [ dictTCD[tCode]['id'] ]
                listAll.append( newList )
            else:
                # regular test data that have moderate size
                lTstIDs.append( dictTCD[tCode]['id'] )

    return listAll  #lTstIDs


# to calculate the number of consecutive bad strips
def find_cons_bad( badMap, valType ):
    logFCB = logging.getLogger('LOG-FCB')
    listS = []
    for aK in badMap:
        zV = badMap[aK]
        # we have a weird default
        if zV == "9-9999":
            continue
        check_strips_bounds(logFCB,"DB",aK,zV,valType,listS)

    # check the number of consecutive bad strips
    nConsBad = consecutive_strips(listS)

    return nConsBad


# our data contain non-numbers, unfortunately
# this stemed from the mess in the original data 
# (sometimes strings with percentage, sometimes numbers)
# and the input parser not catching it
def clean_number( inp, name ):
    logCN_ = logging.getLogger('LOG-CN_')
    if ( inp is None or 
         not name in NUM_KEYS ):
        return inp
    #if name != "hpkBadPerc":
    #    return inp
    if isinstance(inp,numbers.Number):
        return inp
    else:
        # dbg -- funny early data
        if type(inp) is list:
            # early data had this issue for the IV test
            if not name in ['I500V','Vbd']:
                logCN_.error(" for variable <" + name + "> see the data being a list!!! " + str(inp) + ", replacing by <None>")
                
            return None
        if isinstance(inp,str):
            if name != 'hpkBadPerc':
                logCN_.error(" for variable <" + name + "> see the data being a string! " + str(inp) )
            # Known issue for the HPK bad percentage
            v = float(inp.strip('%'))
            return v
        logCN_.error(" for variable <" + name + "> see unkown data type issue!! " + str(inp) )
        return None


# "date"       : "stripDate",
# "runNumber"  : "stripRunNo",
# "SEGMENTNO"  : "segmentNo",
def add_to_buffer( iBuffer, dSNvals, SN, Date, RunNo, segNo ):
    # the algorithm:
    # 1) get the initial info:
    # - segment No
    # - test datetime
    # - runNumber
    # 2) if segment No not inside, add the info
    #    else find the proper index and replace
    newDateT = dSNvals[SN][Date]  #['stripDate']
    newRunNo = dSNvals[SN][RunNo] #['stripRunNo']
    newSegNo = dSNvals[SN][segNo] #['segmentNo']
    oldDateT = iBuffer[SN][Date]  #['stripDate']
    oldRunNo = iBuffer[SN][RunNo] #['stripRunNo']
    oldSegNo = iBuffer[SN][segNo] #['segmentNo']

    # had the test done for this segment before?
    if oldSegNo is None:
        # never filled it in - make a list
        for var in iBuffer[SN]:
            iBuffer[SN][var] = [ dSNvals[SN][var] ]
    elif not newSegNo in oldSegNo:
        # new value - to add
        for var in iBuffer[SN]:
            iBuffer[SN][var].append( dSNvals[SN][var] )
    else:
        # to replace:
        # find the index first
        indx = oldSegNo.index(newSegNo)
        prevRunNo = oldRunNo[indx]
        prevDateT = oldDateT[indx]
        if not newLater(newDateT,prevDateT,newRunNo,prevRunNo):
            return
        # replace
        for var in iBuffer[SN]:
            iBuffer[SN][var][indx] = dSNvals[SN][var]
            
    return


def backfill_data( iBuffer, dSNvals ):
    for SN in iBuffer:
        for var in iBuffer[SN]:
            dSNvals[SN][var] = iBuffer[SN][var]
        # end loop over vars
    # end loop over SNs
    return


#with open("structure_getComponentBulk_"+aB.bName()+".json", "w") as oF:
#    json.dump( aResp, oF, indent=2 )
#with open("getTestRunBulk_"+aB.bName()+".json", "w") as oF:
#    json.dump( tResp, oF, indent=2 )
#logATD.info( json.dumps(dSNvals,indent=2) )

# https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/dcb3f6d1f130482581ba1e7bbe34413c/testRunView?id=6010a0ff78d6c1000a48fbd5

def add_test_data(c,lBatches):

    logATD = logging.getLogger('LOG-ATD')
    
    logATD.info(" Got the variables to fill: " + str(MON_KEYS) )
    logATD.info(" Got the strip test variables: " + str(STRIP_ATL_KEYS) )
    logATD.info(" Got the strip test variables: " + str(STRIP_KEK_KEYS) )

    nBatches = len(lBatches)
    for iB, aB in enumerate(lBatches):
        logATD.info( ("\n finding components for Batch = " + aB.bName() +
                      ", No " + str(iB+1) + " out of " + str(nBatches) ) )
        lCodes = aB.codesMainHMconsider() # want non-final stuff for test data

        # The input list has codes, but not the test data
        # Want to obtain the data with the bulk call
        t0 = time.perf_counter()
        success, aResp = get_components_bulk(c,lCodes)
        t1 = time.perf_counter()
        if not success:
            logATD.error(" in add_test_data, failed to get the components")
            return False

        outputLength = len(aResp)
        logATD.info( ( "   got the component list of size = " + str(outputLength) + 
                       " in {:.3f} sec".format(t1-t0) ) )

        # make a dummy default one -- SN-indexed dictionary of test dictionaries
        lSNs = aB.SNsMain() # Consider() # Want all the SNs in the batch for ini
        dSNvals = {}
        iBufATL = {}
        iBufKEK = {}
        for sn in lSNs:
            dSNvals[sn] = {}
            iBufKEK[sn] = {}
            iBufATL[sn] = {}
            for el in MON_KEYS:
                dSNvals[sn][el] = None
            for el in STRIP_ATL_KEYS:
                iBufATL[sn][el] = None
            for el in STRIP_KEK_KEYS:
                iBufKEK[sn][el] = None
                
        # initialization
        success = aB.fillTestData( dSNvals )
        if not success:
            return False

        logATD.info(" finding the runs in the component structures")
        lAllTestIDs = find_latest_runs(aResp)
        nTests = 0
        for aList in lAllTestIDs:
            nTests += len(aList)
        logATD.info("   got test list of size = " + str(nTests) )

        # don't waste time on the call, if got no data
        if nTests == 0:
            continue


        # Now let's find the test runs
        logATD.info(" finding the select runs in DB")
        dResp = []
        t0 = time.perf_counter()
        for aList in lAllTestIDs:
            success, tResp = get_testdata_bulk(c,aList) #lTestIDs)
            if not success:
                logATD.error(" in add_test_data, failed to retrieve the test data")
                return False
            dResp.append(tResp)
        t1 = time.perf_counter()
        logATD.info( "   obtained the test data from DB in {:.3f} sec".format(t1-t0) )
        logATD.info( "   extracting info from the test records for this batch " )

        t0 = time.perf_counter()
        for tResp in dResp:
            for aTst in tResp:
                # filter on status
                if aTst['state'] != "ready":
                    continue # must've been deleted

                # filter on type
                testKey = aTst['testType']['code']
                if not testKey in MON_TESTS:
                    continue

                # get the SN. God knows why it's a list
                lComp = aTst['components']
                nComp = len(lComp)
                if nComp != 1:
                    logATD.error(" strange number of components attached to a test," + str(nComp))
                aSN    = lComp[0]['serialNumber']
                aStage = lComp[0]['testedAtStage']['code']

                # The IV test is also defined for the last stage, unfortunately
                # Skip if it's a wrong stage data
                if ( testKey == 'ATLAS18_IV_TEST_V1' and
                     aStage != 'SENS_TEST_STAGE' ): 
                    continue

                # convert to MAIN sensor SN, if needed
                theSN = aSN
                if isHalfmoon(aSN): 
                    theSN = makeSN_sensor( aSN )

                # Also skip if earlier than what we need
                if testKey == 'ATLAS18_IV_TEST_V1':
                    newDate = aTst['date']
                    jsnDate = dSNvals[theSN]['ivDate']
                    if jsnDate is not None:
                        if newDate < jsnDate:
                            continue
                    dSNvals[theSN]['ivDate'] = newDate
                # end IV data check

                # get the corresponding variables in our dict for this test
                Vars = MON_TESTS[testKey]

                # get the common structures -- purposefully put them in all tests
                for aWord in ['id','passed']:
                    aRef = Vars[aWord]
                    dSNvals[theSN][aRef] = aTst[aWord]

                # check the "results"
                for aResult in aTst['results']:
                    aVar = aResult['code']
                    if aVar in Vars:
                        aVal = aResult['value']
                        myName = Vars[aVar]
                        aVal = clean_number(aVal,myName)
                        dSNvals[theSN][myName] = aVal

                # and now check the "properties", as if they are different
                for aResult in aTst['properties']:
                    aVar = aResult['code']
                    if aVar in Vars:
                        aVal = aResult['value']
                        myName = Vars[aVar]
                        aVal = clean_number(aVal,myName)
                        dSNvals[theSN][myName] = aVal

                # our unusual data structure, where the weird built-in construct is used
                if testKey == "MANUFACTURING18":
                    badMap = {}
                    for aDef in aTst['defects']:
                        aVar = aDef['name']
                        if aVar in Vars:
                            aVal = aDef['description']
                            myName = Vars[aVar]
                            aVal = clean_number(aVal,myName)
                            dSNvals[theSN][myName] = aVal
                            if "List" in myName:
                                badMap[myName] = aVal
                    # weird call. Only need it b/c reusing the code checking the boundaries
                    sensType = aB.sensor_type( theSN )
                    dSNvals[theSN]['hpkMaxNBad'] = find_cons_bad( badMap, sensType )
                else:
                    # Fill in the test location!
                    testLoc = aTst['institution']['code']
                    if testLoc in NICE_SITES:
                        testLoc = NICE_SITES[testLoc]
                    locDB = dSNvals[theSN]['testedAt']
                    if locDB is None:
                        locDB = testLoc
                    elif testLoc not in locDB:
                        locDB += "/" + testLoc
                    dSNvals[theSN]['testedAt'] = locDB

                if testKey == 'ATLAS18_FULLSTRIP_STD_V1':
                    dSNvals[theSN]['stripDate' ] = aTst['date']
                    dSNvals[theSN]['stripRunNo'] = aTst['runNumber']
                    add_to_buffer( iBufATL, dSNvals, theSN,
                                   'stripDate', 'stripRunNo', 'segmentNo' )
                if testKey in ['ATLAS18_KEKTEST_NEW_V1', 'ATLAS18_KEKTEST_OLD_V1']:
                    dSNvals[theSN]['kekDate' ] = aTst['date']
                    dSNvals[theSN]['kekRunNo'] = aTst['runNumber']
                    add_to_buffer( iBufKEK, dSNvals, theSN,
                                   'kekDate', 'kekRunNo', 'kekSegNo' )
            # end of loop over the tests            
        # end of the loop over the responses (to each test list)
        backfill_data( iBufATL, dSNvals )
        backfill_data( iBufKEK, dSNvals )

        success = aB.fillTestData( dSNvals )
        if not success:
            return False

        #aB.evaluate_data()
        t1 = time.perf_counter()
        logATD.info("   processed the info for this batch in {:.3f} sec ".format(t1-t0) )

        #logATD.info( json.dumps(dSNvals,indent=2) )

    return True


# just quickly show what we got
def show_batch_data(lB):
    logSBD = logging.getLogger('LOG-SBD')
    
    startT = datetime.now()
    dateString = startT.strftime("%Y-%m-%d")

    for aB in lB:
        logSBD.info("checking the test info for Batch = " + aB.bName())
        lMains = aB.lMAINs()
        for aSensor in lMains:
            tData = aSensor.testData()
            showData = {}
            showData["code"        ] = aSensor.code()
            showData["batchWaferNo"] = aSensor.ID()
            showData["Type"        ] = aSensor.Type()
            showData["reception"   ] = aSensor.rDate()
            showData["stage"       ] = aSensor.stage()
            showData["location"    ] = aSensor.locQC()
            if tData is not None:
                for aKey in tData:
                    showData[aKey] = tData[aKey]
            logSBD.debug(" SN = " + aSensor.SN() + ", data = " + json.dumps(showData) )

        suffix = "run"
        if aB.toApprove():
            suffix = "app"
        elif aB.isFinal():
            suffix = "fin"
        name_base = ( "summary_" + aB.bName() + "_" + 
                      dateString + "_" + 
                      aB.testedAtNice() + "_" + suffix )
        name_html = name_base + ".html"
        name_json = name_base + ".json"
        html_string = aB.html_summary()
        with open( name_html, "w" ) as oF:
            oF.write(html_string)
        with open( name_json, "w" ) as jF:
            json.dump( aB.toJD(), jF, indent=2 )
        ## 1st verification - to re-create the file again
        #with open( name_json, "r" ) as iF:
        #    new_json = json.load(iF)
        #nB = Batch.fromJD( new_json )
        #name_json2 = name_base + "_2nd.json"
        #with open( name_json2, "w" ) as jF:
        #    json.dump( nB.toJD(), jF, indent=2 )
        # 2nd verification - by re-creating the file from the JSON data, then comparing the strings
        json_1st = aB.toJD()
        json_1st_str = json.dumps( json_1st, sort_keys=True )
        aB_2nd = Batch.fromJD( json_1st )
        json_2nd = aB_2nd.toJD()
        json_2nd_str = json.dumps( json_2nd, sort_keys=True )
        data_verif = json_1st_str == json_2nd_str
        logSBD.info(" batch data integrity verification = " + str(data_verif) )

        
    return


# check if the right types... because this stuff exists
def is_production_type( aComp ):
    kT = 'type'
    kS = 'currentStage'
    if not ( kT in aComp and 
             kS in aComp ):
        return False
    if not ( 'code' in aComp[kT] and
             'code' in aComp[kS] ):
        return False

    aType  = aComp[kT]['code']
    aStage = aComp[kS]['code']
    if ( not ( aType  in PROD_MAIN_TYPES and 
               aStage in PROD_MAIN_STAGES ) ):
        return False

    return True


def get_warranty_flag(c,aCode,log2use):
    wFlag = False
    goodCall,cInfo = get_resp(c,aCode)
    if goodCall:
        flags = cInfo["flags"]
        if flags is not None:
            for aFlag in cInfo["flags"]:
                if ( aFlag['code' ] == 'WARRANTY_WAFER' and
                     aFlag['state'] == 'ready'):
                    wFlag = True
            # loop over the flag list
        # check if the structure is not None
    else:
        log2use.error(" for object = " + aCode + " could not find flags")
            
    return wFlag


#if aBatch == "VPX30816":
#if aBatch == "VPX37414":
#if aBatch == "VPX30906":
#if aBatch == "VPX99999":
#    with open("dump_batch_info_"+aBatch+".json", "w") as oF:
#        json.dump( aResp, oF, indent=2 )
'''
logLBO.info(" Batch Components:")
logLBO.info("   N(Total  ) = " + str(nComp   ) )
logLBO.info("   N(Deleted) = " + str(nDeleted) )
logLBO.info("   N(Wafers ) = " + str(nWafers ) )
logLBO.info("   N(MAIN   ) = " + str(nMAINs  ) )
logLBO.info("   N(HMs    ) = " + str(nHMs    ) )
logLBO.info("   N(QAminis) = " + str(nQAminis) )
logLBO.info("   N(QAchips) = " + str(nQAchips) )
'''

# set zero-length lists to None, in order to avoid issues with the empty lists passing
def wash_lists( l1, l2, l3, l4, l5 ):
    if len(l1) == 0:
        l1 = None
    if len(l2) == 0:
        l2 = None
    if len(l3) == 0:
        l3 = None
    if len(l4) == 0:
        l4 = None
    if len(l5) == 0:
        l5 = None
    return l1, l2, l3, l4, l5

# parse the batch information, filter some, make our own batch structure
def info_batch_structures( c, lB, iControl, bDBG ):

    logIBS = logging.getLogger('LOG-IBS')
    lBatches   = []
    first   = True
    for aBatch in lB:
        #logIBS.info(" Batch = " + aBatch )
        # A quick counting report
        if first:
            first = False
            logIBS.info(" BatchName, N(del), N(Tot) ")
        msg = " " + aBatch

        # Filter 1: wrong batch name formatting
        if not check_batch_name(aBatch):
            msg += "    Weird batch name, skipping!"
            logIBS.info(msg)
            continue

        # Filter 2: remove the old numbers: the pre-pro started with range in 32_000s
        nBatch = int(aBatch[3:])
        if nBatch < 32_000:
            msg += "    Prototyping stuff, skipping!"
            logIBS.info(msg)
            continue

        # get the batch info with the descendant nodes
        (err, aResp) = get_batch_byNumber(c,aBatch,bDBG)
        if err:
            logIBS.error(msg + " in <list_batch_objects>, got error , exiting...")
            return lBatches
            # print( json.dumps(aResp,indent=2) )

        # Filter 3: no components
        bComp = aResp['components']
        if len(bComp) == 0:
            logIBS.info("    No components, skipping!")
            continue

        # Let's loop over the components that belong to the batch
        qaTC  = None
        qaCCE = None
        ifReturned = False
        ifFailed   = False
        if 'batches' in iControl:
            cB = iControl['batches']
            if aBatch in cB:
                if "QATC"  in cB[aBatch]:
                    qaTC  = cB[aBatch]["QATC" ]
                if "QACCE" in cB[aBatch]:
                    qaCCE = cB[aBatch]["QACCE"]
                if "ifReturned"  in cB[aBatch]:
                    ifReturned = cB[aBatch]["ifReturned"]
                if "ifFailed" in cB[aBatch]:
                    ifFailed = cB[aBatch]["ifFailed"]
                    
        lWafers  = []
        lMAINs   = []
        lMAINno  = []
        lHMs     = []
        lQAminis = []
        lQAchips = []
        nComp    = 0
        nDeleted = 0
        haveRealMAIN = False
        haveDummyMAIN = False
        Type = ""
        isProto = False
        isReal  = False
        for aComp in bComp:
            aState   = aComp['state']
            # don't pay attention to the deleted things
            if aState == 'deleted':
                nDeleted += 1
                #logIBS.info(" state = " + aState)
                continue

            # Counting the total number of components
            nComp += 1

            # count the MAINs and Halfmoons
            compType = aComp['componentType']['code']
            aSN      = aComp['serialNumber']
            aCode    = aComp['code']
            ordPath  = aComp['institution']['code']
            if bDBG:
                logIBS.info(" SN = " + aSN + ", component_type = " + compType ) #+ ", state = " + aState )

            #if compType not in comptype_MAINs and compType not in comptype_HMs:
            #    continue

            if compType in comptype_WAFERs:
                newWafer = Wafer(aSN,aCode)
                lWafers.append(newWafer)
            elif compType in comptype_MAINs:
                owData = None
                if 'sensors' in iControl:
                    if aSN in iControl['sensors']:
                        owData = iControl['sensors'][aSN]
                if compType == 'SENSOR'       : haveRealMAIN  = True
                if compType == 'SENSOR_S_TEST': haveDummyMAIN = True
                if not is_production_type( aComp ): 
                    isProto = True
                    continue
                # check out the warranty flag
                wFlag = get_warranty_flag(c,aCode,logIBS)
                #logIBS.info(" for SN = " + aSN + " see warranty flag = " + str(wFlag))
                aStage   = aComp['currentStage']['code']
                sensType = aComp['type'        ]['code']
                if ordPath != 'KEK':
                    if ordPath != 'CERN':
                        if haveRealMAIN:
                            logIBS.error( (" for SN = " + aSN + 
                                           " changing ordering path value from " + 
                                           ordPath + " to CERN" ) )
                        ordPath = 'CERN'
                # VF, 2021-09-06: This will only store the current location
                #   ==> Might have to cache it perhaps??
                newType  = aComp['type']['code']
                if newType != Type:
                    if Type == "": 
                        Type = newType
                    else:
                        logIBS.error(" Changing the component type in batch! Exiting")
                        return {}                    
                aLoc   = aComp['currentLocation']['code']
                BatchWaferNo = ""
                rDate = ""
                for aProp in aComp['properties']:
                    if aProp['code'] == 'ID'            : BatchWaferNo = aProp['value']
                    if aProp['code'] == 'DATE_RECEIVED' : rDate        = aProp['value']
                newMAIN = MAIN(aSN,aCode,BatchWaferNo,sensType,rDate,ordPath,wFlag,aStage,aLoc,QATC=qaTC,QACCE=qaCCE,owDATA=owData)
                newNo = int(aSN[-5:])
                insertIndx = bisect(lMAINno,newNo)
                lMAINno.insert(insertIndx,newNo)
                lMAINs.insert(insertIndx,newMAIN)
                #lMAINs.append(newMAIN)
            elif compType in comptype_HMs:
                newHM = HM(aSN,aCode)
                lHMs.append(newHM)
            elif compType in comptype_QAmini:
                newQAmini = QAmini(aSN,aCode)
                lQAminis.append(newQAmini)
            elif compType in comptype_QAchip:
                newQAchip = QAchip(aSN,aCode)
                lQAchips.append(newQAchip)
            else:
                # should never get here
                logIBS.error(" IMPOSSIBLE Error in <list_batch_objects>, compType = " + compType + ", exiting...")
                return lBatches

        # A quick counting report for things we wont' care in the future
        #logIBS.info(" BatchName, N(del), N(Tot)")
        msg += "   {:5}   {:5} ".format(nDeleted,nComp)

        # VF, 2021-09-03: We checked that this doesn't happen in practice
        if ( ( not haveRealMAIN and not haveDummyMAIN ) or
             ( haveRealMAIN and haveDummyMAIN ) ):
            msg += " ---> Weird!!!"
            logIBS.info(msg)
            continue
        # Filter 4: should only have production-style objects
        if isProto:
            msg += " ---> Non-production!"
            logIBS.info(msg)
            continue
        # now, count what looks like semi-real things
        if haveRealMAIN and not haveDummyMAIN:
            msg  += " ---> Real"
            isReal = True
        if not haveRealMAIN and haveDummyMAIN:
            msg  += " ---> Dummy"

        lWafers,lMAINs,lHMs,lQAminis,lQAchips = wash_lists(lWafers,lMAINs,lHMs,lQAminis,lQAchips)
        newBatch = Batch( aBatch, aResp['id'], isReal, Type,
                          lWafers, lMAINs, lHMs, lQAminis, lQAchips,
                          ifReturned, ifFailed, qaTC, qaCCE )
        lBatches.append(newBatch)

        msg += " ...added."
        logIBS.info(msg)
    # end of the loop over batches

    return lBatches


# want to measure "length" of the None's as well
def nItem( L ):
    if L is None:
        return 0
    else:
        return len(L)
    

# A quick counting report
def list_batch_summary( lBatches ):

    logLBS = logging.getLogger('LOG-LBS')
    nMAINreal  = 0
    nMAINdummy = 0
    nBreal  = 0
    nBdummy = 0
    first = True
    for aBatch in lBatches:
        if first:
            first = False
            logLBS.info("")
            logLBS.info(" BatchName,   Wfrs,    HMs, QAmins, QAchips; (isReal?)  MAINs, Bless, Final")

        msg = " " + aBatch.bName() 

        # Let's loop over the components that belong to the batch
        nWafers  = nItem(aBatch.lWafers() )
        nMAINs   = nItem(aBatch.lMAINs()  )
        nHMs     = nItem(aBatch.lHMs()    )
        nQAminis = nItem(aBatch.lQAminis())
        nQAchips = nItem(aBatch.lQAchips())
        nBless = 0
        nFinal = 0
        isReal  = aBatch.isReal()
        if isReal :
            nBreal += 1
            nMAINreal += nMAINs
        else:
            nBdummy += 1
            nMAINdummy += nMAINs

        lMAINs = aBatch.lMAINs()
        for aMAIN in lMAINs:
            aStage = aMAIN.stage()
            if aStage == "BLESSING"  : nBless += 1
            if aStage in FINAL_STATES: nFinal += 1

        # A quick counting report
        #logLBO.info(" BatchName, N(del), N(Tot), N(Wfr), N(Main), N(HMs), N(QAmin), N(QAchip)")
        msg += "    {:5}   {:5}   {:5}   {:5} ;".format(nWafers,nHMs,nQAminis,nQAchips)
        if isReal: msg += " (real ) ; "
        else     : msg += " (dummy) ; "
        msg += " {:5}  {:5}  {:5}".format(nMAINs,nBless,nFinal)
        logLBS.info(msg)

    # end of the loop over batches

    logLBS.info( " ___________________________________________________________________________________")
    logLBS.info( " The total of real  Batches is {:5}, with {:6} sensors".format(nBreal ,nMAINreal ) )
    logLBS.info( " The total of dummy Batches is {:5}, with {:6} sensors".format(nBdummy,nMAINdummy) )

    return


# to check that the input Json file has the right structure
def check_control_Json( iJson, iLog ):
    for K in iJson:
        if not K in ['batches','sensors']:
            iLog.error(" wrong JSON file structure: see illegal key = <" + K + ">, exiting.")
            return False

    # Now, check the substructure
    if 'batches' in iJson:
        dicB = iJson['batches']
        iLog.info(" Seeing " + str(len(dicB)) + " <batches> in the batch control file.")
        for B in dicB:
            # supposed to be the batch name
            if not check_batch_name(B):
                iLog.error(" see a wrong batch name = <" + B + ">, exiting.")
                return False
            for F in dicB[B]:
                if not F in ["QATC","QACCE","Comment","ifReturned"]:
                    iLog.error(" see a wrong batch key = <" + F + "> for batch <" + B + ">, exiting.")
                    return False
                val = dicB[B][F]
                if val is None:
                    continue
                msg_details = " for batch <" + B + ">, key = <" + F + ">, exiting."
                if F in ["QATC","QACCE"] and type(val) != bool:
                    iLog.error(" see a wrong QA value = <" + str(val) + "> " + msg_details)
                    return False
                if F in ["Comment"] and type(val) != str:
                    iLog.error(" see a wrong Comment = <" + str(val) + "> " + msg_details)
                    return False
                if F in ["ifReturned"] and type(val) != bool:
                    iLog.error(" see a wrong <returned> flag = <" + str(val) + msg_details)
                    return False
    else:
        iLog.info(" Don't see <batches> info in the control file.")

    # and sensors
    if 'sensors' in iJson:
        dicS = iJson['sensors']
        iLog.info(" Seeing " + str(len(dicS)) + " <sensors> in the batch control file.")
        for SN in dicS:
            if not checkSN_basic(SN):
                iLog.error(" see a wrong sensor SN = <" + SN + ">, exiting.")
                return False
            for F in dicS[SN]:
                if not ( F.endswith("Pass") or F == "Destination" or F == "Comment" ):
                    iLog.error(" see a wrong keyword = <" + F + "> for sensor SN = <" + SN + ">, exiting.")
                    return False
                if F.endswith("Pass"):
                    val = dicS[SN][F]
                    msg_details = "> for sensor <" + SN + ">, key = <" + F + ">, exiting."
                    if type(val) != bool:
                        iLog.error(" see a wrong value = <" + str(val) + msg_details )
                        return False
                if F == "Destination":
                    val = dicS[SN][F]
                    if type(val) != str:
                        iLog.error(" see a wrong value = <" + str(val) + msg_details )
                        return False
                    if val not in FINAL_STATES:
                        iLog.error(" see a wrong value = <" + str(val) + msg_details )
                        return False
                if F == "Comment":
                    val = dicS[SN][F]
                    if type(val) != str:
                        iLog.error(" see a wrong value = <" + str(val) + msg_details )
                        return False
    else:
        iLog.info(" Don't see <sensors> info in the control file.")

    # everthing is ok if made this far
    return True
    

def main(args):
    iBatches = args.iBatches
    iControl = args.iControl
    bDBG     = args.debug
    
    log_base_file = "DBbatches_"
    logFile = setup_logging(log_base_file)

    logMAIN = logging.getLogger('LOG-MAIN')
    logMAIN.info(" starting the log file for DB : " + logFile )
    logMAIN.info('\n *** classify_batches.py ***')
    logMAIN.info(" scriptVersion = " + scriptVersion + "\n" )

    logMAIN.info(" ------------------------------------- ")
    logMAIN.info(" Got input: "                           )
    logMAIN.info("   iBatches = " + iBatches              )
    logMAIN.info("   iControl = " + iControl              )
    logMAIN.info("   bDBG     = " + str(bDBG)             )

    # find the control file with the directives, if available
    controlJson = {}
    if len(iControl) > 0:
        if not os.path.isfile(iControl):
            logMAIN.error(" Don't see the input file <" + iControl + ">, exiting.")
            return
        try:
            with open(iControl, 'r') as iF:
                controlJson = json.load(iF)
        except Exception as e:
            logMAIN.error("  Could not open the batch control file!")
            controlJson = {}
            logMAIN.error(e)
            return

        if len(controlJson) > 0:
            logMAIN.info("\n Using control JSON file with " +
                         str(len(controlJson['batches'])) + " batches  and " +
                         str(len(controlJson['sensors'])) + " sensors. \n")
            if not check_control_Json(controlJson, logMAIN):
                return
        else:
            logMAIN.info("\n Do not have the over-writing control file to use.\n")

            
    # establish a DB client
    c = itkdb.Client()# expires_after=dict(days=1) )


    lNums = []
    # if given use it
    if len(iBatches) > 0:
        lNums = iBatches.split(",")
    else:
        # otherwise, go look them all up
        # list all batches
        logMAIN.info("getting the batch list")
        success, lNums = get_sensor_batches(c,bDBG)
        if success:
            logMAIN.info("happy: got " + str(len(lNums)) + " batches")
        else:
            logMAIN.info("unhappy")

    #with open("test_list_batches.json","w") as oF:
    #    json.dump( list(resp), oF, indent=2 )

    logMAIN.info("getting info for these batches, making our structure")
    lBatches = info_batch_structures(c,lNums, controlJson, bDBG)

    logMAIN.info("getting the batches summary")
    list_batch_summary( lBatches )

    logMAIN.info("going for the test data, filling the batch structure with it")
    success = add_test_data(c,lBatches)
    if not success:
        logMAIN.error(" Failed to find the test data! Exiting")

    logMAIN.info("\n reporting what we got for this collection of batches")
    show_batch_data(lBatches)


    return



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'to summarize the sensor information')
    parser.add_argument('-b', '--batchID', dest = 'iBatches', type = str, default = '', help = 'input batch ID')
    parser.add_argument('-c', '--controlFile', dest = 'iControl',
                        type = str, default = '', help = 'input file with control/corrections')
    parser.add_argument('-d', '--debug', dest = 'debug', action = 'store_true', help = 'debugging printout')

    args = parser.parse_args()

    main(args)
