#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
#To use:
import ImportDataFromDatabase
FINALTESTLIST=ImportDataFromDatabase.ImportDataFromDatabase()


#To do queries for example get all wafers who have had an IV test:
[i['Wafer'] for i in FINALTESTLIST if i['TestType'] in ['SENSOR_IV','IV']]
"""
"""
###Author: David Rousso

Note that this assumes all units are consistent
"""
#import __path__
#import dbAccess
import pickle #nosec
import re

import itkdb
from CommonConfig import APIAlternateNamesTABLES
from CommonConfig import APIAlternateNamesValues
from CommonConfig import APIpicklefilename
from CommonConfig import APITestTypeList
from CommonConfig import DateTime2Timestamp
from CommonConfig import fullkeylist
from CommonConfig import ITK_COMPONENTTYPE
from CommonConfig import ITK_PROJECT
from CommonConfig import NoneList
from CommonConfig import norprint
from CommonConfig import picklefilename
from CommonConfig import string2BatchWafer
from CommonConfig import TestType_Manufacturing


def ImportDataFromDatabase():
    print('')
    print('')
    print('')
    print('')
    print('')
    print("Running ImportDataFromDatabase.py: Downloading Tests from ITK Database to a TESTDICTLIST Object:")
    print('')
    
    
    #Get List of TestTypes
    TestTypeList=[i['code'] for i in APITestTypeList]
   # print("TestTypeList,",TestTypeList)
    ###Pull current list of all non-deleted tests from database along with their updated timestamps
    APITestList=[]
    client = itkdb.Client()
    for TestType in TestTypeList:
        for testRun in (client.get("listTestRunsByTestType", json = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE, 'testType':TestType} )):
            APITestList.append(testRun)
        """
        APITestList.extend(dbAccess.extractList("listTestRunsByTestType", method = "GET",
                                      data = {
                                          "project": ITK_PROJECT,
                                          'componentType':ITK_COMPONENTTYPE, 
                                          'testType':TestType
                                      })
                          )
        """
    #APITestList = list(client.get("listTestRunsByTestType", json = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE, 'testType':"ATLAS18_CV_TEST_V1"} ))
    #Only take non-deleted tests
    #print("APITestList,", APITestList)
    CURRENTTESTIDLIST=[(i['id'],i['cts']) for i in APITestList if i['state']=='ready'] #'ready' means not deleted!
    #print("CURRENT", CURRENTTESTIDLIST)
    norprint('Completed Pull of List of Existing Tests from Database')
    
    ###Check Saved Test List to See What Must Be Updated
    try:
        with open(picklefilename, "rb") as fp:  #nosec # Unpickling
            OLDTESTLIST = pickle.load(fp)
    except:
        OLDTESTLIST =  []

    if len(OLDTESTLIST)>0:
        OLDTESTIDLIST=[(testdict['TestID'],testdict['TimeofUpload']) for testdict in OLDTESTLIST]
    else:
        OLDTESTIDLIST=[]
    #print("OLDTESTIDLIST,", OLDTESTIDLIST)
    #print("CURRENTTESTIDLIST,",CURRENTTESTIDLIST)
    #Make List of Tests We Need to Pull!
    ListofMissingTests=[testid[0] for testid in CURRENTTESTIDLIST if testid not in OLDTESTIDLIST]
    #print("ListofMissingtest,", ListofMissingTests)
    #Fill test list with old data IF it is not deleted (i.e. still in the current list)
    FINALTESTLIST=[testdict for testdict in OLDTESTLIST if (testdict['TestID'],testdict['TimeofUpload']) in CURRENTTESTIDLIST] 

    #print("FINALTESTLIST,",FINALTESTLIST)

    ###Download Updated or New Tests from Database:
    APITESTLIST=[]
    for testid in ListofMissingTests:
        APITESTLIST.append(client.get("getTestRunBulk", json = {'testRun':testid} ))
        """
        APITESTLIST.append(dbAccess.extractList("getTestRun", method = "GET",
                                      data = {'testRun':testid},
                                      ))
        """
    norprint('Completed Pull of Tests from Database')
    #print("APITESTLIST,",APITESTLIST)
    print('')
    print('')
    print('')    
    norprint('Extracting ITK Database Data into TESTDICTLIST object')
    
    ###Extract data pulled from database into a standard format:
    for APITestDicts in APITESTLIST:
        for APITestDict in APITestDicts:
            #print("APITestDict,",APITestDict)
            TESTDICT=dict.fromkeys(fullkeylist)
            #Extract actual data to correct format
            #Make a useable dictionary of the API Data
            APIParamDict={}
            PropResDictList=[]
            PropResDictList.extend(APITestDict['properties'])
            PropResDictList.extend(APITestDict['results'])
            for PropResDict in PropResDictList:
                APIParamDict[PropResDict['code']]=PropResDict['value'] 
                
                #This adds all of the variables found to the testdictlist in their original forms. 
                #This is to make things generic
                TESTDICT[PropResDict['code']]=PropResDict['value'] 
                
                
            #Fill in variables in TESTDICT if the names of the API Data match them
            #This needs to be done separately for tables and headers since 
            #The variable names on the ITK DB side are overloaded
            for param in APIAlternateNamesTABLES.keys():
                if param in fullkeylist:
                    for APIparam in APIParamDict.keys():
                        if APIparam in APIAlternateNamesTABLES[param]:
                            if type(APIParamDict[APIparam])==list:
                                output=[]
                                for i in APIParamDict[APIparam]:
                                    if i not in NoneList:
                                        output.append(i)
                                    else:
                                        output.append(None)
                                TESTDICT[param]=output
            for param in APIAlternateNamesValues.keys():
                if param in fullkeylist:
                    for APIparam in APIParamDict.keys():
                        if APIparam in APIAlternateNamesValues[param]:
                            if type(APIParamDict[APIparam])!=list:
                                TESTDICT[param]=APIParamDict[APIparam]
                
                
            #Extract Metadata to correct format (overwriting it if it is in the data)
            #print(APITestDict)
            #ComponentID=APITestDict['component']['code'] 
            ComponentID=APITestDict['components'][0]['code'] 
            TESTDICT['ComponentCode']=ComponentID
            TestType=APITestDict['testType']['code'] 
            TESTDICT['TestType']=TestType 
            
            #Special Case with 'MANUFACTURING' defects which is weird
            if TestType==TestType_Manufacturing:
                try:
                    TESTDICT['Defects']={i['name']:(i['description'],i['properties']) for i in APITestDict['defects']}
                except:
                    TESTDICT['Defects']=APITestDict['defects']
                    
            try:
                #TESTDICT['Component']=APITestDict['component']['serialNumber']
                TESTDICT['Component']=APITestDict['components'][0]['serialNumber']
            except:
                TESTDICT['Component']=None
            #TESTDICT['Type']=APITestDict['component']['type']['code']
            TESTDICT['Type']=APITestDict['components'][0]['type']['code']
            TESTDICT['Institute']=APITestDict['institution']['code'] 
            TESTDICT['TimeofUpload']=APITestDict['cts']
            TESTDICT['TestID']=APITestDict['id'] 
            TESTDICT['RunNumber']=APITestDict['runNumber'] 
            TESTDICT['DataFormat']='FromITKDatabase'     
            
            
            #Extracting Batch and Wafer from Name
            #Name=APITestDict['component']['alternativeIdentifier'].upper() 
            
            Name=APITestDict['components'][0]['alternativeIdentifier']
            if Name is not None:
                Name=Name.upper()

            SplitName=string2BatchWafer(Name)
            TESTDICT['Batch']=SplitName[0]
            TESTDICT['Wafer']=SplitName[1]
            
            #Extract Timestamp to correct format
            DateTime=APITestDict['date']
            SplitDateTime=DateTime.split(' ')
            if re.search(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z',DateTime) is not None:
                TESTDICT['Timestamp']=DateTime
            elif len(SplitDateTime)==1:
                TESTDICT['Timestamp']=DateTime2Timestamp(SplitDateTime[0],'00:00:00')
                print("No time found in received from  database, using  00:00:00 instead.")
            elif len(SplitDateTime)==2:
                TESTDICT['Timestamp']=DateTime2Timestamp(SplitDateTime[0],SplitDateTime[1])
            else:
                print('Unknown Date Time Format: '+DateTime)
                TESTDICT['Timestamp']=None
            
            try: 
                TESTDICT['Segment']=int(TESTDICT['Segment'])
            except:
                TESTDICT['Segment']=TESTDICT['Segment']
                
            #If anything is a None type make it none.
            for key in TESTDICT.keys():
                if TESTDICT[key] in NoneList:
                    TESTDICT[key]=None
                    
            #Try to make any list a float list instead of strings
            for key in TESTDICT.keys(): 
                value=TESTDICT[key]
                if type(value) is list:
                    try:
                        TESTDICT[key]=[float(i) for i in value]
                    except:
                        TESTDICT[key]=value
                    
                    
            try:
                TESTDICT['Wafer']=int(TESTDICT['Wafer'])
            except:
                TESTDICT['Wafer']=TESTDICT['Wafer']
                
                
            #Append TESTDICT to TESTDICTLIST
            FINALTESTLIST.append(TESTDICT)
	
    ###Dump to memory
    with open(picklefilename, "wb") as fp:   #Pickling
        pickle.dump(FINALTESTLIST, fp)
        
    ###Below not actually needed, just useful for debugging
    try:
        with open(APIpicklefilename, "rb") as fp:  #nosec # Unpickling
            TOTALAPITESTLIST = pickle.load(fp)
    except:
        TOTALAPITESTLIST = []
    TOTALAPITESTLIST.extend(APITESTLIST)
    with open(APIpicklefilename, "wb") as fp:   #Pickling
        pickle.dump(TOTALAPITESTLIST, fp)
           
    print('ImportDataFromDatabase.py Complete!')
    
     
    return FINALTESTLIST
