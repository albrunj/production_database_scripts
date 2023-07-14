#!/usr/bin/python
import json
import os #noreorder

import itkdb

from __path__ import updatePath
updatePath()
from inventory2CSV import getInventory

from inventory2CSV import inventory2CSV

import postprocess_localDB

#from pprint import PrettyPrinter

fieldsS = ['code','serialNumber','componentType','type','currentStage','currentLocation','origLocation','assembled','DATE_RECEIVED','ID']
fieldsW = ['code','serialNumber','componentType','currentLocation','origLocation','assembled']
fieldsQ = ['code','serialNumber','componentType','currentStage','currentLocation','origLocation','assembled']
sensor_type_abbrevs = ['SS','LS','R0','R1','R2','R3','R4','R5','DUMMY']

testrun_codes = ['ATLAS18_HM_THICKNESS_V1','ATLAS18_CURRENT_STABILITY_V1','ATLAS18_CV_TEST_V1','ATLAS18_MAIN_THICKNESS_V1','ATLAS18_FULLSTRIP_STD_V1','ATLAS18_VIS_INSPECTION_V1','ATLAS18_IV_TEST_V1','ATLAS18_SHAPE_METROLOGY_V1','MANUFACTURING18']

required_testruns = ['ATLAS18_CV_TEST_V1','ATLAS18_VIS_INSPECTION_V1','ATLAS18_IV_TEST_V1','ATLAS18_SHAPE_METROLOGY_V1','MANUFACTURING18']

#THESE MAY CHANGE in the near future
# VF, 2021-05-01: 'POST-IRRAD TESTS' --> 'POST-IRRAD_TESTS'
# VF, 2021-05-11: code run-time error with "new" stage "PASS" => adding it to the list
#                 "RECEPTION" and "STORAGE" don't exist anymore, actually. But older items have them => to keep for now
# VF, 2021-08-02: Added the verbose mode to debug/report the process better

QA_STAGE_CODES = ['REGISTRATION','PRE-IRRAD_TESTS','IRRADIATION','POST-IRRAD_TESTS','PASS','UNKNOWN_STAGE','RECEPTION','STORAGE']

# VF, 2021-05-01: Will use a global variable to indicate the state of DB connection affairs
bad_connection = False # original goodness

def get_cdata( line, fields ):
    values = line.strip().split(',')
    cdata = {}
    for f in range(len(fields)):
        cdata[fields[f]] = values[f]
    return cdata

def get_batch_and_wafer_number(cdata):
    id = cdata['ID']
    if id == 'None': 
        return None
    id_split = id.split('-')
    batch_number = id_split[0]
    wafer_number = id_split[1].lstrip('W').lstrip('0')
    return batch_number,wafer_number

def get_testdata(c,testID):
    global bad_connection
    try:
        resp = c.get('getTestRun',json ={'testRun':testID})
    except Exception as e:
        resp = None
        if e.__class__.__name__ == 'Forbidden' :
            bad_connection = True

    return resp

def get_qastage(c,qacode):
    global bad_connection

    currentStage = 'UNKNOWN_STAGE'
    found_qa = True
    try:
        qaResp = c.get('getComponent', json = {'component':qacode})
    except Exception as e:
        found_qa = False
        if e.__class__.__name__ == 'Forbidden' :
            bad_connection = True
        
    if found_qa:
        stages = qaResp['stages']
        #if stages != None:
        if stages is not None:
            if len(stages) > 0:
                if stages[-1]['code'] in QA_STAGE_CODES:
                    currentStage = stages[-1]['code']

    return currentStage


def get_components(c,inputfilepathS,inputfilepathW,inputfilepathQ, localDB, verbose):
    global bad_connection

    if verbose: print(" in <get_components> now ")

    print("Getting components...")
    #pp = PrettyPrinter(indent = 1,width=100)
    components_blank = {'data_by_SN':{},'by_sensor':{},'by_ingot':{},
        'by_batch':{},'by_arrivalDate':{},
        'by_sensorType':{},'by_origLocation':{},
        'by_currentLocation':{},'by_shipment':{}}
    
    with open(inputfilepathS,'r') as fS:
        linesS = fS.readlines()

    with open(inputfilepathW,'r') as fW:
        linesW = fW.readlines()

    with open(inputfilepathQ,'r') as fQ:
        linesQ = fQ.readlines()

    # Let's parse 
    listW = []
    for lineind in range(2,len(linesW)):
        line = linesW[lineind]
        cdataW = get_cdata( line, fieldsW )
        SNW = cdataW['serialNumber']
        listW.append( SNW )
    print(" Got " + str( len(listW) ) + " wafers")

    # Let's parse: this will be a dictionary referenced off (unique!) SN number
    listQ = []
    dictQ = {}
    for lineind in range(2,len(linesQ)):
        line = linesQ[lineind]
        cdataQ = get_cdata( line, fieldsQ )
        SNQ = cdataQ['serialNumber']
        listQ.append( SNQ )
        stageQ = cdataQ['currentStage']
        # will redefine the weird unknown stage
        if stageQ == 'None':
            stageQ = 'UNKNOWN_STAGE'
            print(" got undefined stage for object: ", line )
        dictQ[SNQ] = stageQ
    print(" Got " + str( len(listQ) ) + " other objects")

    # DBG: check the SN lists
    print(" Wafer SNs: " + listW[0] + " " + listW[1] + " " + listW[2] + " " + listW[len(listW)-1]  )
    print(" Other SNs: " + listQ[0] + " " + listQ[1] + " " + listQ[2] + " " + listQ[len(listQ)-1]  )

    #try to load cache
    try:
        with open(localDB,'r') as f:
            components = json.load(f)
    except IOError:
        components = components_blank

    skipped_lines = []
    skipped_testruns = []
    bad_connection = False
    # Ideally, want to replace with the while loop, and to go back to the previous step, and to redo it.
    for lineind in range(2,len(linesS)):
        line = linesS[lineind]
        print("\n\n\nLine {}".format(lineind))

        # check if connection stalled
        if bad_connection :
            # c.authenticate()
            # bad_connection = False
            skipped_lines.append(lineind)
            print(" Skipping: Bad connection! ")
            continue

        cdata = get_cdata( line, fieldsS )
        SN = cdata['serialNumber']
        #if components['data_by_SN'].get(SN,None) != None:
        if components['data_by_SN'].get(SN,None) is not None:
            print(" Skipping: SN {} already loaded in components dict".format(SN))
            continue

        # VF, 2021-05-1: report the SN we are dealing with
        print( "sensorSN = {}".format(SN) )

        #check if parent exists, only process if assembled to a wafer
# VF, 2021-04-26: here is where we get a wrong message, when the damn token is expired
# VF, 2021-04-26: rename "parent" -> "wafer" below
        waferSN = SN[:8] + '5' + SN[9:]

        # VF, 2021-04-27: do it with the wafer list now
        if not ( waferSN in listW ) :
            skipped_lines.append(lineind)
            print(" Skipping: wafer not found: " + SN )
            continue
        # try:
        #     waferResp = c.get('getComponent', json = {'component':waferSN})
        # except Exception as e:
        #     # print("wafer not found",e)
        #     # print( " ___Exception Type = ", type(e) )
        #     # print( "____Exception Args = ", e.args )
        #     # print( "____Exception Itself = ", e )
        #     skipped_lines.append(lineind)
        #     print("wafer not found: " + SN )
        #     if e.__class__.__name__ == 'Forbidden' :
        #         bad_connection = True
        #     continue

        # VF, 2021-05-1: report the found wafer SN
        print( "wafer SN = {}".format(waferSN) )

        rv = get_batch_and_wafer_number(cdata)
        #if rv == None:
        if rv is None:
            skipped_lines.append(lineind)
            print(" Skipping: batch and wafer number not found")
            continue

        batchnumber,wafernumber = rv
        sensorType = cdata['type']

        #remove the uppercase keys
        arrival_date = cdata['DATE_RECEIVED']
        cdata['id'] = cdata['ID']
        del cdata['DATE_RECEIVED']
        del cdata['ID']

        cdata['batch'] = batchnumber
        cdata['waferNumber'] = wafernumber
        cdata['arrivalDate'] = arrival_date
        #print("component data:")

        if verbose: print(" sensorType = " + sensorType + ", arrivalDate = " + arrival_date )
        

        #get testruns
        any_testruns_found = True
        try:
            testruns_resp = c.get('listTestRunsByComponent', json ={'component': cdata['code']})
            #pp.pprint(testruns_resp)
        except Exception as e:
            any_testruns_found = False
            if e.__class__.__name__ == 'Forbidden' :
                bad_connection = True
            if verbose : print(e)
            print(" Skipping: did not find the test runs ")
            continue
        #if verbose: print(" got <" + str(len(testruns_resp)) + "> test runs" )

        ingotnumber = 'None'
        cdata['tests'] = {}
        for testrun_code in testrun_codes:
            required_testrun = False
            if testrun_code in required_testruns:
                required_testrun = True
            cdata['tests'][testrun_code] = {'passed':None,
                                            'required':required_testrun,
                                            'NG':None,
                                            'tested':False}
        if any_testruns_found:
            for testrun in testruns_resp:
                testrun_code = testrun['testType']['code']
                if verbose: print(" got test run code = " + testrun_code )
                testID = testrun['id']
                testData = get_testdata(c,testID)
                #if testData in DB is invalid, continue
                #if testData == None:
                if testData is None:
                    print("skipping testrun because it is None",testrun_code)
                    skipped_testruns.append((SN,testrun_code))
                    continue

                #if this type of testrun is not in testrun_codes,
                # ignore it for now.
                #if cdata['tests'].get(testrun_code) == None:
                if cdata['tests'].get(testrun_code) is None:
                    skipped_testruns.append((SN,testrun_code))
# VF, 2021-04-18: to print more stuff about the unusual test runs
#                    print("testrun {} not in testrun_codes".format(testrun_code))
                    print("SN = " + str(SN) + "testrun {} not in testrun_codes".format(testrun_code))
                    continue

                #DONT DO THIS BECAUSE THE SAME TESTRUN CAN BE PERFORMED
                #MULTIPLE TIMES ON THE SAME SENSOR AT DIFFERENT TIMES
                #if this type of testrun has already been done 
                # and it passed, skip this testrun.
                #try:
                #    if cdata['tests'][testrun_code]['passed']:
                #        print("testrun already done and passed: ",testrun_code)
                #        continue
                #except Exception:
                #    pass
                
                cdata['tests'][testrun_code]['passed'] = testrun.get('passed')
                cdata['tests'][testrun_code]['tested'] = True
                cdata['tests'][testrun_code]['id'] = testID
                
                if testrun_code == 'ATLAS18_VIS_INSPECTION_V1':
                    #just care about pass/fail for visual
                    continue
                
                results = testData['results']
                #pp.pprint(testData)
            
                if testrun_code == 'MANUFACTURING18':
                    vfd_valid,Ileak_valid = False,False
                    microdischarge_valid,percentNGstrips_valid = False,False
                    for prop in testData['properties']:
                        if prop['code'] == 'SUBSTRATE_LOT_NUMBER':
                            ingotnumber = prop['value']
                    
                    cdata['ingot'] = ingotnumber #can be 'None'
                    
                    for result in results:
                        if result['code'] == 'DEPLETION_VOLTAGE':
                            if type(result['value']) == float:
                                vfd_valid = result['value'] < 350
                            cdata['tests'][testrun_code]['vfd'] = {'value':result['value'],'NG': not vfd_valid}
                        if result['code'] == 'LEAKAGE_CURRENT_500V':
                            if type(result['value']) == float:
                                Ileak_valid = result['value'] < 10
                            cdata['tests'][testrun_code]['Ileak@500V'] = {'value':result['value'],'NG': not Ileak_valid}
                        if result['code'] == 'MICRODISCHARGE_VOLTAGE':
                            if type(result['value']) == float:
                                microdischarge_valid = result['value'] >= 500
                            cdata['tests'][testrun_code]['microdischarge'] = {'value':result['value'],'NG': not microdischarge_valid}
                        for defect in testData['defects']:
                            if defect['name'] == 'Percentage of NG Strips':	
                                #check if "0.03%" < 1%
                                percent_str = defect['description']
                                if percent_str.endswith('%'):
                                    val = float(percent_str[:-1])
                                else:
                                    try: val = float(percent_str)
                                    except ValueError: val = 0
                                percentNGstrips_valid = val < 1
                                cdata['tests'][testrun_code]['percentNGstrips'] = {'value':val,'NG': not percentNGstrips_valid}
                    
                    cdata['tests'][testrun_code]['NG'] = not (vfd_valid and Ileak_valid and microdischarge_valid and percentNGstrips_valid)


                elif testrun_code == 'ATLAS18_SHAPE_METROLOGY_V1':
                    bowing_valid = False
                    for result in results:
                        if result['code'] == 'BOWING':
                            if type(result['value']) == float:
                                bowing_valid = result['value'] < 200
                            cdata['tests'][testrun_code]['bowing'] = {'value':result['value'],'NG': not bowing_valid}
                    cdata['tests'][testrun_code]['NG'] = not bowing_valid
                            
                elif testrun_code == 'ATLAS18_CV_TEST_V1':
                    vfd_valid = False
                    for result in results:
                        if result['code'] == 'VFD':
                            if type(result['value']) == float:
                                vfd_valid = result['value'] < 350
                            cdata['tests'][testrun_code]['vfd'] = {'value':result['value'],'NG': not vfd_valid}
                        if result['code'] == 'NEFF':
                            cdata['tests'][testrun_code]['Neff'] = {'value':result['value'],'NG':False}
                    cdata['tests'][testrun_code]['NG'] = not vfd_valid 

                elif testrun_code == 'ATLAS18_FULLSTRIP_STD_V1':
                    bcm_valid,bsf_valid = False,False
                    for result in results:
                        if result['code'] == 'N_BADCLUSTER_MAX':
                            if type(result['value']) == int:
                                bcm_valid = result['value'] <= 8
                            cdata['tests'][testrun_code]['N_badcluster_max'] = {'value':result['value'],'NG': not bcm_valid}
                        if result['code'] == 'BAD_STRIP_FRACTION':
                            if type(result['value']) == float:
                                bsf_valid = result['value'] < 1.0
                            cdata['tests'][testrun_code]['bad_strip_fraction'] = {'value':result['value'],'NG': not bsf_valid}
                    cdata['tests'][testrun_code]['NG'] = not (bsf_valid and bcm_valid)

                elif testrun_code == 'ATLAS18_IV_TEST_V1': 
                    I500V_valid,vbd_valid = False,False
                    for result in results:
                        if result['code'] == 'I_500V':
                            if type(result['value']) == float:
                                I500V_valid = 0 < result['value'] < 0.1
                            cdata['tests'][testrun_code]['I_500V'] = {'value':result['value'],'NG': not I500V_valid}
                        if result['code'] == 'VBD':
                            if type(result['value']) == float:
                                vbd_valid = result['value'] > 500
                            cdata['tests'][testrun_code]['VBD'] = {'value':result['value'],'NG': not vbd_valid}
                        if result['code'] == 'RMS_STABILITY':
                            cdata['tests'][testrun_code]['RMS_stability'] = {'value':result['value'],'NG':False}
                    cdata['tests'][testrun_code]['NG'] = not (I500V_valid and vbd_valid)

                elif testrun_code == 'ATLAS18_CURRENT_STABILITY_V1':
                    #TODO: get criterion for values
                    for result in results:
                        if result['code'] == 'ABS_I_LEAK_AV':
                            cdata['tests'][testrun_code]['Abs_I_leak_av'] = {'value':result['value'],'NG':False}
                        if result['code'] == 'I_LEAK_VARIATION':
                            cdata['tests'][testrun_code]['I_leak_variation'] = {'value':result['value'],'NG':False}
                    cdata['tests'][testrun_code]['NG'] = False
                elif testrun_code == 'ATLAS18_MAIN_THICKNESS_V1':
                    av_thickness_valid = False
                    for result in results:
                        if result['code'] == 'AVTHICKNESS':
                            if type(result['value']) == float:
                                av_thickness_valid = abs(result['value']-320) < 15
                            cdata['tests'][testrun_code]['AvThickness'] = {'value':result['value'],'NG':not av_thickness_valid}
                    cdata['tests'][testrun_code]['NG'] = not av_thickness_valid
                else:

                    pass



        else:
            print("NO TESTRUNS FOUND")


        #get QA pieces
        cdata['QAchip_stageCount'] = {}
        for qastagecode in QA_STAGE_CODES:
            cdata['QAchip_stageCount'][qastagecode] = 0

# VF, 2021-04-26. This seems to be the only section of code, where the hierarchy is explored.
# And it's only expored to check out the QA pieces and the Halfmoons.  
        cdata['QAmini_stageCount'] = dict(cdata['QAchip_stageCount'])
        qachips,qaminis = 0,0

        # explicitly construct the SNs for the QA pieces and halfmoons. VF, 2021-04-26
        SN_QAmini_prim = SN[:8] + '1' + SN[9:]
        SN_QA_TCh_prim = SN[:8] + '7' + SN[9:]
        SN_QAmini_dice = SN[:7] + '11' + SN[9:]
        SN_QA_TCh_dice = SN[:7] + '17' + SN[9:]
        SN_HM          = SN[:8] + '9' + SN[9:]
        OtherObjects = [SN_QAmini_prim, SN_QA_TCh_prim, SN_QAmini_dice, SN_QA_TCh_dice, SN_HM]

        for objSN in OtherObjects: #parentResp['children']:

            # check if it exists: going after the example with wafer object. VF, 2021-04-26
            # now, do it withe the list! VF, 2021-04-27
            # if not ( objSN in listQ ) : # just skip it
            #     continue
            aStage = 'IllegalStageName'
            if objSN in dictQ :
                aStage = dictQ[objSN]
            else :
                continue

            # should get it now!
            try:
                objResp = c.get('getComponent', json = {'component':objSN})
            except Exception as e:
                print("object not found <AHTUNG!> ",e)
                if e.__class__.__name__ == 'Forbidden' :
                    bad_connection = True
                continue

            comptype = objResp['componentType']['code']
            if verbose: print(" see related component = " + comptype )
            # comptype = wchild['componentType']['code']
            # Think we don't need this - the object should exist at this point. VF, 2021-04-26
            # if objResp['component'] == None: 
            #     continue
            if comptype in ['SENSOR_QCHIP_TEST','SENSOR_TESTCHIP_MD8']:
                qachips += 1
                # qacode = objResp['code']
                # qacode = wchild['component']['code']
                # qastage = get_qastage(c,qacode)
                cdata['QAchip_stageCount'][aStage] += 1
        
            elif comptype in ['SENSOR_QAMINI_TEST','SENSOR_MINI_MD8']:
                qaminis += 1
                # qacode = objResp['code']
                # qacode = wchild['component']['code']
                # qastage = get_qastage(c,qacode)
                cdata['QAmini_stageCount'][aStage] += 1

            elif comptype in ['SENSOR_HALFMOONS','SENSOR_H_TEST']:
                halfmoons_code = objResp['code']
                # halfmoons_code = wchild['component']['code']
                # Already know it exists. VF, 2021-04-26
                # found_halfmoons = True
                # try:
                #     halfmoons_resp = c.get('getComponent', json = {'component':halfmoons_code})
                # except Exception:
                #     found_halfmoons = False

                # if found_halfmoons:
                #first, check for a thickness test
                halfmoon_tests_found = True
                try:
                    halfmoon_tests_resp = c.get('listTestRunsByComponent', json ={'component': halfmoons_code})
                except Exception as e:
                    halfmoon_tests_found = False
                    if e.__class__.__name__ == 'Forbidden' :
                        bad_connection = True

                if halfmoon_tests_found:
                    for htest in halfmoon_tests_resp:
                        testrun_code = htest['testType']['code']
                        if testrun_code == 'ATLAS18_HM_THICKNESS_V1':
                            # VF, 2021-04-18: looks like a wrong key. (There is an error thrown now.) Will change to the exact test run code.
                            #                                htest_data = cdata['tests']['ATLAS18_HM_THICKNESS']
                            # Does "cdata" pertain only to the MAIN/dummy sensors?
                            #                                htest_data = cdata['tests'][testrun_code]
                            testID = htest['id']
                            testData = get_testdata(c,testID)
#                                for result in htest_data['results']:
                            for result in testData['results']:
                                if result['code'] == 'AVTHICKNESS':
                                    cdata['tests'][testrun_code]['AvThickness'] = {'value':result['value'],'NG':False}

        cdata['QAminiCount'] = qaminis
        cdata['QAchipCount'] = qachips
        #pp.pprint(parentResp)	




#         cdata['QAmini_stageCount'] = dict(cdata['QAchip_stageCount'])
#         qachips,qaminis = 0,0
#         for wchild in parentResp['children']:
#             comptype = wchild['componentType']['code']
#             if wchild['component'] == None: 
#                 continue
#             if comptype in ['SENSOR_QCHIP_TEST','SENSOR_TESTCHIP_MD8']:
#                 qachips += 1
#                 qacode = wchild['component']['code']
#                 qastage = get_qastage(c,qacode)
#                 cdata['QAchip_stageCount'][qastage] += 1
        
#             elif comptype in ['SENSOR_QAMINI_TEST','SENSOR_MINI_MD8']:
#                 qaminis += 1
#                 qacode = wchild['component']['code']
#                 qastage = get_qastage(c,qacode)
#                 cdata['QAmini_stageCount'][qastage] += 1
#             elif comptype in ['SENSOR_HALFMOONS','SENSOR_H_TEST']:
#                 halfmoons_code = wchild['component']['code']
#                 found_halfmoons = True
#                 try:
#                     halfmoons_resp = c.get('getComponent', json = {'component':halfmoons_code})
#                 except Exception:
#                     found_halfmoons = False

#                 if found_halfmoons:
#                     #first, check for a thickness test
#                     halfmoon_tests_found = True
#                     try:
#                         halfmoon_tests_resp = c.get('listTestRunsByComponent', json ={'component': halfmoons_code})
#                     except Exception:
#                         halfmoon_tests_found = False
#                     if halfmoon_tests_found:
#                         for htest in halfmoon_tests_resp:
#                             testrun_code = htest['testType']['code']
#                             if testrun_code == 'ATLAS18_HM_THICKNESS_V1':
# # VF, 2021-04-18: looks like a wrong key. (There is an error thrown now.) Will change to the exact test run code.
# #                                htest_data = cdata['tests']['ATLAS18_HM_THICKNESS']
# # Does "cdata" pertain only to the MAIN/dummy sensors?
# #                                htest_data = cdata['tests'][testrun_code]
#                                 testID = testrun['id']
#                                 testData = get_testdata(c,testID)
# #                                for result in htest_data['results']:
#                                 for result in testData['results']:
#                                     if result['code'] == 'AVTHICKNESS':
#                                         cdata['tests'][testrun_code]['AvThickness'] = {'value':result['value'],'NG':False}

#                     #now check for qa children
#                     for hchild in halfmoons_resp['children']:
#                         hchild_comptype = hchild['componentType']['code']
#                         if hchild['component'] == None:
#                             continue
#                         if hchild_comptype in ['SENSOR_QCHIP_TEST','SENSOR_TESTCHIP_MD8']:
#                             qachips += 1
#                             qacode = hchild['component']['code']
#                             qastage = get_qastage(c,qacode)
#                             cdata['QAchip_stageCount'][qastage] += 1
#                         elif hchild_comptype in ['SENSOR_QAMINI_TEST','SENSOR_MINI_MD8']:
#                             qaminis += 1
#                             qacode = hchild['component']['code']
#                             qastage = get_qastage(c,qacode)
#                             cdata['QAmini_stageCount'][qastage] += 1
#                         else:
#                             continue
#         cdata['QAminiCount'] = qaminis
#         cdata['QAchipCount'] = qachips
#         #pp.pprint(parentResp)	





        #get shipments
        found_shipments = True
        cdata['shipments'] = []
        try:
            shipment_resps = c.get('listShipmentsByComponent', json = {'component':cdata['code']})
        except Exception as e:
            found_shipments = False
            if e.__class__.__name__ == 'Forbidden' :
                bad_connection = True

        # VF, 2021-05-01: 
        # We are done with the queries here. 
        # Let's not change the uber-structure, if the DB connection went stale during the data collection
        if bad_connection :
            # add the lines here, since the data collection calls are nested => we were not skipping the outer loop
            skipped_lines.append(lineind)
            print(" Skipping: The connection went stale, will not add data ")
            continue

        if found_shipments:
            for shipment_resp in shipment_resps:
                shipment_id = shipment_resp['id']
                cdata['shipments'].append(shipment_id)
                try: 
                    components['by_shipment'][shipment_id].append(SN)
                except KeyError: 
                    components['by_shipment'][shipment_id] = [SN]



        location = cdata['currentLocation']
        origLocation = cdata['origLocation']

        components['data_by_SN'][SN] = cdata
        components['by_sensor'][SN] = [SN]

        for by_filter,key in [('by_sensorType',sensorType),
                              ('by_ingot',ingotnumber),
                              ('by_batch',batchnumber),
                              ('by_arrivalDate',arrival_date),
                              ('by_currentLocation',location),
                              ('by_origLocation',origLocation)]:
            try:
                components[by_filter][key].append(SN)
            except KeyError:
                components[by_filter][key] = [SN]

        if verbose: print(" got the data for this SN = < " + SN + " >")
    

    # VF, 2021-05-01: let's do it at the end though... will be more of an issue later, according to the profiling.
    # VF, 2021-04-27: let's indent the file. It's hard to read/compare otherwise
    #cache components after every line - not too expensive compared to DB querying time
    if verbose: 
        dictSensors = components['data_by_SN']
        nSensors = len(dictSensors)
        print(" >>>> Got data for " + str( nSensors ) + 
              " sensors. Will dump the info to the file.")
        if nSensors > 0:
            # data for 1st SN in the dictionary
            mkey4one = next(iter(dictSensors))
            dict4one = dictSensors[mkey4one]
            print( json.dumps(dict4one, indent=2) )
        else:
            print(" No sensors in the dictionary!!")


    with open(localDB,'w') as f:
        json.dump( components, f, indent=2 )

    print("SKIPPED LINES: ",skipped_lines)
    print("SKIPPED TESTRUNS: ",skipped_testruns)
    print("Done")


def main(args):
    localDB = args.localDB
    verbose = args.verbose
    #localDB = '/home/dhamersl/db-work/production_database_scripts/strips/sensors/{}'.format(args.localDB)
    #inputfilepath = '/home/dhamersl/db-work/production_database_scripts/strips/sensors/componentInfo.csv'
    # To add other csv files: for wafer and "other" types (Halfmoon and QA pieces)
    # VF, 2021-04-27
    inputfilepathS = 'componentInfoS.csv'
    inputfilepathW = 'componentInfoW.csv'
    inputfilepathQ = 'componentInfoO.csv'
    if not ( os.path.exists(inputfilepathS) and os.path.exists(inputfilepathW) and os.path.exists(inputfilepathQ) ):
        #I wish I could use Giordon's client to do this, but there were some bugs
        if verbose : print(" Authenticating PDB session ")
        from itk_pdb.dbAccess import ITkPDSession
        session = ITkPDSession()
        code1,code2 = os.getenv('ITKDB_ACCESS_CODE1'),os.getenv('ITKDB_ACCESS_CODE2')
        #print("CODES:",code1,code2)
        session.authenticate(accessCode1=code1,accessCode2=code2)

        if verbose : print(" Getting <Sensor> inventory ")
        types = ['ATLAS18' + s for s in ['SS','LS','R0','R1','R2','R3','R4','R5']]
        types.append('ATLASDUMMY18')
        kwargs = {'project':'S','componentType':['SENSOR_S_TEST','SENSOR'],
            'type':types,'currentStage':None,'currentLocation':None,
            'institution':None,'assembled':None}
        inventoryS = getInventory(session, **kwargs)
        # VF, 2021-09-29: The inventory2CSV script changed => now need to specify the code explicitly...
        #write to inputfile
        write = ['code','serialNumber','componentType', 'type', 'currentStage', 'currentLocation', 'institution', 'assembled']
        inventory2CSV(outfile = inputfilepathS, inventory = inventoryS, write = write, properties = ['DATE_RECEIVED','ID'], overwrite = True)

        if verbose : print(" Getting <Wafer> inventory ")
        # For wafers: to omit the type and Stage
        kwargs = {'project':'S','componentType':['SENSOR_W_TEST','SENSOR_WAFER'],
            'type':None,'currentStage':None,'currentLocation':None,
            'institution':None,'assembled':None}
        inventoryW = getInventory(session, **kwargs)
        write = ['code','serialNumber','componentType', 'currentLocation', 'institution', 'assembled']
        inventory2CSV(outfile = inputfilepathW, inventory = inventoryW, write = write, overwrite = True)

        if verbose : print(" Getting <QA pieces> inventory ")
        # For others: to omit the type
        kwargs = {'project':'S','componentType':['SENSOR_QCHIP_TEST','SENSOR_TESTCHIP_MD8','SENSOR_QAMINI_TEST','SENSOR_MINI_MD8', 'SENSOR_HALFMOONS','SENSOR_H_TEST'],
            'type':None,'currentStage':None,'currentLocation':None,
            'institution':None,'assembled':None}
        inventoryQ = getInventory(session, **kwargs)
        write = ['code','serialNumber','componentType', 'currentStage', 'currentLocation', 'institution', 'assembled']
        inventory2CSV(outfile = inputfilepathQ, inventory = inventoryQ, write = write, overwrite = True)

    else:
        print("USING existing {} !!! (this might not be desired)".format(inputfilepathS))

    # VF, 2021-04-27: to crash the "session" ?
    # os.environ["ITK_DB_AUTH"] = dbAccess.authenticate(pass1,pass2)

    # Now need to set up the client here, ***after*** the ITkPDSession stuff above
    # VF, 2021-04-30: Giordon's example in the email is "itkdb.Client(cache=cache, expires_after={'days': 1})
    #                 But regardless, the expiration seems to be for the cache, not anything else...
    # need the "expires" flag for the cache longevity
    client = itkdb.Client() # expires_after=dict(days=1) )

    #query all sensors listed in inputfilepath -> create local database in components_DB
    if verbose : print(" calling the <get_components> now ")
    get_components(client,inputfilepathS,inputfilepathW,inputfilepathQ,localDB, verbose)
    if verbose : 
        print(" localDB has size of <" + str(len(localDB)) + ">")
        print(" calling the <postprocess_localDB> now ")
    postprocess_localDB.main(localDB)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Create local database of sensors')
    parser.add_argument('-d', '--localDBname', dest = 'localDB', type = str, default = 'localDB.json', help = 'Local json database name')
    parser.add_argument('-v', '--verbose', dest = 'verbose',action="store_true", help = 'To write more processing details')
    args = parser.parse_args()

    #import redis
    #from cachecontrol.caches.redis_cache import RedisCache
    #cache = RedisCache(redis.Redis(connection_pool=redis.ConnectionPool(host='itkstrips.ucsc.edu', port=6379, db=0)))
    #client = itkdb.Client(cache=cache, expires_after={'days': 1})
    # VF, 2021-04-27: move the client up, to initialize after the ITkPDSession stuff. 
    # Hope this would remove the token crashes.
    #client = itkdb.Client(expires_after=dict(days=1))
    #main(client,args)
    main(args)
