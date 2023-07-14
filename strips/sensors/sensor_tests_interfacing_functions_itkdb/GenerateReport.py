"""
import GenerateReport
import ImportDataFromDatabase

ITKDBTESTDICTLIST=ImportDataFromDatabase.ImportDataFromDatabase()

Batch='VPX30816'

CURRENTTESTBATCHLIST=[[]]
HISTORICALTESTBATCHLIST=[[i for i in ITKDBTESTDICTLIST if i['Batch']==Batch]]
TITLESLIST=[Batch]

GenerateReport.MAIN(CURRENTTESTBATCHLIST,HISTORICALTESTBATCHLIST,TITLESLIST,outputfile)

"""
##Rearrange Tests Into TestTypes and Batches for Comparing in Report:
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
import copy
import os
import webbrowser

import numpy
import numpy as np
from CommonConfig import colorlistonoff
from CommonConfig import colorlistonoffuseful
from CommonConfig import DisplayFieldsForTestTypes
from CommonConfig import eng_string
from CommonConfig import GoodChars
from CommonConfig import TestType_CV
from CommonConfig import TestType_IV
from CommonConfig import TestType_IV_Hammamatsu
from CommonConfig import TestType_Manufacturing
from CommonConfig import TestType_Metrology
from CommonConfig import TestType_Stability
from CommonConfig import TestType_Strip
from CommonConfig import TestType_Thickness
from CommonConfig import TestType_Visual_Inspection
from CommonConfig import TestV
from SENSOR_STRIPTEST_Analysis import STRIPS_SUMMARY
from SENSOR_STRIPTEST_Analysis import STRIPS_SUMMARY_HPK
    
colourhtmlformat=".{0} {{ background-color:{1}; }}"
colourshtmloutput=''
for decisionkey in colorlistonoff.keys():
    colourshtmloutput+=colourhtmlformat.format(decisionkey,'#%02x%02x%02x' % colorlistonoff[decisionkey])
    
    
"""th {{
  text-align: left;
}}
td {{
  text-align: center;
}}
table, th, td {{
  border: 1px solid black;
  border-collapse: collapse;
}}"""    
    
header="""
<!DOCTYPE html>
<html>
    <head>
        <style>
 table {{
  font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
  border-collapse: collapse;
  width: 100%;
  table-layout: fixed;
}}
td,th {{
    overflow: hidden; 
    text-overflow: ellipsis; 
    word-wrap: break-word;
}}


 td, th {{
  border: 1px solid #ddd;
  padding: 8px;
}}

 tr:nth-child(even){{background-color: #f2f2f2;}}

th {{
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: left;
  background-color: #0033A0;
  color: white;
}}

td {{
  vertical-align: top;
}}


{0}
        </style>
        <!-- Plotly.js -->
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
""".format(colourshtmloutput)
footer="""
    </body>
</html>
"""
    
batchheader="""
    <h1>Batch: {0}</h1>
"""
batchfooter=""""""

#<table style="width:100%">
tableheader="""
    <font size="2">
    <table>
    """
tableheader+='<col width="80">\n'
"""
for TestType in DisplayFieldsForTestTypes.keys():
    tableheader+='<col width="250">\n'
"""
tableheader+="""
  <tr>
    <th>Wafer</th>
"""
for TestType in DisplayFieldsForTestTypes.keys():
    tableheader+="<th>{0}</th>\n".format(str(TestType))
tableheader+="""
  </tr>
"""
tablefooter="""</table>"""

rowheader="""<tr>"""
rowfooter="""</tr>"""

cellheader="""<td>"""
cellfooter="""</td>"""

subcellheader="""<br><span style="display: block" class="{0}">""" 
subcellfooter="""</span>"""

        

def MAIN(CURRENTTESTBATCHLIST,HISTORICALTESTBATCHLIST,TITLESLIST,outputfile):
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
            #Keep Hammatsu and our IV separate
            if False:
            #if TestType==TestType_IV:
                #Special Case to add "IV as well"
                TESTCOMPARISONDATA[TestType]['CurrentTests'].append([i for i in CURRENTTESTBATCHLIST[Batchind] if (i['TestType']==TestType or i['TestType']==TestType_IV_Hammamatsu)])
                TESTCOMPARISONDATA[TestType]['HistoricalTests'].append([i for i in HISTORICALTESTBATCHLIST[Batchind] if (i['TestType']==TestType or i['TestType']==TestType_IV_Hammamatsu)])
            else:
                TESTCOMPARISONDATA[TestType]['CurrentTests'].append([i for i in CURRENTTESTBATCHLIST[Batchind] if (i['TestType']==TestType)])
                TESTCOMPARISONDATA[TestType]['HistoricalTests'].append([i for i in HISTORICALTESTBATCHLIST[Batchind] if (i['TestType']==TestType)])



    ###Run the Analysis Code to Update the Test Dictionaries
    ####Repeat these next 6 lines of code for each TestType, changing only the first three lines
    import SENSOR_CV_Analysis
    TestType=TestType_CV
    AnalysisFunction=SENSOR_CV_Analysis.Analyze_CV
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST

    import SENSOR_IV_Analysis
    TestType=TestType_IV_Hammamatsu
    AnalysisFunction=SENSOR_IV_Analysis.Analyze_IV
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST
    
    import SENSOR_IV_Analysis
    TestType=TestType_IV
    AnalysisFunction=SENSOR_IV_Analysis.Analyze_IV
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST


    import SENSOR_STRIPTEST_Analysis
    TestType=TestType_Strip
    AnalysisFunction=SENSOR_STRIPTEST_Analysis.Analyze_STRIPTEST_SEG
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST
    
    
    import SENSOR_BOW_Analysis
    TestType=TestType_Metrology
    AnalysisFunction=SENSOR_BOW_Analysis.Analyze_BOW
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST
    
    
    import SENSOR_STABILITY_Analysis
    TestType=TestType_Stability
    AnalysisFunction=SENSOR_STABILITY_Analysis.Analyze_STABILITY
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST

    import SENSOR_THICKNESS_Analysis
    TestType=TestType_Thickness
    AnalysisFunction=SENSOR_THICKNESS_Analysis.Analyze_THICKNESS
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST
    
    import SENSOR_VISUAL_INSPECTION_test
    TestType=TestType_Visual_Inspection
    AnalysisFunction=SENSOR_VISUAL_INSPECTION_test.Visual_Inspection
    TEMPANALYZEDNEWLISTTESTDICTLIST,TEMPANALYZEDOLDLISTTESTDICTLIST=AnalyzeBatches(AnalysisFunction,TESTCOMPARISONDATA[TestType]['CurrentTests'],TESTCOMPARISONDATA[TestType]['HistoricalTests'])
    TESTCOMPARISONDATA[TestType]['CurrentTests']=TEMPANALYZEDNEWLISTTESTDICTLIST
    TESTCOMPARISONDATA[TestType]['HistoricalTests']=TEMPANALYZEDOLDLISTTESTDICTLIST
  
    ###Generate the HTML Report 
    GenerateReportHTML(TESTCOMPARISONDATA,outputfile)
    print('')
    print('')
    print('Report printed out to '+outputfile)
    webbrowser.open(os.path.abspath(outputfile),new=2, autoraise=True)
    return TESTCOMPARISONDATA
    

###Since the AnalysisFunction's just convert one test dict at a time, this serves as a wrapper for the batch divided lists
def AnalyzeBatches(AnalysisFunction,NEWLISTTESTDICTLIST,OLDLISTTESTDICTLIST):

    ANALYZEDNEWLISTTESTDICTLIST=[]
    ANALYZEDOLDLISTTESTDICTLIST=[]

    for compareind in range(0,len(NEWLISTTESTDICTLIST)):

        NEWCOMPTESTDICTLIST=NEWLISTTESTDICTLIST[compareind]
        OLDCOMPTESTDICTLIST=OLDLISTTESTDICTLIST[compareind]

        ANALYZEDNEWCOMPTESTDICTLIST=[]
        ANALYZEDOLDCOMPTESTDICTLIST=[]


        for WAFERDICT in NEWCOMPTESTDICTLIST: 
            ANALYZEDWAFERDICT=AnalysisFunction(WAFERDICT)
            ANALYZEDNEWCOMPTESTDICTLIST.append(ANALYZEDWAFERDICT)

        for WAFERDICT in OLDCOMPTESTDICTLIST:
            ANALYZEDWAFERDICT=AnalysisFunction(WAFERDICT)
            ANALYZEDOLDCOMPTESTDICTLIST.append(ANALYZEDWAFERDICT)


        ANALYZEDNEWLISTTESTDICTLIST.append(ANALYZEDNEWCOMPTESTDICTLIST)
        ANALYZEDOLDLISTTESTDICTLIST.append(ANALYZEDOLDCOMPTESTDICTLIST)

    return ANALYZEDNEWLISTTESTDICTLIST,ANALYZEDOLDLISTTESTDICTLIST




###This generates the HTML Report
def GenerateReportHTML(TESTCOMPARISONDATA,outputfile):
    
    htmloutput=""
    htmloutput+=header
    
    for BatchInd in range(0,len(TESTCOMPARISONDATA['TITLES'])):
        htmloutput+=batchheader.format(TESTCOMPARISONDATA['TITLES'][BatchInd])
        
        #TABLE
        htmloutput+=GenerateSummaryTable(TESTCOMPARISONDATA,BatchInd)
        
        #IV_Hammamatsu
        #htmloutput+=GenerateFitPlot(TESTCOMPARISONDATA[TestType_IV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV]['HistoricalTests'][BatchInd],'IV Test Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Voltage [V]','Current Normalized to Area [nA/cm^2]',True)
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_IV_Hammamatsu]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV_Hammamatsu]['HistoricalTests'][BatchInd],'HPK IV Test Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Voltage [V]','Current Normalized to Area [nA/cm^2]','xdata','ydata',True)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_IV_Hammamatsu]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV_Hammamatsu]['HistoricalTests'][BatchInd],'HPK Current at Test V ({0} V) Histogram: '.format(TestV)+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Current at Test V Normalized to Area [nA/cm^2]','Wafers','IDataAtTestV',0.05-0.1,0.1)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_IV_Hammamatsu]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV_Hammamatsu]['HistoricalTests'][BatchInd],'HPK Breakdown Voltage Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Breakdown Voltage [V]','Wafers','MicroDischargeV',2.5-5,5)
        
        #IV
        #htmloutput+=GenerateFitPlot(TESTCOMPARISONDATA[TestType_IV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV]['HistoricalTests'][BatchInd],'IV Test Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Voltage [V]','Current Normalized to Area [nA/cm^2]',True)
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_IV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV]['HistoricalTests'][BatchInd],'IV Test Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Voltage [V]','Current Normalized to Area [nA/cm^2]','xdata','ydata',True)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_IV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV]['HistoricalTests'][BatchInd],'Current at Test V ({0} V) Histogram: '.format(TestV)+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Current at Test V Normalized to Area [nA/cm^2]','Wafers','IDataAtTestV',0.05-0.1,0.1)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_IV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_IV]['HistoricalTests'][BatchInd],'Breakdown Voltage Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Breakdown Voltage [V]','Wafers','MicroDischargeV',2.5-5,5)
        
        
        #CV
        #htmloutput+=GenerateFitPlot(TESTCOMPARISONDATA[TestType_CV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_CV]['HistoricalTests'][BatchInd],'CV Test Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Voltage [V]','1/Capacitance^2 [pF^{-2}]')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_CV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_CV]['HistoricalTests'][BatchInd],'CV Test Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Voltage [V]','1/Capacitance^2 [pF^{-2}]','xdata','ydata',False)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_CV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_CV]['HistoricalTests'][BatchInd],'Depletion Voltage Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Initial Depletion Voltage [V]','Wafers','Vdep[V]',0.5,1)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_CV]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_CV]['HistoricalTests'][BatchInd],'Active Thickness Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Active Thickness [um]','Wafers','Dfull[um]',0.5,1)
    
    
        #STRIP
        htmloutput+=GenerateWaferStrips(TESTCOMPARISONDATA,BatchInd,'Our Wafer Bad Strips Map '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Segment','Strip')
        
        htmloutput+=GenerateWaferStripsHPK(TESTCOMPARISONDATA,BatchInd,'HPK Wafer Bad Strips Map '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Segment','Strip')
        
        htmloutput+=GenerateHistStrips(TESTCOMPARISONDATA[TestType_Strip]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Strip]['HistoricalTests'][BatchInd],'Strips I Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Current[nA]','','TABLE_Current[nA]',-0.025,0.05,2,"stack")
        htmloutput+=GenerateHistStrips(TESTCOMPARISONDATA[TestType_Strip]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Strip]['HistoricalTests'][BatchInd],'Strips C Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Capacitance[pF]','','TABLE_Capacitance[pF]',50.25,0.5,200,"stack")
        htmloutput+=GenerateHistStrips(TESTCOMPARISONDATA[TestType_Strip]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Strip]['HistoricalTests'][BatchInd],'Strips R Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Resistance[MOhm]','','TABLE_Resistance[MOhm]',0.205,0.01,3,"stack")

        
        #METROLOGY
        htmloutput+=GenerateSurface(
            TESTCOMPARISONDATA[TestType_Metrology]['CurrentTests'][BatchInd], 
            TESTCOMPARISONDATA[TestType_Metrology]['HistoricalTests'][BatchInd], 
            'Metrology Data Surface: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]), 
            'X [mm]','Y [mm]','Z [mm]',
            'TABLE_X[mm]','TABLE_Y[mm]','TABLE_Z_bow[mm]')
        
        htmloutput+=GenerateScatter3D(
            TESTCOMPARISONDATA[TestType_Metrology]['CurrentTests'][BatchInd], 
            TESTCOMPARISONDATA[TestType_Metrology]['HistoricalTests'][BatchInd], 
            'Metrology Data Scatter: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]), 
            'X [mm]','Y [mm]','Z [mm]',
            'TABLE_X[mm]','TABLE_Y[mm]','TABLE_Z_bow[mm]')
        
        
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_Metrology]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Metrology]['HistoricalTests'][BatchInd],'Max Abs Bow Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Maximum Absolute Bow [um]','Wafers','MaxBow[um]',-0.5,1)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_Metrology]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Metrology]['HistoricalTests'][BatchInd],'Average Bow Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Average Bow [um]','Wafers','AvgBow[um]',-300.5,1)
        htmloutput+=GenerateHist(TESTCOMPARISONDATA[TestType_Metrology]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Metrology]['HistoricalTests'][BatchInd],'Standard Deviation Bow Histogram: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Standard Deviation Bow [um]','Wafers','StdBow[um]',-300.5,1)
        
        
        #STABILITY
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Temperature-Compensated Stability Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','T-Compensated Current [nA]','Plot_Time','Plot_NormalisedCurrent')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Temperature Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','Temperature[°C]','TABLE_Time[s]','TABLE_Temperature[°C]')
        htmloutput+=GeneratePlot(TESTCOMPARISONDATA[TestType_Stability]['CurrentTests'][BatchInd],TESTCOMPARISONDATA[TestType_Stability]['HistoricalTests'][BatchInd],'Humidity Traces: '+str(TESTCOMPARISONDATA['TITLES'][BatchInd]),'Time [s]','Humidity[%]','TABLE_Time[s]','TABLE_Humidity[%]')
        
        htmloutput+=batchfooter   
    htmloutput+=footer    
    
    with open(outputfile,'w+') as f:
        f.write(htmloutput)
        
        
#This outputs a string of the html of a summary table
def GenerateSummaryTable(TESTCOMPARISONDATA,BatchInd):
    
    #Transform TESTCOMPARISONDATA into something more manageable to the following BATCHDATAFORTABLE format:
    """
    BATCHDATAFORTABLE={
        'Batch1':{
            'IV':[Test1,Test2],
            'CV':[]
        },
        'Batch2':{
            'IV':[],
            'CV':[]
        }
    }
    """ 
    #Where historical and current are combined. Current are denoted by adding a ***XXX*** to the decision.
    
    #To get there we create an intermediate BATCHDATAFORTABLETEMP
    """
    BATCHDATAFORTABLETEMP={
        'IV':[]
        'CV':[]
    }
    """ 
    
    WaferListForBatch=[]
    BATCHDATAFORTABLETEMP={}
    for TestType in DisplayFieldsForTestTypes.keys():
        BatchTestTypeCurrentTests=copy.deepcopy(TESTCOMPARISONDATA[TestType]['CurrentTests'][BatchInd])
        BatchTestTypeHistoricalTests=copy.deepcopy(TESTCOMPARISONDATA[TestType]['HistoricalTests'][BatchInd])
        
        for Test in BatchTestTypeCurrentTests:
            if Test['Decision'] in ['Pass','SoSo','Fail','MeasErr']:
                #Test['Decision']='***'+Test['Decision']+'***'
                Test['Decision']='LOCAL_'+Test['Decision']+''
            else:
                #Test['Decision']='***Unknown***'
                Test['Decision']='LOCAL_Unknown'
                
        for Test in BatchTestTypeHistoricalTests:
            if Test['Decision'] in ['Pass','SoSo','Fail','MeasErr']:
                #Test['Decision']=''+Test['Decision']+''
                Test['Decision']='ITKDB_'+Test['Decision']+''
            else:
                #Test['Decision']='Unknown'
                Test['Decision']='ITKDB_Unknown'
                
        BATCHDATAFORTABLETEMP[TestType]=BatchTestTypeHistoricalTests+BatchTestTypeCurrentTests
    
        WaferListForBatch.extend([i['Wafer'] for i in BATCHDATAFORTABLETEMP[TestType]])

    WaferListForBatch=set(WaferListForBatch)
    
    BATCHDATAFORTABLE={}
    for Wafer in list(WaferListForBatch):
        BATCHDATAFORTABLE[Wafer]={}
        for TestType in DisplayFieldsForTestTypes.keys():
            BATCHDATAFORTABLE[Wafer][TestType]=[TestDict for TestDict in BATCHDATAFORTABLETEMP[TestType] if TestDict['Wafer']==Wafer]


    outputstr=""
    
    outputstr+=tableheader
    WaferListForBatchNEW=sorted([('W'+str(i),i) for i in list(BATCHDATAFORTABLE.keys())])
    for WaferName,Wafer in WaferListForBatchNEW:
    #for Wafer in BATCHDATAFORTABLE.keys():
        outputstr+=rowheader
        outputstr+=cellheader 
        #outputstr+='W'+str(Wafer)
        outputstr+=WaferName
        outputstr+=cellfooter
        for TestType in DisplayFieldsForTestTypes.keys():
            outputstr+=cellheader 
            for TestDict in BATCHDATAFORTABLE[Wafer][TestType]:
                outputstr+=subcellheader.format(TestDict['Decision'])   
                for Field in DisplayFieldsForTestTypes[TestType].keys():
                    outputstr+=DisplayFieldsForTestTypes[TestType][Field]
                    if Field=='Timestamp':
                        if (TestDict[Field])!=None:
                            outputstr+=str(TestDict[Field][0:10]+', '+TestDict[Field][11:16])
                        else:
                            continue
                            #print("Timestamp",str(TestDict[Field]))
                    elif Field=='Flags':
                        if type(TestDict[Field])==list and len(TestDict[Field])>=1:
                            outputstr+='['+'<br>'.join([str(i).replace('\n','<br>') for i in TestDict[Field]])+']'
                        else:
                            outputstr+=str(TestDict[Field])
                    else:
                        if type(TestDict[Field])==numpy.float64:
                            outputstr+=eng_string(TestDict[Field])
                        else:
                            outputstr+=str(TestDict[Field])
                    outputstr+="<br>\n"
                outputstr+=subcellfooter 
            
            if TestType in [TestType_Strip]:
                outputstr+="<br>\n<b>Summary of Bad Strips: </b><br>\n"
                RegionsProbed,Summary, ConciseSummary=STRIPS_SUMMARY(TESTCOMPARISONDATA,BatchInd,Wafer)
                outputstr+="Regions Probed: "+str(RegionsProbed)
                outputstr+="<br>\n"
                outputstr+="Bad Strips: "+str(ConciseSummary)
                outputstr+="<br>\n"
            outputstr+=subcellfooter 
            
            outputstr+=cellfooter  
        outputstr+=rowfooter
    outputstr+=tablefooter
    
    return outputstr


######################################################################################

######################################################################################
### PLOTTING FUNCTIONS:
# The following are pairs of functions for plotting.
# Each requires a function to formulate the data such that a function that does the actual plotting can do so.


######################################################################################
### Plotting a Fit:

#This outputs the html string to plot xdata,ydata, xdatafit, ydatafit 
def GenerateFitPlot(BatchTestTypeCurrentTests,BatchTestTypeHistoricalTests,title,xlabel,ylabel,ylogTrue=False):
    counter=1
    colorkeylist=list(colorlistonoff.keys())


    #NEWCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    #OLDCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    

    xdatalist=[]
    ydatalist=[]
    xfitlist=[]
    yfitlist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]


    for ANALYZEDWAFERDICT in BatchTestTypeCurrentTests:     
        xdatalist.append(ANALYZEDWAFERDICT['xdata'])
        ydatalist.append(ANALYZEDWAFERDICT['ydata'])
        xfitlist.append(ANALYZEDWAFERDICT['xfit'])
        yfitlist.append(ANALYZEDWAFERDICT['yfit'])
            
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
        counter+=1

        colorkey='LOCAL_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])


    for ANALYZEDWAFERDICT in BatchTestTypeHistoricalTests:             
        xdatalist.append(ANALYZEDWAFERDICT['xdata'])
        ydatalist.append(ANALYZEDWAFERDICT['ydata'])
        xfitlist.append(ANALYZEDWAFERDICT['xfit'])
        yfitlist.append(ANALYZEDWAFERDICT['yfit'])

        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
            
        colorkey='ITKDB_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['ITKDB_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['ITKDB_Unknown'][1])



    #Sort lists by names
    if len(nameslist)>1:
        nameslist,xdatalist,ydatalist,xfitlist,yfitlist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,xdatalist,ydatalist,xfitlist,yfitlist,colorofflist,coloronlist)))]


    return DataToPlotlyFitPlot(xdatalist,ydatalist,xfitlist,yfitlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,ylogTrue)

##This deals with plotly for plotting 1D plots
def DataToPlotlyFitPlot( xdatalist,ydatalist,xfitlist,yfitlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,ylogTrue):
    

    varlist=[xdatalist,ydatalist,xfitlist,yfitlist,nameslist,colorofflist,coloronlist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i

    coloroff=[]
    coloron=[]
    for i in range(0,len(xdatalist)):
        coloroff.append(colorofflist[i])
        coloroff.append(colorofflist[i])
        coloron.append(coloronlist[i])
        coloron.append(coloronlist[i])
        
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        msize=10,
        lsize=16,
        mwidth=2,
        data = [
        {2}   
        ],
        layout = {{
            hovermode:'closest',
            title:'{3}',
                xaxis: {{
                    title: '{4}'
                  }},
                yaxis: {{
                    title: '{5}'{7}
                  }}
            showlegend:true,
         }};

    Plotly.newPlot('myDiv{6}', data, layout);

    myPlot{6}.on('plotly_hover', function(data){{
      var tnm='',
         tn='',
          tnl='',
          coloron ={0};
      var color=coloron;
      for(var i=0; i < data.points.length; i++){{
        tn = data.points[i].curveNumber;
      }}; 
      if(tn % 2 ==0){{
        tnm=tn;
        tnl=tn+1;
      }}else{{
        tnm=tn-1;
        tnl=tn;
      }};
      var updatem = {{marker:{{size:msize, symbol:'x-thin',line:{{width:mwidth,color:color[tnm]}}}}}};
      var updatel = {{'line':{{color: color[tnl], size:lsize,shape:'spline'}}}};
      Plotly.restyle('myDiv{6}', updatem, tnm);
      Plotly.restyle('myDiv{6}', updatel, tnl);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tnm='',
         tn='',
          tnl='',
          coloroff ={1};
      var color=coloroff;
      for(var i=0; i < data.points.length; i++){{
        tn = data.points[i].curveNumber;
      }}; 
      if(tn % 2 ==0){{
        tnm=tn;
        tnl=tn+1;
      }}else{{
        tnm=tn-1;
        tnl=tn;
      }};
      var updatem = {{marker:{{size:msize, symbol:'x-thin',line:{{width:mwidth,color:color[tnm]}}}}}};
      var updatel = {{'line':{{color: color[tnl], size:lsize,shape:'spline'}}}};
      Plotly.restyle('myDiv{6}', updatem, tnm);
      Plotly.restyle('myDiv{6}', updatel, tnl);
    }});

  </script>
    """
    
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        msize=10,
        lsize=16,
        mwidth=2,
        data = [
        {2}   
        ],
        layout = {{
            showlegend:true,
            hovermode:'closest',
            title:'{3}',
                xaxis: {{
                    title: '{4}'
                  }},
                yaxis: {{
                    title: '{5}'{7}
                  }}
         }};
         
    Plotly.newPlot('myDiv{6}', data, layout);

    myPlot{6}.on('plotly_hover', function(data){{
      var tnm='',
         tn= data.points[0].curveNumber,
          tnl='',
          color ={0};
      if(tn % 2 ==0){{
        tnm=tn;
        tnl=tn+1;
      }}else{{
        tnm=tn-1;
        tnl=tn;
      }};
      Plotly.restyle('myDiv{6}', {{marker:{{size:msize, symbol:'x-thin',line:{{width:mwidth,color:color[tnm]}}}}}}, tnm);
      Plotly.restyle('myDiv{6}', {{'line':{{color: color[tnl], size:lsize,shape:'spline'}}}}, tnl);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tnm='',
         tn= data.points[0].curveNumber,
          tnl='',
          color ={1};
      if(tn % 2 ==0){{
        tnm=tn;
        tnl=tn+1;
      }}else{{
        tnm=tn-1;
        tnl=tn;
      }};
      Plotly.restyle('myDiv{6}', {{marker:{{size:msize, symbol:'x-thin',line:{{width:mwidth,color:color[tnm]}}}}}}, tnm);
      Plotly.restyle('myDiv{6}', {{'line':{{color: color[tnl], size:lsize,shape:'spline'}}}}, tnl);
    }});
  </script>
    """

    pairformatstring="""
                {{
                 x:{0}, 
                 y:{1},       
                 type:'scattergl',
                 mode:'markers', 
                 marker:{{size:msize, symbol:'x-thin',line:{{width:mwidth,color:coloroff[{5}]}}}},
                 name:'{2} Data'
                }},
                {{
                 x:{3}, 
                 y:{4},       
                 type:'scattergl',
                 mode:'lines', 
                 line:{{size:lsize, color:coloroff[{6}],shape: 'spline'}},
                 name:'{2} Fit'
                }}
    """
    
    dataoutputstring=''
    
    for ind in range(0,len(xdatalist)):
        #dataoutputstring+= pairformatstring.format(str(xdatalist[ind].tolist()),str(ydatalist[ind].tolist()),str(nameslist[ind]),str(xfitlist[ind].tolist()),str(yfitlist[ind].tolist()),str(2*ind),str(2*ind+1))
        dataoutputstring+= pairformatstring.format(
            str(xdatalist[ind].tolist()),
            ["{:.5e}".format(i) for i in ydatalist[ind].tolist()],
            str(nameslist[ind]),
            ["{:.5e}".format(i) for i in xfitlist[ind].tolist()],
            ["{:.5e}".format(i) for i in yfitlist[ind].tolist()],
            str(2*ind),str(2*ind+1))
        
        dataoutputstring+=','
    
    dataoutputstring=dataoutputstring[:-1]
    
    if ylogTrue==True:
        logstring=",type: 'log',autorange: true"
    else:
        logstring=""
        
    outputstring= formatstringfull.format(str(coloron),str(coloroff),dataoutputstring,str(title),str(xlabel),str(ylabel),identifier,logstring)
    
    htmlformat="""
    <head>
      <!-- Plotly.js -->
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>

    <body>
      {0}
    </body>
    """
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(folder+outputfile+".html",'w+') as f:
        f.write(htmloutput)
    """
        
    return htmloutput


######################################################################################
### Plotting a Histogram:

#This plots xdata,ydata, xdatafit, ydatafit
def GenerateHist(BatchTestTypeCurrentTests,BatchTestTypeHistoricalTests,title,xlabel,ylabel,Var,start,size,barmode="stack"):
    counter=1
    colorkeylist=list(colorlistonoff.keys())


    #NEWCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    #OLDCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    

    histlist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]


    for ANALYZEDWAFERDICT in BatchTestTypeCurrentTests:     
        histlist.append(ANALYZEDWAFERDICT[Var])
            
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
        counter+=1

        colorkey='LOCAL_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])


    for ANALYZEDWAFERDICT in BatchTestTypeHistoricalTests:             
        histlist.append(ANALYZEDWAFERDICT[Var])

        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
            
        colorkey='ITKDB_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['ITKDB_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['ITKDB_Unknown'][1])



    #Sort lists by names
    if len(nameslist)>1:
        nameslist,histlist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,histlist,colorofflist,coloronlist)))]

    return DataToPlotlyHist(histlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,start,size,barmode)


def DataToPlotlyHist( histlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,start,size,barmode):
    varlist=[histlist,nameslist,colorofflist,coloronlist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    
    #Reverse list orders because histograms in plotly are weird:
    histlist.reverse()
    nameslist.reverse()
    colorofflist.reverse()
    coloronlist.reverse()
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i

    coloroff=colorofflist
    coloron=coloronlist
        
        
    """
var x1 = [1];
var x2 = [2];
var start=-0.2
var size=1

var trace1 = {
  x: x1,
  type: "histogram",
  xbins: { 
    size: size, 
    start: start
  }
};
var trace2 = {
  x: x2,
  type: "histogram",
  xbins: { 
    size: size, 
    start: start
  }
};

var data = [trace1, trace2];
var layout = {showlegend:true,barmode: "stack"};
Plotly.newPlot('myDiv', data, layout);
"""
        
        
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        size={7},
        start={8},
        data = [
        {2}   
        ],
        layout = {{
            showlegend:true,
            barmode:"{9}",
            hovermode:'closest',
            title:'{3}',
                  xaxis: {{
        title: '{4}'
      }},
      yaxis: {{
        title: '{5}'
      }}
         }};
         
    Plotly.newPlot('myDiv{6}', data, layout);

    myPlot{6}.on('plotly_hover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={0};
      Plotly.restyle('myDiv{6}', {{marker:{{color:color[tn]}}}}, tn);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={1};
      Plotly.restyle('myDiv{6}', {{marker:{{color:color[tn]}}}}, tn);
    }});
  </script>
    """

    pairformatstring="""
                {{
                 x:[{0}],  
                 type:'histogram',
                 xbins: {{size:size,start:start}},
                 marker:{{color:coloroff[{2}]}},
                 mode:'markers', 
                 name:'{1}'
                }}
    """
    
    dataoutputstring=''
    
    for ind in range(0,len(histlist)):
        #dataoutputstring+= pairformatstring.format(str(xdatalist[ind].tolist()),str(ydatalist[ind].tolist()),str(nameslist[ind]),str(xfitlist[ind].tolist()),str(yfitlist[ind].tolist()),str(2*ind),str(2*ind+1))
        dataoutputstring+= pairformatstring.format(
            ','.join([str("{:.5e}".format(element)) if element is not None else '' for element in (histlist[ind] if type(histlist[ind])==list else [histlist[ind]])]),
            str(nameslist[ind]),
            str(ind)
        )
        
        dataoutputstring+=','
    
    dataoutputstring=dataoutputstring[:-1]
    
    outputstring= formatstringfull.format(
        str(coloron),
        str(coloroff),
        dataoutputstring,
        str(title),
        str(xlabel),
        str(ylabel),
        identifier,
        str(size),
        str(start),
        barmode
    )
    
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(folder+outputfile+".html",'w+') as f:
        f.write(htmloutput)
    """
    return htmloutput


######################################################################################
### Plotting a Bar Graph (i.e. Histogram for the strips since there are too many entries):

#This is for the special case where the histogram is for the strips and needs to be preprocessed.
def GenerateHistStrips(BatchTestTypeCurrentTests,BatchTestTypeHistoricalTests,title,xlabel,ylabel,Var,start,size,end=1e6,barmode="stack"):
    counter=1
    colorkeylist=list(colorlistonoff.keys())


    #NEWCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    #OLDCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    

    histlist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]


    for ANALYZEDWAFERDICT in BatchTestTypeCurrentTests:     
        histlist.append([ANALYZEDWAFERDICT[Var][ind] for ind in range(0,len(ANALYZEDWAFERDICT[Var])) if ANALYZEDWAFERDICT['TABLE_ProbeplanIndex'][ind]!=0 and ANALYZEDWAFERDICT[Var][ind]<=end and ANALYZEDWAFERDICT[Var][ind]>=start])
            
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
        counter+=1

        colorkey='LOCAL_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])


    for ANALYZEDWAFERDICT in BatchTestTypeHistoricalTests:             
        histlist.append([ANALYZEDWAFERDICT[Var][ind] for ind in range(0,len(ANALYZEDWAFERDICT[Var])) if ANALYZEDWAFERDICT['TABLE_ProbeplanIndex'][ind]!=0 and ANALYZEDWAFERDICT[Var][ind]<=end and ANALYZEDWAFERDICT[Var][ind]>=start])
        
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
            
        colorkey='ITKDB_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['ITKDB_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['ITKDB_Unknown'][1])



    #Sort lists by names
    if len(nameslist)>1:
        nameslist,histlist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,histlist,colorofflist,coloronlist)))]
    
    
    xbarlist=[]
    ybarlist=[]
    for subhistlist in histlist:
        if len(subhistlist)>=1:
            bins=np.arange(np.floor((min(subhistlist)-start)/size)*size+start,np.ceil((max(subhistlist)-start)/size)*size+start,size)
            ydata,binedges=np.histogram(subhistlist,bins=bins)
            xdata=(binedges[:-1]+binedges[1:])/2
            xbarlist.append(list(xdata))
            ybarlist.append(list(ydata))
        else:
            xbarlist.append([])
            ybarlist.append([])
    
    
    return DataToPlotlyBar(xbarlist,ybarlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,start,size,barmode)


def DataToPlotlyBar( xbarlist,ybarlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,start,size,barmode):
    varlist=[xbarlist,ybarlist,nameslist,colorofflist,coloronlist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    
    #Reverse list orders because histograms in plotly are weird:
    xbarlist.reverse()
    ybarlist.reverse()
    nameslist.reverse()
    colorofflist.reverse()
    coloronlist.reverse()
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i

    coloroff=colorofflist
    coloron=coloronlist
        
        
    """
var x1 = [1];
var x2 = [2];
var start=-0.2
var size=1

var trace1 = {
  x: x1,
  type: "histogram",
  xbins: { 
    size: size, 
    start: start
  }
};
var trace2 = {
  x: x2,
  type: "histogram",
  xbins: { 
    size: size, 
    start: start
  }
};

var data = [trace1, trace2];
var layout = {barmode: "stack"};
Plotly.newPlot('myDiv', data, layout);
"""
        
        
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        size={7},
        start={8},
        data = [
        {2}   
        ],
        layout = {{
            showlegend:true,
            barmode:"{9}",
            hovermode:'closest',
            title:'{3}',
                  xaxis: {{
        title: '{4}'
      }},
      yaxis: {{
        title: '{5}'
      }}
         }};
         
    Plotly.newPlot('myDiv{6}', data, layout);

    myPlot{6}.on('plotly_hover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={0};
      Plotly.restyle('myDiv{6}', {{marker:{{color:color[tn]}}}}, tn);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={1};
      Plotly.restyle('myDiv{6}', {{marker:{{color:color[tn]}}}}, tn);
    }});
  </script>
    """

    pairformatstring="""
                {{
                 x:[{0}],  
                 y:[{1}],
                 width: size,
                 type:'bar',
                 marker:{{color:coloroff[{3}]}},
                 mode:'markers', 
                 name:'{2}'
                }}
    """
    
    dataoutputstring=''
    
    for ind in range(0,len(xbarlist)):
        #dataoutputstring+= pairformatstring.format(str(xdatalist[ind].tolist()),str(ydatalist[ind].tolist()),str(nameslist[ind]),str(xfitlist[ind].tolist()),str(yfitlist[ind].tolist()),str(2*ind),str(2*ind+1))
        dataoutputstring+= pairformatstring.format(
            ','.join([str("{:.5e}".format(element)) if element is not None else '' for element in (xbarlist[ind] if type(xbarlist[ind])==list else [xbarlist[ind]])]),
            ','.join([str("{:.5e}".format(element)) if element is not None else '' for element in (ybarlist[ind] if type(ybarlist[ind])==list else [ybarlist[ind]])]),
            str(nameslist[ind]),
            str(ind)
        )
        
        dataoutputstring+=','
    
    dataoutputstring=dataoutputstring[:-1]
    
    outputstring= formatstringfull.format(
        str(coloron),
        str(coloroff),
        dataoutputstring,
        str(title),
        str(xlabel),
        str(ylabel),
        identifier,
        str(size),
        str(start),
        barmode
    )
    
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(folder+outputfile+".html",'w+') as f:
        f.write(htmloutput)
    """
    return htmloutput



######################################################################################
### Plotting a Wafer Bad Strips Map


###################Wafer Bad Strip Map###########
#This plots xdata,ydata, xdatafit, ydatafit
def GenerateWaferStrips(TESTCOMPARISONDATA,BatchInd,title,xlabel,ylabel):
    ignoreifthismanybadchannels=100
    
    colorkeylist=list(colorlistonoff.keys())

    seglist=[]
    striplist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]

    Wafers=[i['Wafer'] for i in TESTCOMPARISONDATA[TestType_Strip]['HistoricalTests'][BatchInd]]
    Wafers+=[i['Wafer'] for i in TESTCOMPARISONDATA[TestType_Strip]['CurrentTests'][BatchInd]]
    Wafers=list(set(Wafers))
    print(Wafers)
    
    AllSegs=[]
    AllRange=[]
    for Wafer in Wafers:
        RegionsProbed,Summary, ConciseSummary=STRIPS_SUMMARY(TESTCOMPARISONDATA,BatchInd,Wafer)
        if Summary is None:
            continue
        for Seg in Summary.keys():
            if Seg is None:
                AllSegs.append(0)
            else:
                AllSegs.append(Seg)
            AllRange.append(RegionsProbed[Seg][1])
    
            
            #Ignore if there are too many bad channels
            if len(Summary[Seg].keys())>ignoreifthismanybadchannels:
                continue
            
            for Strip in Summary[Seg].keys():
                if Seg is None:
                    seglist.append(0)
                else:
                    seglist.append(Seg)
                
                striplist.append(Strip)
                name=str(Seg)+'-'+str(Strip)+' W'+str(Wafer)+' ['+','.join(Summary[Seg][Strip])+']'
                nameslist.append(name)
                colorkey='LOCAL_'+'Fail'
                if colorkey in colorkeylist:
                    coloronlist.append(colorlistonoffuseful[colorkey][0])
                    colorofflist.append(colorlistonoffuseful[colorkey][1])
                else:
                    coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
                    colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])
                    
    
    AllSegs=set(AllSegs)
    AllRange=set(AllRange)
    totalsegs=max(AllSegs) if len(AllSegs)>=1 else 0
    totalstrips=max(AllRange) if len(AllRange)>=1 else 0
    
    #Sort lists by names
    if len(nameslist)>1:
        nameslist,seglist,striplist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,seglist,striplist,colorofflist,coloronlist)))]
    
    return DataToPlotlyWaferStrips(seglist,striplist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,totalsegs,totalstrips)

def GenerateWaferStripsHPK(TESTCOMPARISONDATA,BatchInd,title,xlabel,ylabel):
    
    #ignoreifthismanybadchannels=100
    
    colorkeylist=list(colorlistonoff.keys())

    seglist=[]
    striplist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]

    #Get proper range from strips:
    Wafers=[i['Wafer'] for i in TESTCOMPARISONDATA[TestType_Strip]['HistoricalTests'][BatchInd]]
    Wafers+=[i['Wafer'] for i in TESTCOMPARISONDATA[TestType_Strip]['CurrentTests'][BatchInd]]
    Wafers=list(set(Wafers))
    print(Wafers)
    AllSegs=[]
    AllRange=[]
    for Wafer in Wafers:
        RegionsProbed,Summary, ConciseSummary=STRIPS_SUMMARY(TESTCOMPARISONDATA,BatchInd,Wafer)
        if Summary is None:
            continue
        for Seg in Summary.keys():
            if Seg is None:
                AllSegs.append(0)
            else:
                AllSegs.append(Seg)
            AllRange.append(RegionsProbed[Seg][1])
            
            
    #Actually look at HPK Data
    Wafers=[i['Wafer'] for i in TESTCOMPARISONDATA[TestType_Manufacturing]['HistoricalTests'][BatchInd]]
    Wafers+=[i['Wafer'] for i in TESTCOMPARISONDATA[TestType_Manufacturing]['CurrentTests'][BatchInd]]
    Wafers=list(set(Wafers))
    print(Wafers)
    
    for Wafer in Wafers:
        Summary=STRIPS_SUMMARY_HPK(TESTCOMPARISONDATA,BatchInd,Wafer)
        if Summary is None:
            continue
        for Seg in Summary.keys():          
            for Strip in Summary[Seg].keys():
                if Seg is None:
                    seglist.append(0)
                else:
                    seglist.append(Seg)
                
                striplist.append(Strip)
                name=str(Seg)+'-'+str(Strip)+' W'+str(Wafer)+' ['+','.join(Summary[Seg][Strip])+']'
                nameslist.append(name)
                colorkey='LOCAL_'+'Fail'
                if colorkey in colorkeylist:
                    coloronlist.append(colorlistonoffuseful[colorkey][0])
                    colorofflist.append(colorlistonoffuseful[colorkey][1])
                else:
                    coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
                    colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])
    
    
    AllSegs=set(AllSegs)
    AllRange=set(AllRange)
    totalsegs=max(AllSegs) if len(AllSegs)>=1 else 0
    totalstrips=max(AllRange) if len(AllRange)>=1 else 0
    
    #Sort lists by names
    if len(nameslist)>1:
        nameslist,seglist,striplist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,seglist,striplist,colorofflist,coloronlist)))]
    
    return DataToPlotlyWaferStrips(seglist,striplist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,totalsegs,totalstrips)

#x is seg, y is strip
def DataToPlotlyWaferStrips( seglist,striplist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,totalsegs,totalstrips):
    varlist=[seglist,striplist,nameslist,colorofflist,coloronlist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    black='rgba(0,0,0,1)'
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i

    coloroff=colorofflist+[black]
    coloron=coloronlist+[black]
        
        
    """
var x1 = [1];
var x2 = [2];
var start=-0.2
var size=1

var trace1 = {
  x: x1,
  y:
  type: "bar",

};
var trace2 = {
  x: x2,
  type: "histogram",
  xbins: { 
    size: size, 
    start: start
  }
};

var data = [trace1, trace2];
var layout = {barmode: "stack"};
Plotly.newPlot('myDiv', data, layout);
"""
        
        
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        lsize=16,
        data = [
        {2}   
        ],
        layout = {{
            showlegend:true,
            hovermode:'closest',
            title:'{3}',
                  xaxis: {{
        title: '{4}'
      }},
      yaxis: {{
        title: '{5}'
      }}
         }};
         
    Plotly.newPlot('myDiv{6}', data, layout);
    
    myPlot{6}.on('plotly_hover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={0};
      Plotly.restyle('myDiv{6}', {{'line':{{color: color[tn], size:lsize,shape:'spline'}}}}, tn);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={1};
      Plotly.restyle('myDiv{6}', {{'line':{{color: color[tn], size:lsize,shape:'spline'}}}}, tn);
    }});
  </script>
    """

    pairformatstring="""
                {{
                 x:[{0}-0.5,{0}+0.5],  
                 y:[{1},{1}],
                 type:'scattergl',
                 mode:'lines',
                 line:{{size:lsize, color:coloroff[{3}],shape: 'spline'}}, 
                 name:'{2}'
                }}
    """
    
    borderformatstring="""
                {{
                 x:[0.5,0.5,{0}+0.5,{0}+0.5],  
                 y:[0.5,{1}+0.5,{1}+0.5,0.5],
                 type:'scattergl',
                 mode:'lines',
                 line:{{size:lsize, color:coloroff[{2}],shape: 'spline'}}, 
                 name:'Wafer Boundary'
                }}
    """
    
    dataoutputstring=''
    
    ind=0
    for ind in range(0,len(striplist)):
        #dataoutputstring+= pairformatstring.format(str(xdatalist[ind].tolist()),str(ydatalist[ind].tolist()),str(nameslist[ind]),str(xfitlist[ind].tolist()),str(yfitlist[ind].tolist()),str(2*ind),str(2*ind+1))
        dataoutputstring+= pairformatstring.format(
            "{:.5e}".format(seglist[ind]) if seglist[ind] is not None else '',
            "{:.5e}".format(striplist[ind]) if striplist[ind] is not None else '',
            str(nameslist[ind]),
            str(ind)
        )
        
        dataoutputstring+=','
    
    dataoutputstring+=borderformatstring.format(
            "{:.5e}".format(totalsegs) if totalsegs is not None else '',
            "{:.5e}".format(totalstrips) if totalstrips is not None else '',
            str(ind+1)
    )
        
    #dataoutputstring=dataoutputstring[:-1]
    
    
    outputstring= formatstringfull.format(
        str(coloron),
        str(coloroff),
        dataoutputstring,
        str(title),
        str(xlabel),
        str(ylabel),
        identifier
    )
    
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(folder+outputfile+".html",'w+') as f:
        f.write(htmloutput)
    """
    return htmloutput


######################################################################################
### GENERATE 3D SURFACE PLOT

def GenerateSurface(BatchTestTypeCurrentTests,BatchTestTypeHistoricalTests,title,xlabel,ylabel,zlabel,VarX,VarY,VarZ):
    counter=1
    
    #NEWCOMPTESTDICTLIST=BatchTestTypeCurrentTests
   # OLDCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    

    tempxlist=[]
    tempylist=[]
    tempzlist=[]
    nameslist=[]


    for ANALYZEDWAFERDICT in BatchTestTypeCurrentTests:     
        tempxlist.append([ANALYZEDWAFERDICT[VarX][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarX]))])
        tempylist.append([ANALYZEDWAFERDICT[VarY][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarY]))])
        tempzlist.append([ANALYZEDWAFERDICT[VarZ][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarZ]))])
            
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
        counter+=1


    for ANALYZEDWAFERDICT in BatchTestTypeHistoricalTests:             
        tempxlist.append([ANALYZEDWAFERDICT[VarX][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarX]))])
        tempylist.append([ANALYZEDWAFERDICT[VarY][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarY]))])
        tempzlist.append([ANALYZEDWAFERDICT[VarZ][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarZ]))])
        
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)

    toleranceXY=3
    ## convert from linear list to matrix for 
    xlist=[]
    ylist=[]
    zlist=[]
    for listind in range(0,len(tempxlist)):
        x=tempxlist[listind]
        y=tempylist[listind]
        z=tempzlist[listind]
        newx=[]
        newy=[]
        newz=[]
        
        ####Determine dimension of matrix since it is currently just linear 
        fixedxcand=[round(xi/toleranceXY)*toleranceXY for xi in x]
        fixedycand=[round(xi/toleranceXY)*toleranceXY for xi in y]
        if 0 in np.diff(np.array(fixedxcand)):
            fixedx=fixedxcand
        elif 0 in np.diff(np.array(fixedycand)):
            fixedx=fixedycand
        else:
            fixedx=fixedycand

        for ind in range(0,len(fixedx)):
            
            if ind==0:
                sublistx=[x[ind]]
                sublisty=[y[ind]]
                sublistz=[z[ind]]
            elif fixedx[ind]!=fixedx[ind-1]:
                newx.append(sublistx)
                newy.append(sublisty)
                newz.append(sublistz)
                sublistx=[x[ind]]
                sublisty=[y[ind]]
                sublistz=[z[ind]]
            else:
                sublistx.append(x[ind])
                sublisty.append(y[ind])
                sublistz.append(z[ind])
        newx.append(sublistx)
        newy.append(sublisty)
        newz.append(sublistz)
        xlist.append(newx)
        ylist.append(newy)
        zlist.append(newz)
        
    #Sort lists by names
    if len(nameslist)>1:
        nameslist,xlist,ylist,zlist= [list(i) for i in zip(*sorted(zip(nameslist,xlist,ylist,zlist)))]
    
    return DataToPlotlySurface(xlist,ylist,zlist,nameslist,title,xlabel,ylabel,zlabel)

def DataToPlotlySurface( xlist,ylist,zlist,nameslist,title,xlabel,ylabel,zlabel):    
    varlist=[xlist,ylist,zlist,nameslist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i
   
    formatstringfull="""
      <div id="myDiv{5}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{5} = document.getElementById('myDiv{5}'),
        data = [
        {0}   
        ],
        layout = {{
            showlegend:true,
            hovermode:'closest',
            title:'{1}',
            xaxis: {{
                title: '{2}'
              }},
            yaxis: {{
                title: '{3}'
              }},
            zaxis: {{
                title: '{4}'
              }}
         }};
         
    Plotly.newPlot('myDiv{5}', data, layout);
  </script>
    """

    pairformatstring="""
                {{
                 x:{0},  
                 y:{1},
                 z:{2},
                 showscale: false,
                 opacity: 0.2,
                 type:'surface',
                 name:'{3}'
                }}
    """
    
    dataoutputstring=''
    
    
    
    for ind in range(0,len(xlist)):
        dataoutputstring+= pairformatstring.format(
            formatlistoflists(xlist[ind]),
            formatlistoflists(ylist[ind]),
            formatlistoflists(zlist[ind]),
            str(nameslist[ind]),
        )
        
        dataoutputstring+=','
    
    dataoutputstring=dataoutputstring[:-1]
    
    outputstring= formatstringfull.format(
        dataoutputstring,
        str(title),
        str(xlabel),
        str(ylabel),
        str(zlabel),
        identifier,
    )
    
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(folder+outputfile+".html",'w+') as f:
        f.write(htmloutput)
    """
    
    
    return htmloutput


######################################################################################
### GENERATE 3D SCATTER PLOT


def GenerateScatter3D(BatchTestTypeCurrentTests,BatchTestTypeHistoricalTests,title,xlabel,ylabel,zlabel,VarX,VarY,VarZ):
    counter=1
    colorkeylist=list(colorlistonoff.keys())


   # NEWCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    #OLDCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    

    xlist=[]
    ylist=[]
    zlist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]


    for ANALYZEDWAFERDICT in BatchTestTypeCurrentTests:     
        xlist.append([ANALYZEDWAFERDICT[VarX][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarX]))])
        ylist.append([ANALYZEDWAFERDICT[VarY][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarY]))])
        zlist.append([ANALYZEDWAFERDICT[VarZ][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarZ]))])
            
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
        counter+=1

        colorkey='LOCAL_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])


    for ANALYZEDWAFERDICT in BatchTestTypeHistoricalTests:             
        xlist.append([ANALYZEDWAFERDICT[VarX][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarX]))])
        ylist.append([ANALYZEDWAFERDICT[VarY][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarY]))])
        zlist.append([ANALYZEDWAFERDICT[VarZ][ind] for ind in range(0,len(ANALYZEDWAFERDICT[VarZ]))])
        
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
            
        colorkey='ITKDB_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['ITKDB_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['ITKDB_Unknown'][1])



    #Sort lists by names
    if len(nameslist)>1:
        nameslist,xlist,ylist,zlist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,xlist,ylist,zlist,colorofflist,coloronlist)))]
    
    
    
    return DataToPlotlyScatter3D(xlist,ylist,zlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,zlabel)


def DataToPlotlyScatter3D(xlist,ylist,zlist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,zlabel):
    varlist=[xlist,ylist,zlist,nameslist,colorofflist,coloronlist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    
    #Reverse list orders because histograms in plotly are weird:
    """
    xlist.reverse()
    ylist.reverse()
    zlist.reverse()
    nameslist.reverse()
    colorofflist.reverse()
    coloronlist.reverse()
    """
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i

    coloroff=colorofflist
    coloron=coloronlist
        
        
   
        
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        data = [
        {2}   
        ],
        layout = {{
            showlegend:true,
            hovermode:'closest',
            title:'{3}',
            xaxis: {{
                title: '{4}'
            }},
            yaxis: {{
                title: '{5}'
            }},
            zaxis: {{
                title: '{7}'
            }}
         }};
         
    Plotly.newPlot('myDiv{6}', data, layout);
</script>
    """
    """
    myPlot{6}.on('plotly_hover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={0};
      Plotly.restyle('myDiv{6}', {{marker:{{color:color[tn]}}}}, tn);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={1};
      Plotly.restyle('myDiv{6}', {{marker:{{color:color[tn]}}}}, tn);
    }});
    """

    pairformatstring="""
                {{
                 x:[{0}],  
                 y:[{1}],
                 z:[{2}],
                 type:'scatter3d',
                 marker:{{color:coloroff[{4}]}},
                 mode:'markers', 
                 name:'{3}'
                }}
    """
    
    dataoutputstring=''
    
    for ind in range(0,len(xlist)):
        dataoutputstring+= pairformatstring.format(
            ','.join([str("{:.5e}".format(element)) if element is not None else '' for element in xlist[ind]]),
            ','.join([str("{:.5e}".format(element)) if element is not None else '' for element in ylist[ind]]),
            ','.join([str("{:.5e}".format(element)) if element is not None else '' for element in zlist[ind]]),
            str(nameslist[ind]),
            str(ind)
        )
        
        dataoutputstring+=','
    
    dataoutputstring=dataoutputstring[:-1]
    
    outputstring= formatstringfull.format(
        str(coloron),
        str(coloroff),
        dataoutputstring,
        str(title),
        str(xlabel),
        str(ylabel),
        identifier,
        str(zlabel)
    )
    
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    return htmloutput


######################################################################################
### Just Plotting an ordinary trace

########NORMAL PLOT###########
def GeneratePlot(BatchTestTypeCurrentTests,BatchTestTypeHistoricalTests,title,xlabel,ylabel,VarX,VarY,ylogTrue=False):
    counter=1
    colorkeylist=list(colorlistonoff.keys())


    #NEWCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    #OLDCOMPTESTDICTLIST=BatchTestTypeCurrentTests
    

    xdatalist=[]
    ydatalist=[]
    nameslist=[]
    colorofflist=[]
    coloronlist=[]


    for ANALYZEDWAFERDICT in BatchTestTypeCurrentTests:     
        xdata=ANALYZEDWAFERDICT[VarX]
        ydata=ANALYZEDWAFERDICT[VarY]
        xdatalist.append([xdata[ind] for ind in range(0,len(xdata)) if (xdata[ind] is not None) and (ydata[ind] is not None) and (np.isfinite(xdata[ind])) and (np.isfinite(ydata[ind])) ])
        ydatalist.append([ydata[ind] for ind in range(0,len(xdata)) if (xdata[ind] is not None) and (ydata[ind] is not None) and (np.isfinite(xdata[ind])) and (np.isfinite(ydata[ind])) ])
            
        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
        counter+=1

        colorkey='LOCAL_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['LOCAL_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['LOCAL_Unknown'][1])


    for ANALYZEDWAFERDICT in BatchTestTypeHistoricalTests:          
        xdata=ANALYZEDWAFERDICT[VarX]
        ydata=ANALYZEDWAFERDICT[VarY]
        xdatalist.append([xdata[ind] for ind in range(0,len(xdata)) if (xdata[ind] is not None) and (ydata[ind] is not None) and (np.isfinite(xdata[ind])) and (np.isfinite(ydata[ind])) ])
        ydatalist.append([ydata[ind] for ind in range(0,len(xdata)) if (xdata[ind] is not None) and (ydata[ind] is not None) and (np.isfinite(xdata[ind])) and (np.isfinite(ydata[ind])) ])

        name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
        modifiednameslist=[i.split('(')[0] for i in nameslist]
        if name in modifiednameslist:
            nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
        else:
            nameslist.append(name)
            
        colorkey='ITKDB_'+str(ANALYZEDWAFERDICT['Decision'])

        if colorkey in colorkeylist:
            coloronlist.append(colorlistonoffuseful[colorkey][0])
            colorofflist.append(colorlistonoffuseful[colorkey][1])
        else:
            coloronlist.append(colorlistonoffuseful['ITKDB_Unknown'][0])
            colorofflist.append(colorlistonoffuseful['ITKDB_Unknown'][1])



    #Sort lists by names
    if len(nameslist)>1:
        nameslist,xdatalist,ydatalist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,xdatalist,ydatalist,colorofflist,coloronlist)))]


    return DataToPlotlyPlot(xdatalist,ydatalist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,ylogTrue)



def DataToPlotlyPlot(xdatalist,ydatalist,nameslist,colorofflist,coloronlist,title,xlabel,ylabel,ylogTrue):
    varlist=[xdatalist,ydatalist,nameslist,colorofflist,coloronlist]
    lengthscheck=[len(i) for i in varlist]
    if len(set(lengthscheck))!=1:
        print('Error!!')
        return None
    
    identifier=''
    for i in str(title)+str(xlabel):
        if i in GoodChars[:-1]:
            identifier+=i

    coloroff=colorofflist
    coloron=coloronlist
        
        
    formatstringfull="""
      <div id="myDiv{6}" style="width: 800px; height: 500px;"><!-- Plotly chart will be drawn inside this DIV --></div>
  <script>
    var myPlot{6} = document.getElementById('myDiv{6}'),
        coloron ={0},
        coloroff ={1},
        lsize=16,
        data = [
        {2}   
        ],
        layout = {{
            showlegend:true,
            hovermode:'closest',
            title:'{3}',
                  xaxis: {{
        title: '{4}'
      }},
      yaxis: {{
        title: '{5}'{7}
      }}
         }};
         
    Plotly.newPlot('myDiv{6}', data, layout);
    
    myPlot{6}.on('plotly_hover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={0};
      Plotly.restyle('myDiv{6}', {{'line':{{color: color[tn], size:lsize,shape:'spline'}}}}, tn);
    }});

    myPlot{6}.on('plotly_unhover', function(data){{
      var tn= data.points[0].curveNumber,
          color ={1};
      Plotly.restyle('myDiv{6}', {{'line':{{color: color[tn], size:lsize,shape:'spline'}}}}, tn);
    }});
  </script>
    """

    pairformatstring="""
                {{
                 x:[{0}],  
                 y:[{1}],
                 type:'scattergl',
                 mode:'lines',
                 line:{{size:lsize, color:coloroff[{3}],shape: 'spline'}}, 
                 name:'{2}'
                }}
    """
    
    
    dataoutputstring=''
    
    for ind in range(0,len(xdatalist)):
        #dataoutputstring+= pairformatstring.format(str(xdatalist[ind].tolist()),str(ydatalist[ind].tolist()),str(nameslist[ind]),str(xfitlist[ind].tolist()),str(yfitlist[ind].tolist()),str(2*ind),str(2*ind+1))
        dataoutputstring+= pairformatstring.format(
            ",".join([("{:.5e}".format(x) if x is not None else '') for x in xdatalist[ind]]),
            ",".join([("{:.5e}".format(x) if x is not None else '') for x in ydatalist[ind]]),
            str(nameslist[ind]),
            str(ind)
        )
        
        dataoutputstring+=','
    
    dataoutputstring=dataoutputstring[:-1]
    
    if ylogTrue==True:
        logstring=",type: 'log',autorange: true"
    else:
        logstring=""

    outputstring= formatstringfull.format(
        str(coloron),
        str(coloroff),
        dataoutputstring,
        str(title),
        str(xlabel),
        str(ylabel),
        identifier,
        logstring
    )
    
    
    htmlformat="{0}"
    htmloutput=htmlformat.format(outputstring)
    
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(folder+outputfile+".html",'w+') as f:
        f.write(htmloutput)
    """
    return htmloutput


######################################################################################
### Helper Functions for Plotters

def formatlistoflists(listoflists):
    listofstrings=[','.join([str("{:.5e}".format(element)) if element is not None else '' for element in sublist]) for sublist in listoflists]
    string='],['.join(listofstrings)
    string='[['+string+']]'
    return string

'''
def determinedimenstions(x,y):
    toleranceXY=3
    trydimX=np.argwhere(np.round(np.diff(x)/toleranceXY)*toleranceXY!=0)[0][0]
    trydimY=np.argwhere(np.round(np.diff(y)/toleranceXY)*toleranceXY!=0)[0][0]
    if trydimX==0 and trydimY!=0:
        dim1=trydimY+1
    elif trydimY==0 and trydimX!=0:
        dim1=trydimX+1
    else:
        print('Cannot determine dimension of X,Y data',X,Y)
        dim1=1     
    dim2=int(np.ceil(len(x)/dim1))
    
    if dim1!=11 or dim2!=11 or len(x)!=121:
        print(dim1,dim2,len(x))
        print(x,y)
    return dim1,dim2
'''
