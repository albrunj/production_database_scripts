#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
#To use:
#In Python3 Interactive: 

querypath="/var/clus/pc_backup/Cleanroom/data/sisensors/" #can be a directory, file, or a list of directories or files
import ImportData
TESTDICTLIST=ImportData.ImportData(querypath)
"""
"""
Author: David Rousso

Primary Function:
`TESTDICTLIST=ImportData.ImportData(querypath)`

Inputs:
`querypath`: A str path to a single test file or directory of sensor test files, or a list of directories and/or files

Outputs:
`TESTDICTLIST`: A list of dictionaries, where each dictionary represents a separate sensor test. 


Documentation:

The function goes through every file in `querypath` and tries to extract the information into a TESTDICT to be put in the TESTDICTLIST. The test files must be either a .txt or .dat file.

It does so by going through, in alphabetical order, all of the test formats that are available in the `DataFormats` folder.



Data Formats:

Each of these data formats can be formed by taking a regular test format of the format you want, and replacing each value, 
with `$$$Key&&&` where the name of the key corresponds to the key name in `datafields` in `CommonConfig.py`.

Note that if you want to add a new key you will have to add this in `datafields`. 

Note that there are are a few special keys:

Everything that is a table should be replaced by a single `$$$TABLE&&&`. 

If you want to ignore everything after a certain point, you can use `$$$IGNORE&&&` but this is not recommended.

If you have a SINGLE field that might be a component, or it might be a shorthand, or a batch-wafer combo like "VPX30816-W0163"
you may use the field $$$BatchWaferShorthand&&& and the code will try to figure out what it is for you.

The Time and Date should have separate fields in the data format, they will be standardized into a Timestamp field in the TESTDICT.

If you have one of those weird stability formats where there are multiple wafers per file and you have all of the info of the 
wafers concatenated in the same line using a ';', use $$$WaferInfoStringStability&&& to represent that. 

Note that it is assumed that the Manufacturer name has no digits, the Shorthand field has only digits, the Batch begins with a 'V', and the Component Code begins with a '20U'



Initial Extraction:

For the fields, if the field is anything in `valuestotreatasNone`, it will be replaced with None.

If the strip test `TestType` has the segment included in the name, put the regex for the `TestType` format in `StripTestRegexString` 
where the first capture group is the TestType and the second is the segment so we can separate them

If your temperature is hidden in your Settings field, include a regex in `TemperatureRegexString` to extract it.

If your length and voltage for your stability test is hidden in your Settings field, include a regex in `LengthVoltageRegexString` to extract it
The first capture group is the length and the second is the voltage.



Weird Data Formats:

There is a weird type of metrology data format and a weird type of stability data format where 
although the headers are treated the same way (sort of), the table needs to be treated differently from the rest.

For the weird metrology formats, a list of the weird metrology data formats should be placed in `SpecialMetrologyFormats`.
As for the lines in the table, SpecialMetrologyPointRegex is a dictionary where the key is a regex for the line in the table 
portion in the format, and the value is a list of the TABLE_ column names for the capture groups of the regex, in order.

For the weird stability formats, which is when you have multiple wafers in the same file and/or you have the voltage just plopped right in the middle of the table, it will extract the voltage from the middle of the table, and also create separate WAFERDICTs for each wafer in the file. If the columns are of different lengths, it will fill in the missing entries with Nones



Table Extraction:

The code will try to extract the columns and put them in the WAFERDICT. `alternatecolumnnames` is a dictionary where the key
is the name that will appear in the WAFERDICT, and the values are list of the alternate names for these columns that will
appear in your local test data files.


**Note that if the Temperature and Humidity fields are empty, but the TABLE_ versions exist, it will be set as the average of the TABLE_ values.


Shorthand:

Shorthand is a 6 digit number associated with the wafer that may be used by individual institutions. For formats in which there is only shorthand and no batch/wafer information, you must provide a file `shorthandpath` to tell the code which shorthands correspond to which batch/wafer.

This file should be of the following format:

```
Serial Number;Mfr Serial No;Manufacturer;Type;Current Location;Assembled?
{SHORTHAND6DIGITS};{BATCH-WAFER};{MANUFACTURER};{TYPE};{INSTITUTION};{ASSEMBLED}
{SHORTHAND6DIGITS};{BATCH-WAFER};{MANUFACTURER};{TYPE};{INSTITUTION};{ASSEMBLED}
011172;VPX73812-W72;Hamamatsu;ATLAS07;Cambridge;false
012372;VPX73812-W72;Hamamatsu;ATLAS07;Cambridge;false
```

note that the last two fields will not matter.



Filling in Missing Info:

The code will try to fill in missing information from any source it can including the filepath. It will ping the ITK DB to get the data on all the wafers to help do so. It does so by making assumptions on what the batch/wafer/component/manufacturer/shorthand formats should be, which are in functions at the end of this file.



Standardizing Info:

The TestType, Type, and Institution will be standardized. There are dictionaries you may need to edit in CommonConfig `alternatetestnames`, `alternatetypenames` and `alternateinstitutenames`, where the key is the standard name and the values are lists of the non-standard names that appear in local test files. If no institution is set, it will be set to `DefaultInstitute`.



#Note: All code will need the requests module for python3 which can be installed with
# pip3 install requests

#Note if running for the first time it make take a while as it has to pull everything from the ITK Database


"""
import copy
import glob
import os
import re
import string
from datetime import datetime

import GetComponentInfoFromDatabase   
import ImportDataFromDatabase
from CommonConfig import alternatecolumnnames
from CommonConfig import alternateinstitutenames
from CommonConfig import alternatetestnames
from CommonConfig import alternatetypenames
from CommonConfig import dataformatpath
from CommonConfig import DefaultInstitute
from CommonConfig import delimiterslist
from CommonConfig import efpprint
from CommonConfig import errprint
from CommonConfig import fullkeylist
from CommonConfig import KeysMustCheck
from CommonConfig import LengthVoltageRegexString
from CommonConfig import norprint
from CommonConfig import ReduceTESTDICTToMatchITKInfo
from CommonConfig import ShorthandFields
from CommonConfig import shorthandpath
from CommonConfig import SpecialMetrologyFormats
from CommonConfig import SpecialMetrologyPointRegex
from CommonConfig import string2BatchWafer
from CommonConfig import StripTestRegexString
from CommonConfig import tablefields
from CommonConfig import TemperatureRegexString
from CommonConfig import TestType_Metrology
from CommonConfig import TestType_Stability
from CommonConfig import TestType_Thickness
from CommonConfig import TestType_Visual_Inspection
from CommonConfig import valuestotreatasNone

COMPONENTIDDICTLIST=GetComponentInfoFromDatabase.GetComponentInfoFromDatabase() 
DATABASETESTLIST=ImportDataFromDatabase.ImportDataFromDatabase() 


def ImportData(querypath):
    print('\n'*5)
    print("Running ImportData.py: Importing Local .dat/.txt Test Files to a TESTDICTLIST Object:")
    
    ### After looping through we create a list of all of the wafer dictionaries called:
    WAFERDICTLIST=[]
    
    print('')                        
    norprint('Processing the Data Format Files.')    
    print('')   
    ### Extracting all dataformats to a useful form:
    dataformatstrings,keylists,dataformatfilenames,dataformatfilepaths,hastablelist=ImportDataFormats()
    #dataformatstrings is a list of the regex strings representing the data formats
    #keylists are a list of the list of keys for each data format
    #dataformatfilenames is a list of the filenames of the data formats
    #dataformatfilepaths is a list of the filepaths for the data formats
    
    
    
    print('\n'*3)   
    norprint('Compiling a list of files to look through from the inputted query path') 
    ### Find filepaths for all .dat or .txt files in `querypath` and store them in a list called 
    filepaths=GetListOfTestFilepaths(querypath)
    
    
    
    print('\n'*3)
    norprint('Looping through test files.')  
    ###Loop through files 
    
    numtests=len(filepaths)
    totalsuccesscount=0
    for filepath in filepaths:
        #Try opening the file      
        filename=os.path.basename(filepath)
        try:
            with open(filepath,'r',encoding='utf-8',errors='ignore') as f:
                RAWDATA = f.read()
        except:
            efpprint('Could not read file',filename,filepath)
            continue
            
                          
        #Try data extraction by looping through all possible formats.
        dataextractionsuccessful=False
        for formattype in range(0,len(dataformatstrings)):
            regexondata = re.match(dataformatstrings[formattype], ProcessFile(RAWDATA))
            try:
                regexondata.groups()
                if len(regexondata.groups())>=1:
                    dataextractionsuccessful=True
                    break
            except:
                print("Something wrong with Data extraction.")
                continue        
        if dataextractionsuccessful==False:
            efpprint('File format not recognized',filename,filepath)
            continue
        
        
        #Initialize dictionary
        WAFERDICT=dict.fromkeys(fullkeylist)
        
        #Add Data Format and RAWDATA to Dictionary
        WAFERDICT['DataFormat']=dataformatfilenames[formattype]

        #Add header parameters to dictionary:
        if hastablelist[formattype]:
            FORMATEDDATA=list(regexondata.groups()[:-1])
        else:
            FORMATEDDATA=list(regexondata.groups())
        
        Date=None
        Time=None
        BatchWaferShorthand=None
        WaferInfoStringStability=None
        try:
            for i in range(0,len(keylists[formattype])):
                key=keylists[formattype][i]
                if key in fullkeylist:
                    if FORMATEDDATA[i] in valuestotreatasNone:
                        FORMATEDDATA[i]=None
                    WAFERDICT[key]=FORMATEDDATA[i]
                elif key=='Time':
                    Time=FORMATEDDATA[i]
                elif key=='Date':
                    Date=FORMATEDDATA[i]
                elif key=='BatchWaferShorthand':
                    BatchWaferShorthand=FORMATEDDATA[i]
                elif key=='WaferInfoStringStability':
                    WaferInfoStringStability=FORMATEDDATA[i]
                else:
                    WAFERDICT[key]=FORMATEDDATA[i]
        except:
            efpprint('There was an error when extracting fields from the header',filename,filepath)
            continue
            
        #Update Timestamp Format
        Date_Time = Date + Time
        date_time = datetime.strptime(Date_Time, "%d %b %Y%H:%M:%S")
        date_as_string = date_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')     
        #WAFERDICT['Timestamp']=DateTime2Timestamp(Date,Time)
        WAFERDICT['Timestamp']=date_as_string  
        
        #Figure out what BatchWaferShorthand is
        if BatchWaferShorthand!=None and len(BatchWaferShorthand)>0:
            if IsShorthandFormat(BatchWaferShorthand)and WAFERDICT['Shorthand']==None:
                #This is actually a shorthand!
                WAFERDICT['Shorthand']=BatchWaferShorthand
            elif IsComponentFormat(BatchWaferShorthand)and WAFERDICT['Component']==None:
                #This is actually a serial number!
                WAFERDICT['Component']=BatchWaferShorthand
            elif WAFERDICT['Batch']==None and WAFERDICT['Wafer']==None:
                (Batch,Wafer)=string2BatchWafer(BatchWaferShorthand)
                WAFERDICT['Batch']=Batch
                WAFERDICT['Wafer']=Wafer
        
        #Format Batch/Wafer/Component correctly
        if WAFERDICT['Batch'] is not None:
            WAFERDICT['Batch']=WAFERDICT['Batch'].upper()
        if WAFERDICT['Wafer'] is not None:
            WAFERDICT['Wafer']=WAFERDICT['Wafer'].upper()
        if WAFERDICT['Component'] is not None:
            WAFERDICT['Component']=WAFERDICT['Component'].upper()
        try:
            WAFERDICT['Wafer']=int(WAFERDICT['Wafer'].strip('w').strip('W'))
        except:
            WAFERDICT['Wafer']=WAFERDICT['Wafer']
        
        #Extract Segment from StripTest if applicable
        if WAFERDICT['Segment'] is None:
            for regexstring in StripTestRegexString:
                try:
                    regex = re.match(regexstring, WAFERDICT['TestType'])
                    regexresult=regex.groups()
                    WAFERDICT['Segment']=regexresult[1]
                    WAFERDICT['TestType']=regexresult[0]
                    break
                except:
                    print("Something wrong with StripTestRegexString.")
                    continue   
        try: 
            WAFERDICT['Segment']=int(WAFERDICT['Segment'])
        except:
            WAFERDICT['Segment']=WAFERDICT['Segment']
            
        #Extract Temperature, Voltage, or Test Length from Settings if applicable
        Settings=WAFERDICT['Settings']
        for regexstring in TemperatureRegexString:
            try:
                regex = re.match(regexstring, Settings)
                regexresult=regex.groups()
                WAFERDICT['Temperature[°C]']=regexresult[0]
                break
            except:
                print("Something wrong with TemperatureRegexString.")
                continue
        for regexstring in LengthVoltageRegexString:
            try:
                regex = re.match(regexstring, Settings)
                regexresult=regex.groups()
                WAFERDICT['TestTimeLength[hr]']=regexresult[0]
                WAFERDICT['Voltage[V]']=regexresult[1]
                break
            except:
                print("Something wrong with LengthVoltageRegexString.")
                continue
        
        #Add filepath to the TESTDICT
        WAFERDICT['Filepath']=filepath
           
        #Check if the filename in the test file matches its actual filename. If not, replace.
        if WAFERDICT['Filename']!=filename:
            efpprint('Warning! Filename in datafile does not match actual filename! Defaulting to real name',WAFERDICT['Filename'],filepath)
            WAFERDICT['Filename']=filename
        
                
        ############# 
        #Deal with the table:
        
        if hastablelist[formattype]:
            
            #Extract the table rows
            RAWTABLE=regexondata.groups()[-1]
            RAWTABLEROWS=RAWTABLE.split('\n')

            #Check to see if the table may be a weird stability format even if not in SpecialStabilityFormats
            WeirdStabilityFormat=False
            if len(RAWTABLEROWS)>3 and RAWTABLEROWS[1]=="" and RAWTABLEROWS[3]=="":
                WeirdStabilityFormat=True
            if WaferInfoStringStability is not None:
                WeirdStabilityFormat=True

            #For the table, treat differently if it is one of those weird metrology formats
            if dataformatfilenames[formattype] in SpecialMetrologyFormats:

                WAFERDICT['TestType']=TestType_Metrology
                #Try data extraction by looping through all possible weird metrology formats.
                metdataextractionsuccessful=False
                for metformattype in SpecialMetrologyPointRegex.keys():
                    regexondata = re.findall(metformattype, RAWTABLE)
                    if regexondata is not None:
                        try:
                            numlists=len(SpecialMetrologyPointRegex[metformattype])
                            ListofLists=[[] for i in range(0,numlists)]
                            for line in regexondata:
                                for ind in range(0,len(line)):
                                    ListofLists[ind].append(float(line[ind]))
                            for ind in range(0,len(line)):
                                WAFERDICT[SpecialMetrologyPointRegex[metformattype][ind]]=ListofLists[ind]
                            metdataextractionsuccessful=True
                            break
                        except:
                            print("Something wrong with SpecialMetrologyPointRegex.")
                            continue
                    else:
                        continue        
                if metdataextractionsuccessful==False:
                    efpprint('Metrology Table Format not recognized',filename,filepath)
                    continue

                WAFERDICTLIST.append(WAFERDICT)
                totalsuccesscount+=1

            #Take care of weird stability format
            #elif dataformatfilenames[formattype] in SpecialStabilityFormats or WeirdStabilityFormat==True:
            elif WeirdStabilityFormat==True:

                WAFERDICT['TestType']=TestType_Stability

                #Extract voltage row out of table
                #VOLTAGEROW=RAWTABLEROWS[2]
                TABLEROWS=RAWTABLEROWS[0:1]+[row for row in RAWTABLEROWS[3:] if row]

                #Extract Table into Lists
                extracttableresult=ExtractTable(TABLEROWS,filename,filepath)
                if extracttableresult==None:
                    continue
                else:
                    tableheaders,TABLE=extracttableresult

                #Get general WAFERDICT with fields that apply to all wafers in the file
                GEN_WAFERDICT=WAFERDICT

                #Check table makes sense
                if len(TABLE)<5:
                    efpprint('Too few columns in stability test',len(TABLE),filepath)
                    continue
                if not(len(TABLE[0])==len(TABLE[1]) and len(TABLE[1])==len(TABLE[2])):
                    efpprint('Unexpected number of rows for temp/humd in stability test',(len(TABLE[0]),len(TABLE[1]),len(TABLE[2])),filepath)
                    continue

                #Get the general time, temp, and humidity columns
                GEN_TIME=TABLE[0][0:1]
                GEN_TEMP=TABLE[1][0:1]
                GEN_HUMD=TABLE[2][0:1]
                for rowind in range(1,len(TABLE[0])):
                    if TABLE[0][rowind]!=0:
                        GEN_TIME.append(TABLE[0][rowind])
                        GEN_TEMP.append(TABLE[1][rowind])
                        GEN_HUMD.append(TABLE[2][rowind])


                #get number of wafers
                numWafers=(len(TABLE)-3)/2
                if numWafers % 1 !=0:
                    efpprint('Unexpected number of columns for stability test',len(TABLE),filepath)
                    continue
                else:
                    numWafers=int(numWafers)

                #Split up the line with all the wafer information in the header
                if 1==1:
                #if WeirdStabilityFormat==False:
                    WaferInfoList=WaferInfoStringStability.split(';')[:-1]
                    if len(WaferInfoList)!=numWafers:
                        efpprint('Number of columns does not match number of wafers',(len(WaferInfoList),numWafers),filepath)



                #loop though wafers
                for indWafer in range(0,numWafers):
                    numtests+=1
                    #Get general information into WAFERDICT
                    WAFERDICT=copy.deepcopy(GEN_WAFERDICT)

                    if len(TABLE[3+indWafer*2])!=len(TABLE[3+indWafer*2+1]):
                        efpprint('Unexpected number of rows for current in stability test',(len(TABLE[3+indWafer*2]),len(TABLE[3+indWafer*2+1])),filepath)

                    #Get new time and current information for specific wafer
                    NEW_TIME=TABLE[3+indWafer*2][0:1]
                    NEW_CURR=TABLE[3+indWafer*2+1][0:1]
                    for rowind in range(1,len(TABLE[3+indWafer*2+1])):
                        if TABLE[3+indWafer*2][rowind]!=0:
                            NEW_TIME.append(TABLE[3+indWafer*2][rowind])
                            NEW_CURR.append(TABLE[3+indWafer*2+1][rowind])

                    #Because there are multiple time columns of different lengths, this inserts Nones for missing points
                    TIME=copy.deepcopy(GEN_TIME)
                    TEMP=copy.deepcopy(GEN_TEMP)
                    HUMD=copy.deepcopy(GEN_HUMD)
                    CURR=[None for i in range(0,len(GEN_TIME))]
                    for t_ind in range(0,len(NEW_TIME)):
                        if NEW_TIME[t_ind] in GEN_TIME:
                            CURR[GEN_TIME.index(NEW_TIME[t_ind])]=NEW_CURR[t_ind]
                        else:
                            TIME.append(NEW_TIME[t_ind])
                            TEMP.append(None)
                            HUMD.append(None)
                            CURR.append(NEW_CURR[t_ind])

                    #sort tables
                    TIME,TEMP,HUMD,CURR=list(zip(*sorted(zip(TIME,TEMP,HUMD,CURR))))
                    TIME=list(TIME)
                    TEMP=list(TEMP)
                    HUMD=list(HUMD)
                    CURR=list(CURR)

                    WAFERDICT['TABLE_Time[s]']=TIME
                    WAFERDICT['TABLE_Temperature[°C]']=TEMP
                    WAFERDICT['TABLE_Humidity[%]']=HUMD
                    WAFERDICT['TABLE_Current[nA]']=CURR

                    #Get Individual Wafer's information from header
                    if 1==1:
                    #if WeirdStabilityFormat==False:
                        SplitWaferInfo=WaferInfoList[indWafer].split(', ')
                        if len(SplitWaferInfo)==2:
                            SplitBatchWafer=SplitWaferInfo[0].split('-W')
                            if len(SplitBatchWafer)==2:
                                WAFERDICT['Batch']=SplitBatchWafer[0]
                                try:
                                    WAFERDICT['Wafer']=int(SplitBatchWafer[1])
                                except:
                                    WAFERDICT['Wafer']=SplitBatchWafer[1]
                            SplitManuType=SplitWaferInfo[1].split(' ')
                            if len(SplitManuType)==2:
                                WAFERDICT['Manufacturer']=SplitManuType[0]
                                WAFERDICT['Type']=SplitManuType[1]
                        else:
                            efpprint('Unreadable wafer info',WaferInfoList[indWafer],filepath)

                    WAFERDICTLIST.append(WAFERDICT)
                    totalsuccesscount+=1

                numtests=numtests-1
                continue


            ### For all other TestTypes:
            else:
                #Only care about the first table:
                TABLEROWS=[]
                OTHERTABLES=[]
                firsttable=True
                for row in RAWTABLEROWS:
                    if row and firsttable:
                        TABLEROWS.append(row)
                    elif firsttable:
                        firsttable=False
                    elif row:
                        OTHERTABLES.append(row)


                #Extract Table into Dictionary
                extracttableresult=ExtractTable(TABLEROWS,filename,filepath)
                if extracttableresult==None:
                    continue
                else:
                    tableheaders,TABLE=extracttableresult


                TABLEDICT={}
                for j in range(0,len(TABLE)):
                    TABLEDICT[tableheaders[j]]=TABLE[j]

                #Write to dict   
                OTHERCOLUMNS=[]
                for tableheader in TABLEDICT.keys():
                    dictheader=[key for key in alternatecolumnnames.keys() if tableheader in alternatecolumnnames[key]]
                    if len(dictheader)==1:
                        dictheader=dictheader[0]
                        if dictheader in fullkeylist:
                            WAFERDICT[dictheader]=TABLEDICT[tableheader]
                        else:
                            errprint('Table Header Not In CommonConfig tablefields list! Ignoring',tableheader,filepath)
                    else:
                        efpprint('Table Header Not Recognized or duplicated! Check CommonConfig alternatecolumnnames',tableheader,filepath)
                        OTHERCOLUMNS+=[TABLEDICT[tableheader]]



                WAFERDICT['OtherColumns']=OTHERCOLUMNS
                WAFERDICT['OtherTables']=OTHERTABLES


                #Fill in missing temperature or humidity from table if applicable
                if WAFERDICT['Temperature[°C]'] is None and WAFERDICT['TABLE_Temperature[°C]'] is not None:
                    NotNone=[i for i in WAFERDICT['TABLE_Temperature[°C]'] if type(i) in [int,float]]
                    if len(NotNone)>=1:
                        WAFERDICT['Temperature[°C]']=sum(NotNone)/len(NotNone)
                if WAFERDICT['Humidity[%]'] is None and WAFERDICT['TABLE_Humidity[%]'] is not None:
                    NotNone=[i for i in WAFERDICT['TABLE_Humidity[%]'] if type(i) in [int,float]]
                    if len(NotNone)>=1:
                        WAFERDICT['Humidity[%]']=sum(NotNone)/len(NotNone)

                #Make Probe plan index integer array:
                if WAFERDICT['TABLE_ProbeplanIndex'] is not None:
                    try:
                        WAFERDICT['TABLE_ProbeplanIndex']=[int(i) for i in WAFERDICT['TABLE_ProbeplanIndex']]
                    except:
                        errprint('Error converting probeplanindex to int array',WAFERDICT['TABLE_ProbeplanIndex'],filepath)

                WAFERDICTLIST.append(WAFERDICT)
                totalsuccesscount+=1
        else:
            WAFERDICTLIST.append(WAFERDICT)
            totalsuccesscount+=1
        
                

        

        
    print('')
    print('')
    print('')    
    norprint(str(numtests-totalsuccesscount ) +' abandonned files out of '+str(numtests))    


    print('')
    print('')
    print('')
    norprint('Filling in Missing Information from Databases.')  
    FILLEDWAFERDICTLIST=FillMissingInfo(WAFERDICTLIST)    
    
    print('')
    print('')
    print('')
    norprint('Removing Duplicate and Blank Tests.')  
    NODUPWAFERDICTLIST=NonDuplicateTests(FILLEDWAFERDICTLIST)
    
    print('')
    print('ImportData.py Complete!')  

    return NODUPWAFERDICTLIST





def FillMissingInfo(WAFERDICTLIST):
    print(' ')
    print(' ')
    print(' ')
    norprint('Filling in Missing Batch/Wafer/Component/Shorthand/ComponentCode Info')
    for WAFERDICT in WAFERDICTLIST:
        Batch=WAFERDICT['Batch']
        Wafer=WAFERDICT['Wafer']
        Component=WAFERDICT['Component']
        ComponentCode=WAFERDICT['ComponentCode']
        Shorthand=WAFERDICT['Shorthand']
        Filepath=WAFERDICT['Filepath']
        
        
        #Check which fields actually make sense:
        BatchSeemsRight=False
        WaferSeemsRight=False
        ComponentSeemsRight=False
        ShorthandSeemsRight=False
        
       # ComponentCodeSeemsRight=False
    
        if IsBatchFormat(Batch) and not IsComponentFormat(Batch) and not IsShorthandFormat(Batch):
            BatchSeemsRight=True
        if IsWaferFormat(Wafer) and not IsBatchFormat(Wafer) and not IsComponentFormat(Wafer):
            WaferSeemsRight=True
        if IsComponentFormat(Component) and not IsBatchFormat(Component) and not IsShorthandFormat(Component):
            ComponentSeemsRight=True    
        if IsShorthandFormat(Shorthand) and not IsComponentFormat(Shorthand) and not IsBatchFormat(Shorthand):
            ShorthandSeemsRight=True
            
            
            
        #If no fields make sense, try scraping from filepath    
        BatchTemp,WaferTemp,ComponentTemp,ShorthandTemp=ExtractBatchWaferComponentShorthandFromFilepath(WAFERDICT['Filepath'])  
        if BatchTemp is not None and not (BatchSeemsRight and WaferSeemsRight):
            Batch,BatchSeemsRight=CheckConsistency(Batch,BatchTemp,BatchSeemsRight,Filepath)
        if WaferTemp is not None and not (BatchSeemsRight and WaferSeemsRight):
            Wafer,WaferSeemsRight=CheckConsistency(Wafer,WaferTemp,WaferSeemsRight,Filepath)
        if ComponentTemp is not None and not ComponentSeemsRight:
            Component,ComponentSeemsRight=CheckConsistency(Component,ComponentTemp,ComponentSeemsRight,Filepath)
        if ShorthandTemp is not None and not ShorthandSeemsRight:
            Shorthand,ShorthandSeemsRight=CheckConsistency(Shorthand,ShorthandTemp,ShorthandSeemsRight,Filepath)
                
            
        #The Wafer/Batch are the most important. Let's try to find them first from other fields if they aren't there.
        if not BatchSeemsRight or not WaferSeemsRight:
            #We need to find the batch and wafer
            if ShorthandSeemsRight:
                BatchTemp,WaferTemp=Shorthand2BatchWafer(Shorthand)
                if BatchTemp is not None:
                    Batch,BatchSeemsRight=CheckConsistency(Batch,BatchTemp,BatchSeemsRight,Filepath)
                if WaferTemp is not None:
                    Wafer,WaferSeemsRight=CheckConsistency(Wafer,WaferTemp,WaferSeemsRight,Filepath)
            if ComponentSeemsRight:
                BatchTemp,WaferTemp=Component2BatchWafer(Component)
                
                #Take care of stupid special case where they changed the component numbers
                if BatchTemp is None and WaferTemp is None and Component[0:8]=='20USBSL0':
                    TempComponent=''
                    for strind in range(0,len(Component)):
                        if strind==7:
                            TempComponent+='6'
                        else:
                            TempComponent+=Component[strind]
                    BatchTemp,WaferTemp=Component2BatchWafer(TempComponent)
                    if BatchTemp is not None and WaferTemp is not None:
                        Component=TempComponent
                    
                if BatchTemp is not None:
                    Batch,BatchSeemsRight=CheckConsistency(Batch,BatchTemp,BatchSeemsRight,Filepath)
                if WaferTemp is not None:
                    Wafer,WaferSeemsRight=CheckConsistency(Wafer,WaferTemp,WaferSeemsRight,Filepath)
            
            
        
        #Now that we have the batch and wafer (if we don't at this point we have tried all that we can and its a lost cause)
        #We can solve for the remaining missing fields
        if BatchSeemsRight and WaferSeemsRight:
            ShorthandTemp=BatchWafer2Shorthand(Batch,Wafer)
            if ShorthandTemp is not None:
                Shorthand,ShorthandSeemsRight=CheckConsistency(Shorthand,ShorthandTemp,ShorthandSeemsRight,Filepath)
            #Because of the ITK people messing about with the component codes, I will enforce the ITK Component 
            #as truth without giving a warning to the user
            Component,ComponentCode=BatchWafer2ComponentAndCode(Batch,Wafer)
            
            
        
        WAFERDICT['Batch']=Batch
        WAFERDICT['Wafer']=Wafer
        WAFERDICT['Component']=Component
        WAFERDICT['ComponentCode']=ComponentCode
        WAFERDICT['Shorthand']=Shorthand
        
        
        
        
        
    print(' ')
    print(' ')
    print(' ')
    norprint('Standardizing and setting '+DefaultInstitute+' as Default Institute unless stated otherwise (change this using the DefaultInstitute and alternateinstitutenames in CommonConfig.py)')
    for WAFERDICT in WAFERDICTLIST:       
        if WAFERDICT['Institute'] is None:
            WAFERDICT['Institute']=DefaultInstitute
        StandardInstitute=[i for i in list(alternateinstitutenames.keys()) if WAFERDICT['Institute'] in alternateinstitutenames[i]]
        if len(StandardInstitute)==1:
            WAFERDICT['Institute']=StandardInstitute[0]

        
        
        
        
    print(' ')
    print(' ')
    print(' ')
    norprint('Standardizing Test Names') 
    for WAFERDICT in WAFERDICTLIST:  
        ###Standardize Test Names:
        TestType=WAFERDICT['TestType']
        StandardTestType=[i for i in list(alternatetestnames.keys()) if TestType in alternatetestnames[i]]
        if len(StandardTestType)==1:
            WAFERDICT['TestType']=StandardTestType[0]
            
          
    print(' ')
    print(' ')
    print(' ')
    norprint('Standardizing Type Names') 
    for WAFERDICT in WAFERDICTLIST:  
        ###Standardize Type Names:
        Type=WAFERDICT['Type']
        
        #File overrides ITKDB
        """
        if Type is None or Type=='':
            Type=BatchWafer2Type(WAFERDICT['Batch'],WAFERDICT['Wafer'])
            WAFERDICT['Type']=Type
        """
        
        #ITKDB overrides file
        
        Type=BatchWafer2Type(WAFERDICT['Batch'],WAFERDICT['Wafer'])
        if Type is not None:
            WAFERDICT['Type']=Type
        
        StandardType=[i for i in list(alternatetypenames.keys()) if Type in alternatetypenames[i]]
        if len(StandardType)==1:
            WAFERDICT['Type']=StandardType[0]
            
        
        
    print(' ')
    print(' ')
    print(' ')
    norprint('Filling in missing Run Number')    
    for WAFERDICT in WAFERDICTLIST:  
        #Fill in RunNumber by checking what tests have been done already
        if WAFERDICT['RunNumber']==None:
            if WAFERDICT['ComponentCode']==None:
                WAFERDICT['RunNumber']='1'
            else:
                try:
                    RunNumberList=[int(i['RunNumber']) for i in DATABASETESTLIST if (i['ComponentCode']==WAFERDICT['ComponentCode']) and (i['TestType']==WAFERDICT['TestType'])]
                    #RunNumberList=[int(i['RunNumber']) for i in DATABASETESTLIST if (i['ComponentCode']=='d61386d361326c7804f71cfd066c5ed0') and (i['TestType']=='SENSOR_IV')]
                    if len(RunNumberList)>=1:
                        #print(RunNumberList)
                        WAFERDICT['RunNumber']=str(max([len(RunNumberList),max(RunNumberList)])+1)
                        #print(str(max([len(RunNumberList),max(RunNumberList)])+1))
                    else:
                        WAFERDICT['RunNumber']='1'
                except:
                    efpprint('Error trying to determine run number, assuming  1:',str(WAFERDICT['Filepath']) +str(i['RunNumber'] for i in DATABASETESTLIST if (i['ComponentCode']==WAFERDICT['ComponentCode']) and (i['TestType']==WAFERDICT['TestType'])),WAFERDICT['Filepath'])
                    WAFERDICT['RunNumber']='1'
                    
                    
    return WAFERDICTLIST   



upperletters=string.ascii_uppercase
numbers=string.digits

def IsComponentFormat(Input):
    if Input is None:
        return False
    if type(Input) is not str:
        return False
    for char in Input:
        if char not in upperletters+numbers:
            return False
    if len(Input)!=14:
        return False
    if Input[0:3]!='20U':
        return False
    return True

def IsBatchFormat(Input):
    if Input is None:
        return False
    if type(Input) is not str:
        return False
    for char in Input:
        if char not in upperletters+numbers:
            return False
    if len(Input)<=2:
        return False
    if Input[0] not in ['U','V']:
        return False
    try:
        int(Input[-1])
    except:
        return False
    LetterPortion=True
    for char in Input:
        if LetterPortion==True:
            if char not in upperletters:
                LetterPortion=False
        elif LetterPortion==False:
            if char not in numbers:
                return False
    return True

def IsWaferFormat(Input):
    if Input is None:
        return False
    if type(Input) is int:
        return True
    return True

def IsShorthandFormat(Input):
    if Input is None:
        return False
    if type(Input) is not int:
        try:
            int(Input)
        except:
            return False
    if len(str(Input))!=6:
        return False
    return True

filepathdelimiters='[/_\-\.]'
def ExtractBatchWaferComponentShorthandFromFilepath(Filepath):
    Batch=None
    Wafer=None
    Component=None
    Shorthand=None
    
    for cand in re.split(filepathdelimiters,Filepath):
        cand=cand.upper()
        if len(cand)<1:
            continue
        if IsBatchFormat(cand) and not IsComponentFormat(cand) and not IsShorthandFormat(cand):
            Batch=cand
        elif IsComponentFormat(cand) and not IsBatchFormat(cand) and not IsShorthandFormat(cand):
            Component=cand
        elif IsShorthandFormat(cand) and not IsBatchFormat(cand) and not IsComponentFormat(cand):
            Shorthand=cand
        elif cand[0]=='W':
            candtemp=cand[1:]
            if IsWaferFormat(candtemp) and not IsBatchFormat(candtemp) and not IsComponentFormat(candtemp):
                Wafer=candtemp
                try:
                    Wafer=int(Wafer)
                except:
                    Wafer=Wafer
    return Batch,Wafer,Component,Shorthand
    
    
def CheckConsistency(Field,FieldTemp,FieldSeemsRight,Filepath):
    output=Field
    
    if FieldSeemsRight==False:
        output=FieldTemp
        FieldSeemsRight=True
    elif FieldTemp!=Field:
        efpprint('Field I tried to extract from elsewhere does not match that in data file:',FieldTemp+', '+Field,Filepath)
    
    return output,FieldSeemsRight

def LoadShorthand(shorthandpath):
    ########Load shorthand database to python readable format:
    #First row is header
    #710004;VXX71041-W04;Hamamatsu;ATLAS07;Cambridge;false
    TEMPSHDICTLIST=[]
    try:
        with open(shorthandpath,'r',encoding='utf-8',errors='ignore') as f:
            SHORTHANDDATA = f.read()
    except:
        errprint('Could not read shorthand data file',shorthandpath)
        return None

    ROWS=[i for i in SHORTHANDDATA.split('\n') if i]
    SPLITROWS=[i.split(';') for i in ROWS]
    SPLITROWS=SPLITROWS[1:]

    for row in SPLITROWS:
        SHDICT=dict.fromkeys(ShorthandFields)

        #populate fields that aren't batch or wafer
        SHDICT[ShorthandFields[0]]=row[0]
        for i in range(3,7):
            SHDICT[ShorthandFields[i]]=row[i-1]

        #Populate the Batch and Wafer Fields    
        (Batch,Wafer)=string2BatchWafer(row[1])
        if (Batch!=None) and (Wafer!=None):
            SHDICT['Batch']=Batch.upper()       
            SHDICT['Wafer']=Wafer.upper()
            try:
                SHDICT['Wafer']=int(SHDICT['Wafer'])
            except:
                SHDICT['Wafer']=SHDICT['Wafer']
        else:
            errprint('Could not split batch and wafer in shorthand data file',str(row))

        TEMPSHDICTLIST.append(SHDICT)

    #Remove duplicates!
    SHDICTLIST=[]
    for Dict in TEMPSHDICTLIST:
        if Dict not in SHDICTLIST:
            SHDICTLIST.append(Dict)

    norprint(str(len(SHDICTLIST))+' Wafers found in Shorthand Database') 
    
    return SHDICTLIST
      
SHDICTLIST=LoadShorthand(shorthandpath)
if SHDICTLIST is not None:
    SHList=[i['Shorthand'] for i in SHDICTLIST]
    BatchList=[i['Batch'] for i in SHDICTLIST]
    WaferList=[i['Wafer'] for i in SHDICTLIST]

def BatchWafer2Shorthand(Batch,Wafer):
    Shorthand=None
    if SHDICTLIST is not None:
        Batchinds=[ i for i in range(len(BatchList)) if BatchList[i] == Batch ]
        Waferinds=[ i for i in range(len(WaferList)) if WaferList[i] == Wafer ]
        Intersectinds=[value for value in Batchinds if value in Waferinds] 
        if len(Intersectinds)==1:
            Shorthand=SHList[Intersectinds[0]]
        elif len(Intersectinds)==0:
            #errprint('Shorthand Info in Shorthand Data File for Batch/Wafer NOT FOUND',(Batch,Wafer))
            print()
        else:
            #errprint('Shorthand Info in Shorthand Data File for Batch/Wafer NOT UNIQUE',(Batch,Wafer))
            print()
    return Shorthand
    
def Shorthand2BatchWafer(SH):
    Batch=None
    Wafer=None
    if SHDICTLIST is not None:
        SHinds=[ i for i in range(len(SHList)) if SHList[i] == SH ]
        if len(SHinds)==1:
            Batch=BatchList[SHinds[0]]
            Wafer=WaferList[SHinds[0]]
        elif len(SHinds)==0:
            errprint('Batch and Wafer Info in Shorthand Data File for Shorthand NOT FOUND',str(SH))
        else:
            errprint('Batch and Wafer Info in Shorthand Data File for Shorthand NOT UNIQUE',str(SH)) 
    return Batch,Wafer



def Component2BatchWafer(Component):
    Batch=None
    Wafer=None
    compindlist=[i for i in range(0,len(COMPONENTIDDICTLIST)) if COMPONENTIDDICTLIST[i]['Component']==Component]
    if compindlist!=None:
        if len(compindlist)==1:
            compind=compindlist[0]
            Batch=COMPONENTIDDICTLIST[compind]['Batch']
            Wafer=COMPONENTIDDICTLIST[compind]['Wafer']
        elif len(compindlist)==0:
            errprint('Wafer is not in the ITK Database!',str([Component]))
        else:
            errprint('This wafer is not unique in the ITK database???',str([Component]))
    return Batch,Wafer

    
    
def BatchWafer2ComponentAndCode(Batch,Wafer):
    Component=None
    ComponentCode=None
    compindlist=[i for i in range(0,len(COMPONENTIDDICTLIST)) if (COMPONENTIDDICTLIST[i]['Batch']==Batch) and (COMPONENTIDDICTLIST[i]['Wafer']==Wafer)]
    if compindlist!=None:
        if len(compindlist)==1:
            compind=compindlist[0]
            Component=COMPONENTIDDICTLIST[compind]['Component']
            ComponentCode=COMPONENTIDDICTLIST[compind]['ComponentCode']
        elif len(compindlist)==0:
            errprint('Wafer is not in the ITK Database!',str([Batch,Wafer]))
        else:
            errprint('This wafer is not unique in the ITK database???',str([Batch,Wafer]))
    return Component,ComponentCode

def BatchWafer2Type(Batch,Wafer):
    Type=None
    compindlist=[i for i in range(0,len(COMPONENTIDDICTLIST)) if (COMPONENTIDDICTLIST[i]['Batch']==Batch) and (COMPONENTIDDICTLIST[i]['Wafer']==Wafer)]
    if compindlist!=None:
        if len(compindlist)==1:
            compind=compindlist[0]
            Type=COMPONENTIDDICTLIST[compind]['Type']
        elif len(compindlist)==0:
            errprint('Wafer is not in the ITK Database!',str([Batch,Wafer]))
        else:
            errprint('This wafer is not unique in the ITK database???',str([Batch,Wafer]))
    return Type



#Extract Table into Rows
def ExtractTable(TABLEROWS,filename,filepath):
    if len(TABLEROWS)<=1:
        efpprint('Table Rows not formatted properly. Could not find any rows!',filename,filepath)
        return None 
    #Guess Delimiters
    headerdelimiter=GuessDelimiter(TABLEROWS[0])   
    if headerdelimiter==None:
        efpprint('Could not guess header delimiter!',filename,filepath)
        return None       
    delimiter=GuessDelimiter(TABLEROWS[1])   
    if delimiter==None:
        efpprint('Could not guess table delimiter!',filename,filepath)
        return None 
        
    #Extract Headers   
    temptableheaders=(TABLEROWS[0]).split(headerdelimiter)
    
    #Because someone decided to make a header have a space:
    tableheaders=[]
    if delimiter==' ':
        for i in temptableheaders:
            if i!='[%]':
                tableheaders.append(i)
            else:
                tableheaders[-1]+=' '+i
    else:
        tableheaders=temptableheaders

    #Get the table to be a proper list of columns
    TABLETRANS=[f.split(delimiter) for f in TABLEROWS[1:] if f]
    

    #find number of columns and rows
    columns=len(TABLETRANS[0])
    rows=len(TABLETRANS)
    
    try:
        #transposing the table
        TABLE=[[] for j in range(0,columns)]
        for i in range(0,rows):
            for j in range(0,columns):
                if TABLETRANS[i][j]=='None':
                    TABLE[j].append(None)
                else:
                    TABLE[j].append(float(TABLETRANS[i][j]))                   
                
        return tableheaders,TABLE
        """
        #filling the dictionary
        TABLEDICT={}
        for j in range(0,columns):
            TABLEDICT[tableheaders[j]]=TABLE[j]
        
        return TABLEDICT
        """
    except:
        efpprint('Error in transposing the table',filename,filepath)
        #print(TABLEROWS)
        #print(TABLETRANS)
        return None

    
    
    
#Guess the delimiter    
def GuessDelimiter(Row):
    #Guess the delimiter
    delimiter=None
    
    try:
        for dl in delimiterslist:
            if len((Row).split(dl))>1:
                delimiter=dl     
    except:
        delimiter=None
    return delimiter

#Return unique tests barring duplicates
def NonDuplicateTests(WAFERDICTLIST):
    norprint('There are '+str(len(WAFERDICTLIST))+' successfully processed tests total')
    NODUPWAFERDICTLIST=[]
    templist=[]
    for WAFERDICT in WAFERDICTLIST:
        compressed=ReduceTESTDICTToMatchITKInfo(WAFERDICT)
        
        #continue if test already exists
        if compressed in templist:
            copiedlists=[List for List in templist if List==compressed]
            if len(copiedlists)==1:
                efpprint('Test is copy of ',str([copiedlists[0][key] for key in KeysMustCheck]),WAFERDICT['Filepath'])
            else:
                efpprint('Test is copy of ',"ERROR IN FINDING DUPLICATE",WAFERDICT['Filepath'])
            continue

        if WAFERDICT['TestType'] == TestType_Thickness and WAFERDICT['AvThickness'] is not None and float(WAFERDICT['AvThickness'])>0:
            NODUPWAFERDICTLIST.append(WAFERDICT)
            templist.append(compressed)
            continue
        if WAFERDICT['TestType'] == TestType_Visual_Inspection:
            NODUPWAFERDICTLIST.append(WAFERDICT)
            templist.append(compressed)
            continue

        isempty=True
        #check all table fields in dict
        for key in tablefields:
            #if there is a field which is not none and not all zero it is a real test so append
            if WAFERDICT[key]!=None and not all(0==x for x in WAFERDICT[key]):
                NODUPWAFERDICTLIST.append(WAFERDICT)
                templist.append(compressed)
                isempty=False
                break
        if isempty==True:
            efpprint('Test is empty','',WAFERDICT['Filepath'])
    print('')
    print('')
    norprint('Of those, there are '+str(len(NODUPWAFERDICTLIST))+' UNIQUE and NON-BLANK/ZERO tests.')
    print('')
    return NODUPWAFERDICTLIST


regexspecialcharacterstoescape='.[]()-|'

def ImportDataFormats():
    dataformatfilenamestemp=sorted(os.listdir(dataformatpath))
    dataformatfilepathstemp = [os.path.join(dataformatpath,f) for f in dataformatfilenamestemp]
    
    norprint('Data Format Files Found:')
    print('')          
    [norprint(i) for i in dataformatfilenamestemp]
    print('')

    dataformatstrings=[]
    keylists=[]
    dataformatfilenames=[]
    dataformatfilepaths=[]
    hastablelist=[]
    #Looping through dataformat files and turning them into regex strings
    ###NOTE, THIS ASSUMES THAT BATCH STARTS WITH "V" AND COMPONENT STARTS WITH "20U"!
    for dataformatfilepath in dataformatfilepathstemp:
        try:
            with open(dataformatfilepath,encoding='utf-8',errors='ignore') as f:
                RAWDATAFORMAT=f.read()
                
                #Generate Key List:
                keylist=[f.split('&&&')[0] for f in RAWDATAFORMAT.split('$$$') if f]
                keylist=[f for f in keylist if f!='TABLE']
                keylist=[f for f in keylist if f!='IGNORE']
                keylists.append(keylist)
                
                #Generate regex string from file:
                trylist=[f.split('&&&') for f in RAWDATAFORMAT.split('$$$') if f]
                
                #Take care of regex special characters
                for f in trylist:
                    for char in regexspecialcharacterstoescape:
                        if len(f)>=2:
                            f[1]=f[1].replace(char,'\\'+char)
                    
                hastable=False
                for f in trylist:
                    if f[0]=='TABLE':
                        f[0]='([\s\S]*)'
                        hastable=True
                    elif f[0]=='IGNORE':
                        #f[0]='.*'
                        f[0]='[\s\S]*'
                    elif f[0]=='Shorthand':
                        f[0]='([0-9]*)'
                    elif f[0]=='Manufacturer':
                        f[0]='([^0-9]*|)'
                    elif f[0]=='Batch':
                        f[0]='(V.*|)'
                    elif f[0]=='Component':
                        f[0]='(20U.*|)'
                    elif f[0]=='WaferInfoStringStability':
                        f[0]='(.*;+.*)'
                    else:
                        f[0]='(.*)'
                dataformatstring=''
                for f in trylist:
                    for ff in f:
                        dataformatstring+=ff
                dataformatstrings.append(ProcessFile(dataformatstring))
                dataformatfilenames.append(os.path.basename(dataformatfilepath))
                dataformatfilepaths.append(dataformatfilepath)
                hastablelist.append(hastable)
        except:
            errprint('Could not read data format file', dataformatfilepath)
            continue
    return dataformatstrings,keylists,dataformatfilenames,dataformatfilepaths,hastablelist


def GetListOfTestFilepaths(querypath):
    if type(querypath)==str:
        querypath=[querypath]
    filepaths=[]
    for querypathsub in querypath:
        querypathsub=querypathsub.replace('\\','/')
        #If it is a path, look for all .dat and .txt inside it
        if os.path.isdir(querypathsub):
            if querypathsub[-1]!='/':
                querypathsub+='/'
            filepaths.extend([f for f in glob.glob(querypathsub+"**/*.dat",recursive=True)])
            filepaths.extend([f for f in glob.glob(querypathsub+"**/*.txt",recursive=True)])
        elif os.path.isfile(querypathsub):
            #if it is a .dat or .txt file
            if (querypathsub[-4:]=='.dat') or (querypathsub[-4:]=='.txt'):
                filepaths.append(querypathsub)
            else:
                errprint('The given query path is not a .dat or .txt file',querypathsub)
        else:
            errprint('The given query path could not be recognized as a filepath or a file',querypathsub)
        
    return filepaths

def ProcessFile(DATA):
    NEWDATA=DATA.replace('\r\n','\n')
    NEWDATA=NEWDATA.replace(' \n','\n')
    NEWDATA=NEWDATA.replace(': ',':')
    return NEWDATA
