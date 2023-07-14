#
# VF, 2021-09-17: The data structures we use for the data summary.
# 
DESIGN = "1.0.0"


# Final states/destinations for the sensors
PROD_MAIN_STAGES = ['REGISTERED', 'SENS_TEST_STAGE', 'BLESSING',
                    "READY_FOR_MODULE","UNHAPPY","DAMAGED","PHANTOM","SPECIAL_USE","RETURNED"]
FINAL_STATES     = ["READY_FOR_MODULE","UNHAPPY","DAMAGED","PHANTOM","SPECIAL_USE","RETURNED"]

PROD_MAIN_TYPES = ['ATLASDUMMY18', 'ATLAS18LS', 'ATLAS18SS', 'ATLAS18R0', 'ATLAS18R1', 'ATLAS18R2', 'ATLAS18R3', 'ATLAS18R4', 'ATLAS18R5']



# the ID/Pass of the next 2 steps are the same variables:
# the assumption is that they are not present for the same objects in DB
# this was the case so far, since the tests wer5e enabled at diff times!
# --VF, 2021-09-17
MON_TESTS = { "MANUFACTURING18": { "id"                     : "hpkID",
                                   "passed"                 : "hpkPass",
                                   "SUBSTRATE_LOT_NUMBER"   : "ingot",
                                   "DEPLETION_VOLTAGE"      : "hpkVfd",
                                   "LEAKAGE_CURRENT_500V"   : "hpkI500V",
                                   "MICRODISCHARGE_VOLTAGE" : "hpkVbd",
                                   # artificial thing to fill in
                                   "hpkMaxNBad"             : "hpkMaxNBad",
                                   "IV_VOLTAGE"             : "hpkiv_v",
                                   "IV_CURRENT"             : "hpkiv_i",
                                   "CURRENT_STABILITY_10S_700V" : "hpkI10s",
                                   "CURRENT_STABILITY_20S_700V" : "hpkI20s",
                                   "CURRENT_STABILITY_30S_700V" : "hpkI30s",
                                   "Oxide Pinholes"         : "hpkListPinholes",
                                   "Metal Shorts"           : "hpkListMetShorts",
                                   "Metal Opens"            : "hpkListMetOpens",
                                   "Implant Shorts"         : "hpkListImplShorts",
                                   "Implant Opens"          : "hpkListImplOpens",
                                   "Microdischarge strips"  : "hpkListDischarge",
                                   "Bias Resistor Disconnection": "hpkListRbiasDisc",
                                   "Percentage of NG Strips": "hpkBadPerc" },
              "ATLAS18_VIS_INSPECTION_V1": { "id"           : "inspecID",
                                             "passed"       : "inspecPass",
                                             "COMMENTS"     : "inspecComm" },
              "ATLAS18_VIS_INSPECTION_V2": { "id"           : "inspecID",
                                             "passed"       : "inspecPass",
                                             "DAMAGE_TYPE1" : "inspecDmg1",
                                             "DAMAGE_TYPE2" : "inspecDmg2",
                                             "DAMAGE_TYPE3" : "inspecDmg3",
                                             "DAMAGE_TYPE4" : "inspecDmg4",
                                             "DAMAGE_TYPE5" : "inspecDmg5",
                                             "DAMAGE_TYPE6" : "inspecDmg6" },
              "ATLAS18_IV_TEST_V1": { "id"             : "ivID",
                                      "passed"         : "ivPass",
                                      "date"           : "ivDate",
                                      "I_500V"         : "I500V",
                                      "VBD"            : "Vbd",
                                      "RMS_STABILITY"  : "RMS700V",
                                      "VOLTAGE"        : "atliv_v",
                                      "CURRENT"        : "atliv_i" },
              "ATLAS18_CV_TEST_V1": { "id"             : "cvID",
                                      "passed"         : "cvPass",
                                      "VFD"            : "Vfd",
                                      "NEFF"           : "Neff",
                                      "ACTIVETHICKNESS": "actThick" },
              "ATLAS18_CURRENT_STABILITY_V1": { "id"              : "stabID",
                                                "passed"          : "stabPass",
                                                "ABS_I_LEAK_AV"   : "stabIleak",
                                                "I_LEAK_VARIATION": "stabIvar" },
              "ATLAS18_FULLSTRIP_STD_V1": { "id"                 : "fullstripID",
                                            "passed"             : "fullstripPass",
                                            "date"               : "stripDate",
                                            "runNumber"          : "stripRunNo",
                                            "SEGMENTNO"          : "segmentNo",
                                            "N_BADCLUSTER_MAX"   : "atlNbadSeq",
                                            "BAD_STRIP_FRACTION" : "atlNbadFrac",
                                            "LIST_SHORTS"        : "atlListShorts",
                                            "LIST_PINHOLES"      : "atlListPinholes",
                                            "LIST_IMPLANT_BREAKS": "atlListImplBreak",
                                            "LIST_METAL_SHORTS"  : "atlListMetalShorts",
                                            "LIST_OPEN_RESISTOR" : "atlListRbiasOpen",
                                            "LIST_RBIAS_DEFECT"  : "atlListRbiasDefect" },
              "ATLAS18_SHAPE_METROLOGY_V1": { "id"     : "shapeID",
                                              "passed" : "shapePass",
                                              "BOWING" : "Bow" },
              "ATLAS18_MAIN_THICKNESS_V1": { "id"         : "thickID",
                                             "passed"     : "thickPass",
                                             "AVTHICKNESS": "TH" },
              "ATLAS18_HM_THICKNESS_V1"  : { "id"         : "thickID",
                                             "passed"     : "thickPass",
                                             "AVTHICKNESS": "TH"  },
              # tests that we don't collect much data to the ntuple
              "ATLAS18_KEKTEST_NEW_V1"   : { "id"         : "kekID",
                                             "passed"     : "kekPass",
                                             "date"       : "kekDate",
                                             "runNumber"  : "kekRunNo",
                                             "SEGMENTNO"  : "kekSegNo" },
              "ATLAS18_KEKTEST_OLD_V1"   : { "id"         : "kekID",
                                             "passed"     : "kekPass",
                                             "date"       : "kekDate",
                                             "runNumber"  : "kekRunNo",
                                             "SEGMENTNO"  : "kekSegNo" },
              "ATLAS18_HANDLING_DAMAGE_V1" : { "id"       : "handleID",
                                               "passed"   : "handlePass",
                                               "DAMAGE_TYPE" : "handleDamage" },
              "ATLAS18_RECOVERY_V1"      : { "id"         : "recovID",
                                             "passed"     : "recovPass",
                                             "METHOD"     : "recovMeth" },
              "ATLAS18_SPECIAL_USE_V1"   : { "id"         : "specUseID",
                                             "passed"     : "specUsePass",
                                             "DESCRIPTION": "specUseDescr" }  }


# our keys from this uber-dictionary
MON_KEYS = ["testedAt"]  # the test data that we extract differently
STRIP_ATL_KEYS = []
STRIP_KEK_KEYS = []
for test in MON_TESTS:
    dictVars = MON_TESTS[test]
    for var in dictVars:
        V = dictVars[var]
        # Our Vis. Insp. versions overlap
        if V not in MON_KEYS:
            MON_KEYS.append( V )
            # a special list of keys for the strip test
            if test == 'ATLAS18_FULLSTRIP_STD_V1':
                STRIP_ATL_KEYS.append( V )
            if test in ['ATLAS18_KEKTEST_NEW_V1',
                        'ATLAS18_KEKTEST_OLD_V1'] :
                STRIP_KEK_KEYS.append( V )                        
        # end of checking if already in
    # end of loop over the variables for a test
# end of the loop over tests


# the keys to delete and add
DEL_KEYS = [ "hpkiv_v","hpkiv_i","hpkI10s","hpkI20s","hpkI30s",
             "hpkListPinholes",
             "hpkListMetShorts",
             "hpkListMetOpens",
             "hpkListImplShorts",
             "hpkListImplOpens",
             "hpkListDischarge",
             "hpkListRbiasDisc",
             "atliv_v","atliv_i",
             "stripDate",
             "stripRunNo",
             "atlListShorts",
             "atlListPinholes",
             "atlListImplBreak",
             "atlListMetalShorts",
             "atlListRbiasOpen",
             "atlListRbiasDefect",
             "kekDate",
             "kekRunNo" ]

# the keys to merge
MERGE_KEYS = { "inspecDmg" : [ "inspecComm",
                               "inspecDmg1", "inspecDmg2", "inspecDmg3", 
                               "inspecDmg4", "inspecDmg5", "inspecDmg6" ] }
# the SN properties
ADD_KEYS = [ "SN"   , 
             "code" ,
             #"Type" ,
             "rDate",
             "warFlag",
             "stage",
             "site"]

#----------------------------------------------------------------------
# for these, we expect to see the numbers -- will check!
NUM_KEYS = ['hpkVfd', 'hpkI500V', 'hpkVbd', 'hpkMaxNBad', 'hpkBadPerc', 'I500V', 'Vbd', 'RMS700V', 'Vfd', 'Neff', 'actThick', 'stabIleak', 'stabIvar', 'atlNbadSeq', 'atlNbadFrac', 'Bow', 'TH']
#----------------------------------------------------------------------

# the remaining summary keys
TABLE_KEYS = MON_KEYS.copy()
for aKey in DEL_KEYS:
    TABLE_KEYS.remove( aKey )

# add data about the SNs
for i,aKey in enumerate(ADD_KEYS):
    TABLE_KEYS.insert(i,aKey)

for aKey in MERGE_KEYS:
    lVals = MERGE_KEYS[aKey]
    first = True
    for aVal in lVals:
        # first replaced in-situ
        if first:
            first = False
            for i,el in enumerate(TABLE_KEYS):
                if el == aVal:
                    TABLE_KEYS[i] = aKey
        else:
            # the others are removed
            TABLE_KEYS.remove( aVal )
    #TABLE_KEYS.append( aKey )

print(TABLE_KEYS)


#---------- for the html header ---------------
HEAD_CASE = {'warFlag'  : 'golden',
             'inspecID' : "VisInsp", 
             'inspecDmg': "Damage", 
             'hpkID'    : "HPK", 
             'ingot'    : "ingot", 
             'hpkVfd'   : "Vfd", 
             'hpkI500V' : "I500V", 
             'hpkVbd'   : "Vbd", 
             'hpkMaxNBad': "MaxNBad", 
             'hpkBadPerc': "Bad%", 
             'ivID'     : "IV", 
             'I500V'    : 'I500V'  , 
             'Vbd'      : 'Vbd'    , 
             'RMS700V'  : 'RMS700V', 
             'cvID'     : "CV", 
             'Vfd'      : 'Vfd'      , 
             'Neff'     : 'Neff'     , 
             'actThick' : 'actThick' , 
             'stabID'   : "Stab", 
             'stabIleak': "Ileak", 
             'stabIvar' : "Ivar", 
             'fullstripID': "Strip", 
             'atlNbadSeq' : "NbadSeq", 
             'atlNbadFrac': "NbadFrac", 
             'shapeID'  : "Shape", 
             'Bow'      : "Bow", 
             'thickID'  : "Thick", 
             'TH'       : "TH", 
             'kekID'    : "KEK", 
             'handleID' : "handle", 
             'handleDamage' : "Damage", 
             'recovID'  : "recov", 
             'recovMeth': "Method", 
             'specUseID': "SpecUse", 
             'specUseDescr' : "Descr"}


#---------- for the evaluations ---------------
# IDs for the tests that we need to get done for *EVERY* sensor
NEED_ALL_IDs = [ 'inspecID'   ,
                 'hpkID'      ,
                 'ivID'       ,
                 'cvID'       ,
                 'shapeID'    ]
NEED_ALL_IDs_KEK = [ 'hpkID'  ,
                     'shapeID'    ]

# IDs for the tests that we need to get done on the sampling basis
NEED_SAMPLE_IDs = [ 'stabID'     ,
                    'fullstripID',
                    'thickID'    ]

# IDs for the tests where sampling is not embodies in this code (yet)
NEED_TODO_IDs = [ 'kekID'      ,
                  'handleID'   ,
                  'recovID'    ,
                  'specUseID'   ]

LIMITS = { 'hpkVfd'   : { 'oper': 'less', 'val': 360.0 }, # [V]
           'hpkI500V' : { 'oper': 'less', 'val':  10.0 }, # [uA] 
           'hpkVbd'   : { 'oper': 'more', 'val': 500.0 }, # [V]
           'hpkMaxNBad':{ 'oper': 'less', 'val':   9   }, # [consecutive bad strips]
           'hpkBadPerc':{ 'oper': 'less', 'val':   1.0 }, # [%]
           'I500V'    : { 'oper': 'less', 'val': 100.0 }, # [nA/cm^2]
           'Vbd'      : { 'oper': 'more', 'val': 500.0 }, # [V]
           'RMS700V'  : { 'oper': 'none', 'val':  -1.0 }, # [nA/cm^2 ?? should be in nA], no spec
           'Vfd'      : { 'oper': 'less', 'val': 360.0 }, # [V]
           'Neff'     : { 'oper': 'none', 'val':  -1.0 }, # [10^12 1/cm^3]
           'actThick' : { 'oper': 'more', 'val': 270.0 }, # [um]
           'stabIleak': { 'oper': 'less', 'val': 10000.0 }, # [nA ?]
           'stabIvar' : { 'oper': 'leeq', 'val':  0.15 }, # [1] calculated relative to the Ileak!!
           'atlNbadSeq' :{ 'oper': 'less', 'val':  9   }, # [consecutive bad strips]
           'atlNbadFrac':{ 'oper': 'less', 'val':  1.0 }, # [%]
           'Bow'      : { 'oper': 'leeq', 'val': 200.0 }, # [um]
           'TH'       : { 'oper': 'leeq', 'val':  15.0, 'cval': 320.0 } # [um] - tolerance around the central value
       }


#---------- Nicer site names ---------------
NICE_SITES = { "UCSC_STRIP_SENSORS" : "SCIPP" }
