#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
#To use:
import UploadDataToDatabase
UploadDataToDatabase.UploadDataToDatabase(UPLOADTESTLIST)
"""
"""
###Author: David Rousso
"""
#import __path__    
#import dbAccess
import GetComponentInfoFromDatabase
import itkdb
from CommonConfig import APIParamTypeList
from CommonConfig import errprint
from CommonConfig import isTESTDICTinTESTDICTLISTDUPCHECK
from CommonConfig import makeTESTDICTLISTDUPCHECK
from CommonConfig import NoneInTable
from CommonConfig import NoneOutputType
from CommonConfig import norprint
from CommonConfig import PropertiesDictList
from CommonConfig import ResultsTablesDictList
from CommonConfig import ResultsValuesDictList
from CommonConfig import Timestamp2ITKTime
COMPONENTIDDICTLIST=GetComponentInfoFromDatabase.GetComponentInfoFromDatabase()
#print("COMPONENTIDDICTLIST,",COMPONENTIDDICTLIST)
import ImportDataFromDatabase

def UploadDataToDatabase(UPLOADTESTLIST):
    #We need to recheck this everytime we run because the data on the database changes every time we run this!
    DATABASETESTLIST=ImportDataFromDatabase.ImportDataFromDatabase()
    DATABASETESTLISTDUPCHECK=makeTESTDICTLISTDUPCHECK(DATABASETESTLIST)
    print('')
    print('')
    print('')
    print('')
    print('')
    
    print("Running UploadDataToDatabase.py: Uploading Tests from TESTDICTLIST Object to ITK Database:")
    print('')
    
    for Test in UPLOADTESTLIST:
        print(' ')
        #print("test,",Test)
        Nameforprintout=  str((Test['Component'],Test['Batch'], Test['Wafer'], Test['TestType'], Test['Timestamp']))+' : \n\t\t'+str(Test['Filepath'])
        norprint('Uploading: '+Nameforprintout)
            
        #Add Flags to Comments
        Test['Settings']=str(Test['Settings'])+'; \n'+str(Test['Flags'])
        
        #Get TestType 
        TestType=Test['TestType']

        if (TestType not in ResultsValuesDictList.keys()) and (TestType not in ResultsTablesDictList.keys()) and (TestType not in PropertiesDictList.keys()):
            errprint('Test Type Not In Database!!',TestType)
            continue
        
        #compile properties and results
        PropertiesDict={}
        for Param in PropertiesDictList[TestType].keys():
            TestDictKey=PropertiesDictList[TestType][Param]
            if TestDictKey=='Time':
                output=Timestamp2ITKTime(Test['Timestamp'])
            elif Param in Test.keys(): #to catch case where you set the variable explicitly
                output=Test[Param]
            elif (TestDictKey is None) or (TestDictKey not in Test.keys()) or (Test[TestDictKey] is None):
                output=NoneOutputType(APIParamTypeList[TestType][Param])
            else:
                output=Test[TestDictKey]
            PropertiesDict[Param]=output
           
            
        ResultsDict={}
        for Param in ResultsValuesDictList[TestType].keys():
            TestDictKey=ResultsValuesDictList[TestType][Param]
            if Param in Test.keys(): #to catch case where you set the variable explicitly
                output=Test[Param]
            elif (TestDictKey is None) or (TestDictKey not in Test.keys()) or (Test[TestDictKey] is None):
                output=NoneOutputType(APIParamTypeList[TestType][Param])
            else:
                output=Test[TestDictKey]
            ResultsDict[Param]=output
        for Param in ResultsTablesDictList[TestType].keys():
            TestDictKey=ResultsTablesDictList[TestType][Param]
            if Param in Test.keys(): #to catch case where you set the variable explicitly
                output=Test[Param]
            elif (TestDictKey is None) or (TestDictKey not in Test.keys()) or (Test[TestDictKey] is None):
                output=NoneOutputType(APIParamTypeList[TestType][Param])
            else:
                output=[]
                for i in Test[TestDictKey]:
                    if i is not None:
                        output.append(i)
                    else:
                        output.append(NoneInTable)
            ResultsDict[Param]=output
        #print(ResultsDict)
            
        #Check if Test is already uploaded
        if isTESTDICTinTESTDICTLISTDUPCHECK(Test,DATABASETESTLISTDUPCHECK):
            errprint('Already Uploaded!','')
            continue  
            

        #Convert Test Decision to a passed/problems boolean
        Decision=Test['Decision']
        if Decision=='Pass':
            passed=True
            problems=False
        elif Decision=='SoSo':
            passed=True
            problems=True
        elif Decision=='Fail':
            passed=False
            problems=True
        else:
            passed=False
            problems=False

        #Compile data structure for upload
        dataforupload={
            "component":   Test['ComponentCode'],
         #   "serialNumber":    Test['Component'],
            "testType":     Test['TestType'],
            "institution": Test['Institute'],
            "runNumber":   Test['RunNumber'],
            #"date":        Timestamp2ITKDateTime(Test['Timestamp']),
            "date":        Test['Timestamp'],
            "passed":      passed,
            "problems":    problems,
            "properties":  PropertiesDict,
            "results":     ResultsDict
        }

        
        #Check for ComponentCode existing
      
        if Test['ComponentCode'] not in [i['ComponentCode'] for i in COMPONENTIDDICTLIST]:
            errprint('Cannot upload as wafer does not exist on database. Please add it first.','')
            continue

        client = itkdb.Client()

        result=(client.post("uploadTestRunResults", json = dataforupload))
        if (('uuAppErrorMap')=={}):
            norprint('Upload of Test and File Succesful!')
        elif (('uuAppErrorMap'))[0]=='cern-itkpd-main/uploadTestRunResults/':
            print("Error in Test Upload.")
        elif list(('uuAppErrorMap'))[0]=='cern-itkpd-main/uploadTestRunResults/componentAtDifferentLocation':
            errprint('Component cannot be uploaded as is not currently at the given location',Test['Institute'])
        elif (('uuAppErrorMap'))[0]=='cern-itkpd-main/uploadTestRunResults/unassociatedStageWithTestType':
            errprint('Component cannot be uploaded as the current stage does not have this test type. You will need to update the stage of the component on the ITK DB. Note that due to a bug on the ITK DB, you might also get this error if the component is not at your current location.',Test['Institute'])
        elif (('uuAppErrorMap'))[0]!='cern-itkpd-main/uploadTestRunResults/':
            print("Upload of Test Succesful!","\n")
        else:
            errprint('^Error Uploading File',dataforupload)
            
        #attachmetresult = client.post("createTestRunAttachment", json = { "testRun":"047cd5c68ab6e100cd382aca5bacc057", "type": "file","data":dataforupload,"url" :Test['Filepath']})
        #
        #upload the data
   
        
        if (('uuAppErrorMap')[0]!='cern-itkpd-main/uploadTestRunResults/'):
            ###Upload the attached file!
            testRun=result['testRun']['id']
            Test['TestRunCode']=testRun
            dataforuploadattachment={
                    "testRun":Test['TestRunCode'],
                    "title": Test['Filename'], 
                    "description": "Automatic Attachment of Original Data File", 
                    "type": "file",
                    'url' : Test['Filename']
                }
            attachment = {'data': (Test['Filename'], open(Test['Filepath'], 'rb'), 'text')}
            #attachmentresult={'uuAppErrorMap':{'Generic Error':'Generic Error'}}
           # try:
            attachmentresult = client.post("createTestRunAttachment", data=dataforuploadattachment, files= attachment)
                
                #attachmentresult = dbAccess.doSomething("createTestRunAttachment", method = "POST",
                 #                                   data = dataforuploadattachment,
                  #                                  attachments={'data':open( Test['Filepath'],'rb')}
                   #             )
            #except:
             #   print('Error Uploading File. See above.')
            '''
            result={'uuAppErrorMap':{'Generic Error':'Generic Error'}}
            #upload the data
            try:
                result=dbAccess.extractList("uploadTestRunResults", method = "POST",
                                            data = dataforupload,
                                            )    
            except:
                print('Error in Uploading. See Above.')
            #fake upload
            #print(Test)
                #print(APIParamTypeList[TestType])
            
            #result={'uuAppErrorMap':{}}
            #Check for errors
            if result['uuAppErrorMap']=={}:
                norprint('Upload of Test Succesful!')
            elif list(result['uuAppErrorMap'].keys())[0]=='cern-itkpd-main/uploadTestRunResults/componentAtDifferentLocation':
                errprint('Component cannot be uploaded as is not currently at the given location',Test['Institute'])
            elif list(result['uuAppErrorMap'].keys())[0]=='cern-itkpd-main/uploadTestRunResults/unassociatedStageWithTestType':
                errprint('Component cannot be uploaded as the current stage does not have this test type. You will need to update the stage of the component on the ITK DB. Note that due to a bug on the ITK DB, you might also get this error if the component is not at your current location.',Test['Institute'])
            else:
                errprint('^Error Uploading File',dataforupload)
                
            
            if result['uuAppErrorMap']=={}:
                ###Upload the attached file!
                testRun=result['testRun']['id']
                Test['TestRunCode']=testRun
                dataforuploadattachment={
                        "testRun":testRun, 
                        "title": Test['Filename'], 
                        "description": "Automatic Attachment of Original Data File", 
                        "type": "file"   
                    }
                attachmentresult={'uuAppErrorMap':{'Generic Error':'Generic Error'}}
                try:
                    attachmentresult=dbAccess.doSomething(
                        "createTestRunAttachment", 
                        method = "POST",
                        data = dataforuploadattachment,
                        attachments={'data':open( Test['Filepath'],'rb')}
                    )
                except:
                    print('Error Uploading File. See above.')
            '''        
            #Check for errors
            result=attachmentresult
            #Check for errors
            if (('uuAppErrorMap')=={}):
                norprint('Upload of Attachment Succesful!' )
            elif (('uuAppErrorMap'))[0]=='cern-itkpd-main/createTestRunAttachment/':
                print("Error in the Attachment Upload.")
            else:
                errprint('^Error Uploading Attachment',dataforupload)
    print("data for upload,", dataforupload)    
    print('')
    print('')
    print('UploadDataToDatabase.py Complete!')
    
    return None
