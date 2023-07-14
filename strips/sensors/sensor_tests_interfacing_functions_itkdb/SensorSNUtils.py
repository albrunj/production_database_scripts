#!/usr/bin/env python
from __path__ import updatePath
updatePath()

import dbAccess

_PREFIX = '20U'

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


# VF, 2021-06-04: to compose the (parent) wafer SN from the one from MAIN or Haflmoon
def makeSN_wafer(SN):
   #20 U XX YY AB 00000
    A = '0'
    B = '5'
    wSN = SN[:7] + A + B + SN[9:]
    return wSN


# VF, 2021-07-20: extract the sensor type from SN
def type_from_SN(SN):
    snType = SN[5:7]
    if snType == "SS" : return "ATLAS18SS"
    if snType == "SL" : return "ATLAS18LS"
    if snType == "R0" : return "ATLAS18R0"
    if snType == "R1" : return "ATLAS18R1"
    if snType == "R2" : return "ATLAS18R2"
    if snType == "R3" : return "ATLAS18R3"
    if snType == "R4" : return "ATLAS18R4"
    if snType == "R5" : return "ATLAS18R5"
    if snType == "SX" : return "ATLASDUMMY18"

    # Should never get here
    return "TypeError"


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
	if len(wafer_number) < 5:
		wafer_number = "0"*(5-len(wafer_number)) + wafer_number
	return batch_number,wafer_number


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
        return e,{}

    listObjCodes = []
    for anObj in Resp:
        objCode = anObj['code']
        listObjCodes.append( objCode )

    return error, listObjCodes


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


def get_testruns_4_comp(c, objCode):
    any_testruns_found = True
    try:
        testruns_resp = c.get('listTestRunsByComponent', json ={'component': objCode })
    except Exception as e:
        any_testruns_found = False
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_testruns_dict>")

    return any_testruns_found, testruns_resp


# VF, 2021-06-27: to upload a json file for a test run
def upload_testrun(c,test_data):
    try:
        Resp = c.post('uploadTestRunResults', json = test_data )
    except Exception as e:
        print("There was an issue with uploading the test results" )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_code>")
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


if __name__ == '__main__':
    print(makeSN('SENSOR', 'ATLAS18R0', '12345'))
    print(makeSN('SENSOR', 'ATLAS17LS', '98765'))
    print(makeSN('SENSOR_WAFER', 'ATLAS18LS', '12345'))
    print(makeSN('SENSOR_MINI', 'ATLAS18SS', '98765'))
