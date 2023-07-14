#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys, os, argparse
import itk_pdb.dbAccess as dbAccess
from itk_pdb.dbAccess import ITkPDSession
from requests.exceptions import RequestException
try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except Exception:
    print("module 'requests_toolbelt' not found. Install: 'pip install requests_toolbelt'")
    sys.exit()
from SensorSNUtils import makeSN
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

import re

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
                                if all(p.strip().isdigit() for p in re.split(r',|-', lines[iii])):
                                    v += lines[iii]
                                    iii += 1
                                    continue
                                else:
                                    break
                            v = ', '.join([p.strip() for p in v.split(',')])
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
    data['TEST']['PASSED'] = True if (data['TEST']['PASSED'].upper() == 'YES') else False
    data['TEST']['PROBLEM'] = True if (data['TEST']['PROBLEM'].upper() == 'YES') else False

    pp.pprint(data)
    print('')

def upload_manufacturer_testrun_results(session, data, comp_code, institution):

    voltages_sorted = sorted(list(data['RAWDATA']['IV Characteristics (A)'].keys()), key = lambda v: float(v))
    dto_in = {
        'component':    comp_code,
        'testType':     'MANUFACTURING18',
        'institution':  institution,
        'runNumber':    '1',
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

    response = session.doSomething('uploadTestRunResults', 'POST', dto_in)
    return response

def delete_testrun(session,sensor_json):
    try:
        #index 0 gets latest data
        test_id = sensor_json['tests'][0]['testRuns'][0]['id']
    except Exception:
        raise Exception("Error getting testrun id!")
    #print("tests ",sensor_json['tests'])
    if sensor_json['tests'][0]['testRuns'][0]['state'] == 'ready':
        session.doSomething(action = 'deleteTestRun',method = 'POST', data = {'testRun':test_id})
        return True
    else:
        print("Testrun not 'ready', probably already deleted")
        return False

def get_sensor_json(session, data, dummy):
    wafer_number = data['ITEM']['Identification Number'][9:]
    subproject = data['ITEM']['Identification Number'][3:5]
    sensor_type = data['ITEM']['Sensor Type']
    sensor_code = 'SENSOR' if not dummy else 'SENSOR_S_TEST'
    #parent_code = 'SENSOR_WAFER' if not dummy else 'SENSOR_W_TEST'
    #parent_type = sensor_type if not dummy else 'ATLASDUMMY18W'
    sensor_SN = makeSN(sensor_code, sensor_type, wafer_number,dummy=dummy,subproject=subproject)
    
    response_json = session.doSomething(action = 'getComponent', method = 'GET', data = {'component':sensor_SN})
    return response_json
    
def set_stage(session,sensor_json,comment='',stage=''):
    setStageData = {
            'component':sensor_json['serialNumber'],
            'stage':stage,
            'rework':False,
            'comment':comment,
    }
    session.doSomething(action = 'setComponentStage',method= 'POST', data = setStageData)

def process_files_in_folder(session, input_dir, institution, dummy):
    txt_files = list(filter(lambda x: x[-4:] == '.txt', os.listdir(input_dir)))
    for filename in txt_files:
        data = {}
        with open(os.path.join(input_dir,filename), 'r') as file:
            get_sensor_data(file, data)
        subtype = data['ITEM']['Sensor Type']
        if not check_type(subtype, r'ATLAS18(R[0-5]|LS|SS)') and \
		not (dummy and subtype == 'ATLASDUMMY18'):
            print('Sensor type (%s) in file \'%s\' does not match \'ATLAS18*\' (excluding mechanicals) or \'ATLASDUMMY18\' (for dummys) -- skipping!' % (subtype, filename))
            continue
        sensor_json = get_sensor_json(session, data, dummy)

        sensor_stage = sensor_json['currentStage'].get('code')
        #revert stage of sensor back to registered
        if data['TEST']['PASSED']:
            set_stage(session,sensor_json,
                    comment='Reverting stage to Registration in order to update manufacturer testrun',
                    stage="REGISTERED")
            #delete old testrun
            delete_testrun(session,sensor_json) 
            
            #upload updated testrun
            comp_code = sensor_json['code']
            resp = upload_manufacturer_testrun_results(session, data, comp_code, institution)
            #add attachment
            testrun_code = resp['testRun']['id']
            resp = create_testrun_attachment(session, filename, testrun_code, input_dir)
            
            #revert stage to what it was before
            if sensor_stage not in ["REGISTERED","QC_TESTS"] and data['TEST']['PASSED']:
                set_stage(session,sensor_json,
                        comment='Reverting stage to what it was before',
                        stage=sensor_stage)
        else:
            print("\n\nSensor ({}) didn't pass manufacturer tests!\n\n".format(sensor_json['serialNumber']))
        # pp.pprint(resp)
        # print('')

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

def main(args):
    try:
        input_dir = args.input_dir
        institution = args.institution
        dummy = args.dummy
        session = ITkPDSession()
        session.authenticate()
        print('\n*** updateTestRuns.py ***\n')
        process_files_in_folder(session, input_dir, institution, dummy)
        print("files in {} were processed successfully!".format(input_dir))
    except RequestException as e:
        print('Request exception: ' + str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Update/upload manufacturer testruns', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-d', '--inputDir', dest = 'input_dir', type = str, required = True, help = 'Location of manufacturer test results files (directory)')
    required.add_argument('-i', '--institution', dest = 'institution', type = str, required = True, help = 'institution code to register the sensors with (e.g., CUNI, CA, etc.) (same for ALL sensors in dir)')
    required.add_argument('-D','--dummies',dest='dummy',action='store_true',help='dummy or real toggle')
    args = parser.parse_args()
    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")
    else:
        print("Token expired.")
    sys.exit(main(args))
