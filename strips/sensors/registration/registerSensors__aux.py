#!/usr/bin/python
import json
import re
from datetime import datetime
from pathlib import Path

import itkdb
from __path__ import updatePath
#from pprint import PrettyPrinter
updatePath()

from strips.sensors.SensorSNUtils import get_code
from strips.sensors.SensorSNUtils import get_batch_and_wafer_numbers
from strips.sensors.SensorSNUtils import makeSN
from strips.sensors.SensorSNUtils import makeSN_wafer

###
# 2021-06-03, VF: a code for a sequence of steps:
#                  - registering MAIN sensor without the HPK data upload
#                  - registering its wafer
#                  - associating the sensor and the wafer
#                  - dis-associating the sensor and the wafer
#                The purpose is to register "wrongly sent" sensors.
#                This closely follows "registerQA.py" code
# 2021-10-03, VF: updated halfmoon "suffixes" in the ID, provided a possibly existing wafer (from the same script run)
#
#------ example for "dummy" objects registration:
#institution	UCSC_STRIP_SENSORS
#subproject      SB
##
## Please *note*:
## The 1st value in every line is *MAIN* type (not halfmoons type!)
##
#ATLASDUMMY18,	VPX90032-W00750,	MAIN,	25/03/2006
#ATLASDUMMY18,	VPX90032-W00751,	halfmoon
#------ example for "real" objects registration:
#institution	CERN
#ATLAS18R4,	VPX32496-W00123,	halfmoon
#ATLAS18R1,	VPX32587-W00065,	halfmoon
##
## Please *note*:
## The 1st value in every line is *MAIN* type (not halfmoons type!)
## Cannot have comments on the 2nd line!
##
## VF, 2021-08-05: adjusted batch code for dummy pieces
#----------------------------


acceptable_sensor_types = ['ATLASDUMMY18','ATLAS18LS', 'ATLAS18SS', 'ATLAS18R0', 'ATLAS18R1', 'ATLAS18R2', 'ATLAS18R3', 'ATLAS18R4', 'ATLAS18R5','ATLAS18_HALFMOONS','ATLASDUMMY18H']
acceptable_component_type_names = ['MAIN','HALFMOON','main','halfmoon']
component_code_real = {'MAIN':'SENSOR',
                       'main':'SENSOR',
                       'HALFMOON':'SENSOR_HALFMOONS',
                       'halfmoon':'SENSOR_HALFMOONS'}
component_code_dummy = {'MAIN':'SENSOR_S_TEST',
                        'main':'SENSOR_S_TEST',
                        'HALFMOON':'SENSOR_H_TEST',
                        'halfmoon':'SENSOR_H_TEST'}
acceptable_subprojects = ['SE','SB']

# so that we don't try to re-register the wafer again
listW={}


def get_institution(line):
    institution = line.strip().split()[1]
    return institution

def get_subproject_from_line(line):
    splitline = line.strip().split()
    if len(splitline) > 2:
        #this means it is a "real" file (not dummy)
        return None
    subproject = splitline[1]
    if subproject in acceptable_subprojects:
        return subproject
    raise Exception("Invalid subproject: {}".format(subproject))

def get_subproject_from_sensor_type(sensor_type):
    #only used for real components. For dummy's, subproject must
    # be listed in the file.
    if bool(re.search(r'R\d{1}$',sensor_type)):
        return 'SE'
    elif bool(re.search(r'S$',sensor_type)):
        return 'SB'
    else:
        #shouldn't ever get here...
        raise Exception("Invalid sensor type")

def parse_line(line, dummy):
    #comma separated: "ATLAS18SS,VPX99999-W102,MAIN/halfmoon"
    stripped_line = [s.strip() for s in line.split(',')]
    rdate = "" # think the most likely error is omission. This may or may not be true.
    if   len(stripped_line) == 3 :
        sensor_type,vpx,component_type_name = stripped_line
    elif len(stripped_line) == 4 :
        sensor_type,vpx,component_type_name,rdate = stripped_line
    else:
        return None
    
    #check if each value is acceptable
    # VF, 2021-10-20: have to allow for the VPA, in addition to VPX
    if sensor_type not in acceptable_sensor_types or \
       component_type_name not in acceptable_component_type_names or \
       not bool(re.search(r'VP(X|A)\d{5}-W\d{1,}$',vpx)) :
        return None 

    if dummy:
        component_type_code = component_code_dummy[component_type_name]
    else:
        component_type_code = component_code_real[component_type_name]

    return sensor_type,vpx,component_type_code,rdate


def register_and_footwork(c,bDBG,sensor_type,vpx,component_type, subproject, institution, dummy,rdate):
    # figure out SNs, object type
    # expect the sensor_type to be that of the MAIN sensor (so that we can figure out SN), even when registering halfmoons
    # The SN will be correctly figured out for halfmoons, due to the sensor_type clause in the utils
    batch_number,wafer_number = get_batch_and_wafer_numbers(vpx)

    SN = makeSN(component_type, sensor_type, wafer_number, dummy=dummy, qa_piece=False,subproject=subproject)
    object_type = sensor_type
    # change the type for halfmoons to the one expected by DB in the object structure
    if component_type == 'SENSOR_HALFMOONS':
        object_type = 'ATLAS18_HALFMOONS'
    elif component_type == 'SENSOR_H_TEST':
        object_type = 'ATLASDUMMY18H'
    batch_code = 'SENSORS_PROD_BATCH' if not dummy else 'BATCH_TEST_SENSOR'

    batchNo, waferNo = get_batch_and_wafer_numbers(vpx)
    ID       = batchNo + "-W" + waferNo
    ID_Wafer = ID + "-WFR" if not dummy else ID + "-WRT"
    ID_HalfM = ID + "-HFM" if not dummy else ID + "-HMT"

    print("\n Got SN = " + SN )    # DBG --

    # compose the properties dictionary for the MAIN type
    prop_dict = {}
    if component_type in ['SENSOR', 'SENSOR_S_TEST', 'SENSOR_HALFMOONS', 'SENSOR_H_TEST']:
        # check that the date exists for this type
        if len(rdate) == 0 :
            print(" in <register_and_footwork>, got wrong date = " + rdate + ", returning...")
            return False
        # check that the date has a correct format
        print("rdate = " + rdate ) # DBG --
        try:
            true_date = datetime.strptime( rdate, "%d/%m/%Y" )
            #print("   true date = " + str( true_date ) )
        except ValueError:
            print(" ERROR: incorrect date format! Exiting... ")
            return False
        if bDBG:
            print(" given date = " + rdate + " true_date check = " + str(true_date) )

    if component_type in ['SENSOR', 'SENSOR_S_TEST'] :
        # didn't fail yet => use the date
        # VF, 2021-12-26: use proper ID
        prop_dict = { 'ID' : ID,
                      'DATE_RECEIVED' : rdate }
    elif component_type in ['SENSOR_HALFMOONS', 'SENSOR_H_TEST']:
        prop_dict = { 'ID': ID_HalfM,
                      'DATE_RECEIVED' : rdate }


    # make the input JSON file for the component
    dto = {
        "project"      : 'S',
        "subproject"   : subproject,
        "institution"  : institution,
        "componentType": component_type,
        "type"         : object_type,
        "serialNumber" : SN,
        "batches": {batch_code: batch_number},
        "properties"   : prop_dict
    }

    # print the input
    # pp = PrettyPrinter(indent = 1,width=200)
    if bDBG:
        print("PRINTING dto")
        print( json.dumps(dto, indent=2) )
    # pp.pprint(dto)

    # return False # DBG --
    # register the component (MAIN or halfmoon)
    try:
        Resp = c.post('registerComponent', json = dto)
    except Exception as e:
        print("post operation failed: " + SN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <register_and_footwork>")

        print(" in register_and_footwork: could not register the component ")
        print(e)
        return False

    # want to check the response
    if bDBG:
        print("//--- registration response")
        print( json.dumps(Resp, indent=2) )

    # find the code
    (err,oCode) = get_code(c, SN)
    if err : return False
        

    # then to register the parent wafer ----------------------------------------
    wSN = makeSN_wafer( SN )
    print("\n Got wafer SN = " + wSN )    # DBG --

    if wSN not in listW:

        # make the input JSON file for the component
        w_comp_type = 'SENSOR_WAFER'
        w_subtype = 'ATLAS18_WAFER'
        if dummy :
            w_comp_type = 'SENSOR_W_TEST'
            w_subtype = 'ATLASDUMMY18W'
        w_dto = {
            "project"      : 'S',
            "subproject"   : subproject,
            "institution"  : institution,
            "componentType": w_comp_type,
            "type"         : w_subtype,
            "serialNumber" : wSN,
            "batches"      : {batch_code: batch_number},
            "properties"   : {'ID': ID_Wafer, 'SENSOR_WAFER_INGOT_NUMBER': 'Unknown'} # since we dont' know it in this case
        }   
        if bDBG:
            print("PRINTING wafer dto")
            print( json.dumps(w_dto, indent=2) )
        #pp.pprint(w_dto)

        # register the component (wafer)
        try:
            wResp = c.post('registerComponent', json = w_dto)
        except Exception as e:
            print("post operation failed: " + wSN )
            if e.__class__.__name__ == 'Forbidden' :
                print("got bad connection in <register_and_footwork>")

            print(" in register_and_footwork: could not register the component ")
            print(e)
            return False
        # want to check the response
        if bDBG:
            print("//--- wafer registration response")
            print( json.dumps(wResp, indent=2) )

        # find codes of these objects
        (err,wCode) = get_code(c, wSN)
        if err : return False

        listW[wSN] = wCode
    else:
        # it's in => use the existing code
        wCode = listW[wSN]


    # then to assemble the new object and the wafer ---------------------------
    try:
        # aResp = c.post('assembleComponent', json = { 'parent': wSN, 'child': SN } )
        aResp = c.post('assembleComponent', json = { 'parent': wCode, 'child': oCode } )
    except Exception as e:
        print("post operation failed (assemble): " + wSN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <register_and_footwork>")

        print(" in register_and_footwork: could not register the component ")
        print(e)
        return False

    print(" ...assembled!")
    # want to check the response
    if bDBG:
        print("//--- assembly result")
        print( json.dumps(aResp, indent=2) )
    

    # then to disassemble -----------------------------------------------------
    # first wait - the DB may not be ready after the assembly
    #time.sleep(1.0)

    try:
        # dResp = c.post('disassembleComponent', json = { 'parent': wSN, 'child': SN, 'trashed': False } )
        dResp = c.post('disassembleComponent', json = { 'parent': wCode, 'child': oCode, 'trashed': False } )
    except Exception as e:
        print("post operation failed (disassemble): " + wSN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <register_and_footwork>")

        print(" in register_and_footwork: could not register the component ")
        print(e)
        return False

    print(" ...dis-assembled!")
    # want to check the response
    if bDBG:
        print("//--- dis-assembly result")
        print( json.dumps(dResp, indent=2) )
    
    # must've been a success
    return True



def main(args):
    iFile = args.iFile
    fDBG  = args.debug
    print(" Got input: ")
    print("   iFile     = " + iFile )
    print("   fDBG      = " + fDBG )

    bDBG = False
    if fDBG == 'no':
        bDBG = False
    elif fDBG == 'yes':
        bDBG = True
    else:
        print(" wrong input option for the debugging flag, exiting...")
        return

    # do some checks on the input file
    if len(iFile) == 0:
        print(" input file is not specified, exiting...")
        return

    lAbsPath = Path(iFile)
    if lAbsPath.is_file():
        with open(iFile,'r') as iF:
            lines = iF.readlines()
    else:
        print(" could not find the input file, exiting...")
        return

    # establish a DB client
    c = itkdb.Client()# expires_after=dict(days=1) )


    # Fine, start parsing the input file ------------------------
    institution = get_institution(lines[0])
    subproject = get_subproject_from_line(lines[1])
    if subproject == None:
        #means this is a "real" file (not dummy components)
        #subproject not yet defined! (is None)
        dummy = False
        component_list_start_line = 1
    else:
        #Note: subproject is this value for whole file
        dummy = True
        component_list_start_line = 2

    nTotal = 0
    nFail  = 0
    for line in lines[component_list_start_line:]:
        if line.startswith('#'): 
            #allow for commented lines
            continue
        rv = parse_line(line,dummy)
        if rv == None:
            #error reading line
            raise Exception("Error reading line: '{}'".format(line))
        sensor_type,vpx,component_type,rdate = rv                

        if not dummy:
            #extract subproject from sensor type
            subproject = get_subproject_from_sensor_type(sensor_type)
        # DBG --
        if fDBG:
            print("\n Got arguments:")
            print(" sensor_type    = " + sensor_type )
            print(" vpx            = " + vpx )
            print(" component_type = " + component_type )
            print(" subproject     = " + subproject )
            print(" institution    = " + institution )
            print(" dummy          = " + str(dummy) )
            print(" rdate          = " + rdate )

        res = register_and_footwork(c,bDBG,sensor_type,vpx,component_type, subproject, institution, dummy,rdate)
        nTotal += 1
        if not res:
            nFail += 1
            print("\n Got arguments:")
            print(" sensor_type    = " + sensor_type )
            print(" vpx            = " + vpx )
            print(" component_type = " + component_type )
            print(" subproject     = " + subproject )
            print(" institution    = " + institution )
            print(" dummy          = " + str(dummy) )
            print(" rdate          = " + rdate )
            print(" See failure !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("\n Total MAIN/halfmoon objects = " + str(nTotal) )
    print(" Got " + str(nFail) + " failures" )



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'to register the MAIN sensors and wafers, to associate and dis-associate them')
    parser.add_argument('-i', '--inputFile', dest = 'iFile', type = str, default = '', help = 'input file with <batch-wafer type real/dummy>')
    parser.add_argument('-d', '--debug', dest = 'debug', type = str, default = 'no', help = 'debugging printout')

    args = parser.parse_args()

    main(args)
