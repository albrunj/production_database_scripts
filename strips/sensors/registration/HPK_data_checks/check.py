#check.py
#this module should be used to check if all data attributes are present and valid, and identifies shifts starting at a key specified in "shiftkeys"
#this module doesn't care about line numbers or extra filler lines (e.g. doesn't catch repeated %IV)
import logging
import re

from __path__ import updatePath
updatePath()

from strips.sensors.registration.HPK_data_checks.check_non_regex_value import check_non_regex_value

#Known data glitches:
#1) shifted parameter values across many parameters
#2) extra key/line
#3) wrong ingot number

expected_keys_reduced_EC = [
    #"#General information ITEM section",
    #"%ITEM",
    "Identification Number",
    "Serial Number",
    "Sensor Type",
    #"",
    #"#Test information Test section",
    #"%TEST",
    "Test Date (DD/MM/YYYY)",
    "PROBLEM",
    "PASSED",
    #"",
    #"#Test data Data section",
    #"%DATA",
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
    #"",
    #"",
    #"",
    #"",
    #"#Defects section",
    #"%DEFECT",
    #"#DEFECT NAME",
    "Oxide pinholes",
    "Metal Shorts",
    "Metal Opens",
    "Implant Shorts",
    "Bias resistor disconnection",
    "Percentage of NG strips",
    #"",
    #"#IV raw data Raw data section",
    #"%RAWDATA",
    "IV Temperature(C)", #repeated!
    "Humidity (%)",
    "Voltage step (V)",
    "Delay time (second)",
    #"IV Characteristics (A)",
    #"#IV",
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
    #"",
    #"Id stability test @ 700V",
    "10 sec",
    "20 sec",
    "30 sec",
    #"",
    #"",
    #"#End of manufacturer data file"
]

# VF, 2021-08-18: to tune the length of SN, Wafer number digits
#r'^20US(E(S[0-5]|SX)|B(SS|SL|SX))\d{1,}',
#r'^VPX\d{5}-W\d{3}',
# VF, 2021-08-24: Damn, HPK used 2-digit number now
#r'^VPX\d{5}-W\d{3,5}',
# VF, 2021-10-20: And now we have to allow for both VPX and VPA
#    r'^VPX\d{5}-W\d{2,5}',
expected_values_regex_reduced_EC = [
    #r'',
    #r'',
    r'^20US(E(S[0-5]|SX)|B(SS|SL|SX))\d{7}',
    r'^VP(X|A)\d{5}-W\d{2,5}',
    r'^ATLAS(18(SS|LS|R[0-5])|DUMMY18)',
    #r'',
    #r'',
    #r'',
    None,
    r'^NO',
    r'^YES',
    #r'',
    #r'',
    #r'',
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
    #r'',
    #r'',
    #r'',
    #r'',
    #r'',
    #r'',
    #r'',
    None,
    None,
    None,
    None,
    None,
    None,
    #r'',
    #r'',
    #r'',
    r'^2[0-9]',
    r'^[2-5][0-9]',
    r'^20',
    r'^1',
    #r'',
    #r'',
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
    #r'',
    #r'',
    None,
    None,
    None,
    #r'',
    #r'',
    #r''
]

#define keys and values for barrel, only slightly different than EC
expected_keys_reduced_barrel = list(expected_keys_reduced_EC)
diff_index = expected_keys_reduced_EC.index("Bias resistor disconnection")
expected_keys_reduced_barrel[diff_index] = "Implant Opens"
expected_keys_reduced_barrel.insert(diff_index+1,"Microdischarge strips")
expected_values_regex_reduced_barrel = list(expected_values_regex_reduced_EC)
expected_values_regex_reduced_barrel.insert(diff_index+1,'')



#use re.sub('[^\d.,]' , '', x) to get float within string

#prescribe keys at which to check for shifts
shiftkeys = ["Substrate R Upper (kOhm.cm)"]

def check_value(sensor_type,line_ind,k,values,msg,shift=0,depth=0): 
    #sensor_type = 'EC' or 'barrel'
    #expected_keys = eval("expected_keys_reduced_{}".format(sensor_type))

    #parse value from val_str, and return None if invalid
    #print("line_ind,shift,len(vals)=",line_ind,shift,len(values))
    v = values[line_ind+shift]
    if sensor_type == 'barrel':
        expected_values_regex = expected_values_regex_reduced_barrel
    elif sensor_type == 'EC':
        expected_values_regex = expected_values_regex_reduced_EC
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

    if expected_value_regex == None:
        #not simple regex
        rv = check_non_regex_value(k,v,sensor_type,msg)
        v,msg,valid = rv
        if valid:
            return v,msg
    else:
        if bool(re.search(expected_value_regex,v)):
            shift = 0 #reset if doesn't look shifted anymore
            return v,msg
        else:
            if k.startswith("Substrate Lot No"):
                msg += "Ingot num warning '{}'\n".format(v)


    #value wasn't recognized for that key, so look above and below (shift?)
    if depth >= 1:
        #don't recurse more than once...return None here because the value for
        #key at expected_keys[line_ind+shift] is invalid
        return None,msg

    #test if shift has ended before returning None/looking for other nonzero shifts
    unshiftedval,msg = check_value(sensor_type,line_ind,k,values,msg,shift=0,depth=depth+1)
    if type(unshiftedval) == str:
        return unshiftedval,0,msg

    if k not in shiftkeys:
        return None,msg

    #search values above/below this line until a valid value is found, then store that line difference as the shift
    newval = None
    for i in range(1,max([len(expected_values_regex)-line_ind,line_ind])):
        #i is the shift
        check_ind1 = line_ind - i
        check_ind2 = line_ind + i
        if check_ind1 >= 0:
            #print("line_ind,check_ind1,len(vals)=",line_ind,check_ind1,len(values))
            newval,msg = check_value(sensor_type,line_ind,k,values,msg,shift=-i,depth=depth+1)
            if type(newval) == str:
                #this means valid value was found at a different key
                shift = -i #negative
                break
        if check_ind2 < len(expected_values_regex):
            newval,msg = check_value(sensor_type,line_ind,k,values,msg,shift=i,depth=depth+1)
            if type(newval) == str:
                #this means valid value was found at a different key
                shift = i #positive
                break

    if shift != 0:
        #if shift != 0, newval can't be None
        msg += "found shift of {} lines starting at key '{}'\n".format(shift,k)
        return newval,shift,msg

    return None,msg

def check_key(sensor_type,line_ind,actual_key,msg):
    # VF, 2021-08-13: switch from printing to logging
    logCK_ = logging.getLogger('LOG-CK_')
    to_log = logging.getLogger().hasHandlers() 

    #sensor_type = 'EC' or 'barrel'
    #parse key from key_str, and return None if invalid
    if sensor_type == 'barrel':
        expected_keys = expected_keys_reduced_barrel
    elif sensor_type == 'EC':
        expected_keys = expected_keys_reduced_EC
    else:
        raise RuntimeError('Unknown sensor type: \'%s\'' % sensor_type)
    # VF. 2021-08-22: had a crash with these exceptions
    # => will change to an explicit check
    #try:
    if line_ind < len(expected_keys):
        expected_key = expected_keys[line_ind]
        if actual_key == expected_key:
            return expected_key,line_ind,msg
    #except IndexError as e:
    else:
        if to_log:
            logCK_.error("TOO MANY LINES! possible repeat")
        else:
            print("TOO MANY LINES! possible repeat")

    #check if key is shifted or incorrect on this line_ind
    #either incorrect key or a shift
    print("Checking if key {} is at other line...".format(actual_key))
    new_line_ind = -1
    for i in range(1,max([len(expected_keys)-line_ind,line_ind])):
        check_ind1 = line_ind - i
        check_ind2 = line_ind + i
        if check_ind1 >= 0:
            if actual_key == expected_keys[check_ind1]:
                new_line_ind = check_ind1
                break
        if check_ind2 < len(expected_keys):
            if actual_key == expected_keys[check_ind2]:
                new_line_ind = check_ind2
                break

    if new_line_ind != -1:
        #print("FOUND KEY {} ON INCORRECT LINE (line {}), should be on line {}".format(actual_key,new_line_ind,line_ind))
        loc_msg = "FOUND KEY {} ON INCORRECT LINE (line {}), should be on line {}".format(actual_key,new_line_ind,line_ind)
        if to_log:
            logCK_.error( loc_msg )
        else:
            print( loc_msg )
        msg += "found key {} on incorrect line\n"
        k = expected_keys[new_line_ind]
        #print("returning key={}".format(k))
        loc_msg = "returning key={}".format(k)
        if to_log:
            logCK_.error( loc_msg )
        else:
            print( loc_msg )
        return k,new_line_ind,msg
    
    return None,line_ind,msg
