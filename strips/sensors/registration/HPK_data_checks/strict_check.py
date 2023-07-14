#strict_check.py
#this module should be used for strict errors--checks if keys/values are at correct/expected line numbers, doesn't look for shifts
import re

from strips.sensors.registration.HPK_data_checks.check_non_regex_value import check_non_regex_value
#Known data glitches:
#1) shifted parameter values across many parameters
#2) extra key/line
#3) wrong ingot number

#expected_key_prefixes = expected key for each line (in order)
expected_keys_EC = [
    "#General information ITEM section",
    "%ITEM",
    "Identification Number",
    "Serial Number",
    "Sensor Type",
    "",
    "#Test information Test section",
    "%TEST",
    "Test Date (DD/MM/YYYY)",
    "PROBLEM",
    "PASSED",
    "",
    "#Test data Data section",
    "%DATA",
    "IV Temperature(C)", #be careful, this is repeated!
    "IV Humidity(%)",
    "Deplation Volts (V)",
    "Leakage Current at Vfd + 50V (microA)",
    "Leakage current at 500 V (microA)",
    "Substrate Lot No.",
    "Substrate Type",
    "Substrate Orient",
    "Substrate R Upper (kOhm.cm)",
    "Substrate R Lower (kOhm.cm)",
    "Active thickness (nominal value)",
    "Polysilicon Bias Resistance Upper (MOhm)",
    "Polysilicon Bias Resistance Lower (MOhm)",
    "Onset voltage of Microdischarge (V)",
    "",
    "",
    "",
    "",
    "#Defects section",
    "%DEFECT",
    "#DEFECT NAME",
    "Oxide pinholes",
    "Metal Shorts",
    "Metal Opens",
    "Implant Shorts",
    "Bias resistor disconnection",
    "Percentage of NG strips",
    "",
    "#IV raw data Raw data section",
    "%RAWDATA",
    "IV Temperature(C)", #repeated!
    "Humidity (%)",
    "Voltage step (V)",
    "Delay time (second)",
    "IV Characteristics (A)",
    "#IV",
    "20",
    "40",
    "60",
    "80",
    "100",
    "120",
    "140",
    "160",
    "180",
    "200",
    "220",
    "240",
    "260",
    "280",
    "300",
    "320",
    "340",
    "360",
    "380",
    "400",
    "420",
    "440",
    "460",
    "480",
    "500",
    "520",
    "540",
    "560",
    "580",
    "600",
    "620",
    "640",
    "660",
    "680",
    "700",
    "",
    "Id stability test @ 700V",
    "10 sec",
    "20 sec",
    "30 sec",
    "",
    "",
    "#End of manufacturer data file"
]

# VF, 2021-08-18: to tune the length of SN, Wafer number digits
#r'^20US(E(S[0-5]|SX)|B(SS|SL|SX))\d{1,}',
#r'^VPX\d{5}-W\d{3}',
# VF, 2021-08-24: Damn, HPK used 2-digit number now
#r'^VPX\d{5}-W\d{3,5}',
# VF, 2021-10-20: And now we have to allow for both VPX and VPA
#r'^VPX\d{5}-W\d{2,5}',
expected_values_regex_EC = [
r'',
r'',
r'^20US(E(S[0-5]|SX)|B(SS|SL|SX))\d{7}',
r'^VP(X|A)\d{5}-W\d{2,5}',
r'^ATLAS(18(SS|LS|R[0-5])|DUMMY18)',
r'',
r'',
r'',
None,
r'^NO',
r'^YES',
r'',
r'',
r'',
r'^2[0-9]',
r'^[2-5][0-9]',
None,
None,
None,
r'^\d{1,}-\d{1,}$',
r'^(FZ1|\(FZ1\)|FZ-1)',
r'^(100|\(100\))',
None,
None,
r'^290',
None,
None,
None,
r'',
r'',
r'',
r'',
r'',
r'',
r'',
None,
None,
None,
None,
None,
None,
r'',
r'',
r'',
r'^2[0-9]',
r'^[2-5][0-9]',
r'^20',
r'^1',
r'',
r'',
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
None,
r'',
r'',
None,
None,
None,
r'',
r'',
r''
]

#define keys and values for barrel, only slightly different than EC
expected_keys_barrel = list(expected_keys_EC)
diff_index = expected_keys_EC.index("Bias resistor disconnection")
expected_keys_barrel[diff_index] = "Implant Opens"
expected_keys_barrel.insert(diff_index+1,"Microdischarge strips")
expected_values_regex_barrel = list(expected_values_regex_EC)
expected_values_regex_barrel.insert(diff_index+1,'')



#use re.sub('[^\d.,]' , '', x) to get float within string


def strict_check_value(sensor_type,line_ind,k,v,msg): 
    #sensor_type = 'EC' or 'barrel'
    #expected_keys = eval("expected_keys_{}".format(sensor_type))

    #parse value from val_str, and return None if invalid
    #print("line_ind,shift,len(vals)=",line_ind,shift,len(values))
    if sensor_type == 'barrel':
        expected_values_regex = expected_values_regex_barrel
    elif sensor_type == 'EC':
        expected_values_regex = expected_values_regex_EC
    else:
        raise RuntimeError('Unknown sensor type: \'%s\'' % sensor_type)
    try:
        expected_value_regex = expected_values_regex[line_ind]
        #expected_key = expected_keys[line_ind]
    except IndexError:
        return None,msg
    #print('EXPECTED VALUE REGEX IS {}'.format(expected_value_regex))
    #print("Shift = {}".format(shift))
    #print("parsing '{}','{}'".format(k,v))
    #print("regex = ",expected_value_regex)
    #print("depth",depth)

    #now k,v have no leading/trailing whitespace and no trailing \n's
     
    if expected_value_regex == None:
        #not simple regex
        rv = check_non_regex_value(k,v,sensor_type,msg)
        v,msg,valid = rv
        if valid: 
            return v,msg
    else:
        if bool(re.search(expected_value_regex,v)):
            return v,msg

    return None,msg

def strict_check_key(sensor_type,line_ind,actual_key,msg):
    #sensor_type = 'EC' or 'barrel'
    #key_str might have extra whitespace/chars
    #parse key from key_str, and return None if invalid
    #expected_value_regex = eval("expected_values_regex_{}[line_indn]".format(sensor_type))
    if sensor_type == 'barrel':
        expected_keys = expected_keys_barrel
    elif sensor_type == 'EC':
        expected_keys = expected_keys_EC
    else:
        raise RuntimeError('Unknown sensor type: \'%s\'' % sensor_type)
    try:
        #print("indx = " + str(line_ind) + ", array length = " + str(len(expected_keys)) )
        expected_key = expected_keys[line_ind]
        #print("actual_key,expected_key = '{}','{}'".format(actual_key,expected_key))
        if actual_key == expected_key:
            #print("Correct key")
            return expected_key,line_ind,msg
    except IndexError:
        #print(e,"TOO MANY LINES! possible repeat")
        msg += "Too many lines. Possibly a repeat somewhere?\n"
        #print("line ind =",line_ind,", len(expected_keys_{} = ".format(sensor_type), len(eval("expected_key_prefixes_{}".format(sensor_type))))

    #check if key is shifted or incorrect on this line_ind
    #either incorrect key or a shift
    ####################
    return None,line_ind,msg
