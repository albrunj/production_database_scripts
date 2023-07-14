"""###Author: David Rousso and Dominic Jones"""
"""This is a file with all the configurations common to all scripts"""
import logging.config
import math
import os
import re
import string
import sys
import textwrap
from datetime import datetime
from os.path import abspath
from os.path import dirname
from os.path import join

import itkdb
import numpy as np
#import __path__ #comment out this line when debugging
#import dbAccess

stream_handler = logging.StreamHandler()
stream_handler.terminator = ""
file_handler =logging.FileHandler("logfile.log")
file_handler.terminator = ""
logging.basicConfig(
    level=logging.INFO,
    format=(" %(message)s"),
    handlers=[
        file_handler,
        stream_handler
    ]
)
logger = logging.getLogger()
sys.stdout.write= logger.info

now = datetime.now() # current date and time
date_and_time = now.strftime("%d %b %Y, %H:%M:%S")
print("\n\n\n")
# Current date and time to distinguish different logs in the log file
print("* * * * * * * * * *  Current date and time: ".center(80),date_and_time, "* * * * * * * * * *")

#Algorithm Version
ALGORITHM_VERSION="1.1.7"

#ITK DB Things
ITK_PROJECT='S'

# For ITK_COMPONENTTYPE='SENSOR_H_TEST' set ITK_MAIN_COMPONENT="SENSOR_S_TEST", for ITK_COMPONENTTYPE='SENSOR_HALFMOONS' set ITK_MAIN_COMPONENT="SENSOR"

#ITK_COMPONENTTYPE='SENSOR_HALFMOONS'
ITK_COMPONENTTYPE='SENSOR_H_TEST'#dummy halfmoons

#ITK_MAIN_COMPONENT="SENSOR"
ITK_MAIN_COMPONENT="SENSOR_S_TEST"#dummy sensors

#######NEW FROM VITALIY
### Names of Tests on the ITK DB
TestType_IV='ATLAS18_IV_TEST_V1' 
TestType_CV='ATLAS18_CV_TEST_V1' 
TestType_Metrology='ATLAS18_SHAPE_METROLOGY_V1'
TestType_Strip='ATLAS18_FULLSTRIP_STD_V1'
TestType_Stability='ATLAS18_CURRENT_STABILITY_V1'
TestType_Manufacturing='MANUFACTURING18'
TestType_IV_Hammamatsu='MANUFACTURING18'
TestType_Thickness='ATLAS18_MAIN_THICKNESS_V1'
TestType_Thickness_Halfmoons='ATLAS18_HM_THICKNESS_V1'
#######################################################################################################
### SECTION 1:
# Things that WILL need to be changed by institution. 

#ITK Name of Default Institution
DefaultInstitute='FZU'

#Path to local shorthand to wafer/batch conversion file. Set to None if you do not have this.
#First row is header
#shorthand;Batch-Wafer;Manufacturer;Type;Location;Assembled?
#710004;VXX71041-W04;Hamamatsu;ATLAS07;Cambridge;false
### THIS MUST BE AN ABSOLUTE PATH!!
shorthandpath=abspath(join(dirname(__file__),"Example Files","Example Shorthand Table","components.csv"))

#Default output filepath for analysis report
defaultoutputfile=abspath(join(dirname(__file__),"Example Files","Example HTML Reports","TestHTMLReport.html"))


#######################################################################################################
### SECTION 2:
# Things that MAY need to be changed by institution depending on the local test file formats
# Most of these are to deal with alternate names of things in local test files.

#Alternate names for the same institutions in LOCAL test files: (key is ITK name)
alternateinstitutenames={
                            'FZU':['Prague', 'FZU', 'PRG']
            }

#Alternate names for the same tests in LOCAL test files: (key is ITK name)
alternatetestnames={
                    TestType_CV            :['SENSOR_CV','CV Scan','CVScan','Depletion','CV'],
                    TestType_IV            :['SENSOR_IV','IV Scan','IVscan','IV'],
                    TestType_Stability     :['SENSOR_STABILITY','Current Stability','CurrentStability'],
                    TestType_Strip         :['SENSOR_STRIP_TEST','Full Strip Test'],
                    TestType_Metrology     :['SENSOR_BOW'],
                    TestType_Manufacturing :['MANUFACTURING'],
                    TestType_Thickness     :['AVTHICKNESS'],
                    TestType_Thickness_Halfmoons    :['AVTHICKNESS'],
                   }

#Alternate names for the same wafer types in LOCAL test files: (key is ITK name)
alternatetypenames={
                    'NARROW'            :['ATLAS12SS'],
                    'R0'                :['ATLAS12EC']
                   }

#Alternate names for the same column names in LOCAL test files: (key is TESTDICTLIST name)
alternatecolumnnames={
                          'TABLE_Voltage[V]':['Voltage[V]','Voltage','Volts','Voltage[mV]'],#
                          'TABLE_Vnominal[V]':['Vnominal'],#
                          'TABLE_Capacitance[pF]':['Capacitance[pF]','Capacitance(pF)','Capacitance'],#
                          'TABLE_Resistance[MOhm]':['Resistance[MOhm]','Resistance','Resistance[kOhm]'],#
                          'TABLE_Temperature[°C]':['Temperature[°C]','Temperature', 'Temperature[C]', 'Temp[C]'],
                          'TABLE_Current[nA]':['Current[nA]','Current'],#
                          'TABLE_ProbeplanIndex':['ProbeplanIndex'],
                          'TABLE_Flag':['Flag'],
                          'TABLE_PinholeFlag':['PinholeFlag'],
                          'TABLE_Humidity[%]':['Humidity [%]','Humidity[%]'],
                          'TABLE_Time[s]':['Time[s]'],
                          'TABLE_Shunt_voltage[mV]':['Shunt_voltage[mV]'],
                          'TABLE_X[mm]':['X[mm]','X-Pos[mm]'],
                          'TABLE_Y[mm]':['Y[mm]','Y-Pos[mm]'],
                          'TABLE_Z[mm]':['Z[mm]','Z-Pos[mm]'],
                          'TABLE_Z_bow[mm]':['Z_bow[mm]'],
                          'TABLE_Current_AC[nA]'  :["Current_AC[nA]"],
                          'TABLE_Current_DC[nA]'  :["Current_DC[nA]"],
                     }

#These are values in the header to be treated as "None"
valuestotreatasNone=['Not known', 'Not known Not', 'known','','None']

#If the strip test `TestType` has the segment included in the name, put the regex for the `TestType` format here 
#where the first capture group is the TestType and the second is the segment so we can separate them
StripTestRegexString=['(.*) - S[0-9] - Segment.*([0-9]).*','(.*) S[0-9] - Segment.*([0-9]).*','(.*) - Segment.*([0-9]).*','(.*) - Seg ment.*([0-9]).*']

#If your temperature is hidden in your Settings field, include a regex here to extract it.
TemperatureRegexString=['Temperature ([0-9,\-,\.]*)'] #in settings

#If your length and voltage for your stability test is hidden in your Settings field, include a regex here to extract it
#The first capture group is the length and the second is the voltage.
LengthVoltageRegexString=['([0-9,\.]*)h@([0-9,\-,\.]*)V'] #in settings

#These are a list of possible delimeters that will be looked through for the table
delimiterslist=[' ','\t'] #for table reading



#######################################################################################################
### SECTION 3:
# Wafer properties are now stored in StandardWaferProperties.py

from StandardWaferProperties import StripLengthDict,AreaDict

#######################################################################################################
### SECTION 4:
# Things that may need to be changed for defining the standard data format if you want to convert to it

#The columns that each testtype needs. 
#NOTE THAT THIS ASSUMES THAT THE UNIT YOU SET FOR THE TESTDICTLIST ARE THE SAME AS WHAT YOU WANT IN THE STANDARD FORMAT
ColumnsDict={
         TestType_IV        :['TABLE_Voltage[V]','TABLE_Current[nA]','TABLE_Shunt_voltage[mV]'],
         TestType_CV        :['TABLE_Voltage[V]','TABLE_Capacitance[pF]','TABLE_Resistance[MOhm]'],
         TestType_Strip     :['TABLE_ProbeplanIndex','TABLE_Current[nA]','TABLE_Capacitance[pF]','TABLE_Resistance[MOhm]'],
         TestType_Stability : ['TABLE_Time[s]','TABLE_Temperature[°C]','TABLE_Humidity[%]','TABLE_Current[nA]','TABLE_Shunt_voltage[mV]'],
         TestType_Metrology :['TABLE_X[mm]','TABLE_Y[mm]','TABLE_Z[mm]','TABLE_Z_bow[mm]']
        }

#The standard file dataformat for each test type
FormatFilesDict={
         TestType_IV        :"STANDARD_2020_10_26_IV.txt",
         TestType_CV        :"STANDARD_2020_10_26_CV.txt",
         TestType_Strip     :"STANDARD_2020_10_26_STRIPS.txt",
         TestType_Stability :"STANDARD_2020_10_26_STABILITY.txt",
         TestType_Metrology :"STANDARD_2020_10_26_BOW.txt",
         TestType_Thickness :"STANDARD_2021_4_THICKNESS.txt",
         TestType_Thickness_Halfmoons :"STANDARD_2021_4_THICKNESS.txt",
        }        

#The delimiter to use for the standard tables
standarddelimiter='\t'

#table formatting
floatformat='{0:09.2f}'
intformat='{0:07d}'

#The prefix to put in front of the standard file filename
standardfilenameprefix="STD_"


#######################################################################################################
### SECTION 5:
# Things that may need to be changed for the report generation and analysis

#Test Voltage for IV Test: current at this reading is printed out and recorded in the WAFERDICT, (e.g. to make histograms with) 
TestV=500

#Maximum Humidity allowed
MaxHumidity = 20

#rgb values for colours in report
colorlistonoff={
    'LOCAL_Pass':(0, 230, 118), 
    'LOCAL_SoSo':(255, 215, 64), 
    'LOCAL_Fail':( 244, 67, 54 ), 
    'LOCAL_MeasErr':(0, 229, 255),
    'LOCAL_Unknown':(207, 216, 220),
    'ITKDB_Pass':(27,94,32), 
    'ITKDB_SoSo':(255, 111, 0), 
    'ITKDB_Fail':(183, 28, 28), 
    'ITKDB_MeasErr':(25, 118, 210),
    'ITKDB_Unknown':(84, 110, 122)
}

#Number of points that the fit curve in the interactive plots should have
fitnpoints=30

#sig figs to display in valuse in the table
sig_figs=5

#whether or not to use si suffixes in the values in the table
si=True

#What fields to display for what test types. Key is variable, value is display prefix
DisplayFieldsForTestTypes={
    #TestType_Manufacturing:{'Decision':'',
    #                        'Timestamp':'',
    #                        'Defects':'Defects='},
    TestType_Thickness:{'Decision':'',
                        'Filename':'',
                        'Timestamp':'',
                        'Flags':'',
                        },
    TestType_Thickness_Halfmoons:{'Decision':'',
                        'Filename':'',
                        'Timestamp':'',
                        'Flags':'',
                        },
}
'''
    TestType_Metrology:{'Decision':'',
                        'Filename':'',
                        'Timestamp':'',
                        'Flags':'',
                        'MaxBow[um]':'Max Bow [um]=',
                        'AvgBow[um]':'Avg Bow [um]=',
                        'StdBow[um]':'Std Bow [um]='},
    TestType_IV_Hammamatsu:{'Decision':'',
                 'Filename':'',
                 'Timestamp':'',
                 'Flags':'',
                 'IDataAtTestV':"I at {0} V [nA/cm^2]=".format(TestV),
                 "MicroDischargeV":"Breakdown Voltage[V]=",
                 'Defects':'Defects='}, #Added due to issues of manufacturing and Hammatsu being the same
    TestType_IV:{'Decision':'',
                 'Filename':'',
                 'Timestamp':'',
                 'Flags':'',
                 'IDataAtTestV':"I at {0} V [nA/cm^2]=".format(TestV),
                 "MicroDischargeV":"Breakdown Voltage[V]="},
    TestType_CV:{'Decision':'',
                 'Filename':'',
                 'Timestamp':'',
                 'Flags':'',
                 'Vdep[V]': 'Depletion Voltage [V]=',
                 'Dfull[um]':'Active Thickness [um]=',
                 'Neff[1e12/cm^3]':'Neff[1e12/cm^3]='},
    TestType_Stability:{'Decision':'',
                        'Filename':'',
                        'Timestamp':'',
                        'Flags':'',
                        'AbsILeakAvg[nA]':'AbsILeakAvg[nA]=',
                        'ILeakVariation':'ILeakVariation='},
    TestType_Strip:{'Decision':'',
                    'Filename':'',
                    'Timestamp':'',
                    'Segment':'Segment ',
                    'ChannelRange':'Probed Range: ',
                    'Flags':'',
                    'BadChannelsDictConcise':'Bad Channels: '},
    '''



#######################################################################################################
### SECTION 6:
# Things that may need to be changed if you need to alter the test type formats

    
### Keys of the TESTDICTLIST

#Date and Time are protected but not in the key list!!!

#This is the standard datafields for our standard format (for single values)
#Note that 'Date', 'Time', and 'BatchWaferShorthand' are protected fields
#BatchWaferShorthand is for a field which is sometimes Shorthand, sometimes, Component, or sometimes a 
#Combined Batch and Wafer like VPX30816-W0163

datafields=[
                'Filename',
                'Filepath',       
                'Component',         #This is the Serial Number
                'Batch',
                'Wafer',
                'Shorthand',
                'Manufacturer',
                'Type',              #i.e. ATLAS17LS
                'Institute',         #This is using the ITK Database conventions!!
                'Timestamp',
                'TestType',
                'Settings',
                'Instrument',
                'Temperature[°C]',
                'Humidity[%]',
                'Voltage[V]',
                'Frequency[kHz]',
                'TestTimeLength[hr]',
                'Segment',
                'RunNumber',
                'TimeofUpload',
                'TestID',
                'ComponentCode',
                'DataFormat',        #'FromITKDatabase' if from database
                'numColumns',
                'numRows',
                'strFormat',
                'MetrologyVersion',
                'MetrologyFormat',
                'Vbias_SMU',       ##FROM NEW STANDARD BART FORMAT
                'Rseries[MOhm]',
                'Test_DMM',
                'Rshunt[MOhm]',
                'LCR',
                'Circuit',
                'Amplitude[V]',
                'Vbias[V]',
                'Test_SMU',
                'Rseries_Test[MOhm]',
                'CMM',
                'Probe',
                'OtherInfo',
                'OtherTables',
                'OtherColumns',
                'Other',
                'Defects',
                'AvThickness',
           ]

#This is the standard datafields for our standard format (for table entries) 
tablefields=[
                 'TABLE_Voltage[V]',
                 'TABLE_Current[nA]',
                 'TABLE_Capacitance[pF]',
                 'TABLE_Resistance[MOhm]',
                 'TABLE_Time[s]',
                 'TABLE_Temperature[°C]',
                 'TABLE_Humidity[%]',
                 'TABLE_ProbeplanIndex',
                 'TABLE_Flag',
                 'TABLE_PinholeFlag',
                 'TABLE_Vnominal[V]',
                 'TABLE_MetUnknownNumber',
                 'TABLE_MetTolerance',
                 'TABLE_X[mm]',
                 'TABLE_Y[mm]',
                 'TABLE_Z[mm]',
                 'TABLE_Z_bow[mm]',
                 'TABLE_Shunt_voltage[mV]'
            ]
tablefields=list(set(tablefields+list(alternatecolumnnames.keys())))

SpecialMetrologyFormats=["0Metrology.txt"]
SpecialMetrologyPointRegex={
    """\s*0mm Point True Position                   ,             ,             ,             ,             ,             ,             ([\-\.0-9]*),        ([\-\.0-9]*),        Fail
X-Pos         ([\-\.0-9]*)
Y-Pos         ([\-\.0-9]*)
Z-Pos         ([\-\.0-9]*)""":['TABLE_MetUnknownNumber','TABLE_MetTolerance','TABLE_X[mm]','TABLE_Y[mm]','TABLE_Z[mm]']
}

#This is the standard datafields for our standard format AFTER the test has been processed by our analysis functions!
processedfields=[
                    'AlgorithmVersion',
                    'Decision',
                    'Flags',
                    'xdata',
                    'ydata',     
                    'xfit',
                    'yfit',  
                    'popt',
                    'R',    
                    'norm',           
                    'popt',    
                    #CV
                    'Vdep[V]',
                    'Neff[1e12/cm^3]',
                    'Dfull[um]',    
                    #Stability
                    'AbsILeakAvg[nA]',       
                    'ILeakVariation',
                    'CurrentOrShuntV', 
                    'Ivariation', #Can be removed?
                    #Strip
                    'N_badcluster_max',
                    'Bad_strip_fraction[%]',
                    'ChannelRange',
                    'NumBadChannels',
                    'BadChannelsList',
                    'BadChannelsDict',
                    'NumSoSoChannels',
                    'SoSoChannelsList',
                    'SoSoChannelsDict',
                    'NumMeasErrChannels',
                    'MeasErrChannelsList',
                    'MeasErrChannelsDict',
                    'NumBadChannelsNoMeasErr',
                    'BadChannelsNoMeasErrList',
                    'BadChannelsNoMeasErrDict',
                    'List_pinholes',
                    'List_implant_break',
                    'List_metal_short',
                    'List_open_resistor',
                    'List_rbias_defect',
                    'BadChannelsDictConcise',
                    'List_shorts',
                    'List_bad_contact',
                    'N_strips',
                    #IV
                    'PassIV',
                    'ExceedImax',
                    'IDataAtTestV',
                    'MicroDischarge',
                    'MicroDischargeV',
                    'RMS_Stability[nA]',
                    #Metrology
                    'TABLE_Z_bow[mm]',
                    'MaxBow[um]',
                    'AvgBow[um]',
                    'StdBow[um]',
        ]

    
#######################################################################################################
### SECTION 7:
# Things that may need to be changed if you need to mess with the ITK API side of things

#This is a map of the database's names for test results to our names for them for each test.
APIAlternateNamesValues={
    #In parameters and properties only. Note that only keys that appear in fullkeylist above will actually be imported. 
    'Component'             :['SENSOR_TEST_SN','Sensor Serial Number','SERIAL_SCV','SENSOR_ST_SN','SENSOR_SN'],
    'RunNumber'             :["RUNNUMBER"],
    'Settings'              :['COMMENTS'],
    'AlgorithmVersion'      :["ALGORITHM_VERSION"],
    'Temperature[°C]'       :['TEMPERATURE','SENSOR_T_CV','TEMP_S','SENSOR_TEST_TEMP'],
    'Humidity[%]'           :['HUMIDITY','SENSOR_H_CV','HUMIDITY_S','SENSOR_TEST_HUMIDITY'],
    'Instrument'            :['SENSOR=_MU_CV','SENSOR_MU','SENSOR_STA_MU','SENSOR_TEST_MU','INSTRUMENT'],
    'Voltage[V]'            :['SENSOR_STA_SETV','SENSOR_TEST_VB'],#
    'Frequency[kHz]'        :['FREQUENCY','S_FREQ','SENSOR_TEST_FREQ'],#
    'Amplitude[V]'          :["AMPLITUDE"],
    'LCR'                   :["LCR"],
    'Vbias_SMU'             :["VBIAS_SMU"],
    'Rseries[MOhm]'         :["RSERIES"],
    'Rseries_Test[MOhm]'    :["RSERIES_TEST"],
    'Vbias[V]'              :["VBIAS"],
    'Circuit'               :["CIRCUIT"],
    'Rshunt[MOhm]'          :["RSHUNT"],
    'Test_DMM'              :["TEST_DMM"],
    'TestTimeLength[hr]'    :["DURATION"],
    'Segment'               :["SEGMENTNO"],
    'Test_SMU'              :["TEST_SMU"], 
    'CMM'                   :['CMM'],
    'Probe'                 :["PROBE"],
    #CV
    'Vdep[V]'               :["VFD"],
    'Neff[1e12/cm^3]'       :["NEFF"],
    'Dfull[um]'             :["ACTIVETHICKNESS"],
    #Stability
    'AbsILeakAvg[nA]'       :["ABS_I_LEAK_AV"],
    'ILeakVariation'        :["I_LEAK_VARIATION"],
    #Strip
    'N_badcluster_max'      :["N_BADCLUSTER_MAX"],
    'Bad_strip_fraction[%]':["BAD_STRIP_FRACTION"],
    'N_strips'              :["NSTRIPS"],
    #IV
    'IDataAtTestV'          :["I_500V"],
    'MicroDischargeV'       :["VBD"],
    'RMS_Stability[nA]'     :['RMS_STABILITY'],
    #Metrology
    'MaxBow[um]'            :["BOWING"],   
    #Thickness
    'AvThickness'           :["AVTHICKNESS"],
}

APIAlternateNamesTABLES={
    'TABLE_Voltage[V]'      :['VOLTAGE','VOLTAGE ','IV_VOLTAGE','SENSOR_CV_V','SENSOR_VOLTAGE'],#
    'TABLE_Current[nA]'     :['CURRENT','CURRENT ','IV_CURRENT','SENSOR_CURRENT','SENSOR_STA_CURRENT','SENSOR_TEST_CURRENT'],#
    'TABLE_Capacitance[pF]' :['CAPACITANCE','SENSOR_CV_C','SENSOR_TEST_CAP'],#
    'TABLE_Resistance[MOhm]':['RESISTANCE','SENSOR_CV_R','SENSOR_TEST_RES'],#
    'TABLE_Temperature[°C]' :['TEMPERATURE','SENSOR_STA_TEMP'],
    'TABLE_Humidity[%]'     :['HUMIDITY','SENSOR_STA_HUM'],
    'TABLE_Time[s]'         :['TIME','SENSOR_STA_TIME'],
    'TABLE_ProbeplanIndex'  :["PROBEINDEX",'SENSOR_TEST_PPI'],
    'TABLE_Shunt_voltage[mV]':["SHUNT_VOLTAGE"],
    'TABLE_X[mm]'           :["X"],
    'TABLE_Y[mm]'           :["Y"],
    'TABLE_Z[mm]'           :["Z"],
    'TABLE_Z_bow[mm]'       :["Z_BOW"],
    'TABLE_Current_AC[nA]'  :["CURRENT_AC"],
    'TABLE_Current_DC[nA]'  :["CURRENT_DC"],
    'List_metal_short'      :["LIST_METAL_SHORT"],
    'List_implant_break'    :["LIST_IMPLANT_BREAK"],
    'List_pinholes'         :["LIST_PINHOLES"],
    'List_open_resistor'    :["LIST_OPEN_RESISTOR"],
    'List_rbias_defect'     :["LIST_RBIAS_DEFECT"],
    'List_shorts'           :["LIST_SHORTS"],
}
    
#However keys added here which don't exist in fullkeylist can be coded for stuff that needs processing (like time->timestamp) #for upload.
APIAlternateNamesFake={
    'Time'                 :['SENSOR_TEST_TT','SENSOR_TT_CV','SENSOR_TT_CV','TIME','SENSOR_TT'] 
}

NoneInt=[] #What to say a none integer/float is in the database
#NoneInt=-999
NoneInTable=-9999
NoneList=[[],'',-9999,-999999999,None,NoneInt,NoneInTable,{}] #All the forms "None" can take in the database (when checking for duplicates)


#When uploading, what to put if something is None
def NoneOutputType(ParamType):
    #return {}
    
    if ParamType[2]!=True:
        return None
    else:
        if ParamType[1]=='array':
            return []
        elif ParamType[1]=='single':
            if ParamType[0]=='string':
                return '' 
            else:
                return NoneInt
        else: 
            errprint('Data Type Not Recognized',str(ParamType))
            return {}
    

#######################################################################################################
### SECTION 8:
# Delving deeper. This is for telling if files are duplicates of each other

#Normally only keys that are in the ITK DB that are not processed fields will be checked except:

#Will definitely check these fields
KeysMustCheck=['Timestamp', 'TestType', 'ComponentCode', 'Segment']

#Will definitely ignore these fields
KeysToIgnore=['Filename','Filepath','DataFormat','TestID', 'numRows','numColumns','Settings','RunNumber'] 



#######################################################################################################
#######################################################################################################
#######################################################################################################

### THINGS BELOW HERE SHOULD NOT NEED TO BE TOUCHED

#Set token in environment
"""
tokenfile=os.path.join(os.path.dirname(os.path.realpath(__file__)), ".env")
def tryimporttoken():
    token=None
    try:
        with open(tokenfile,'r',encoding='utf-8',errors='ignore') as f:
            token=f.read()
            if token=='':
                token=None        
    except:
        print('Error accessing .env')
    #If the file is openable and not empty, extract token
    #delete the file after extracting the token. The token will be rewritten at the end of CommonConfig, so if the token has expired
    #and an error arises, it will force reauthentication
    #dbAccess.token=token
    itkdb.token=token
    with open(tokenfile,'w',encoding='utf-8',errors='ignore') as f:
        f.write('')
   
def savetoken():
    with open(tokenfile,'w',encoding='utf-8',errors='ignore') as f:
        f.write(dbAccess.token)
     
        
tryimporttoken()
"""
#######################################################################################################
### SECTION A:
# This deals with getting the inputs above into a palatable form


### Combine All Fields into a single full key list
# Add metrology fields to the tablefiels
mettablefields=[]
for values in SpecialMetrologyPointRegex.values():
    mettablefields.extend(values)
mettablefields=set(mettablefields)
tablefields+=mettablefields
#add datafields, table fields, and processed fields into fullkeylist
fullkeylist=datafields
fullkeylist.extend(tablefields)
fullkeylist.extend(processedfields)


### Add Alpha to colour list for hover on/hover off
colorlistonoffuseful={}
for key in colorlistonoff.keys():
    colorlistonoffuseful[key]=['rgba({0},{1},{2},1)'.format(*colorlistonoff[key]),'rgba({0},{1},{2},0.2)'.format(*colorlistonoff[key])]


    
#######################################################################################################
### SECTION B:
# This is a list of hardcoded internal variables

#This will search for all data format .txt files NON-recursively under this directory. 
#This is so the names of the data formats will be unique!
dataformatpath=os.path.join(os.path.dirname(os.path.realpath(__file__)), "DataFormats")+'/' 

#Shorthand to Batch/Wafer Data
ShorthandFields=['Shorthand','Batch','Wafer','Manufacturer','Type','CurrentLocation','Assembled']
#Note that this is hardcoded since Batch and wafer are combined in the same field in the shorthand file

#For storing downloaded tests locally so we don't need to keep re-downloading them.
#Delete this file in your folder to make the code download everything anew.
from os.path import dirname, join, abspath

if ITK_COMPONENTTYPE=='SENSOR_HALFMOONS':
    picklefilename=abspath(join(dirname(__file__),'SENSOR_HALFMOON_ITK_Test_Dictionary_List_Pickle.txt') )
    APIpicklefilename=abspath(join(dirname(__file__),'SENSOR_HALFMOON_API_ITK_Test_Dictionary_List_Pickle.txt' ))
if ITK_COMPONENTTYPE=="SENSOR_H_TEST":
    picklefilename=abspath(join(dirname(__file__),'SENSOR_H_TEST__ITK_Test_Dictionary_List_Pickle.txt' ))
    APIpicklefilename=abspath(join(dirname(__file__),'SENSOR_H_TEST__API_ITK_Test_Dictionary_List_Pickle.txt' ))

    
#possible delimters between batch and wafer if they are combined
delims=['-W',' W','-','.','_','R','/W','/',' '] 

#for date time standardization
DateRegexStringList=['([0-9]{1,2}) ([A-Z][a-z]{2}) ([0-9]{4})',
                         '([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})',
                         '([0-9]{1,2})/([0-9]{1,2})/([0-9]{2})',
                         '.*, ([A-Z][a-z]{2}) ([0-9]{1,2}), ([0-9]{4})',
                         '([0-9]{1,2}).([0-9]{1,2}).([0-9]{4})',
                     '([0-9]{1,2}) ([A-Z][a-z]*) ([0-9]{4})',
                     '([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})',
                        ]
TimeRegexStringList=['([0-9]{2}):([0-9]{2}):([0-9]{2})',
                         ' *([0-9]{1,2}):([0-9]{2}):([0-9]{2}) ([apAP])[mM] BST',
                         ' *([0-9]{1,2}):([0-9]{2}):([0-9]{2}) ([apAP])[mM] GMT',
                         ' *([0-9]{1,2}):([0-9]{2}):([0-9]{2}) ([apAP])[mM]',
                         '([0-9]{2}):([0-9]{2})'
                        ]     
MonthList=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
LongMonthList=['January','February','March','April','May','June','July','August','September','October','November','December']
MonthListUpper=[i.upper() for i in MonthList]
LongMonthListUpper=[i.upper() for i in LongMonthList]


#for error and normal print outs
width=os.get_terminal_size().columns
width=120
prefix1=' '*4
prefix2=' '*8
prefixe='*** '

#Allowed characters for variable names for plotting backend in report
GoodChars=string.ascii_letters+string.digits+'_'+' ' 


#Physics Constants
mm=1e-3
cm=1e-2
um=1e-6
pF=1e-12
e=1.602e-19
eps0=8.8541878128e-12
epsr=11.75

client = itkdb.Client()

APIList_SN = client.get("listComponents",json={"filterMap": {"project": ITK_PROJECT, 'componentType': [ITK_MAIN_COMPONENT]},
                                         #   "includeProperties":"true",
                                            "outputType": "full", 
                                            "pageInfo": {
                                            "pageIndex": 0,
                                            "pageSize": 1000000
                                                }
                                        } 
                                    )
APIList_SN=[i for i in APIList_SN if i['state']=='ready']
'''
APIList_SN=dbAccess.extractList("listComponents", method = "GET",
                                    data = {"project": ITK_PROJECT, 'componentType':ITK_MAIN_COMPONENT,
                                        "includeProperties": True,
                                        "pageInfo": {
                                        "pageIndex": 0,
                                        "pageSize":1000000,
                                            }
                                            }
                                    )
'''
#print("APILIST_SN,",APIList_SN)
#######################################################################################################
### SECTION C:
# This section extracts the test types from the ITK DB and maps out the keys for uploading


#The following extracts the test types from the database and makes a "map" of where they will be in the pulled data
APITestTypeList = list(client.get("listTestTypes", json={"project": ITK_PROJECT, "componentType": ITK_COMPONENTTYPE}))
'''
APITestTypeList=dbAccess.extractList("listTestTypes", method = "GET",
                                      data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE}
                                      )
'''
#print("APITestTypeList,",APITestTypeList)
#This makes a list of all the types of the data fields so we can deal with "None" properly and know which are lists and values
APIParamTypeList={}
for APITestType in APITestTypeList:
    TempDict={}
    List=[]
    List.extend(APITestType['properties'])
    List.extend(APITestType['parameters'])
    for paramdict in List:
        TempDict[paramdict['code']]=(paramdict['dataType'],paramdict['valueType'],paramdict['required'])
    APIParamTypeList[APITestType['code']]=TempDict
        
APIAlternateNamesValuesANDFake={**APIAlternateNamesValues,**APIAlternateNamesFake}

#These create maps for every test type (for properties/results and values/lists) for the APIParam and Our Param. 

#This assumes properties include no TABLES
PropertiesDictList={}
for APITestType in APITestTypeList:
    TempDict={}
    for APIParam in [i['code'] for i in APITestType['properties']]:
        if APIParamTypeList[APITestType['code']][APIParam][1]!='array':
            OurParamList=[key for key in list(APIAlternateNamesValuesANDFake.keys()) if APIParam in APIAlternateNamesValuesANDFake[key]]
            if len(OurParamList)==1:
                OurParam=OurParamList[0]
            else:
                #OurParam=None
                OurParam=APIParam
            TempDict[APIParam]=OurParam
    PropertiesDictList[APITestType['code']]=TempDict

    
ResultsValuesDictList={}
for APITestType in APITestTypeList:
    TempDict={}
    for APIParam in [i['code'] for i in APITestType['parameters']]:
        if APIParamTypeList[APITestType['code']][APIParam][1]!='array':
            OurParamList=[key for key in list(APIAlternateNamesValuesANDFake.keys()) if APIParam in APIAlternateNamesValuesANDFake[key]]
            if len(OurParamList)==1:
                OurParam=OurParamList[0]
                TempDict[APIParam]=OurParam
            else:
                TempDict[APIParam]=APIParam
    ResultsValuesDictList[APITestType['code']]=TempDict
    
ResultsTablesDictList={}
for APITestType in APITestTypeList:
    TempDict={}
    for APIParam in [i['code'] for i in APITestType['parameters']]:
        if APIParamTypeList[APITestType['code']][APIParam][1]=='array':
            OurParamList=[key for key in list(APIAlternateNamesTABLES.keys()) if APIParam in APIAlternateNamesTABLES[key]]
            if len(OurParamList)==1:
                OurParam=OurParamList[0]
                TempDict[APIParam]=OurParam
            else:
                TempDict[APIParam]=APIParam
    ResultsTablesDictList[APITestType['code']]=TempDict
    


#######################################################################################################
### SECTION D:
# Dealing with duplicates

#NON-TABLE Keys to check to see if a cambridge file has already been uploaded to the ITK database
KeysToCheck=fullkeylist.copy()
for key in KeysToIgnore:
    KeysToCheck.remove(key)

#make list of tests with reduced keys
def makeTESTDICTLISTDUPCHECK(TESTDICTLIST):
    TESTDICTLISTDUPCHECK=[ReduceTESTDICTToMatchITKInfo(TESTDICT) for TESTDICT in TESTDICTLIST]
    return TESTDICTLISTDUPCHECK

#Check if test is in existing list
def isTESTDICTinTESTDICTLISTDUPCHECK(TESTDICT,TESTDICTLISTDUPCHECK):
    return ReduceTESTDICTToMatchITKInfo(TESTDICT) in TESTDICTLISTDUPCHECK

#Make a test with reduced keys
def ReduceTESTDICTToMatchITKInfo(TESTDICT):
    #Only the following are passed to ITK, so only those can be "original" in the imported data:
    #Timestamp, TestType, ComponentCode, PropertiesDict,ResultsDict
    
    #If TestType is not in PropertiesDictList.keys(), the ITK doesn't care as it cannot upload it anyways
    #But Local checks might still want to make sure it is not a self duplicate so output KeysToCheck.
    
    #If TestType is in the PropertiesDictList.keys() but there are no keys, then this means we haven't mapped the test yet
    #Which means we don't have the test type settled, and we wouldn't want to upload it and so limiting keys means it will think it is duplicated
    
    REDUCEDTESTDICT={Key:TESTDICT[Key] for Key in KeysMustCheck}

    return REDUCEDTESTDICT
    
    TestType=TESTDICT['TestType']
    
    if TestType in PropertiesDictList.keys():
        for TestDictKey in PropertiesDictList[TestType].values():
            if (TestDictKey is not None) and (TestDictKey!='Time') and (TestDictKey not in processedfields) and (TestDictKey not in KeysToIgnore) and (TestDictKey in TESTDICT.keys()):
                REDUCEDTESTDICT[TestDictKey]=TESTDICT[TestDictKey]

        for TestDictKey in ResultsValuesDictList[TestType].values():
            if (TestDictKey is not None) and (TestDictKey not in processedfields) and (TestDictKey not in KeysToIgnore) and (TestDictKey in TESTDICT.keys()) and (TestDictKey in TESTDICT.keys()):
                REDUCEDTESTDICT[TestDictKey]=TESTDICT[TestDictKey]
                
        for TestDictKey in ResultsTablesDictList[TestType].values():
            if (TestDictKey is not None) and (TestDictKey not in processedfields) and (TestDictKey not in KeysToIgnore) and (TestDictKey in TESTDICT.keys()) and (TestDictKey in TESTDICT.keys()):
                if TESTDICT[TestDictKey] is None:
                    REDUCEDTESTDICT[TestDictKey]=TESTDICT[TestDictKey]
                else:
                    output=[]
                    for i in TESTDICT[TestDictKey]:
                        if i!=NoneInTable:
                            output.append(i)
                        else:
                            output.append(None)
                    REDUCEDTESTDICT[TestDictKey]=output
    else:
        for key in KeysToCheck:
            REDUCEDTESTDICT[key]=TESTDICT[key]
            
    return REDUCEDTESTDICT
            
    



#######################################################################################################
### SECTION E:
# Various Common Functions

#for date time standardization
def Timestamp2ITKDateTime(timestamp):
    #'2019-10-25T14:55:50.165Z'
    return timestamp[8:10]+'.'+timestamp[5:7]+'.'+timestamp[0:4]+' '+timestamp[11:19]

def Timestamp2DateTime(timestamp):
    #'2019-10-25T14:55:50.165Z'
    return (timestamp[8:10]+' '+MonthList[int(timestamp[5:7])-1]+' '+timestamp[0:4],timestamp[11:19])

def Timestamp2ITKTime(timestamp):
    #'2019-10-25T14:55:50.165Z'
    return timestamp[11:19]

def DateTime2Timestamp(date,time):
    
    ########Standardize Date and Time:
    
    ###Date Formatting
    DateFormatFound=-1
    for DateFormat in range(0,len(DateRegexStringList)):
        DateRegexString=DateRegexStringList[DateFormat]
        try:
            regexondata = re.match(DateRegexString, date)
            FormattedDateList=regexondata.groups()
            DateFormatFound=DateFormat
            break
        except:
            FormattedDateList=None
            continue

    try:
        if DateFormatFound==0:
            Day=FormattedDateList[0]
            Month=str(MonthListUpper.index(FormattedDateList[1].upper())+1)
            Year=FormattedDateList[2]
        elif DateFormatFound==1:
            Day=FormattedDateList[0]
            Month=FormattedDateList[1]
            Year=FormattedDateList[2]
        elif DateFormatFound==2:
            Day=FormattedDateList[1]
            Month=FormattedDateList[0]
            Year='20'+FormattedDateList[2]
        elif DateFormatFound==3:
            Day=FormattedDateList[1]
            Month=str(MonthListUpper.index(FormattedDateList[0].upper())+1)
            Year=FormattedDateList[2]
        elif DateFormatFound==4:
            Day=FormattedDateList[0]
            Month=FormattedDateList[1]
            Year=FormattedDateList[2]
        elif DateFormatFound==5:
            Day=FormattedDateList[0]
            Month=str(LongMonthListUpper.index(FormattedDateList[1].upper())+1)
            Year=FormattedDateList[2]
        elif DateFormatFound==6:
            Day=FormattedDateList[2]
            Month=FormattedDateList[1]
            Year=FormattedDateList[0]
        else:
            Month=None
            Day=None
            Year=None
            errprint('The code for formatting this date format has not been added yet',(date,DateFormatFound,FormattedDateList))
    except:
        errprint('There was an error extracting the date',date)
        Month=None
        Day=None
        Year=None
    
    if Day!=None:
        Day=Day.zfill(2)
    if Month!=None:
        Month=Month.zfill(2)
    
    
    
    ###Time Formatting
    TimeFormatFound=-1
    for TimeFormat in range(0,len(TimeRegexStringList)):
        TimeRegexString=TimeRegexStringList[TimeFormat]
        try:
            regexondata = re.match(TimeRegexString, time)
            FormattedTimeList=regexondata.groups()
            TimeFormatFound=TimeFormat
            break
        except:
            efpprint("Something wrong with TimeRegexString.")
            continue
    try:
        #print(TimeFormatFound)
        #print(FormattedTimeList)
        if TimeFormatFound==0:
            Hour=FormattedTimeList[0]
            Min=FormattedTimeList[1]
            Sec=FormattedTimeList[2]   
        elif (TimeFormatFound==1) or (TimeFormatFound==2) or (TimeFormatFound==3):
            Hour=int(FormattedTimeList[0])
            Min=FormattedTimeList[1]
            Sec=FormattedTimeList[2]       
            if FormattedTimeList[3].lower()=='p':
                Hour+=12           
            Hour=str(Hour).zfill(2)
        elif TimeFormatFound==4:
            Hour=int(FormattedTimeList[0])
            Min=FormattedTimeList[1]
            Sec='00'      
            Hour=str(Hour).zfill(2)
        else:
            errprint('This time format has not been coded yet',(time,TimeFormatFound))
            Hour=None
            Min=None
            Sec=None
    except:
        errprint('There was an error extracting the time',time)
        Hour=None
        Min=None
        Sec=None
        
        
        #'2019-10-25T14:55:50.165Z'
    try:
        timestamp=Year+'-'+Month+'-'+Day+'T'+Hour+':'+Min+':'+Sec+'.000Z'
    except:
        timestamp=None
    #print("TIMESTAMP,", timestamp)
    return timestamp


def string2BatchWafer(Name):
    if Name==None:
        return (None,None)
    Name=Name.upper()
    
    success=False
    try:
        for delim in delims:
            trysplit=Name.split(delim)
            if len(trysplit)>1:
                Batch=trysplit[0]
                Wafer=trysplit[1]
                success=True
                break
        if success==False:
            errprint('Could not split batch and wafer',str(Name))
            Batch=None
            if Name[0]=='W':
                Wafer=Name[1:]
            else:
                Wafer=Name
    except:
        errprint('Could not split batch and wafer',str(Name))
        Batch=None
        if Name[0]=='W':
            Wafer=Name[1:]
        else:
            Wafer=Name
        
    return (Batch,Wafer)

def HMComponent2BatchWafer(Component):
    Batch=None
    Wafer=None
    
    Corr_Component = Component[:8] + '0' + Component[9:]
    #print("Corresponding MAIN component,",Corr_Component) 
    
    a=0
   # for i in range(0,len(APIList_SN.content)):
    
    for i in APIList_SN:
        if i['serialNumber'] == Corr_Component:
            a+=1
            Name=i['alternativeIdentifier']
            #print ("Alternative Identifier:", APIList_SN[i]['alternativeIdentifier'])
            (Batch,Wafer)=string2BatchWafer(Name)
            #print ("batch wafer,", Batch, Wafer)
           # print('HM has corresponding Main in the ITK Database.',str(Component))
        else:
            a+=0
    if a== 0:
        if Component == '20USBSX0900499':
            Batch = 'VPX90011'
            Wafer = 499
            print('HM has not corresponding Main in the ITK Database. Established manually.',str(Component))
        elif Component == '20USESX0900529':
            Batch = 'VPX90022'
            Wafer = 529
            print('HM has not corresponding Main in the ITK Database. Established manually.',str(Component))
        elif Component == '20USBSX0900751':
            Batch = 'VPX90032'
            Wafer = 751
            print('HM has not corresponding Main in the ITK Database. Established manually.',str(Component))
        elif Component == '20USES10900066':
            Batch = 'VPX32587'
            Wafer = 66
            print('HM has not corresponding Main in the ITK Database. Established manually.',str(Component))
        elif Component == '20USES40900124':
            Batch = 'VPX32496'
            Wafer = 124
            print('HM has not corresponding Main in the ITK Database. Established manually.',str(Component))      
        else:
            errprint('HM has not corresponding Main in the ITK Database.',str(Component))
        print("batch, wafer : ", Batch,Wafer)
    return(Batch,Wafer)

def AreaFromType(Type):
    if Type in list(AreaDict.keys()):
        return (True,AreaDict[Type])
    else:
        errprint('Could not find the wafer area for type. Please add this to the AreaDict in CommonConfig.py. Currently assuming AreaDict[\'Unknown\']='+str(AreaDict['Unknown'])+'. Problem with Type',str(Type))
        return (False,AreaDict['Unknown'])
    
    
def StripLengthFromType(Type, segment):
    if (Type is not None) and (Type in list(StripLengthDict.keys())):
        if type(StripLengthDict[Type]) is dict:
            if segment in StripLengthDict[Type].keys():
                return (True,StripLengthDict[Type][segment])
        else:
            return (True,StripLengthDict[Type])    
    print('Warning: Could not find strip length for the type ({}) and segment ({}). Please add this to the StripLengthDict (in CommonConfig.py)'.format(Type,segment))
    print('Assuming strip length is {} mm'.format(StripLengthDict['Unknown']/mm))  
    return (False,StripLengthDict['Unknown'])


def CheckHumidity(WAFERDICT):   
    HumidityFlag=None
    if WAFERDICT['Humidity[%]'] is not None and WAFERDICT['Humidity[%]']!='': 
        try:
            Humidity = float(WAFERDICT['Humidity[%]'])
        except:
            errprint("Error: Could not process humidity in data file!",WAFERDICT['Humidity[%]'])
            HumidityFlag="Could not process humidity in data file!"
        if Humidity <= MaxHumidity:
            norprint("Relative Humidity = {}%, Acceptable (< {}%)".format(Humidity, MaxHumidity))
        else:
            HumidityFlag='Humidity Exceeded: '+str(Humidity)+'%'
            errprint("Relative Humidity = {}%, Exceeds limit of {}%! Aborting Analyze IV.".format(Humidity, MaxHumidity),'')
            
                 
    else: 
        errprint("Error: Could not find humidity in data file!",WAFERDICT['Filename'])
        HumidityFlag="Could not find humidity in data file!"
    return HumidityFlag

def GetTempNormalizedI (I, T):
    """Returns an new array Inorm which is I normalized to temperatures in T. I and T must be arrays of the same length. Normalizes using temperature reading at the same time or if this doesn't exist, the previous time reading (first temperature reading must exist)"""
    #Check I and T are same length
    if np.size(I) != np.size(T):
        print ("Error: Can't normalize Current to Temperature as they are not the same length")
    normI = np.zeros([np.size(I)])
    for j in range(len(I)): 
        if I[j] is not None:
            if T[j] is not None:
                Tnorm = T[j]
            else: 
                Tnorm = next((item for item in reversed(T[:j]) if item is not None), None) #previous Temp reading
                if Tnorm is None:
                    print ("Error normalising to temperature")
            normI[j] = GetTempScaleFactor(Tnorm) * I[j]
        else: 
            normI[j] = I[j]
    return (normI) 


def GetTempScaleFactor(T):
    """ Gives factor to multiply current by to normalize to Tref, formula described in https://iopscience.iop.org/article/10.1088/1748-0221/8/10/P10003"""
    #Constants
    Tref = 20 #degrees C, Temperature current measurements are normalized to, in degrees C
    SiBandGap = 1.21 #Band Gap for bulk Silicon in eV
    eCharge = 1.6e-19
    kB = 1.38e-23
    KelvinOffset = 273.15
    T_k = T + KelvinOffset
    Tref_k = Tref + KelvinOffset
    ScaleFactor = (Tref_k/T_k)**2*np.exp(SiBandGap*eCharge * (Tref_k-T_k)/(2*kB*Tref_k*T_k)  )
    return (ScaleFactor)



def eng_string( x, sig_figs=sig_figs, si=si):
    """
    Returns float/int value <x> formatted in a simplified engineering format -
    using an exponent that is a multiple of 3.

    sig_figs: number of significant figures

    si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
    e-9 etc.
    """
    if x is None:
        return 'None'
    x = float(x)
    sign = ''
    if x < 0:
        x = -x
        sign = '-'
    if x == 0:
        exp = 0
        exp3 = 0
        x3 = 0
    else:
        exp = int(math.floor(math.log10( x )))
        exp3 = exp - ( exp % 3)
        x3 = x / ( 10 ** exp3)
        x3 = round( x3, -int( math.floor(math.log10( x3 )) - (sig_figs-1)) )
        if x3 == int(x3): # prevent from displaying .0
            x3 = int(x3)

    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        exp3_text = ' '+'yzafpnum kMGTPEZY'[ exp3 // 3 + 8]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3
        
    return ( '%s%s%s') % ( sign, x3, exp3_text)

#for RUNME arguments
def extractRUNMEargsfromcmd(ARGS):
        querypath=tuple(ARGS)[1]
        #check if query path is actually a list, in which case separate it into a list
        if ',' in querypath or '[' in querypath or ']' in querypath:
            querypath=querypath.replace('[','')
            querypath=querypath.replace(']','')
            querypath=querypath.replace('"','')
            querypath=querypath.replace("'",'')

            querypathlist=querypath.split(',')
            querypath=[i.strip() for i in querypathlist]

        try:
            outputfile=tuple(ARGS)[2]
        except:
            outputfile=defaultoutputfile

        try:
            batch=tuple(ARGS)[3]
        except:
            batch=None

        try:
            wafers=tuple(ARGS)[4]
            #check if wafers is actually a list, in which case separate it into a list
            if ',' in wafers or '[' in wafers or ']' in wafers:
                wafers=wafers.replace('[','')
                wafers=wafers.replace(']','')
                wafers=wafers.replace('"','')
                wafers=wafers.replace("'",'')

                waferslist=wafers.split(',')
                wafers=[i.strip() for i in waferslist]
            elif type(wafers)==str:
                wafers=[wafers]

            waferslist=[]
            for wafer in wafers:
                try:
                    waferslist.append(int(wafer))
                except:
                    waferslist.append(wafer)

            wafers=waferslist
        except:
            wafers=None
        return querypath,outputfile,batch,wafers
            
    

#for formatted printing to terminal
wrapper1=textwrap.TextWrapper(initial_indent=prefix1, width=width, subsequent_indent=prefix1)
wrapper2=textwrap.TextWrapper(initial_indent=prefix2, width=width, subsequent_indent=prefix2)
wrappere=textwrap.TextWrapper(initial_indent=prefixe, width=width, subsequent_indent=prefix1)

def efpprint(string,info, filepath):
    print(wrappere.fill(str(string)+': \t'+str(info)))
    print(wrapper2.fill(filepath))
    
def errprint(string,info):
    print(wrappere.fill(str(string)+': \t'+str(info)))
    
def norprint(string):
    print(wrapper1.fill(str(string)))
    
#savetoken()
