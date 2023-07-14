#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
import RUNME_GenerateSpecialStabilityReport

#To generate a special stability html report comparing whatever is in the querypath to whatever is on the database, by batch:
querypath=["/var/clus/pc_backup/Cleanroom/data/sisensors/","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019"]
outputfile='TestNow.html'
RUNME_GenerateSpecialStabilityReport.MAIN(querypath,outputfile)

#

"""
import sys
import webbrowser

import ImportData
import ImportDataFromDatabase
from CommonConfig import defaultoutputfile
from CommonConfig import efpprint
from CommonConfig import extractRUNMEargsfromcmd
from CommonConfig import isTESTDICTinTESTDICTLISTDUPCHECK
from CommonConfig import makeTESTDICTLISTDUPCHECK
from CommonConfig import TestType_Stability
from GenerateReport import AnalyzeBatches
from GenerateReport import batchfooter
from GenerateReport import batchheader
from GenerateReport import DisplayFieldsForTestTypes
from GenerateReport import footer
from GenerateReport import GeneratePlot
from GenerateReport import header

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
    
    
    
    
    CURRENTTESTBATCHLIST=[]
    HISTORICALTESTBATCHLIST=[]
    TITLESLIST=[]
    for Batch in set(i['Batch'] for i in CAMDBTESTLIST):
        TITLESLIST.append(str(Batch))
        CURRENTTESTBATCHLIST.append([i for i in CAMDBTESTLIST if (i['Batch']==Batch)])
        HISTORICALTESTBATCHLIST.append([i for i in ITKDBTESTLIST if (i['Batch']==Batch)])
        
        
        
    if len(HISTORICALTESTBATCHLIST)!=len(CURRENTTESTBATCHLIST) or len(HISTORICALTESTBATCHLIST)!=len(TITLESLIST):
        print('Error: lengths of inputs are not the same. They must be list of batches, where each batch is a list of tests')
    
    TestTypesToAnalyze=DisplayFieldsForTestTypes.keys()
    TESTCOMPARISONDATA={}
    TESTCOMPARISONDATA['TITLES']=TITLESLIST
    


    for TestType in TestTypesToAnalyze:
        TESTCOMPARISONDATA[TestType]={}
        TESTCOMPARISONDATA[TestType]['CurrentTests']=[]
        TESTCOMPARISONDATA[TestType]['HistoricalTests']=[]
        for Batchind in range(0,len(HISTORICALTESTBATCHLIST)):
            if TestType==TestType_Stability:
                TESTCOMPARISONDATA[TestType]['CurrentTests'].append([i for i in CURRENTTESTBATCHLIST[Batchind] if (i['TestType']==TestType)])
                TESTCOMPARISONDATA[TestType]['HistoricalTests'].append([i for i in HISTORICALTESTBATCHLIST[Batchind] if (i['TestType']==TestType)])



    ###Run the Analysis Code to Update the Test Dictionaries
    ####Repeat these next 6 lines of code for each TestType, changing only the first three lines
    import SENSOR_STABILITY_Analysis
    TestType=TestType_Stability
    AnalysisFunction=SENSOR_STABILITY_Analysis.Analyze_STABILITY
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST
    
    
    ###Generate the HTML Report 
    GenerateStabilityReportHTML(TESTCOMPARISONDATA,outputfile)
    print('')
    print('')
    print('Report printed out to '+outputfile)
    webbrowser.open(outputfile,new=2, autoraise=True)
    return TESTCOMPARISONDATA



###This generates the HTML Report
def GenerateStabilityReportHTML(TESTCOMPARISONDATA,outputfile):
    
    htmloutput=""
    htmloutput+=header
    
    for BatchInd in range(0,len(TESTCOMPARISONDATA['TITLES'])):
        htmloutput+=batchheader.format(TESTCOMPARISONDATA['TITLES'][BatchInd])
        
        #STABILITY
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Temperature-Compensated Stability Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','T-Compensated Current [nA]','Plot_Time','Plot_NormalisedCurrent')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'NON Temperature-Compensated Stability Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','Raw Current [nA]','Plot_Time','Plot_Current')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Temperature Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','Temperature[°C]','TABLE_Time[s]','TABLE_Temperature[°C]')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Humidity Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','Humidity[%]','TABLE_Time[s]','TABLE_Humidity[%]')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Humidity-Current Correlation Plots: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Humidity[%]','T-Compensated Current [nA]','INTERP_TABLE_Humidity[%]','INTERP_TABLE_COMPCurrent[nA]')
        
        
        htmloutput+=batchfooter   
    htmloutput+=footer    
    
    with open(outputfile,'w+') as f:
        f.write(htmloutput)
        
        

#Run from bash
if __name__=='__main__':
    querypath,outputfile,batch,wafers=extractRUNMEargsfromcmd(sys.argv)
    MAIN(querypath,outputfile,batch,wafers)
