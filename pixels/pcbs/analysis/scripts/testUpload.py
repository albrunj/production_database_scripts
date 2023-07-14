import copy
import sys
from datetime import datetime

import pandas as pd
## common PDB access
pdsDir = globals()['_dh'][0]
sys.path.insert(1, pdsDir+'/pixels/pcbs/analysis')
import PDBinfrastructure as infra
import myDetails


#####################
### access PDB
#####################
deets=myDetails.SetITk()
myClient=infra.AuthenticateUser(deets.ac1,deets.ac2)
user=myClient.get('getUser', json={'userIdentity': myClient.user.identity})
user['firstName']
myClient.user.expires_in


#####################
### get data from csv
#####################

dataPath=pdsDir+"/pixels/pcbs/data/"
#fileName=dataPath+"RD53A Quad Hybrid QC register - Sheet1.csv"
fileName=dataPath+"TestSheet1.csv"
df_raw = pd.read_csv(fileName)
df_raw=df_raw.convert_dtypes()
df_raw.dtypes
df_raw.head(5)


#####################
### checking component results
#####################

# get all components of type
myProjCode="P"
myCompTypeCode="PCB"
compList= list(myClient.get('listComponents',json={'componentType':myCompTypeCode, 'project':myProjCode }))
# sort groups by state
df_compState=pd.DataFrame([{'ASN':x['serialNumber'],'state':x['state'],'institution':x['institution']['code'],'stage':x['currentStage']['code']} for x in compList])
df_compState.head(3)
# sort by states
df_compState.pivot_table(index=['state'], aggfunc='size')
# sort by institution
df_compState.pivot_table(index=['institution'], aggfunc='size')
# sort by stage
df_compState.pivot_table(index=['stage'], aggfunc='size')
# select by query
df_compState.query("institution=='GOETTINGEN'")
df_compState.query("~(stage=='PCB_QC')")

# Gottingen SNs
gotts=["20UPGPQ0012026","20UPGPQ0012028"]
# get components
checkComps = list(map(lambda x: myClient.get('getComponent', json={'component':x}), list(df_compState.query("institution=='GOETTINGEN'")['ASN'])) )
df_check=pd.DataFrame([{'ASN':x['serialNumber'],'inst':x['institution']['code'],'compType':x['componentType']['code'],'state':x['state']} for x in checkComps])
df_check


#####################
### upload test data
#####################

### some mapping of test names & keys to input data column names
# map test key to column name
testKeyDict={
            'POPULATION_CHECK':'Scans taken?',
            'CAP_REWORK':'Shorts on capacitors?',
            'MASS':'mass (g)',
            'CONNECTOR_ZHEIGHT':'hv cap height (mm)',
            'HV_CAP_ZHEIGHT':'connector height (mm)',
            'TOP_CU':'top cu thickness (microns)',
            'BOTTOM_CU':'bot cu thickness (microns)',
            'R111':'SLDO 1 (kOhms)',
            'R112':'SLDO 2',
            'R114':'SLDO3',
            'R115':'SLDO4',
            'LEAKAGE':'HV leakage (mV on readout card)',
            'NTC_VOLT':'NTC reading',
            'NTC_TEMP':'Temp (°C) (@HV test)',
            'VIN_DROP':'Vin drop with jig compensation',
            'GND_DROP':'GND drop with jig compensation',
            'TEMPERATURE':'Temp (°C) (@HV test)',
            'HUMIDITY':'humidity (%) (@HV test)',
            'OPERATOR':'Chloe Stanton',
            'HUMIDITY':'humidity (%) (@HV test)',
            }
# map test to instrument
testInstDict={
             'OPTICAL_INSPECTION':'EPSON V550 flatbed scanner',
             'BOARD_DIMENSIONS':'0.1mm Resolution Calipers',
             'COPPER_THICKNESS':'Mitutoyo 293 series micrometer',
             'METROLOGY':'Tree HRB203',
             'SLDO_RESISTORS':'Agilent LCR meter with 4 wire probe/ Fluke multimeter',
             'LV_RAIL_TEST':'TTi QL355TP for low voltage. Keithley 2410 for High voltage. Bespoke readout system + picologger for taking measurements',
             'HV_TEST':'TTi QL355TP for low voltage. Keithley 2410 for High voltage. Bespoke readout system + picologger for taking measurements',
             'WIREBOND_PULL_TEST':'Hesse and Knipps 820, Dage 4000',
             'VIA_RESISTANCE':'Agilent LCR meter',
             'NTC_VERIFICATION':'Environmental chamber. For NTC readout, and Arduino reading out a potential 440 divider circuit',
             'SIGNAL_TRANSMISSION':'Keysight PNA-L network analyser'
             }

# map test to vendor
testVendDict={
            'REPORT_BARE_BOARD':'Graphic',
            'REPORT_POPULATION':'Garner Osborne'
            }

### set-up stage and test map
# [ {stage:"", tests:[""]} ]
stageTestMap=[
            {'stage':"PCB_RECEPTION", 'tests':["COPPER_THICKNESS_RD53A","REPORT_POPULATION"]},
            {'stage':"PCB_QC", 'tests':["COPPER_THICKNESS_RD53A","SLDO_RESISTORS","LV_RAIL_TEST","HV_TEST","NTC_VERIFICATION_RD53A","METROLOGY"]}
            ]

# format input data for upload - map booleans
df_raw['Shorts on capacitors?']=df_raw['Shorts on capacitors?'].map({'no':False,'not tested':False,'No':False,'reworked':True,'yes':True,'Yes':True})
df_raw['Shorts on capacitors?'].value_counts()

df_raw['Scans taken?']=df_raw['Scans taken?'].map({'no':False,'not tested':False,'No':False,'reworked':True,'yes':True,'Yes':True})
df_raw['Scans taken?'].value_counts()

# basic column names
snCol='Serial numbering for all 3 batches of 3.8s'
dateCol='Date Processed'

# use stageTestMap
for st in stageTestMap:
    # run over tests for stage
    for t in st['tests']:
        # reset credentials after each test (avoid tiome out)
        myClient=infra.AuthenticateUser(deets.ac1,deets.ac2)
        print("time remaining(s)",myClient.user.expires_in)
        # get test schema (faster to limit PDB requests and run over df repeatedly)
        try:
            testObj=myClient.get('generateTestTypeDtoSample', json={'project':"P", 'componentType':"PCB", 'code':t,'requiredOnly':True})
        except infra.itkX.BadRequest as b: # catch double registrations
            print("generateTestTypeDtoSample: went wrong for:",t)
            print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks
            continue
        except:
            print("generateTestTypeDtoSample: went wrong for:",t)
            print("Reason unknown")
            continue
        # now loop over rows
        for index, row in df_raw.iterrows():
            # check SN
            try:
                print("found SN:",row[snCol])
            except:
                print("no SN found for column:",snCol)
                continue
            # check date
            try:
                print("found date:",row[dateCol])
            except:
                print("no date found for column:",dateCol)
                continue
            # set component stage for test
            try:
                setStageVal=myClient.post('setComponentStage', json={'component':row[snCol], 'stage':st['stage']})
            except infra.itkX.BadRequest as b:
                print("setComponentStage: went wrong for:",row[snCol],"@",st['stage'])
                print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks
                continue
            except:
                print("setComponentStage: went wrong for:",row[snCol],"@",st['stage'])
                print("Reason unknown")
                continue
            # copy and update test schema
            newObj = copy.deepcopy(testObj)
            newObj['component']=row[snCol]
            newObj['institution']="GL"
            # format date
            try:
                newObj['date']=datetime.strptime(row[dateCol]+" 21:00", '%d/%m/%Y %H:%M').strftime("%d.%m.%Y %H:%M")
            except:
                newObj['date']=datetime.strptime("11/08/2020"+" 21:00", '%d/%m/%Y %H:%M').strftime("%d.%m.%Y %H:%M")
            ### loop over properties
            for k,v in newObj['properties'].items():
                if k=="OPERATOR":
                    newObj['properties'][k]="Chloe Stanton"
                elif k=="INSTRUMENT":
                    newObj['properties'][k]=testInstDict[t.replace('_RD53A','')]
                elif k=="VENDOR":
                    newObj['properties'][k]=testVendDict[t.replace('_RD53A','')]
                else:
                    try:
                        newObj['properties'][k]=str(row[testKeyDict[k]])
                    except KeyError:
                        print("no correspondant found for properties key:",k)
            ### loop over results
            for k,v in newObj['results'].items():
                try:
                    if type(v)==type(True):
                        if row[testKeyDict[k]]:
                            newObj['results'][k]=True
                        else:
                            newObj['results'][k]=False
                    else:
                        newObj['results'][k]=str(row[testKeyDict[k]])
                except KeyError:
                    print("no correspondant found for results key:",k)
                    continue
            try:
                upVal=myClient.post('uploadTestRunResults',json=newObj)
                print("uploadTestRunResults:",t,"("+st['stage']+") SUCCESS! - row_",index)
            except infra.itkX.BadRequest as b: # catch double registrations
                print("uploadTestRunResults: went wrong for:",row[snCol],"@",t)
                print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks
                print(newObj)
                continue
            except:
                print("uploadTestRunResults: went wrong for:",row[snCol],"@",t)
                print("Reason unknown")
                continue

### test single uploads
# stageTestMap=[{'stage':"PCB_RECEPTION", 'tests':["REPORT_POPULATION"]}]
# newObj={'component': '20UPGPQ0029999', 'testType': 'NTC_VERIFICATION', 'institution': 'GL', 'runNumber': '...', 'date': '11.08.2020 21:00', 'passed': True, 'problems': False, 'properties': {'OPERATOR': 'Chloe Stanton', 'INSTRUMENT': 'Environmental chamber. For NTC readout, and Arduino reading out a potential 440 divider circuit'}, 'results': {'NTC_TEMP': '24.1', 'NTC_VOLT': '1.4'}}
# newObj
# upVal=myClient.post('uploadTestRunResults',json=newObj)
