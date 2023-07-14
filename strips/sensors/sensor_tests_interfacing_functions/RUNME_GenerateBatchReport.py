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

import GenerateReport
import ImportData
import ImportDataFromDatabase
from CommonConfig import defaultoutputfile
from CommonConfig import efpprint
from CommonConfig import extractRUNMEargsfromcmd
from CommonConfig import isTESTDICTinTESTDICTLISTDUPCHECK
from CommonConfig import makeTESTDICTLISTDUPCHECK

def MAIN(querypath,outputfile=defaultoutputfile,batch=None,wafers=None):
    if type(wafers)==str:
        wafers=[wafers]
            
    #Import Historical Data From Database And Current Data From Disk
    ITKDBTESTLIST=ImportDataFromDatabase.ImportDataFromDatabase()
    CAMDBTESTLIST=ImportData.ImportData(querypath)
    
    
    #Temp removal of ITK IV CV STRIP tests until bugs there are fixed
    #ITKDBTESTLIST=[i for i in ITKDBTESTLIST if i['TestType'] not in ['SENSOR_IV','SENSOR_CV','SENSOR_STRIP_TEST']]

    
    #Make sure the CAMDB tests are not already on the ITKDB 
    ITKDBTESTLISTDUPCHECK=makeTESTDICTLISTDUPCHECK(ITKDBTESTLIST)
    TEMPCAMDBTESTLIST=[]
    for TESTDICT in CAMDBTESTLIST:
        if isTESTDICTinTESTDICTLISTDUPCHECK(TESTDICT,ITKDBTESTLISTDUPCHECK):
            efpprint('Already Uploaded To ITK DB! Treating as such in report','',TESTDICT['Filepath'])
        else:
            TEMPCAMDBTESTLIST.append(TESTDICT)
    CAMDBTESTLIST=TEMPCAMDBTESTLIST
    
    ###Rearrange Tests Into TestTypes and Batches for Comparing in Report:
    """
    #The TESTCOMPARISONDATA format is as follows. Each test type will be updated by a function and the 
    #updated verion will be sent to graphing and report making
    TESTCOMPARISONDATA={
        'TITLES':['Batch 1','Batch 2'],
        'SENSOR_IV':{
            'CurrentTests':[TESTDICTLISTCURRENTBATCH1,TESTDICTLISTCURRENTBATCH2],
            'HistoricalTests':[TESTDICTLISTCURRENTBATCH1,TESTDICTLISTCURRENTBATCH2]
        },
        'SENSOR_CV':{
            'CurrentTests':[],
            'HistoricalTests':[]
        }
    }
    """
    
    #Sort Tests By Wafer Number and Timestamp
    CAMDBTESTLIST=[i[1] for i in sorted(zip([str(CAMDBTESTLIST[ind]['Wafer']).zfill(4)+str(CAMDBTESTLIST[ind]['Timestamp'])+str(ind) for ind in range(0,len(CAMDBTESTLIST))],CAMDBTESTLIST))]
    ITKDBTESTLIST=[i[1] for i in sorted(zip([str(ITKDBTESTLIST[ind]['Wafer']).zfill(4)+str(ITKDBTESTLIST[ind]['Timestamp'])+str(ind) for ind in range(0,len(ITKDBTESTLIST))],ITKDBTESTLIST))]
    
    
    
    
    
    
    if batch is None:
        batchlist=list(set(i['Batch'] for i in CAMDBTESTLIST))
    else:
        batchlist=[batch]
        
    print(batchlist)
    try:
        CURRENTTESTBATCHLIST=[]
        HISTORICALTESTBATCHLIST=[]
        TITLESLIST=[]
        for Batch in batchlist:
            TITLESLIST.append(str(Batch))
            CURRENTTESTBATCHLIST.append([i for i in CAMDBTESTLIST if (i['Batch']==Batch) and (i['Wafer'] in wafers)])
            HISTORICALTESTBATCHLIST.append([i for i in ITKDBTESTLIST if (i['Batch']==Batch) and (i['Wafer'] in wafers)])
    except:
        if wafers is not None:
            print('Warning: Could not parse input for the "wafers" parameter, please make it a list of integer wafer numbers without a W. Continuing with the entire batch.')
            
        CURRENTTESTBATCHLIST=[]
        HISTORICALTESTBATCHLIST=[]
        TITLESLIST=[]
        for Batch in batchlist:
            TITLESLIST.append(str(Batch))
            CURRENTTESTBATCHLIST.append([i for i in CAMDBTESTLIST if (i['Batch']==Batch)])
            HISTORICALTESTBATCHLIST.append([i for i in ITKDBTESTLIST if (i['Batch']==Batch)])
            
        
        

    return GenerateReport.MAIN(CURRENTTESTBATCHLIST,HISTORICALTESTBATCHLIST,TITLESLIST,outputfile)


#Run from bash
if __name__=='__main__':
    querypath,outputfile,batch,wafers=extractRUNMEargsfromcmd(sys.argv)
    MAIN(querypath,outputfile,batch,wafers)
