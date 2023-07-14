#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
import RUNME_GenerateBatchReport

#To generate an html report comparing whatever is in the querypath to whatever is on the database, by batch:
querypath=["/var/clus/pc_backup/Cleanroom/data/sisensors/","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019"]
outputfile='TestNow.html'
RUNME_GenerateBatchReport.MAIN(querypath,outputfile)

#

"""
import sys

import RUNME_GenerateBatchReport
import UploadDataToDatabase
from CommonConfig import defaultoutputfile
from CommonConfig import extractRUNMEargsfromcmd
from CommonConfig import ITK_COMPONENTTYPE


def MAIN(querypath,outputfile=defaultoutputfile,batch=None,wafers=None):   
    if type(wafers)==str:
        wafers=[wafers]
    """
    #check if query path is actually a list, in which case separate it into a list
    if ',' in querypath or '[' in querypath or ']' in querypath:
        querypath=querypath.replace('[','')
        querypath=querypath.replace(']','')
        querypath=querypath.replace('"','')
        querypath=querypath.replace("'",'')
        
        querypathlist=querypath.split(',')
        querypath=[i.strip() for i in querypathlist]
    """
    #Import Data and Generate Report
    TESTCOMPARISONDATA=RUNME_GenerateBatchReport.MAIN(querypath,outputfile)
    #print ("TESTCOMPARISONDATA,", TESTCOMPARISONDATA)
    #Get things in good format
    FlattenedTestList=[]
    TestTypes=list(TESTCOMPARISONDATA.keys())
    TestTypes.remove('TITLES')

    #if ITK_COMPONENTTYPE!='SENSOR_H_TEST':
    for BatchInd in range(0,len(TESTCOMPARISONDATA['TITLES'])):
        for TestType in TestTypes:
            FlattenedTestList.extend(TESTCOMPARISONDATA[TestType]['CurrentTests'][BatchInd])
            """
    else:
        for TestType in TestTypes:
            FlattenedTestList=TESTCOMPARISONDATA[TestType]['CurrentTests']
            """
    ShouldUploadList=[]
    """
    for i in FlattenedTestList:
        if i['Decision'] in ['Pass']:
            ShouldUploadList.append(True)
        else:
            ShouldUploadList.append(False)
    """
   
    Decision= list(findkeys(FlattenedTestList, 'Decision'))
    print(list(findkeys(FlattenedTestList, 'Decision')), "\n")
    print ("Desicion,", Decision)

    for desicion in Decision:
        print ("Desicion,", desicion)
        if desicion == 'Pass':
            print("is pass")
            ShouldUploadList.append(True)
        else:
            print("is failed")
            ShouldUploadList.append(False)
    
    #print("FlattenedTestList,", FlattenedTestList ,"\n")
    #print("Shouldupload,", ShouldUploadList)
    ###UI Loop

    ConfirmUpload=False
    Exit=False
    while ConfirmUpload==False or Exit==False:
        print('')
        print('')
        PrintList(FlattenedTestList,ShouldUploadList)

        INPUT=input('>>')

        if INPUT=='Confirm Upload' or INPUT=='0':
            ConfirmUpload=True
            break
        elif INPUT=='Change Upload' or INPUT=='1':
            print('')
            print("Please write your input as follows: '0-2:True; 2,3,14:False; 10-12:False'")
            NEWINPUT=input('>>>>')
            UploadInput=ParseInput(NEWINPUT,len(FlattenedTestList))
            if type(UploadInput) is str:
                print("***ERROR***    "+UploadInput)
                continue
            else:
                print(UploadInput)
                for ind in UploadInput.keys():
                    if UploadInput[ind] in [True,False]:
                        ShouldUploadList[ind]=UploadInput[ind]
                    else:
                        print("***ERROR***    "+"Decision for index "+str(ind)+" not recognized. Must be in ['True','False']")
                        continue
        elif INPUT=='Change Decision' or INPUT=='2':
            print('')
            print("Please write your input as follows: '0,1-3,5:Pass; 2:Fail; 4,2:SoSo; 11-13:MeasErr'")
            NEWINPUT=input('>>>>')
            DecisionInput=ParseInput(NEWINPUT,len(FlattenedTestList))
            if type(DecisionInput) is str:
                print("***ERROR***    "+DecisionInput)
                continue
            else:
                for ind in DecisionInput.keys():
                    if DecisionInput[ind] in ['Pass','SoSo','Fail','MeasErr']:
                        FlattenedTestList[ind]['Decision']=DecisionInput[ind]
                    else:
                        print("***ERROR***    "+"Decision for index "+str(ind)+" not recognized. Must be in ['Pass','SoSo','Fail','MeasErr']")
                        continue
        elif INPUT=='Exit' or INPUT=='3':
            Exit=True
            break    
        else:
            print("***ERROR***    "+'Sorry, your input was not recognized.')


    #Upload To Database
    if ConfirmUpload==True and Exit==False:
        UPLOADTESTLIST=[FlattenedTestList[i] for i in range(0,len(FlattenedTestList)) if ShouldUploadList[i]==True]
        UploadDataToDatabase.UploadDataToDatabase(UPLOADTESTLIST)
   # print ("flattened,", FlattenedTestList)
    return FlattenedTestList

def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x    

#This function has been deprecated but has been left here in case the sensor people want this
def OldParseInput(NEWINPUT,lenFlattenedTestList):
    
    OutputDict={}
    
    NEWINPUT=NEWINPUT.replace(" ","")
    ListOfEntries=NEWINPUT.split(',')
    DictList=[Entry.split(':') for Entry in ListOfEntries]
    
    for Entry in DictList:
        if len(Entry)!=2:
            return """Unrecognized input. Please write your input as follows: 
            '0:True, 2:False, 10:False' for Upload 
            '0:Pass, 2:Fail, 4:SoSo, 11:MeasErr' for Decision changes"""
        
        try:
            key=int(Entry[0])
        except:
            return "The index keys must be integers"            
        
        if key<0 or key>=lenFlattenedTestList:
            return 'Sorry, one of your index keys was out of range'
        
        value=Entry[1]
        if value=='True':
            value=True
        elif value=='False':
            value=False
            
        OutputDict[key]=value
                          
    return OutputDict


def ParseInput(NEWINPUT,lenFlattenedTestList):
    
    OutputDict={}
    
    NEWINPUT=NEWINPUT.replace(" ","")
    ListOfEntries=NEWINPUT.split(';')
    DictList=[Entry.split(':') for Entry in ListOfEntries]
    
    for Entry in DictList:
        if len(Entry)!=2:
            return """Unrecognized input. Please write your input as follows: 
            '1,2-3:False; 5,6-8:True' for Upload changes
            '0:Pass; 2:Fail; 4-5,8:SoSo; 11:MeasErr' for Decision changes
            Note that ranges are inclusive!"""

        
        value=Entry[1]
        if value=='True':
            value=True
        elif value=='False':
            value=False
        
        keys=[]
        for key in Entry[0].split(','):
            print(key)
            try:
                key=int(key)
                keys.append(key)
            except:
                keyrange=key.split('-')
                keyrangestart=None
                keyrangeend=None
                if len(keyrange)==2:
                    try: 
                        keyrangestart=int(keyrange[0])
                        keyrangeend  =int(keyrange[1])
                        keys.extend(list(range(keyrangestart,keyrangeend+1)))
                    except:
                        return "The index keys must be integers (like '1') or a range (like '1-3' [inclusive])"    
                else:
                    return "The index keys must be integers (like '1') or a range (like '1-3' [inclusive])"     
        
        for key in keys:
            if key<0 or key>=lenFlattenedTestList:
                return 'Sorry, one of your index keys was out of range: '+str(key)
            OutputDict[key]=value
                          
    return OutputDict
        
    
def PrintList(FlattenedTestList,ShouldUploadList):
    tab="    "
    #print("Flattened,", FlattenedTestList)
    print("Shouldup,", ShouldUploadList)
    print("The current state of uploadable wafers is as follows.")
    print("Note the format is:")
    #print(tab+tab+"[Index]\tPass?\tUpload?\tWafer#\tTimestamp :\t\t\tFilename")
    print("")
    
    CurrentBatch="THIS IS NOT A BATCH"
    CurrentTestType="THIS IS NOT A TESTTYPE"
    if ITK_COMPONENTTYPE not in ['SENSOR_H_TEST','SENSOR_HALFMOONS']:
        print(tab+tab+"[Index]\tPass?\tUpload?\tWafer#\tTimestamp :\t\t\tFilename")
        for index in range(0,len(FlattenedTestList)):
            if CurrentBatch!=FlattenedTestList[index]['Batch']:
                CurrentBatch=FlattenedTestList[index]['Batch']
                print(str(CurrentBatch)+':')
            if CurrentTestType!=FlattenedTestList[index]['TestType']:
                CurrentTestType=FlattenedTestList[index]['TestType']
                print(tab+str(CurrentTestType)+':')
        
        
        print(tab+tab+"[{0}]\t{1}\t{2}\tW{3}\t{4} :\t{5}".format(index,FlattenedTestList[index]['Decision'],ShouldUploadList[index],FlattenedTestList[index]['Wafer'],FlattenedTestList[index]['Timestamp'],FlattenedTestList[index]['Filename']))
    else:
        print(tab+tab+"[Index]\tPass?\tUpload?\tWafer#\tTimestamp :\t\t\tFilename")
        for index in range(0,len(FlattenedTestList)):
            print(tab+tab+"[{0}]\t{1}\t{2}\tW{3}\t{4} :\t{5}".format(index,FlattenedTestList[index]['Decision'],ShouldUploadList[index],FlattenedTestList[index]['Wafer'],FlattenedTestList[index]['Timestamp'],FlattenedTestList[index]['Filename']))
    print('')
    print('')
    print("If you are satisfied, to upload: \t\ttype 'Confirm Upload' or '0'.")    
    print("To change whether to upload a wafer or not: \ttype 'Change Upload' or '1'.")    
    print("To change the Pass/Fail Decision: \t\ttype 'Change Decision' or '2'.")    
    print("To exit: \t\t\t\t\ttype 'Exit' or '3'.")
    
    
    
#Run from bash
if __name__=='__main__':
    querypath,outputfile,batch,wafers=extractRUNMEargsfromcmd(sys.argv)
    MAIN(querypath,outputfile,batch,wafers)
