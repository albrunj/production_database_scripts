#!/usr/bin/env python
import argparse
import os
import re
import sys

from __path__ import updatePath
updatePath()

from requests.exceptions import RequestException

import itk_pdb.dbAccess as dbAccess
from itk_pdb.dbAccess import ITkPDSession
try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except Exception:
    print("module 'requests_toolbelt' not found. Install: 'pip install requests_toolbelt'")
    sys.exit()
from HPK_data_checks.error_checker import Data
from strips.sensors.SensorSNUtils import makeSN
from pprint import PrettyPrinter

pp = PrettyPrinter(indent = 1, width = 200)

# VF, 2021-06-13: adapting the standard registration file for the case when we only are re-registering the sensor (no halfmoons or QA pieces)
# Changes:
# - commented out registration/assembly of HMs and QA pieces
# - added dis-assembly of the HM (after assembly)
#
# VF, 2021-08-05: adjusted batch code for dummy pieces


#if __name__ == '__main__':
#    from __path__ import updatePath
#    updatePath()


def check_type(subtype, regex):
    match = re.search(regex, subtype)
    if match:
        return True
    return False

def get_sensor_data(file, data):

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

    pp.pprint(data)
    print('')

def upload_manufacturer_testrun_results(session, data, comp_code, institution):

    voltages_sorted = sorted(list(data['RAWDATA']['IV Characteristics (A)'].keys()), key = lambda v: float(v))
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
            'MICRODISCHARGE_VOLTAGE':       float(data['DATA']['Onset voltage of Microdischarge (V)']) if data['DATA']['Onset voltage of Microdischarge (V)'] != 'over 700' else 700.,
            'CURRENT_STABILITY_10S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['10 sec']) if data['RAWDATA']['Id stability test @ 700V']['10 sec'] != 'O.L.' else 999.,
            'CURRENT_STABILITY_20S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['20 sec']) if data['RAWDATA']['Id stability test @ 700V']['20 sec'] != 'O.L.' else 999.,
            'CURRENT_STABILITY_30S_700V':   float(data['RAWDATA']['Id stability test @ 700V']['30 sec']) if data['RAWDATA']['Id stability test @ 700V']['30 sec'] != 'O.L.' else 999.
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

    # TO-CHANGE #5
    #print("")
    #print( json.dumps(dto_in, indent=2) )

    response = session.doSomething('uploadTestRunResults', method='POST', data=dto_in)
    return response


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


def register_components(session, data, institution, date_received, do_qa, dummy):

    sensor_type       = data['ITEM']['Sensor Type']
    subproject = data['ITEM']['Identification Number'][3:5]
    if type in ['ATLAS18R0', 'ATLAS18R1', 'ATLAS18R2', 'ATLAS18R3', 'ATLAS18R4', 'ATLAS18R5'] and subproject != 'SE':
        subproject = 'SE'
    elif type in ['ATLAS18SS', 'ATLAS18LS'] and subproject != 'SB':
        subproject = 'SB'
    wafer_number = data['ITEM']['Identification Number'][9:]
    id           = data['ITEM']['Serial Number']
    batch_number = id.split('-')[0]

    responses = {}
    sensor_code = 'SENSOR'             if not dummy else 'SENSOR_S_TEST'
    parent_code = 'SENSOR_WAFER'       if not dummy else 'SENSOR_W_TEST'
    parent_type = 'ATLAS18_WAFER'      if not dummy else 'ATLASDUMMY18W'
    # halfmoons_code = 'SENSOR_HALFMOONS' if not dummy else 'SENSOR_H_TEST'
    # halfmoons_type = 'ATLAS18_HALFMOONS' if not dummy else 'ATLASDUMMY18H'
    batch_code  = 'SENSORS_PROD_BATCH' if not dummy else 'BATCH_TEST_SENSOR'
    dto_in_wafer = {
        'project':          'S',
        'subproject':       subproject,
        'institution':      institution,
        'componentType':    parent_code,
        'type':             parent_type,
        'serialNumber':     makeSN(parent_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject),
        'properties':       {'SENSOR_WAFER_INGOT_NUMBER': data['DATA']['Substrate Lot No.']},
        'batches':          {batch_code: batch_number}
    }
    responses[parent_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_wafer)
    wafer_code = responses[parent_code]['component']['code']

    dto_in_sensor = {
        'project':          'S',
        'subproject':       subproject,
        'institution':      institution,
        'componentType':    sensor_code,
        'type':             sensor_type,
        'serialNumber':     makeSN(sensor_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject),
        'properties' :      {'ID': id, 'DATE_RECEIVED': date_received},
        'batches':          {batch_code: batch_number}
    }
    responses[sensor_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_sensor)
    session.doSomething(action = 'assembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[sensor_code]['component']['code']})
# VF, 2021-06-13: since we want the end state to be "disassembled"...
    session.doSomething(action = 'disassembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[sensor_code]['component']['code'], 'trashed': False})

    # dto_in_halfmoons = {
    #     'project':          'S',
    #     'subproject':       subproject,
    #     'institution':      institution,
    #     'componentType':    halfmoons_code,
    #     'type':             halfmoons_type,
    #     'serialNumber':     makeSN(halfmoons_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject),
    #     'batches':          {batch_code: batch_number}
    # }
    # responses[halfmoons_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_halfmoons)
    # session.doSomething(action = 'assembleComponent', method = 'POST', data = {'parent': wafer_code, 'child': responses[halfmoons_code]['component']['code']})

    # qa_mini_code = 'SENSOR_MINI_MD8' if not dummy else 'SENSOR_QAMINI_TEST'
    # qa_chip_code = 'SENSOR_TESTCHIP_MD8' if not dummy else 'SENSOR_QCHIP_TEST'
    # wafer_pos_label_mini,wafer_pos_label_chip = get_wpls(sensor_type)
    # if do_qa:

    #     dto_in_qamini = {
    #         'project':          'S',
    #         'subproject':       subproject,
    #         'institution':      institution,
    #         'componentType':    qa_mini_code,
    #         'serialNumber':     makeSN(qa_mini_code, sensor_type, wafer_number,dummy=dummy,qa_piece=True,subproject=subproject),
    #         'batches':          {batch_code: batch_number},
    #         'properties':{'WAFER_POSITION_LABEL':wafer_pos_label_mini}
    #     }
        
    #     responses[qa_mini_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_qamini)
    #     assembly_data_mini = {'parent': wafer_code, 'child': responses[qa_mini_code]['component']['code'],'properties':{'WAFER_POSITION_LABEL':wafer_pos_label_mini}}
    #     session.doSomething(action = 'assembleComponent', method = 'POST', data = assembly_data_mini)

    #     dto_in_qachip = {
    #         'project':          'S',
    #         'subproject':       subproject,
    #         'institution':      institution,
    #         'componentType':    qa_chip_code,
    #         'serialNumber':     makeSN(qa_chip_code, sensor_type, wafer_number, dummy=dummy,qa_piece=True,subproject=subproject),
    #         'batches':          {batch_code: batch_number},
    #         'properties':{'WAFER_POSITION_LABEL':wafer_pos_label_chip}
    #     }
    #     responses[qa_chip_code] = session.doSomething(action = 'registerComponent', method = 'POST', data = dto_in_qachip)
    #     assembly_data_chip = {'parent': wafer_code, 'child': responses[qa_chip_code]['component']['code'],'properties':{'WAFER_POSITION_LABEL':wafer_pos_label_chip}}
    #     session.doSomething(action = 'assembleComponent', method = 'POST', data = assembly_data_chip)

    # else:
    #     responses[qa_mini_code]     = {}
    #     responses[qa_chip_code]     = {}

    return responses

def process_files_in_folder(session, input_dir, institution, date_received, do_qa, only_tests, force_upload, dummy):
    flags = Data([input_dir]).flags
    print("flags:")
    pp.pprint(flags)
    txt_files = list(filter(lambda x: x[-4:] == '.txt', os.listdir(input_dir)))
    for filename in txt_files:
        data = {}
        with open(os.path.join(input_dir,filename), 'r') as file:
            get_sensor_data(file, data)
        # Check whether problems were encountered in the HPK datafile
        wafer_number  = data['ITEM']['Identification Number'][9:]
        type = data['ITEM']['Sensor Type']
        sensor_code = 'SENSOR' if not dummy else 'SENSOR_S_TEST'
        subproject = data['ITEM']['Identification Number'][3:5]
        sensor_serial_number = makeSN(sensor_code, type, wafer_number,dummy=dummy,subproject=subproject)
        # DBG
        # print("")
        # print(" SN = " + sensor_serial_number)
        # print(" subproject = " + subproject )
        # print(" sensor_code = "+ sensor_code)
        # print(" type = " + type )
        # print(" wafer_number = " + wafer_number )
        # print(" the actual test data = ")
        # print( json.dumps(data,indent=2) )
        # TO-CHANGE #1
        #return

        if not force_upload and flags[sensor_serial_number] != 'OK':
            print('WARNING :: Non-OK flag (\'%s\') encountered checking datafile consistency for \'%s\' (sensor SN \'%s\') -- skipping registration of components/upload of data for this file!' % (flags[sensor_serial_number], filename, sensor_serial_number))
            continue
        subtype = data['ITEM']['Sensor Type']
        if not check_type(subtype, r'ATLAS18(R[0-5]|LS|SS)') and \
		not (dummy and subtype == 'ATLASDUMMY18'):
            print('Sensor type (%s) in file \'%s\' does not match \'ATLAS18*\' (excluding mechanicals) or \'ATLASDUMMY18\' (for dummys) -- skipping!' % (subtype, filename))
            continue
        # Special handling for registering components + uploading tests versus only uploading tests
        if not only_tests:
            print('Registering components.')
            # TO-CHANGE #2
            response_json = register_components(session, data, institution, date_received, do_qa, dummy)
            comp_code = response_json[sensor_code]['component']['code']
            #comp_code = "abcd"
        else:
            print('Arg \'--uploadOnlyTests\' has been selected, looking for main sensor in the DB\'.')
            response_json = session.doSomething(action = 'getComponent', method = 'GET', data = {'component': sensor_serial_number})
            comp_code = response_json['code']
        resp = upload_manufacturer_testrun_results(session, data, comp_code, institution)
        pp.pprint(resp)
        print('')
        testrun_code = resp['testRun']['id']
        # TO-CHANGE #3
        resp = create_testrun_attachment(session, filename, testrun_code, input_dir)

def create_testrun_attachment(session,filename,testrun_code,input_dir):
    bdata = (filename, open(os.path.join(input_dir,filename), 'rb'))
    filedata = {'testRun':testrun_code,
                'title':filename,
                'description':filename,
                'type':'file',
                'data':bdata,
    }
    filedata = MultipartEncoder(fields = filedata)
    response = session.doSomething(action = 'createTestRunAttachment', method = 'POST',
                        data = filedata)
    return response

def check_date(date):
    if len(date) != 10:
        raise RuntimeError('Date must be 10 digits long: len(date) = %s' % len(date))
    split = date.split('/')
    if not (len(split) == 3 and len(split[0]) == 2 and len(split[1]) == 2 and len(split[2]) == 4):
        raise RuntimeError('Date must match the format \'DD/MM/YYYY\': date = \'%s\'' % date)
    return

def main(args):
    try:
        input_dir     = args.input_dir
        institution   = args.institution
        date_received = args.date_received
        check_date(date_received)
        do_qa         = args.do_qa
        only_tests    = args.only_tests
        force_upload  = args.force_upload
        dummy         = args.dummy
        session = ITkPDSession()
        session.authenticate()
        print('\n*** registerSensors__ATLAS18.py ***\n')
        process_files_in_folder(session, input_dir, institution, date_received, do_qa, only_tests, force_upload, dummy)
    except RequestException as e:
        print('Request exception: ' + str(e))
        sys.exit(1)
    except KeyboardInterrupt:
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
    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")
    else:
        print("Token expired.")
    sys.exit(main(args))
