#!/usr/bin/env python
import datetime
import json
import logging
import os
import sys
import time

from __path__ import updatePath
updatePath()

import itk_pdb.dbAccess as dbAccess

_PREFIX = '20U'

#import time

#value for 'SX' will be replaced...can't determine subproject
# from just XX for dummy's
_XX =   {   'SX':'XX','SL': 'SB', 'SS': 'SB', 'S0': 'SE', 'S1': 'SE', 'S2': 'SE', 'S3': 'SE', 'S4': 'SE', 'S5': 'SE'
        }

_YY =   {   'ATLASDUMMY18':'SX','ATLAS18LS': 'SL', 'ATLAS18SS': 'SS', 'ATLAS18R0': 'S0', 'ATLAS18R1': 'S1', 'ATLAS18R2': 'S2', 'ATLAS18R3': 'S3', 'ATLAS18R4': 'S4', 'ATLAS18R5': 'S5',
            'ATLAS18LS_MECHANICAL': 'SL', 'ATLAS18SS_MECHANICAL': 'SS', 'ATLAS18R0_MECHANICAL': 'S0', 'ATLAS18R1_MECHANICAL': 'S1', 'ATLAS18R2_MECHANICAL': 'S2', 'ATLAS18R3_MECHANICAL': 'S3',
            'ATLAS18R4_MECHANICAL': 'S4', 'ATLAS18R5_MECHANICAL': 'S5', 'NARROW': 'SS', 'R0': 'S0', 'R3': 'S3', 'ATLAS17LS': 'SL', 'SENSOR_R3_M': 'S3'
        }

_DICED   = ['SENSOR_MINI_SS', 'SENSOR_MINI_LS', 'SENSOR_MINI', 'SENSOR_WBTS']
_A_DICED = '1'

_A  =   {   'ATLASDUMMY18':'0','ATLAS18LS': '0', 'ATLAS18SS': '0', 'ATLAS18R0': '0', 'ATLAS18R1': '0', 'ATLAS18R2': '0', 'ATLAS18R3': '0', 'ATLAS18R4': '0', 'ATLAS18R5': '0',
            'ATLAS18LS_MECHANICAL': '9', 'ATLAS18SS_MECHANICAL': '9', 'ATLAS18R0_MECHANICAL': '9', 'ATLAS18R1_MECHANICAL': '9', 'ATLAS18R2_MECHANICAL': '9', 'ATLAS18R3_MECHANICAL': '9',
            'ATLAS18R4_MECHANICAL': '9', 'ATLAS18R5_MECHANICAL': '9', 'NARROW': '6', 'R0': '6', 'R3': '9', 'ATLAS17LS': '6', 'SENSOR_R3_M': '9'
        }

# the items below are the "dummy" components for DB verification
_B =    {   'SENSOR': '0', 'SENSOR_MINI_MD8': '1', 'SENSOR_MINI_SS': '2', 'SENSOR_MINI_LS': '3', 'SENSOR_MINI': '4', 'SENSOR_WAFER': '5', 'SENSOR_MD8': '6',
            'SENSOR_TESTCHIP_MD8': '7', 'SENSOR_WBTS': '8', 'SENSOR_HALFMOONS': '9',
            'SENSOR_QCHIP_TEST': '7', 'SENSOR_QAMINI_TEST':'1',
            'SENSOR_W_TEST': '5','SENSOR_S_TEST':'0','SENSOR_H_TEST':'9'
        }


# VF, 2021-06-11: Note that this process doesn't work for the real halfmoons. Their "type" does not define their SN.
# Usually this is not a problem, so will assume being supplied by "real" types in these function calls.
# (SN transformation from MAIN to halfmoons is trivial.)
def makeSN_basic(component_type, sensor_type, wafer_number):
    #create initial SN that might not be correct for qa pieces or dummys
    sn = _PREFIX
    yy = _YY[sensor_type]
    xx = _XX[yy]
    sn += xx
    sn += yy
    if component_type in _DICED:
        sn += _A_DICED
    else:
        sn += _A[sensor_type]
    sn += _B[component_type]
    sn += wafer_number
    return sn

def makeSN(component_type, sensor_type, wafer_number,
           dummy=False, subproject=None, qa_piece=False):

    #modify SN from makeSN_basic() for special cases (if dummy or qa piece)
    #if dummy, must pass subproject to change 'XX' to an actual XX value (from the dictionary above)

    SN = makeSN_basic(component_type, sensor_type, wafer_number)

    #20 U XX YY AB 00000

    A = "0" #default (SN[7])

    #YY = "SX" for dummy
    if dummy:
        #change XX to passed subproject, and set YY = "SX"
        if subproject == None:
            raise Exception("Subproject is none when trying to register a dummy component!")
        SN = SN[:3] + subproject + "SX" + SN[7:]


    if qa_piece:
        ###################
        #check if this qa piece has already been registered
        print("Checking if QA piece {} has already been registered...".format(SN))
        this_qa_data = getData(SN)
        if this_qa_data != None:
            print("This exact SN has already been registered.")
            A = "1" #set A=1 to not conflict with registered qa piece
            ########################
            #check if A=1 has been registered too
            SN_A1 = SN = SN[:7] + "1" + SN[8:]
            print("Checking if QA piece with A=1 (SN:{}) has already been registered...".format(SN_A1))
            if getData(SN_A1) != None:
                raise Exception("Two QA pieces (A=0 and A=1) from same wafer have already been registered!")
            else:
                print("QA piece with A=1 not yet registered. Using new SN with A=1: '{}'".format(SN_A1))
        else:
            print("QA piece (SN:{}) not yet registered...".format(SN))
            A = "0"

        #modify SN with new value of A
        SN = SN[:7] + A + SN[8:]

    return SN


# VF, 2021-09-08: Don't want to check for the QA pieces existence anymore...
# (Should be able to assume they don't exist for the production wafers - same as other pieces.)
def makeSN_nocheck(component_type, sensor_type, wafer_number,
                   dummy=False, subproject=None, qa_piece=False):

    #modify SN from makeSN_basic() for special cases (if dummy or qa piece)
    #if dummy, must pass subproject to change 'XX' to an actual XX value (from the dictionary above)

    SN = makeSN_basic(component_type, sensor_type, wafer_number)

    #20 U XX YY AB 00000

    A = "0" #default (SN[7])

    #YY = "SX" for dummy
    if dummy:
        #change XX to passed subproject, and set YY = "SX"
        if subproject == None:
            raise Exception("Subproject is none when trying to register a dummy component!")
        SN = SN[:3] + subproject + "SX" + SN[7:]


    if qa_piece:
        A = "0"
        #modify SN with new value of A
        SN = SN[:7] + A + SN[8:]

    return SN


# VF, 2021-06-04: to compose the (parent) wafer SN from the one from MAIN or Haflmoon
def makeSN_wafer(SN):
   #20 U XX YY AB 00000
    A = '0'
    B = '5'
    wSN = SN[:7] + A + B + SN[9:]
    return wSN


# VF, 2021-09-09: to compose the MAIN sensor SN from other components.
# Will only care about the production versions (no proto/mechanicals/etc)
def makeSN_sensor(SN):
   #20 U XX YY AB 00000
    A = '0'
    B = '0'
    sSN = SN[:7] + A + B + SN[9:]
    return sSN


# VF, 2021-09-09: to check if this is halfmoon
def isHalfmoon(SN):
    #20 U XX YY AB 00000
    B = SN[8]
    if B == '9':
        return True
    return False


# VF, 2021-07-20: extract the sensor type from SN
def type_from_SN(SN):
    snType = SN[5:7]
    if snType == "SS" : return "ATLAS18SS"
    if snType == "SL" : return "ATLAS18LS"
    if snType == "S0" : return "ATLAS18R0"
    if snType == "S1" : return "ATLAS18R1"
    if snType == "S2" : return "ATLAS18R2"
    if snType == "S3" : return "ATLAS18R3"
    if snType == "S4" : return "ATLAS18R4"
    if snType == "S5" : return "ATLAS18R5"
    if snType == "SX" : return "ATLASDUMMY18"

    # Should never get here
    return "TypeError"


# VF, 2021-08-19: get min/max for the strip segments and strip numbers
# ****************************************


# VF, 2021-08-19: check if this is a barrel SN
def barrel_SN(SN):
    snType = SN[4:5]
    if snType == "B":
        return True
    else:
        return False


def getData(SN):
    try:
        data = dbAccess.extractList("getComponent",
                                    method = "GET",
                                    data = {'component':SN})
    except:
        print("Request failed:")
        import traceback
        traceback.print_exc()

        return None

    return data



# VF, 2021-06-03: lifted from "registerQA", seems generic enough
def get_batch_and_wafer_numbers(vpx):
    #always 5 digits '#####'
    vpx_split = vpx.split('-')
    batch_number = vpx_split[0]
    wafer_number = vpx_split[1][1:]
    # VF. 2021-08-25: use the built-in function instead
    wafer_number = wafer_number.zfill(5)
    #if len(wafer_number) < 5:
    #	wafer_number = "0"*(5-len(wafer_number)) + wafer_number
    return batch_number,wafer_number


# VF, 2021-08-31: Let's do a basic generic check of the batch name
def check_batch_name(VPX):
    # to remove the trailing newlines and spaces
    locVPX = VPX.strip()

    if ( ( locVPX.startswith("VPX") or locVPX.startswith("VPA") )
         and 
         len(locVPX) == 8 ) :
        return True

    return False


# VF, 2021-05-10: Let's do a basic generic check of the SN number
def checkSN_basic(aSN):
    # to remove the trailing newlines and spaces
    locSN = aSN.rstrip()

    # to extract prefix (1st 3 positions are sacred!)
    aPref = locSN[:3]

    #print(" checkSN_basic: aPref = " + aPref + ", equal to ini? " + str(aPref==_PREFIX) )
    #print(" checkSN_basic: name " + locSN + " is of length: " + str(len(locSN)) )
    if aPref == _PREFIX and len(locSN) == 14 :
        # print(" checkSN_basic: returning " + str(True) )
        return True

    # otherwise it's bad
    #print(" checkSN_basic: returning " + str(False) )
    return False


# VF, 2021-08-19: unified check of basic info
def checkSN_BWNo_type( SN, BWNo, sType ):
    logging.getLogger()
    if not checkSN_basic : 
        logging.error(" SN = <" + SN + "> is misformatted")
        return False

    # Check the batch-wafer number format
    if ( ( BWNo[:3] != "VPX" and BWNo[:3] != "VPA" ) or
         BWNo[8]  != "-"   or
         BWNo[9]  != "W"   or
         len(BWNo) < 12    or
         len(BWNo) > 15 ) :
        logging.error(" batch-wafer number = <" + BWNo + "> is misformatted")
        return False

    # Check that the type is allowed
    if sType not in _YY:
        logging.error(" sensor type = <" + sType + "> is not allowed")
        return False

    # Check that SN and the sensor type are compatible
    if type_from_SN(SN) != sType:
        logging.error(" SN = <" + SN + "> and sensorType <" + sType + "> don't match")
        return False

    # check the SN and batch-wafer number compatibility
    last5SN = SN[-5:]
    lastNBW = BWNo.split("W")[1]
    wSN = int(last5SN)
    wBW = int(lastNBW)
    if wSN != wBW :
        logging.error(" SN = <" + SN + "> and batch-wafer number <" + BWNo + "> don't match")
        return False
   
    return True


# VF, 2021-06-03: a typical call to find the object code
def get_code(c,SN,iDBG=False):
    try:
        Resp = c.get('getComponent', json = {'component':SN})
    except Exception as e:
        print("object not found: " + SN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_code>")
        if iDBG:
            print(e)
        return True, {}

    objCode = Resp['code']
    return False, objCode


# VF, 2021-08-25: want the full response for more info
def get_resp(c,SN,iDBG=False):
    try:
        Resp = c.get('getComponent', json = {'component':SN})
    except Exception as e:
        print("object not found: " + SN )
        if iDBG:
            print(e)
        return False, {}

    return True, Resp


# VF, 2021-06-23: a call to find the codes for a list of components
def get_codes_bulk(c,listSNs,iDBG=False):
    error = False  # original goodness
    try:
        Resp = c.get('getComponentBulk', 
                     json = {'component' : listSNs,
                             'outputType': "object",
                             'force': True })
    except Exception as e:
        error = True
        print("Bulk Components not found... " )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_codes_bulk>")
        if iDBG:
            print(e)
        return error,[]

    listObjCodes = []
    for anObj in Resp:
        objCode = anObj['code']
        listObjCodes.append( objCode )

    return error, listObjCodes


# VF, 2021-09-09: get bulk component info, full....
# VF, 2021-09-24: added iterations, since having the timeouts
def get_components_bulk(c,lCodes):
    logGCB = logging.getLogger('LOG-GCB')
    aResp = {}
    # we are having the weird timouts
    nTimeout = 5
    nIter = 0
    while nIter < nTimeout:
        nIter += 1

        success = True
        ServerError = False
        try:
            aResp = c.get( 'getComponentBulk', 
                           json = {'component'  : lCodes,
                                   'outputType' : "full",
                                   'force' : True } )
        except Exception as e:
            logGCB.error("Bulk Components not found..." )
            logGCB.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logGCB.info(" exc_type =         " + str(exc_type) )
            logGCB.info(" fname    =         " + str(fname)    )
            logGCB.info(" exc_tb.tb_lineno = " + str(exc_tb.tb_lineno) )
            # check if we got our timeout, damn it
            str_type = str(exc_type)
            if "ServerError" in str_type:
                ServerError = True
                logGCB.info(" Seeing the ServerError, assume it is a timeout.")

            success = False

        if success or not ServerError:
            break
        else:
            if nIter < nTimeout:
                logGCB.info(" will sleep for 30 sec, then re-issue the request.")
                time.sleep(30)
            else:
                logGCB.info(" already issued " + str(nTimeout) + " queries, will stop!")

    return success, aResp


# VF, 2021-07-26: similar to the above, except:
# - with an optional site filter
# - returning {SN,code} dictionary
def get_codes_bulk_filter(c,listSNs,codeSite,iDBG=False):
    error = False  # original goodness
    try:
        Resp = c.get('getComponentBulk', 
                     json = {'component' : listSNs,
                             'outputType': "object",
                             'force': True })
    except Exception as e:
        error = True
        print("Bulk Components not found... " )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_codes_bulk>")
        if iDBG:
            print(e)
        return error,{}

    listObjCodes = {}
    #import json
    #with open( "test_structure.txt", 'w') as oF:
    #    json.dump( Resp, oF, indent=2 )
    for anObj in Resp:
        objCode = anObj['code']
        objSN   = anObj['serialNumber']
        if len(codeSite) == 0 : # no filter
            listObjCodes[objCode] = objSN
        else:
            # add those at the expected location:
            #   only the code is available for the fast/forced call done above
            #   hence need to compare to the (previously obtained) institute code
            currSite = anObj['currentLocation']
            if currSite == codeSite : 
                listObjCodes[objCode] = objSN

    return error, listObjCodes


# VF, 2021-07-26: as per above, sometimes need to get to know the institute's code
def get_inst_code(c, inst_handle, iDBG=False):
    try:
        Resp = c.get( 'getInstitutionByCode',
                      json = {'code': inst_handle} )
    except Exception as e:
        print("Error calling <GetInstitutionByCode> from get_inst_code, inst_handle = " + inst_handle )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_inst_code>")
        if iDBG:
            print(e)
        return False, ""

    #import json
    #print( json.dumps( Resp, indent=2 ) )
    instCode = Resp['id']
    return True, instCode


# VF, 2021-06-20: to get the batch information
def get_batch_byNumber(c,bNumber,iDBG=False,bType="SENSORS_PROD_BATCH"):
    error = False  # original goodness
    Resp = {}
    try:
        Resp = c.get( 'getBatchByNumber', 
                      json = {'project'  : "S",
                              'batchType': bType,
                              'number'   : bNumber} )
    except Exception as e:
        error = True
        print("Batch not found, number = " + bNumber )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_batch_info>")
        if iDBG:
            print(e)
        return (error,Resp)

    return error, Resp


# VF, 2021-10-07: to set the batch property
def set_batch_prop(c,bID, prop, val, aLog ):
    succ = True  # original goodness
    Resp = {}
    try:
        Resp = c.post( 'setBatchProperty', 
                       json = { 'id'   : bID,
                                'code' : prop,
                                'value': val } )
    except Exception as e:
        succ = False
        aLog.error("Issues updating Batch = <" + bID + ">, " +
                   "prop = <" + prop + ">, val = <" + str(val) + ">" )
        aLog.error(e)
        return (succ,Resp)

    return succ, Resp


def get_testdata(c,testID):
    success = True  # original goodness
    try:
        resp = c.get('getTestRun',json ={'testRun':testID})
    except Exception as e:
        success = False
        resp = None
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_testdata>")

    return success, resp


# VF, 2021-09-09: need the bulk call for the test data as well
# VF, 2021-09-24: added iterations, since having the timeouts
def get_testdata_bulk(c,lTestIDs):
    logGTB = logging.getLogger('LOG-GTB')

    tResp = {}
    # we are having the weird timouts
    nTimeout = 5
    nIter = 0
    while nIter < nTimeout:
        nIter += 1

        success = True
        ServerError = False
        try:
            tResp = c.get( 'getTestRunBulk', 
                           json = {'testRun' : lTestIDs} )
        except Exception as e:
            logGTB.error("Bulk TestRuns not found..." )
            logGTB.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logGTB.info(" exc_type =         " + str(exc_type) )
            logGTB.info(" fname    =         " + str(fname)    )
            logGTB.info(" exc_tb.tb_lineno = " + str(exc_tb.tb_lineno) )
            # check if we got our timeout, damn it
            str_type = str(exc_type)
            if "ServerError" in str_type:
                ServerError = True
                logGTB.info(" Seeing the ServerError, assume it is a timeout.")

            success = False

        if success or not ServerError:
            break
        else:
            if nIter < nTimeout:
                logGTB.info(" will sleep for 30 sec, then re-issue the request.")
                time.sleep(30)
            else:
                logGTB.info(" already issued " + str(nTimeout) + " queries, will stop!")


    return success, tResp


def get_testruns_4_comp(c, objCode):
    any_testruns_found = True
    try:
        testruns_resp = c.get('listTestRunsByComponent', json ={'component': objCode })
    except Exception as e:
        any_testruns_found = False
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_testruns_dict>")

    return any_testruns_found, testruns_resp


# VF, 2021-08-25: do need this stuff...
def set_stage(c,code,stage, DBG=False):
    success = True
    try:
        resp = c.post('setComponentStage', 
                      json = {'component': code,
                              'stage'    : stage,
                              'comment'  : "setting to new stage"})
    except Exception as e:
        success = False
        print(" Error setting stage <{}> for component <{}>".format(stage,code))
        print(e)
    if DBG:
        logging.getLogger()
        logging.debug( json.dumps(resp, indent=2) )

    return success


#VF, 2021-08-09: the component registration call
def register_item(c, payload, DBG=False):
    # register the component
    logging.getLogger()
    Resp = {}
    try:
        Resp = c.post('registerComponent', json = payload)
    except Exception as e:
        logging.error("In <register_item>: could not register the component. ")
        logging.error("post operation failed: " + payload['serialNumber'] )
        logging.error("Error = ", exc_info=e)
        return False, Resp

    # want to check the response
    if DBG:
        logging.debug("//--- component registration response")
        logging.debug( json.dumps(Resp, indent=2) )

    return True, Resp


# VF, 2021-08-09: the assembly/disassembly
def make_assembly_history(c, pCode, cCode, DBG = False ):
    # then to assemble the new object and the wafer ---------------------------
    logging.getLogger()
    try:
        aResp = c.post('assembleComponent', json = { 'parent': pCode, 'child': cCode } )
    except Exception as e:
        logging.error("post operation failed (assemble): " + pCode )
        logging.error(" in make_assembly_history: could not assemble the components ")
        logging.error(" Error is ", exc_info=e)
        return False

    if DBG: print(" ...assembled!")
    # want to check the response
    if DBG:
        logging.debug("//--- assembly result")
        logging.debug( json.dumps(aResp, indent=2) )
    

    # then to disassemble -----------------------------------------------------
    # first wait - the DB may not be ready after the assembly
    # VF, 2021-08-10: was the sleep statement below a bug??
    #time.sleep(1.0)

    try:
        dResp = c.post('disassembleComponent', 
                       json = { 'parent': pCode, 'child': cCode, 'trashed': False } )
    except Exception as e:
        logging.error("post operation failed (disassemble): " + pCode )
        logging.error(" in make_assembly_history: could not disassemble the component ")
        logging.error(" Error is ", exc_info=e)
        return False

    if DBG: print(" ...dis-assembled!")
    # want to check the response
    if DBG:
        logging.debug("//--- dis-assembly result")
        logging.debug( json.dumps(dResp, indent=2) )

    return True


# VF, 2021-06-27: to upload a json file for a test run
# VF, 2021-08-09: add logger (if it exists)
def upload_testrun(c,test_data):
    try:
        Resp = c.post('uploadTestRunResults', json = test_data )
    except Exception as e:
        # Check if the logger has handles (Therefore it's alive).
        if logging.getLogger().hasHandlers() :
            logging.error("There was an issue with uploading the test results" )
            logging.error(" Error is ", exc_info=e)
            return False, {}
        else: # traditional printout
            print("There was an issue with uploading the test results" )
            if e.__class__.__name__ == 'Forbidden' :
                print("got bad connection in <upload_testrun>")
                print(e)
            return False, {}

    return True, Resp


#  Upload individual image for a relevant test run parameter
# 2021-07-21, VF
def add_image_to_test( c, testID, ParamType, Image ):

    f = open( Image, "rb")
    c.post( "createBinaryTestRunParameter", 
            data = { "testRun": testID,
                     "parameter": ParamType },
            files = dict(data=f)
    )
    # files = { "data": ( Image, f, Image.split(".")[-1] ) }
    f.close()

    # The code from PB software:
    #
    # client.post("uploadTestRunResults", json={'component': powerboard.code, 'runNumber': runNumber, 'passed': passed, 'date': str(datetime.now().strftime('%d.%m.%Y %H:%M')), 'institution':'LBNL_STRIP_POWERBOARDS', 'testType': "PICTURE", 'results': {"PICTURE": "undefined", "COMMENT": comment}})
    # testRun = pwbdbtools.getLatestTestRunByComponent(client, component=powerboard.code, testType=["PICTURE"], stage=[powerboard.currentStage])
    # print("Uploading image to testRun: "+testRun['id'])
    # client.post("createBinaryTestRunParameter", data=dict(testRun=testRun['id'], parameter="PICTURE"), files={'data': (filename, open(filename, mode='rb'), filename.split(".")[-1])})
    # print("Image uploaded, check it here: https://itkpd-test.unicorncollege.cz/testRunView?id="+testRun['id'])

    return 


# VF, 2021-09-09: need code to list all batches
# VF, 2021-09-20: involving the dummy sensor batches becomes problematic...
#                 the other calls don't include the list option
def get_sensor_batches(c, iDBG):
    logGB_ = logging.getLogger('LOG-GB_')
    success = True
    aResp = {}
    try:
        aResp = c.get( 'listBatches', 
                       json = {'filterMap' : { 'project': 'S',
                                               'batchType' : ['SENSORS_PROD_BATCH'] },
                                                #'BATCH_TEST_SENSOR'] },
                                                #'state' : 'ready' },
                               'outputType' : "object"} )
                               #'outputType' : "full"} )
    except Exception as e:
        success = False
        logGB_.error("listBatches did not work..." )
        if iDBG:
            logGB_.debug(e)
        return (success, aResp )

    lNums = []
    for aBatch in aResp:
        lNums.append( aBatch['number'] )

    return success, lNums

#______________________________________________________________________
# Stuff with sensor-specific numerology
#
# VF, 2021-08-20, provide the maximum segment number per sensor type
def maxSegNo(sType):
    if sType == "ATLAS18SS"    : return 4
    if sType == "ATLAS18LS"    : return 2
    if sType == "ATLAS18R0"    : return 4
    if sType == "ATLAS18R1"    : return 4
    if sType == "ATLAS18R2"    : return 2
    if sType == "ATLAS18R3"    : return 4
    if sType == "ATLAS18R4"    : return 2
    if sType == "ATLAS18R5"    : return 2
    if sType == "ATLASDUMMY18" : return 4

    # should not get here
    return -1

    
# VF, 2021-08-20, provide the maximum segment number per sensor type
def maxStripNo(segNo, sType):
    if sType == "ATLAS18SS"    : return 1281
    if sType == "ATLAS18LS"    : return 1281
    if sType == "ATLAS18R0" : 
        if segNo == 1 or segNo == 2 : return 1025
        if segNo == 3 or segNo == 4 : return 1153
    if sType == "ATLAS18R1" : 
        if segNo == 1 or segNo == 2 : return 1281
        if segNo == 3 or segNo == 4 : return 1409
    if sType == "ATLAS18R2"    : return 1537
    if sType == "ATLAS18R3"    : return 897
    if sType == "ATLAS18R4"    : return 1025
    if sType == "ATLAS18R5"    : return 1153
    if sType == "ATLASDUMMY18" : return 1537

    # should not get here
    return -1


# VF, 2021-08-20, provide the maximum segment number per sensor type
# Assume the count from *zero*
def nTotalStrips(sT):
    if sT in ["ATLAS18R0", "ATLAS18R1"] :
        return ( maxStripNo(1,sT)+1 + 
                 maxStripNo(2,sT)+1 + 
                 maxStripNo(3,sT)+1 + 
                 maxStripNo(4,sT)+1 )
    else:
        return ( maxSegNo(sT) * (maxStripNo(1,sT)+1) )
  
    # should not get here
    return -1


# VF, 2021-08-20, check if the strip {segment,stripNo} are within the expected bouds
def in_bounds(segNo, stripNo, sType):
    # check on the segNo - if b/w 1 and max for the type
    # historical compatibility with the dummy sensor's fake data generation
    minSeg = 1
    if sType == "ATLASDUMMY18": minSeg = 0

    if not ( minSeg <= segNo <= maxSegNo(sType) ):
        return False

    # check on the stripNo - if b/w 0 and max for the segNo, type
    if not ( 0 <= stripNo <= maxStripNo(segNo,sType) ):
        return False

    return True


# VF, 2021-08-19, function for checking the strip data, mostly from Derek's "check_non_regex_value"
def check_strips_bounds(logRVD,filename,zKey,zVal,sType,listS):
    goodData = True
    nBadStrip = 0
    if zVal not in ["none","-"]:

        if len(zVal.split('-')) > 2: #multiple n-m pairs
            try:
                if zVal[0] == '"': zVal = zVal[1:-1]
                vlist = zVal.split(',')
                for nm in vlist[:-1]:
                    a,b = nm.split('-')
                    n,m = int(a),int(b)
                    nBadStrip += 1
                    listS.append((n,m))
                    if not in_bounds(n,m,sType):
                        goodData = False
                        logRVD.error("in file {} see out of bound strip ".format(filename) + 
                                     " (seg,strip) = ({},{}) ".format(n,m) )
                        logRVD.error(" from  (key,value) = ({},{}) ".format(zKey,zVal) )
                        #if not (minn <= int(n) <= maxn and minm <= int(m) <= maxm):
                #last element of vlist can be '' so check specifically for that
                if vlist[-1] != '': #happens when line ends with a comma
                    a,b = vlist[-1].split('-')
                    n,m = int(a),int(b)
                    nBadStrip += 1
                    listS.append((n,m))
                    if not in_bounds(n,m,sType):
                        goodData = False
                        logRVD.error("in file {} see out of bound strip ".format(filename) + 
                                     " (seg,strip) = ({},{}) ".format(n,m) )
                        logRVD.error(" from  (key,value) = ({},{}) ".format(zKey,zVal) )
            except Exception as e:
                goodData = False
                logRVD.error("in file {} see bad defect formatting ".format(filename) + 
                             " (key,value) = ({},{}) ".format(zKey,zVal) )
                logRVD.error(e)

        else: #single n-m pair
            try:
                a,b = zVal.split('-')
                n,m = int(a),int(b)
                nBadStrip += 1
                listS.append((n,m))
                if not in_bounds(n,m,sType):
                    goodData = False
                    logRVD.error("in file {} see out of bound strip ".format(filename) + 
                                 " (seg,strip) = ({},{}) ".format(n,m) )
                    logRVD.error(" in  (key,value) = ({},{}) ".format(zKey,zVal) )
            except Exception as e:
                goodData = False
                logRVD.error("in file {} see bad defect formatting ".format(filename) + 
                             " (key,value) = ({},{}) ".format(zKey,zVal) )
                logRVD.error(e)

    return goodData, nBadStrip

#______________________________________________________________________
# Completely generic stuff
# VF, 2021-08-19, function for finding the longest consecutive strip set 
#                 from the list of pairs [(segment,strip)]
def consecutive_strips(listS):
    if len(listS) == 0:
        return 0
    else:
        nCons = 1 # in case of lists with only 1 element (which we don't loop over below)

    # make channel lists for all (up to 4) segments
    l1 = []
    l2 = []
    l3 = []
    l4 = []
    for (seg,strip) in listS:
        if seg == 1: l1.append(strip)
        if seg == 2: l2.append(strip)
        if seg == 3: l3.append(strip)
        if seg == 4: l4.append(strip)

    # make unique sorted channels, loop over them, find consecutive things
    for aL in [l1,l2,l3,l4]:
        uniqL = list(set(aL))
        uniqL.sort()
        maxLoc = -10000
        if len(uniqL) > 1:
            for i,el in enumerate(uniqL):
                if i==0: # initialize
                    maxLoc = 1
                else:    # process the regions
                    if el-uniqL[i-1] == 1: # still connected => continue
                        maxLoc += 1
                        if maxLoc > nCons: nCons = maxLoc
                    else:                  # form a new one
                        maxLoc = 1
                #print("i = " + str(i) + ", el = " + str(el) + ", maxLoc = " + str(maxLoc) + ", nCons = " + str(nCons))
            # end loop over the segment
        #print("maxLoc = " + str(maxLoc) + ", nCons = " + str(nCons))
        # end check if the segment has more than 1
    # end of loop over the 4 segments

    return nCons


# VF, 2021-08-24: we seem to be doing this very often...
def setup_logging(log_file_base):
    startT = datetime.datetime.now()
    startS = startT.strftime("%Y-%m-%d_%Hh-%Mm-%Ss")
    logFile = log_file_base + startS + ".txt"

    # set up logging to file; will print the log origin ("name")
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)-8s: %(message)s',
                        filename=logFile,
                        filemode='w')
    # define a Handler which writes DEBUG messages or higher
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('  %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    return logFile



if __name__ == '__main__':
    print(makeSN('SENSOR', 'ATLAS18R0', '12345'))
    print(makeSN('SENSOR', 'ATLAS17LS', '98765'))
    print(makeSN('SENSOR_WAFER', 'ATLAS18LS', '12345'))
    print(makeSN('SENSOR_MINI', 'ATLAS18SS', '98765'))
