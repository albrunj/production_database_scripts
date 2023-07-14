#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import json, sys, os, argparse
from itk_pdb.dbAccess import ITkPDSession
from requests.exceptions import RequestException
from requests_toolbelt.multipart.encoder import MultipartEncoder
import re

def check_type(subtype, regex):
    match = re.search(regex, subtype)
    if match:
        return True
    return False

def get_sensor_data(f, data):
    mainlines = []
    infolines = []
    infolist = []
    ivlist = {}

    for line in f:
        if (line.strip() == "#IV"):
            switch = 1
        else:
            switch = 0
            # print(f.readlines())
        if (not switch):
            if (line[0] != '#'):
                if (line[0] == "%"):
                    if (len(mainlines) != 0):
                        infolist.append(infolines)
                    infolines = []
                    line = line.strip()
                    if (line.strip('%') in mainlines):
                        line += '2'
                    mainlines.append(line.strip('%'))
                elif ((line != "\t\n") and (line != "\n") and (line != '')):
                    # line = ' '.join(line.split())
                    infolines.append(line)
        else:
            if ((line[0] != '#') and (line[0] != '-') and (line[0] != '\t')):
                ivlist[line[:line.find('\t')].strip()] = line[(line.find('\t') + 1):line.find('\n')].strip()

    infolist.append(infolines)

    for i in range(len(mainlines)):
        parameters = {}
        for j in infolist[i]:
            parameters[j[:j.find('\t')].strip()] = j[(j.find('\t') + 1):j.find('\n')].strip()
        data[mainlines[i]] = parameters

    data["RAWDATA"]["IV Characteristics (A)"] = ivlist

    if (data["TEST"]["PASSED"].upper() == "YES"):
        data["TEST"]["PASSED"] = True
    elif (data["TEST"]["PASSED"].upper() == "NO"):
        data["TEST"]["PASSED"] = False

    if (data["TEST"]["PROBLEM"].upper() == "YES"):
        data["TEST"]["PROBLEM"] = True
    elif (data["TEST"]["PROBLEM"].upper() == "NO"):
        data["TEST"]["PROBLEM"] = False

    print(data)
    print("")

def load_json_file(json_file_path):
    try:
        with open(json_file_path, 'r') as json_file:
            json_file_data = json.load(json_file)
        return json_file_data
    except IOError:
        return None

def create_testrun_attachment(session, filename, code, input_dir):

    data={
        "testRun": code,
        "title": "Manufacturer's data",
        "description": "General information and initial test results of the sensor.",
        "data": (filename, open(input_dir + filename, 'rb')),
        "type": "file"
    }
    data = MultipartEncoder(fields = data)

    response = session.doSomething('createTestRunAttachment', 'POST', data)
    return response

def register_component(session, data, institution):

    dto_in = {
        "project" : "S",
        "subproject" : data["ITEM"]["Identification Number"][3:5],
        "institution" : institution,
        "componentType" : "SENSOR",
        "type" : data["ITEM"]["Sensor Type"],
        "serialNumber" : data["ITEM"]["Identification Number"],
        "properties" : {
            "ID" : data["ITEM"]["Serial Number"]
        }
    }

    response = session.doSomething('registerComponent', 'POST', dto_in)
    return response

def upload_manufacturer_testrun_results(session, data, comp_code, institution):

    dto_in = {
        "component": comp_code,
        "testType": "MANUFACTURING",
        "institution": institution,
        "runNumber": "1",
        "passed": data["TEST"]["PASSED"],
        "properties": {
            "DATE": data["TEST"]["Test Date (DD/MM/YYYY)"],
            "SUBSTRATE_TYPE" : data["DATA"]["Substrate Type"],
            "SUBSTRATE_LOT" : data["DATA"]["Substrate Lot No."],
            "SUBSTRATE_ORIENT" : int(data["DATA"]["Substrate Orient"]),
            "SUBSTRATE_R_UPPER" : float(data["DATA"]["Substrate R Upper (kOhm.cm)"]),
            "SUBSTRATE_R_LOWER" : float(data["DATA"]["Substrate R Lower (kOhm.cm)"]),
            "THICKNESS_A" : int(data["DATA"]["Thickness(A: top-left) (micron)"]),
            "THICKNESS_B": int(data["DATA"]["Thickness(B: top-right) (micron)"]),
            "THICKNESS_C": int(data["DATA"]["Thickness(C: center) (micron)"]),
            "THICKNESS_D": int(data["DATA"]["Thickness(D: bottom-left) (micron)"]),
            "THICKNESS_E": int(data["DATA"]["Thickness(E: bottom-right) (micron)"])
        },
        "results" : {
            "PROBLEM" : data["TEST"]["PROBLEM"],
            "IV_TEMPERATURE" : int(data["DATA"]["IV Temperature(C)"]),
            "DEPLETION_VOLTS" : int(data["DATA"]["Deplation Volts (V)"]),
            "LEAKAGE_CURRENT_200": -1,
            "LEAKAGE_CURRENT_600": -1,
            "LEAKAGE_CURRENT_VFD" : float(data["DATA"]["Leakage Current at Vfd + 50V (microA)"]),
            "LEAKAGE_CURRENT_700" : float(data["DATA"]["Leakage current at 700 V (microA)"]),
            "ACTIVE_THICKNESS" : int(data["DATA"]["Active thickness (nominal value)"]),
            "BIAS_RESISTANCE_U" : float(data["DATA"]["Polysilicon Bias Resistance Upper (MOhm)"]),
            "BIAS_RESISTANCE_L" : float(data["DATA"]["Polysilicon Bias Resistance Lower (MOhm)"]),
            "ONSET_VOLTAGE_MICRODISCHARGE" : data["DATA"]["Onset voltage of Microdischarge (V)"]
        },
        "defects" : [
            {
                "name" : "Oxide Pinholes",
                "description" : data["DEFECT"]["Oxide pinholes"]
            },
            {
                "name" : "Metal Shorts",
                "description" : data["DEFECT"]["Metal Shorts"]
            },
            {
                "name" : "Metal Opens",
                "description" : data["DEFECT"]["Metal Opens"]
            },
            {
                "name" : "Implant Shorts",
                "description" : data["DEFECT"]["Implant Shorts"]
            },
            {
                "name" : "Implant Opens",
                "description" : data["DEFECT"]["Implant Opens"]
            },
            {
                "name" : "Microdischarge Strips",
                "description" : data["DEFECT"]["Microdischarge strips"]
            },
            {
                "name" : "Percentage of NG Strips",
                "description" : data["DEFECT"]["Percentage of NG strips"]
            }
        ]
    }

    response = session.doSomething('uploadTestRunResults', 'POST', dto_in)
    return response

def upload_iv_results(session, data, comp_code, institution):

    voltage_list = []
    current_list = []
    for j in data["RAWDATA"]["IV Characteristics (A)"]:
        try:
          current_list.append(float(data["RAWDATA"]["IV Characteristics (A)"][j]))
          voltage_list.append(int(j))
        except ValueError:
            pass

    dto_in = {
        "component": comp_code,
        "testType": "IV",
        "institution": institution,
        "runNumber": "1",
        "passed": data["TEST"]["PASSED"],
        "properties" : {
            "TEMPERATURE" : int(data["RAWDATA"]["IV Temperature(C)"]),
            "HUMIDITY" : int(data["RAWDATA"]["Humidity (%)"]),
            "VOLTAGE_STEP" : int(data["RAWDATA"]["Voltage step (V)"]),
            "DELAY" : int(data["RAWDATA"]["Delay time (second)"]),
            "VOLTAGE_START" : voltage_list[0],
            "VOLTAGE_END" : voltage_list[-1]
        },
        "results" : {
            "VOLTAGE" : voltage_list,
            "CURRENT" : current_list
        }
    }

    response = session.doSomething('uploadTestRunResults', 'POST', dto_in)
    return response

def process_files_in_folder(session, input_dir, institution):
    txt_files = list(filter(lambda x: x[-4:] == '.txt', os.listdir(input_dir)))
    for filename in txt_files:
        data = {}
        with open(input_dir + filename, "r") as file:
            get_sensor_data(file, data)
        subtype = data["ITEM"]["Sensor Type"]
        if not check_type(subtype, r'ATLAS17*'):
            print("Sensor type (%s) in file '%s' does not match 'ATLAS17*' -- skipping!" % (subtype, filename))
            continue
        response_json = register_component(session, data, institution)
        comp_code = response_json["component"]["code"]
        resp = upload_manufacturer_testrun_results(session, data, comp_code, institution)
        print(resp)
        print("")
        testrun_code = resp["testRun"]["id"]
        create_testrun_attachment(session, filename, testrun_code, input_dir)
        resp_iv = upload_iv_results(session, data, comp_code, institution)
        print(resp_iv)
        print("")

def main(args):
    try:
        input_dir = args.input_dir
        institution = args.institution
        session = ITkPDSession()
        session.authenticate()
        print("\n*** registerSensors__prototypes.py ***\n")
        process_files_in_folder(session, input_dir, institution)
    except RequestException as e:
        print('Request exception: ' + str(e))
        exit(1)
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Batch register/upload sensor data to the ITkPD (prototype or ATLAS17 datasheets)', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-d', '--inputDir', dest = 'input_dir', type = str, required = True, help = 'Location of manufacturer test results files (directory)')
    required.add_argument('-i', '--institution', dest = 'institution', type = str, required = True, help = 'institution code to register the sensors with (e.g., CUNI, CA, etc.)')

    args = parser.parse_args()
    sys.exit(main(args))
