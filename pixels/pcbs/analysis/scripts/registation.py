import sys

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
### register components & set stage
#####################

### PCB registration object (dictionary for jason)
myProjCode="P"
myCompTypeCode="PCB"
regObj = myClient.get('generateComponentTypeDtoSample', json={'project':myProjCode, 'code':myCompTypeCode, 'requiredOnly' : True})
#regObj

# update some settings for particular case...
regObj['subproject']="PG"
regObj['institution']="GL"
regObj['type']="QUAD_PCB"
regObj['properties']['FECHIP_VERSION']="0"
regObj['properties']['PANEL_MANUFACTURER']="Graphic"
regObj['properties']['SMD_POPULATION_VENDOR']="Garner Osborne"
# check object
regObj

# data upload info.
df_raw.columns
df_raw.shape[0] #number of rows of data

# basic column names
snCol='Serial numbering for all 3 batches of 3.8s'
# set stage if required
myStageCode="PCB_RECEPTION"
# loop through data
for index, row in df_raw.iterrows():
    # copy registration object
    newPCBObj=regObj.copy()
    # update SN
    newPCBObj['serialNumber']=row[snCol]

    # delete existing (if required)
    try:
        retVal=myClient.post('deleteComponent', json={'component':row[snCol]})
        print("successful deletion:",row[snCol])
    except infra.itkX.BadRequest as b:
        print("deleteComponent: went wrong for:",row[snCol])
        print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks

    # register component
    try:
        newest_PCB = myClient.post('registerComponent', json=newPCBObj)
        print(newest_PCB['component']['serialNumber'], "has been registered, index_",index) # happy day message
    except infra.itkX.BadRequest as b: # catch double registrations
        print("registerComponent: went wrong for:",newest_PCB['component']['serialNumber'])
        print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks

    # set stage for each object (just registered or not)
    try:
        retValStage = myClient.post('setComponentStage',json={'component':row[snCol],'stage':myStageCode})
        print("successful stage set",retValStage['component']['currentStage']) # happy day message
    except infra.itkX.BadRequest as b: # catch double registrations
        print("setComponentStage: went wrong for:",row[snCol])
        print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks


#####################
### checking any issues
#####################

### check SNs already in PDB
# issue SNs
checks=["20UPGPQ0022026","20UPGPQ0012013","20UPGPQ0021168","20UPGPQ0021159","20UPGPQ0021074"]
# get components
checkComps = list(map(lambda x: myClient.get('getComponent', json={'component':x}), checks))
df_checks=pd.DataFrame(checkComps)
df_checks


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
