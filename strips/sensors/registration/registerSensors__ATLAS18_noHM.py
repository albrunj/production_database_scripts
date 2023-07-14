#!/usr/bin/env python
import argparse
import datetime
import json
import logging
import os
import re
import sys

import itkdb
from __path__ import updatePath
updatePath()

from requests.exceptions import RequestException

#import itk_pdb.dbAccess as dbAccess
#from itk_pdb.dbAccess import ITkPDSession
# try:
#     from requests_toolbelt.multipart.encoder import MultipartEncoder
# except Exception:
#     print("module 'requests_toolbelt' not found. Install: 'pip install requests_toolbelt'")
#     sys.exit()
from HPK_data_checks.error_checker import Data
from HPK_data_checks.check         import expected_keys_reduced_EC
from HPK_data_checks.check         import expected_keys_reduced_barrel
from HPK_data_checks.check_non_regex_value import check_non_regex_value
from strips.sensors.SensorSNUtils import makeSN_nocheck
from strips.sensors.SensorSNUtils import checkSN_BWNo_type
#from strips.sensors.SensorSNUtils import get_code
from strips.sensors.SensorSNUtils import get_resp
from strips.sensors.SensorSNUtils import set_stage
from strips.sensors.SensorSNUtils import register_item
from strips.sensors.SensorSNUtils import make_assembly_history
from strips.sensors.SensorSNUtils import upload_testrun
from strips.sensors.SensorSNUtils import check_strips_bounds
from strips.sensors.SensorSNUtils import consecutive_strips
from strips.sensors.SensorSNUtils import barrel_SN
from strips.sensors.SensorSNUtils import nTotalStrips
from strips.sensors.SensorSNUtils import setup_logging
from strips.sensors.SensorSNUtils import get_batch_and_wafer_numbers

#from pprint import PrettyPrinter

#pp = PrettyPrinter(indent = 1, width = 200)

#------------------------------------------------------------
# Matt Basso, 2019: Created.
#
# Derek Hamersly, Fall 2020: Added the check of the input data integrity
# 
# VF, 2021-08-05, changes:
# - copied over the code changes from *_noHM.py script (dated 2021-06-13 there): 
# - added dis-assembly of the components
# - added the test date (made up on the fly from the "Test Date ..." property)
# - adjusted batch code for dummy pieces
# - added DATE_RECEIVED and ID for the halfmoons and QA pieces
#
# VF, 2021-08-09, changes:
# - itkdb conversion
# - added logging
# VF, 2021-08-14/15: changes:
# - factorized the input data reading/checks from DB
# - added extra verification
#
#------------------------------------------------------------
#scriptVersion = 1 # used for pre-production
#scriptVersion = 2 # after checking addition
#scriptVersion = 3 # after conversion to itkdb (July 2021)
scriptVersion = 4

badStripTypes = ["Oxide pinholes","Metal Shorts","Metal Opens","Implant Shorts","Implant Opens","Microdischarge strips","Bias resistor disconnection"]

#if __name__ == '__main__':
#    from __path__ import updatePath
#    updatePath()


def check_type(subtype, regex):
    match = re.search(regex, subtype)
    if match:
        return True
    return False

def get_sensor_data(file, data):

    # logger area for this function
    #logGSD = logging.getLogger('LOG-GSD')

    lines = [l.strip() for l in file.readlines()]
    for i, l in enumerate(lines):
        # Skip blank lines
        if l == '':
            continue
        # Pay attention to these headers
        elif l.startswith('%'):
            section = l[1:]
            data[section] = {}
            ii = i + 1
            while True:
                # If we reach a blank line, we have finished parsing the section
                if ii == len(lines):
                    #reached end of file
                    break

                if lines[ii] == '':
                    break
                # If a line starts with a #...
                elif lines[ii].startswith('#'):
                    # ...and pertains to IV data, we collect this info
                    if lines[ii] == '#IV':
                        data['RAWDATA']['IV Characteristics (A)'] = {}
                        iii = ii + 1
                        while True:
                            ''' Sometimes see:
                            IV Characteristics (A)
                            #IV
                            #IV
                            20  1.37E-07
                            And sometimes see:
                            IV Characteristics (A)
                            #IV
                            20  1.37E-07 '''
                            if lines[iii] != '#IV':
                                break
                            else:
                                iii += 1
                                continue
                        while True:
                            if lines[iii] == '':
                                ii = iii
                                break
                            else:
                                lsplit = lines[iii].split()
                                if len(lsplit) == 2:
                                    k, v = lsplit
                                    k, v = k.strip(), v.strip()
                                    data['RAWDATA']['IV Characteristics (A)'][k] = v
                            iii += 1
                            continue
                else:
                    lsplit = lines[ii].split('\t')
                    if len(lsplit) == 2:
                        k, v = lsplit
                        k, v = k.strip(), v.strip()
                        # Special handling for defects spilling onto new lines:
                        if section == 'DEFECT':
                            iii = ii + 1
                            while True:
                                if all(p.strip().isdigit() for p in re.split(r',|-', lines[iii]) if p != ''):
                                    v += lines[iii]
                                    iii += 1
                                    continue
                                else:
                                    break
                            v = ', '.join([p.strip() for p in v.split(',') if p != ''])
                        data[section][k] = v
                ii += 1
                continue
        # Special handling for ID stability lines
        elif l == 'Id stability test @ 700V':
            data['RAWDATA']['Id stability test @ 700V'] = {}
            for ii in range(i+1, i+1+3):
                k, v = lines[ii].split('\t')
                k, v = k.strip(), v.strip()
                data['RAWDATA']['Id stability test @ 700V'][k] = v
            # At this point we have all of the data we want, so we can break
            break
        else:
            continue

    # Update our passed and problem statuses to be booleans
    data['TEST']['PASSED' ] = True if (data['TEST']['PASSED' ].upper() == 'YES') else False
    data['TEST']['PROBLEM'] = True if (data['TEST']['PROBLEM'].upper() == 'YES') else False

    #pp.pprint(data)
    ###logGSD.debug( json.dumps(data, indent=2) )
    #logGSD.info(" Got test data.")
    #logGSD.info('')


def flattenMattsDict( aDict ):
    retDict = {}
    for keyL0 in aDict:
        dictL1 = aDict[keyL0]
        for keyL1 in dictL1:

            # Skip this, since it's duplicated
            if keyL1 == "Id stability test @ 700V":
                continue

            # the only L2 possibility
            if keyL1 == "IV Characteristics (A)":
                dictL2 = dictL1[keyL1]
                for keyL2 in dictL2:
                    retDict[keyL2] = dictL2[keyL2]

            # otherwise copy L1 data
            else:
                # special case due to Matt's conversion to bool
                # will convert back to string to make data of the same string type
                if keyL1 == "PROBLEM" or keyL1 == "PASSED":
                    theVal = "YES" if dictL1[keyL1] else "NO"
                    retDict[keyL1] = theVal
                else:
                    retDict[keyL1] = dictL1[keyL1]

        # end of loop within the structures
    # end of loop over the big structures -- "RAWDATA", "DEFECTS", etc
    return retDict


# VF, 2021-08-24: because the spaces are different for production, damn it
def space_bad_strips(Dict):
    for aKey in Dict:
        if ( aKey in badStripTypes and 
             len(Dict[aKey]) > 0 ):
            listVal = Dict[aKey].split(",")
            newVal = ""
            for aV in listVal:
                nV = aV.strip()
                if len(newVal) > 0:
                    newVal += ", "
                newVal += nV
                Dict[aKey] = newVal
            # end of loop over the split strip numbers
    # end of loop over the keys
    return

                
# VF, 2021-08-15: Let's check the two sets of readings
# The first one is from Derek Hamersly's code (from error_checker)
# The second one is from Matt Basso (in this script)
def compare_readings( readingDerek, readingMatt ):

    logCR_ = logging.getLogger("LOG-CR_")
    vCompat = True # original goodness

    if len(readingDerek) == 0:
        logCR_.error(" something is wrong. Derek's dictionary has zero size.")
        vCompat = False
        return vCompat

    for aSensor in readingDerek:
        filename = aSensor.filename
        datD     = aSensor.valuesdict
        # to standardize the spaces b/w the bad strips
        space_bad_strips(datD)
        datM     = readingMatt[filename]
        datMflat = flattenMattsDict(datM)
        if datD != datMflat:
            logCR_.error(" the readings of the input file <" + filename + "> are different!")
            vCompat = False
            # dump the dictionaries for debugging
            logCR_.debug(" Derek's read is ")
            logCR_.debug( json.dumps(datD, indent=2) )
            logCR_.debug("")
            logCR_.debug(" Matt's read is ")
            logCR_.debug( json.dumps(datM, indent=2) )
            # check if Derek's keys are in Matt's dictionary + common 
            for k in datD:
                if k in datMflat:
                    if datD[k] != datMflat[k]:
                        logCR_.error(" read key <" + k + "> as " +
                                     "<" + datD[k] + "> (D) and as " + 
                                     "<" + datMflat[k] + "> (M)")
                else:
                    logCR_.error(" key <" + k + "> as <" + datD[k] + "> was not in Matt's dictionary")
            # check if Matt's keys are in Derek's dictionary
            for k in datMflat:
                if not ( k in datD ):
                    logCR_.error(" key <" + k + "> as <" + datMflat[k] + "> was not in Derek's dictionary")
        # end of checking the dictionaries' compatibility
    # end of loop over the wafers

    return vCompat


def upload_manufacturer_testrun_results(c, data, comp_code, institution):

    voltages_sorted = sorted(list(data['RAWDATA']['IV Characteristics (A)'].keys()), key = lambda v: float(v))
    # Vf, 2021-08-25: expansion of non-availability
    dataNA = ['O.L.', '-']
    # VF, 2021-06-13: to add the date in the expected format
    iDate = str(data['TEST']['Test Date (DD/MM/YYYY)'])
    needed_date = iDate[6:10] + "-" + iDate[3:5] + "-" + iDate[0:2] + "T00:00:00.000Z"
    dto_in = {
        'component':    comp_code,
        'testType':     'MANUFACTURING18',
        'institution':  institution,
        'runNumber':    '1',
        'date':         needed_date,
        'passed':       data['TEST']['PASSED'],
        'problems':     data['TEST']['PROBLEM'],
        'properties':   {
            'DATE':                     str(data['TEST']['Test Date (DD/MM/YYYY)']),
            'IV_TEMPERATURE':           float(data['DATA']['IV Temperature(C)']),
            'IV_HUMIDITY':              float(data['DATA']['IV Humidity(%)']),
            'IV_VOLTAGE_STEP':          float(data['RAWDATA']['Voltage step (V)']),
            'IV_DELAY_TIME':            float(data['RAWDATA']['Delay time (second)']),
            'SUBSTRATE_LOT_NUMBER':     str(data['DATA']['Substrate Lot No.']),
            'SUBSTRATE_TYPE' :          str(data['DATA']['Substrate Type']),
            'SUBSTRATE_ORIENTATION':    str(data['DATA']['Substrate Orient']),
            'SUBSTRATE_R_UPPER':        float(data['DATA']['Substrate R Upper (kOhm.cm)']),
            'SUBSTRATE_R_LOWER':        float(data['DATA']['Substrate R Lower (kOhm.cm)']),
            'ACTIVE_THICKNESS':         float(data['DATA']['Active thickness (nominal value)'])
        },
        'results' : {
            'IV_VOLTAGE':                   [float(V) for V in voltages_sorted],
            'IV_CURRENT':                   [(float(data['RAWDATA']['IV Characteristics (A)'][V]) if data['RAWDATA']['IV Characteristics (A)'][V] != 'O.L.' else 999.) for V in voltages_sorted],
            'DEPLETION_VOLTAGE':            float(data['DATA']['Deplation Volts (V)']),
            'LEAKAGE_CURRENT_FD_PLUS_50V':  float(data['DATA']['Leakage Current at Vfd + 50V (microA)']) if data['DATA']['Leakage Current at Vfd + 50V (microA)'] != 'O.L.' else 999.,
            'LEAKAGE_CURRENT_500V':         float(data['DATA']['Leakage current at 500 V (microA)']) if data['DATA']['Leakage current at 500 V (microA)'] != 'O.L.' else 999.,
            'POLYSILICON_BIAS_R_UPPER':     float(data['DATA']['Polysilicon Bias Resistance Upper (MOhm)']),
            'POLYSILICON_BIAS_R_LOWER':     float(data['DATA']['Polysilicon Bias Resistance Lower (MOhm)']),
            # VF, 2021-08-25: old stuff, needs to change in the light of new creations
            #'MICRODISCHARGE_VOLTAGE':       float(data['DATA']['Onset voltage of Microdischarge (V)']) if data['DATA']['Onset voltage of Microdischarge (V)'] != 'over 700' else 700.,
            #'CURRENT_STABILITY_10S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['10 sec']) if data['RAWDATA']['Id stability test @ 700V']['10 sec'] != 'O.L.' else 999.,
            #'CURRENT_STABILITY_20S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['20 sec']) if data['RAWDATA']['Id stability test @ 700V']['20 sec'] != 'O.L.' else 999.,
            #'CURRENT_STABILITY_30S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['30 sec']) if data['RAWDATA']['Id stability test @ 700V']['30 sec'] != 'O.L.' else 999.
            'MICRODISCHARGE_VOLTAGE':       float(data['DATA']['Onset voltage of Microdischarge (V)']) if not data['DATA']['Onset voltage of Microdischarge (V)'].startswith('over 700') else 700.,
            'CURRENT_STABILITY_10S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['10 sec']) if not data['RAWDATA']['Id stability test @ 700V']['10 sec'] in dataNA else 999.,
            'CURRENT_STABILITY_20S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['20 sec']) if not data['RAWDATA']['Id stability test @ 700V']['20 sec'] in dataNA else 999.,
            'CURRENT_STABILITY_30S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['30 sec']) if not data['RAWDATA']['Id stability test @ 700V']['30 sec'] in dataNA else 999.
        },
        'defects' : [
            {
                'name' : 'Oxide Pinholes',
                'description' : data['DEFECT']['Oxide pinholes']
            },
            {
                'name' : 'Metal Shorts',
                'description' : data['DEFECT']['Metal Shorts']
            },
            {
                'name' : 'Metal Opens',
                'description' : data['DEFECT']['Metal Opens']
            },
            {
                'name' : 'Implant Shorts',
                'description' : data['DEFECT']['Implant Shorts']
            },
            {
                'name' : 'Implant Opens',
                'description' : data['DEFECT'].get('Implant Shorts', '9-9999')
            },
            {
                'name' : 'Microdischarge strips',
                'description' : data['DEFECT'].get('Microdischarge strips', '9-9999')
            },
            {
                'name' : 'Bias Resistor Disconnection',
                'description' : data['DEFECT'].get('Bias resistor disconnection', '9-9999')
            },
            {
                'name' : 'Percentage of NG Strips',
                'description' : data['DEFECT']['Percentage of NG strips']
            }
        ]
    }

    #response = session.doSomething('uploadTestRunResults', method='POST', data=dto_in)
    success, response = upload_testrun(c, dto_in)
    return success, response


def get_wpls(sensor_type):
    wpl_mini,wpl_chip = 'Miniature sensor','ATLAS test chip'
    if sensor_type.endswith('S'):
        wpl_mini += '5 - M1'
        wpl_chip += '2 - A2'
    elif bool(re.search(r'R\d{1}$',sensor_type)):
        if sensor_type[-1] in ['0','2','3','4']:
            wpl_mini += '1 - M1'
            wpl_chip += '1 - A1'
        elif sensor_type[-1] == '1':
            wpl_mini += '5 - M1'
            wpl_chip += '2 - A2'
        elif sensor_type[-1] == '5':
            wpl_mini += '5 - M1'
            wpl_chip += '1 - A3'
    else:
        #must be a dummy sensor, so use these default values
        wpl_mini += '5 - M1'
        wpl_chip += '1 - A1'
    return wpl_mini,wpl_chip


def register_components(c, data, institution, date_received, do_qa, dummy):

    logRC_ = logging.getLogger("LOG-RC_")
    sensor_type       = data['ITEM']['Sensor Type']
    subproject = data['ITEM']['Identification Number'][3:5]
    if type in ['ATLAS18R0', 'ATLAS18R1', 'ATLAS18R2', 'ATLAS18R3', 'ATLAS18R4', 'ATLAS18R5'] and subproject != 'SE':
        subproject = 'SE'
    elif type in ['ATLAS18SS', 'ATLAS18LS'] and subproject != 'SB':
        subproject = 'SB'
    wafer_number = data['ITEM']['Identification Number'][9:]
    id           = data['ITEM']['Serial Number']
    id_Wafer     = id + "-WFR" if not dummy else id + "-WRT"
#    id_HalfM     = id + "-HFM" if not dummy else id + "-HMT"
    id_TestC     = id + "-TCM" if not dummy else id + "-TCT"
    id_TestM     = id + "-MIM" if not dummy else id + "-MIT"
    batch_number = id.split('-')[0]

    #logRC_.info(" \n\n\n\n")
    responses = {}
    sensor_code    = 'SENSOR'             if not dummy else 'SENSOR_S_TEST'
    parent_code    = 'SENSOR_WAFER'       if not dummy else 'SENSOR_W_TEST'
    parent_type    = 'ATLAS18_WAFER'      if not dummy else 'ATLASDUMMY18W'
#    halfmoons_code = 'SENSOR_HALFMOONS'   if not dummy else 'SENSOR_H_TEST'
#    halfmoons_type = 'ATLAS18_HALFMOONS'  if not dummy else 'ATLASDUMMY18H'
    batch_code     = 'SENSORS_PROD_BATCH' if not dummy else 'BATCH_TEST_SENSOR'
    wafer_SN = makeSN_nocheck(parent_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject)
    dto_in_wafer = {
        'project':          'S',
        'subproject':       subproject,
        'institution':      institution,
        'componentType':    parent_code,
        'type':             parent_type,
        'serialNumber':     wafer_SN,
        'properties':       {'ID': id_Wafer, 'SENSOR_WAFER_INGOT_NUMBER': data['DATA']['Substrate Lot No.']},
        'batches':          {batch_code: batch_number}
    }
    success, responses[parent_code] = register_item(c, dto_in_wafer)
    if success: 
        logRC_.info(" Registered Wafer with         SN = " + wafer_SN)
    else:
        logRC_.error(" Failed to register wafer with the following input:")
        logRC_.error( json.dumps(dto_in_wafer, indent=2) )
        logRC_.error(" Will exit. ")
        return success, responses
    # responses[parent_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_wafer)
    wafer_code = responses[parent_code]['component']['code']

    sensor_SN = makeSN_nocheck(sensor_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject)
    dto_in_sensor = {
        'project':          'S',
        'subproject':       subproject,
        'institution':      institution,
        'componentType':    sensor_code,
        'type':             sensor_type,
        'serialNumber':     sensor_SN,
        'properties' :      {'ID': id, 'DATE_RECEIVED': date_received},
        'batches':          {batch_code: batch_number}
    }
    success, responses[sensor_code] = register_item(c, dto_in_sensor)
    if success: 
        logRC_.info(" Registered MAIN sensor with   SN = " + sensor_SN)
    else:
        logRC_.error(" Failed to register MAIN sensor with the following input:")
        logRC_.error( json.dumps(dto_in_sensor, indent=2) )
        logRC_.error(" Will exit. ")
        return success, responses

    success = make_assembly_history(c, wafer_code, responses[sensor_code]['component']['code'] )
    if success: 
        logRC_.info(" Created assembly history for MAIN sensor with   SN = " + sensor_SN)
    else:
        logRC_.error(" Failed to create the assembly history for MAIN sensor: ")
        logRC_.error(" Wafer = " + wafer_SN + ", qa_mini_SN = " + sensor_SN )
        logRC_.error(" Will exit. ")
        return success, responses
    #responses[sensor_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_sensor)
    #session.doSomething(action = 'assembleComponent'   , method = 'POST', data = {'parent': wafer_code, 'child': responses[sensor_code]['component']['code']})
# VF, 2021-06-13: since we want the end state to be "disassembled"...
    #session.doSomething(action = 'disassembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[sensor_code]['component']['code'], 'trashed': False})

    '''
    halfmoons_SN = makeSN_nocheck(halfmoons_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject)
    dto_in_halfmoons = {
        'project':          'S',
        'subproject':       subproject,
        'institution':      institution,
        'componentType':    halfmoons_code,
        'type':             halfmoons_type,
        'serialNumber':     halfmoons_SN,
        'properties' :      {'ID': id_HalfM, 'DATE_RECEIVED': date_received},
        'batches':          {batch_code: batch_number}
    }
    success, responses[halfmoons_code] = register_item(c, dto_in_halfmoons)
    if success: 
        logRC_.info(" Registered Halfmoons with     SN = " + halfmoons_SN)
    else:
        logRC_.error(" Failed to register halfmoons piece with the following input:")
        logRC_.error( json.dumps(dto_in_halfmoons, indent=2) )
        logRC_.error(" Will exit. ")
        return success, responses

    success = make_assembly_history(c, wafer_code, responses[halfmoons_code]['component']['code'] )
    if success: 
        logRC_.info(" Created assembly history for halfmoons with     SN = " + halfmoons_SN)
    else:
        logRC_.error(" Failed to create the assembly history for halfmoons: ")
        logRC_.error(" Wafer = " + wafer_SN + ", qa_mini_SN = " + halfmoons_SN )
        logRC_.error(" Will exit. ")
        return success, responses
    '''
    #responses[halfmoons_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_halfmoons)
    #session.doSomething(action = 'assembleComponent'   , method = 'POST', data = {'parent': wafer_code, 'child': responses[halfmoons_code]['component']['code']})
# VF, 2021-06-13: since we want the end state to be "disassembled"...
    #session.doSomething(action = 'disassembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[halfmoons_code]['component']['code'], 'trashed': False})

    qa_mini_code = 'SENSOR_MINI_MD8' if not dummy else 'SENSOR_QAMINI_TEST'
    qa_chip_code = 'SENSOR_TESTCHIP_MD8' if not dummy else 'SENSOR_QCHIP_TEST'
    wafer_pos_label_mini,wafer_pos_label_chip = get_wpls(sensor_type)
    if do_qa:

        qa_mini_SN = makeSN_nocheck(qa_mini_code, sensor_type, wafer_number,dummy=dummy,qa_piece=True,subproject=subproject)
        dto_in_qamini = {
            'project':          'S',
            'subproject':       subproject,
            'institution':      institution,
            'componentType':    qa_mini_code,
            'serialNumber':     qa_mini_SN,
            'batches':          {batch_code: batch_number},
            'properties':{'ID': id_TestM, 'DATE_RECEIVED': date_received, 'WAFER_POSITION_LABEL':wafer_pos_label_mini}
        }
        
        success, responses[qa_mini_code] = register_item(c, dto_in_qamini)
        if success: 
            logRC_.info(" Registered QA mini piece with SN = " + qa_mini_SN)
        else:
            logRC_.error(" Failed to register QA mini piece with the following input:")
            logRC_.error( json.dumps(dto_in_qamini, indent=2) )
            logRC_.error(" Will exit. ")
            return success, responses

        success = make_assembly_history(c, wafer_code, responses[qa_mini_code]['component']['code'] )
        if success: 
            logRC_.info(" Created assembly history for QA mini piece with SN = " + qa_mini_SN)
        else:
            logRC_.error(" Failed to create the assembly history for QA mini piece: ")
            logRC_.error(" Wafer = " + wafer_SN + ", qa_mini_SN = " + qa_mini_SN )
            logRC_.error(" Will exit. ")
            return success, responses
        # VF, 2021-08-09: seems the properties would updadate them. But we already put them in!
        #responses[qa_mini_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_qamini)
        #assembly_data_mini = {'parent': wafer_code, 'child': responses[qa_mini_code]['component']['code'],'properties':{'WAFER_POSITION_LABEL':wafer_pos_label_mini}}
        #session.doSomething(action = 'assembleComponent'   , method = 'POST', data = assembly_data_mini)
        ## VF, 2021-06-13: since we want the end state to be "disassembled"...
        #session.doSomething(action = 'disassembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[qa_mini_code]['component']['code'], 'trashed': False})

        qa_chip_SN = makeSN_nocheck(qa_chip_code, sensor_type, wafer_number, dummy=dummy,qa_piece=True,subproject=subproject)
        dto_in_qachip = {
            'project':          'S',
            'subproject':       subproject,
            'institution':      institution,
            'componentType':    qa_chip_code,
            'serialNumber':     qa_chip_SN,
            'batches':          {batch_code: batch_number},
            'properties':{'ID': id_TestC, 'DATE_RECEIVED': date_received, 'WAFER_POSITION_LABEL':wafer_pos_label_chip}
        }
        success, responses[qa_chip_code] = register_item(c, dto_in_qachip)
        if success: 
            logRC_.info(" Registered QA chip piece with SN = " + qa_chip_SN)
        else:
            logRC_.error(" Failed to register QA chip piece with the following input:")
            logRC_.error( json.dumps(dto_in_qachip, indent=2) )
            logRC_.error(" Will exit. ")
            return success, responses

        success = make_assembly_history(c, wafer_code, responses[qa_chip_code]['component']['code'] )
        if success: 
            logRC_.info(" Created assembly history for QA chip piece with SN = " + qa_chip_SN)
        else:
            logRC_.error(" Failed to create the assembly history for QA chip piece: ")
            logRC_.error(" Wafer = " + wafer_SN + ", qa_mini_SN = " + qa_chip_SN )
            logRC_.error(" Will exit. ")
            return success, responses
        #responses[qa_chip_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_qachip)
        # VF, 2021-08-09: seems the properties would updadate them. But we already put them in!
        # assembly_data_chip = {'parent': wafer_code, 'child': responses[qa_chip_code]['component']['code'],'properties':{'WAFER_POSITION_LABEL':wafer_pos_label_chip}}
        # session.doSomething(action = 'assembleComponent'   , method = 'POST', data = assembly_data_chip)
        # # VF, 2021-06-13: since we want the end state to be "disassembled"...
        # session.doSomething(action = 'disassembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[qa_chip_code]['component']['code'], 'trashed': False})

    else:
        responses[qa_mini_code]     = {}
        responses[qa_chip_code]     = {}

    return success, responses


# VF, 2021-08-15: to limit this function to processing input data into dictionaries
# The DB upload will take place later
def process_files_in_folder(input_dir, force_upload):
    logPFF = logging.getLogger('LOG-PFF')
    logPFF.info(" Will process files in the folder with data.")
    # the return value
    dictData = {}

    # check the input data quality with Derek's checking code
    CheckData = Data([input_dir])
    flags = CheckData.flags
    CheckSensors = CheckData.wafers
    ## XXXXXXXXXXXXXXXXXXXXX debug, to remove before the end
    #for aSensor in CheckSensors:
    #    dbgfile = aSensor.filename + "Derek.dbg"
    #    with open(os.path.join(input_dir,dbgfile), "w") as dF:
    #        json.dump( aSensor.valuesdict, dF, indent=2 )
    ## XXXXXXXXXXXXXXXXXXXX
    # count the errors, report the error messages
    #eReport = CheckData.error_msgs
    nParsed = 0
    nError = 0
    for aKey in flags:
        nParsed += 1
        if flags[aKey] == "ERROR":
            nError += 1
    logPFF.info(" See " + str(nParsed) + " sensors, and " + str(nError) + " of them have data integrity issues")
    # do not proceed with registrations unless forced to
    if nError > 0:
        logPFF.error(" Seeing data integrity failures")
        if force_upload:
            logPFF.info(" <force> option is used, will attempt to proceed ")
        else:
            logPFF.error(" Will not upload the data!!!")
            return False, dictData, flags
    #pp.pprint(flags)

    txt_files = list(filter(lambda x: x[-4:] == '.txt', os.listdir(input_dir)))
    #logPFF.info(" Seeing " + str(len(txt_files)) + " data files.")

    # VF, 2021-08-14: got to check the consistency b/w the different readings of the data
    # (otherwise the reporting is different from the data intake)
    logPFF.info("")
    logPFF.info(" Reading in the data ")
    for filename in txt_files:
        #logPFF.info("")
        fileData = {}
        with open(os.path.join(input_dir,filename), 'r') as file:
            get_sensor_data(file, fileData)
        dictData[filename] = fileData

        ## XXXXXXXXXXXXXXXXXXXXXXX to remove at the end
        #with open(os.path.join(input_dir,filename+"Matt.dbg"), 'w') as of:
        #    json.dump( fileData, of, indent=2 )
        ## XXXXXXXXXXXXXXXXXXXXXXX

    logPFF.info(" Got the data ")

    # VF, 2021-08-15: Let's check the two sets of readings
    all_ok = compare_readings(CheckSensors, dictData)
    if all_ok:
        logPFF.info(" The 2 readings are compatible.")
    else:
        logPFF.info(" The input readings are NOT compatible.")
        return False, dictData, flags

    # VF, 2021-08-19: Final cut

    return True, dictData, flags



# VF, 2021-08-19: re-verify data
# will correct the data iff the "force_upload" option is used, namely:
# 1) the test output, based on the data supplied
# 2) the bad strip percentage
def reverify_data( force_upload, dictData ):
    logRVD = logging.getLogger('LOG-RVD')

    keySN   = "Identification Number"
    keyBWNo = "Serial Number"
    keyType = "Sensor Type"
    keyProb = "PROBLEM"
    keyPass = "PASSED"
    keysPass = [keySN, keyBWNo, keyType, keyProb, keyPass,
                "IV Temperature(C)","IV Humidity(%)","Substrate Lot No.","Substrate Type","Substrate Orient","Humidity (%)","Voltage step (V)","Delay time (second)"]

    # loop over the sensors
    retVal = True
    for filename in dictData:
        changed = False
        dataHPK = dictData[filename]
        dataFlat = flattenMattsDict(dataHPK)

        Pathology = False
        for aKey in keysPass:
            if aKey not in dataFlat:
                Pathology = True
                logRVD.error(" BAD ERROR: in file " + filename + " key " + aKey + " not found")
        if Pathology:
            retVal = False
            continue
        valSN = dataFlat[keySN]
        # check that the SN and the file name are consistent
        if filename.split(".")[0] != valSN:
            logRVD.error(" filename <" + filename + "> != SN, exiting")
            retVal = False
            continue
        # 2021-08-25: bad fix necessary for early production (confusion b/w SL and LS)
        if valSN.startswith("20USBLS"):
            newVal = "20USBSL" + valSN[7:]
            dictData[filename]["ITEM"][keySN] = newVal
            valSN = newVal

        valBWNo = dataFlat[keyBWNo]
        # re-construct to assure the 5-digit wafer numbers
        bNo, wNo = get_batch_and_wafer_numbers(valBWNo)
        valBWNo = bNo + "-W" + wNo
        dictData[filename]["ITEM"][keyBWNo] = valBWNo
        valType = dataFlat[keyType]
        #valProb = dataFlat[keyProb]
        valPass = dictData[filename]["TEST"]["PASSED"]
        # check on SN, BWNo, Type, find E/B types
        if not checkSN_BWNo_type( valSN, valBWNo, valType ):
            logRVD.error(" in file " + filename + 
                         " misformatted or incompatible " +
                         "SN = <{}>, BWNo = <{}>, Type = <{}>".format(valSN,valBWNo,valType ) )
            retVal = False
            continue
        myKeys = expected_keys_reduced_EC
        eType = "EC"
        if barrel_SN(valSN):
            myKeys = expected_keys_reduced_barrel
            eType = "barrel"

        # loop over keys
        inSpec = True   # check the values
        goodData = True # check formatting
        for zKey in myKeys:
            # skip the already considered
            if zKey in keysPass:
                continue
            # raise the flag if not there
            if not zKey in dataFlat:
                # VF, 2021-08-24: HPK omitted this for the EC sensors
                if not barrel_SN(valSN) and zKey == "Bias resistor disconnection":
                    continue
                goodData = False
                logRVD.warning(" in file " + filename + " key " + zKey + " is missing")
                continue
            zVal = dataFlat[zKey]
            # check the data
            msg = ""
            ref,msg,valid = check_non_regex_value(zKey,zVal,eType,msg)
            if not valid:
                logRVD.warning(" in file {} see out of spec pair ".format(filename) + 
                               " (key,value) = ({},{}) ".format(zKey,zVal) )
                logRVD.warning(" the verification message = <" + msg + ">")
                # separate bad formats from out-of-spec data
                if zKey in ["Test Date (DD/MM/YYYY)"]:
                    goodData = False
                else:
                    inSpec = False

        # count the strip defects
        nBadStrip = 0
        listS = []
        for zKey in badStripTypes:
            if zKey in dataFlat: # There are EC/barrel differences in the keys available
                zVal = dataFlat[zKey]
                gD, nB = check_strips_bounds(logRVD,filename,zKey,zVal,valType,listS)
                if not gD: goodData = False
                nBadStrip += nB

        # check the number of consecutive bad strips
        nConsBad = consecutive_strips(listS)
        if nConsBad > 8:
            inSpec = False
            logRVD.warning(" in file {} see N(consecutive bad strips) = {} > 8 ".format(filename,nConsBad) )

        # check and fix the percentage format
        # Assume we are given the percentage iff "%" sign is there
        pStr = dataFlat["Percentage of NG strips"]
        percentage = 0.0
        if pStr.endswith('%'):
            percentage = float(pStr[:-1])
        else:
            percentage = float(pStr)*100
        # fix the value proactively
        dictData[filename]["DEFECT"]["Percentage of NG strips"] = str(percentage)

        # check the percentage consistency
        pFrac = float(nBadStrip)/float(nTotalStrips(valType))*100
        if pFrac > 1.0: 
            inSpec = False

        goodFracs = True
        if nBadStrip == 0:
            if percentage > (0.5/5120)*100.0:
                goodFracs = False
        else:
            if abs(percentage-pFrac) > 0.01*pFrac :
                goodFracs = False
        # consider the discrepancy
        if not goodFracs:
            # don't want to hang this => Issue warning and correct
            #goodData = False
            msg = " in file " + filename + " see wrong bad strip percentage " + pStr + ", expect " + str(pFrac)
            #if force_upload:
            dictData[filename]["DEFECT"]["Percentage of NG strips"] = str(pFrac)
            changed = True
            logRVD.warning(msg)
            logRVD.info(" Fixed bad strips percentage")
            #else:
            #    logRVD.error(msg)

        # Always fail if formatting issues (goodData)
        # otherwise fail on out-of-spec unlesss force_upload
        #  - then adjust the test passing based on the compliance of the reliable data with specifications
        # bad formatting triggers fail
        if not goodData:
            retVal = False
        else:
            # out-of-spec triggers fail unless force_upload
            if not (inSpec or force_upload) :
                retVal = False
            else:
                # adjust the test pass/fail if difference from inSpec
                if valPass != inSpec:
                    logRVD.warning(" in file {} changing {} to {} ".format(filename,keyPass,inSpec) )
                    dictData[filename]["TEST"]["PASSED" ] = inSpec
                    dictData[filename]["TEST"]["PROBLEM"] = not inSpec
                    changed = True

        if changed:
            logRVD.debug( json.dumps(dictData[filename], indent=2) )

    return retVal


# VF, 2021-08-15: to split this as a separate step!
def process_database_steps(c, input_dir, institution, date_received, do_qa, only_tests, force_upload, dummy, dictData, flags ):
    logPDS = logging.getLogger('LOG-PDS')
    logPDS.info(" Will process the database steps.")
    nTotal = len(dictData)
    logPDS.info(" Seeing " + str(nTotal) + " sensors in data structures.")

    # now will loop over the data
    nF    = 0
    nRegi = 0
    for filename in dictData:
        nF += 1
        data = dictData[filename]

        logPDS.info("")
        logPDS.info(" Processing " + str(nF) + " sensor out of " + str(nTotal))

        # Check whether problems were encountered in the HPK datafile
        wafer_number  = data['ITEM']['Identification Number'][9:]
        type = data['ITEM']['Sensor Type']
        sensor_code = 'SENSOR' if not dummy else 'SENSOR_S_TEST'
        subproject = data['ITEM']['Identification Number'][3:5]
        sensor_serial_number = makeSN_nocheck(sensor_code, type, wafer_number,dummy=dummy,subproject=subproject)

        if not force_upload and flags[sensor_serial_number] != 'OK':
            logPDS.warning(' WARNING :: Non-OK flag (\'%s\') encountered checking datafile consistency for \'%s\' (sensor SN \'%s\') -- skipping registration of components/upload of data for this file!' % (flags[sensor_serial_number], filename, sensor_serial_number))
            continue
        subtype = data['ITEM']['Sensor Type']
        if not check_type(subtype, r'ATLAS18(R[0-5]|LS|SS)') and \
		not (dummy and subtype == 'ATLASDUMMY18'):
            logPDS.warning(' Sensor type (%s) in file \'%s\' does not match \'ATLAS18*\' (excluding mechanicals) or \'ATLASDUMMY18\' (for dummys) -- skipping!' % (subtype, filename))
            continue

        # VF, 2021-08-25: footwork for the stage changes for the "only upload"
        current_stage = "KNOWN_MYSTERY"
        comp_code     = "-777"

        # Special handling for registering components + uploading tests versus only uploading tests
        if only_tests:
            logPDS.info(' Arg \'--uploadOnlyTests\' has been selected, looking for main sensor in the DB\'.')
            #response_json = session.doSomething(action = 'getComponent', method = 'GET', data = {'component': sensor_serial_number})
            #comp_code = response_json['code']
            success, resp = get_resp(c, sensor_serial_number)
            if success:
                logPDS.info (" Obtained the component code for SN = <" + sensor_serial_number + ">")
                comp_code     = resp['code' ]
                current_stage = resp['currentStage']['code']
            else:
                logPDS.error(" Failed to get the component code for SN = <" + sensor_serial_number + ">")
                logPDS.error("   Exiting.")
                return False, nRegi, nTotal
            # change the stage to the initial one, to be able to upload the test data
            if not set_stage(c,comp_code,"REGISTERED"):
                logPDS.error(" Failed resetting the stage for <" + sensor_serial_number + ">, exiting")
                return False, nRegi, nTotal
        else:
            logPDS.info(' Registering components.')
            success, response_json = register_components(c, data, institution, date_received, do_qa, dummy)
            if success: 
                logPDS.info (" Registered all the components requested!")
            else:
                logPDS.error(" Failed to register all the components requested. Exiting.")
                return False, nRegi, nTotal
            comp_code = response_json[sensor_code]['component']['code']

        success, resp = upload_manufacturer_testrun_results(c, data, comp_code, institution)
        if success: 
            logPDS.info (" Uploaded the manufacturer's test results")
        else:
            logPDS.error(" Failed to upload the manufacturer's test results.")
            return False, nRegi, nTotal
        logPDS.debug(json.dumps(resp, indent=2))
        #pp.pprint(resp)
        #logPDS.info('')
        testrun_code = resp['testRun']['id']

        success, resp = create_testrun_attachment(c, filename, testrun_code, input_dir)
        if success: 
            logPDS.info (" Created the test run attachment.")
        else:
            logPDS.error(" Failed to create the test run attachment.")
            return False, nRegi, nTotal

        if only_tests:
            # reset the stage back
            if not set_stage(c,comp_code,current_stage):
                logPDS.error(" Failed resetting the stage for <" + sensor_serial_number + 
                             "> + back to <" + current_stage + ">, exiting")
                return False, nRegi, nTotal            

        nRegi += 1

    retStatus = True
    if nRegi != nTotal or nTotal == 0: 
        retStatus = False
    return retStatus, nRegi, nTotal


def create_testrun_attachment(c,filename,testrun_code,input_dir):
    logCTA = logging.getLogger('LOG-CTA')
#    bdata = (filename, open(os.path.join(input_dir,filename), 'rb'))
    filedata = {'testRun':testrun_code,
                'title':filename,
                'description':filename,
                'type':'file'
                #'data':bdata
    }
    filepath = os.path.join(input_dir,filename)
    attachment = {'data': (filepath, open(filepath, 'rb'), 'text/plain')}
    #filedata = MultipartEncoder(fields = filedata)

    # VF, 2021-08-09: switch it itkdb. Will try the same MiltipartEncoder business
    #response = session.doSomething(action = 'createTestRunAttachment', method = 'POST',
    #                    data = filedata)
    response = {}
    success = True
    try:
        response = c.post('createTestRunAttachment', data = filedata, files = attachment)
    except Exception as e:
        success = False
        logCTA.error(" In <create_testrun_attachment>, post operation failed " )
        logCTA.error("   Could not upload the attachement. The error is:")
        logCTA.error(e)

    return success, response


# VF, 2021-08-09: Let's use the built-in facilities
def check_date(date):
    logCD_ = logging.getLogger('LOG-CD_')
    try:
        maDate = datetime.datetime.strptime(date, "%d/%m/%Y")
    except Exception as e:
        logCD_.error(" In *check_date*: failed to see a correct input date format:")
        logCD_.error(" Expect DD/MM/YYYY, got = " + date + ". The error is:" )
        logCD_.error(e)
        return False

    logCD_.debug(" Got date = " + maDate.isoformat() )
    return True

# def check_date(date):
#     if len(date) != 10:
#         raise RuntimeError('Date must be 10 digits long: len(date) = %s' % len(date))
#     split = date.split('/')
#     if not (len(split) == 3 and len(split[0]) == 2 and len(split[1]) == 2 and len(split[2]) == 4):
#         raise RuntimeError('Date must match the format \'DD/MM/YYYY\': date = \'%s\'' % date)
#     return


# VF, 2021-08-12: let's make a graceful exit
def the_end(logFile):
    logging.shutdown()

    return


def main(args):

    # process the input parameters
    input_dir     = args.input_dir
    institution   = args.institution
    date_received = args.date_received
    do_qa         = args.do_qa
    only_tests    = args.only_tests
    force_upload  = args.force_upload
    dummy         = args.dummy

    # VF, 2021-08-09 : add logging
    log_base_file = "DBregiLOG_" + institution
    logFile = setup_logging(log_base_file)
    '''
    startT = datetime.datetime.now()
    startS = startT.strftime("%Y-%m-%d_%Hh-%Mm-%Ss")
    logFile = "DBregiLOG_" + institution + "_" + startS + ".txt"

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
    '''

    # level = logging.INFO
    # format   = '  %(message)s'
    # handlers = [logging.FileHandler(logFile), logging.StreamHandler()]
    # logging.basicConfig(level = level, format = format, handlers = handlers)
    logMAIN = logging.getLogger('LOG-MAIN')
    logMAIN.info(" starting the log file for DB : " + logFile )
    logMAIN.info('\n *** registerSensors__ATLAS18.py ***')
    logMAIN.info(" scriptVersion = " + str(scriptVersion) + "\n" )

    logMAIN.info(" ------------------------------------- ")
    logMAIN.info(" Got input: "                           )
    logMAIN.info("   input_dir     = " + input_dir        )
    logMAIN.info("   institution   = " + institution      )
    logMAIN.info("   date_received = " + date_received    )
    logMAIN.info("   do_qa         = " + str(do_qa)       )
    logMAIN.info("   only_tests    = " + str(only_tests)  )
    logMAIN.info("   force_upload  = " + str(force_upload))
    logMAIN.info("   dummy         = " + str(dummy)       )
    logMAIN.info(" ------------------------------------ " )

    # Check one datum
    if not check_date(date_received):
        logMAIN.error(" Input date is invalid. Will exit.")
        logMAIN.error(" Registration FAILED.")
        return

    # VF, 2021-08-14: add the check on the directory existence
    if not os.path.isdir(input_dir):
        logMAIN.error(" The input directory is invalid. Will exit.")
        logMAIN.error(" Registration FAILED.")
        return

    # Main information processing
    try:
        files_ok, inputData, flags = process_files_in_folder(input_dir, force_upload)
        if files_ok:
            logMAIN.info(" Processed " + str(len(inputData)) + " files")
            logMAIN.info("")
        else:
            logMAIN.error("")
            logMAIN.error(" See problems with input data.")
            logMAIN.error(" Registration FAILED. The log file may have more details.")
            the_end(logFile)
            return
            
        # Final verification
        logMAIN.info(" 2nd round of data verification.")
        data_pass = reverify_data(force_upload,inputData)
        if data_pass:
            logMAIN.info(" Verification passed. ")
            logMAIN.info("")
        else:
            logMAIN.error("")
            logMAIN.error(" Verification FAILED. The log file may have more details.")
            the_end(logFile)
            return
            
        # VF, 2021-08-09 : a change to itkdb framework for reliability
        #session = ITkPDSession()
        #session.authenticate()
        c = itkdb.Client()

        success, nRegi, nTotal = process_database_steps(c, input_dir, institution, date_received, do_qa, only_tests, force_upload, dummy, inputData, flags)
        if success:
            logMAIN.info("")
            logMAIN.info(" Registered " + str(nRegi) + " wafers out of " + str(nTotal) )
            logMAIN.info(" Registration SUCCESS. " )
        else:
            logMAIN.error("")
            logMAIN.error(" Successfully registered " + str(nRegi) + " wafers out of " + str(nTotal) )
            logMAIN.error(" Registration FAILED. Please see the log file for details.")
        the_end(logFile)
        return

    except RequestException as e:
        logMAIN.error(' Request exception: ')
        logMAIN.error(e)
        the_end(logFile)
        sys.exit(1)
    except KeyboardInterrupt:
        logMAIN.error(' Got a keyboard interrupt. Will exit.')
        logMAIN.error(' Did not calcualte the number of registered wafers. Please see this log for exact details. ')
        the_end(logFile)
        sys.exit(1)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Batch register/upload sensor data to the ITkPD (ATLAS18 datasheets)', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-d', '--inputDir', dest = 'input_dir', type = str, required = True, help = 'Location of manufacturer test results files (directory)')
    required.add_argument('-i', '--institution', dest = 'institution', type = str, required = True, help = 'institution code to register the sensors with (e.g., CUNI, CA, etc.) (same for ALL sensors in dir)')
    required.add_argument('-r', '--dateReceived', dest = 'date_received', type = str, required = True, help = 'date when the shipment was received from HPK (format: DD/MM/YYYY) (same for ALL sensors in dir)')
    required.add_argument('-q', '--doQAPieces', dest = 'do_qa', action = 'store_true', help = 'register QA pieces too')
    required.add_argument('-t', '--onlyUploadTests', dest = 'only_tests', action = 'store_true', help = 'only (re-)upload the test results for the targeted files (the sensors are assumed REGISTERED in this case)')
    required.add_argument('-f', '--forceUpload', dest = 'force_upload', action = 'store_true', help = 'force upload data not passing HPK datafile consistency checks')
    required.add_argument('-D','--dummies',dest='dummy',action='store_true',help='dummy or real toggle')

    args = parser.parse_args()
    # VF, 2021-08-09: don't need this with itkdb
    #if os.getenv("ITK_DB_AUTH"):
    #    dbAccess.token = os.getenv("ITK_DB_AUTH")
    #else:
    #    print("Token expired.")
    sys.exit(main(args))
