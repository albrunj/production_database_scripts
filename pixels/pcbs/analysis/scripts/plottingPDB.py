import sys

import pandas as pd
## common PDB access
pdsDir = globals()['_dh'][0]
sys.path.insert(1, pdsDir+'/pixels/pcbs/analysis')
import PDBinfrastructure as infra
import myDetails
## plotting
import altair as alt
import plotly.express as px



#####################
### access PDB
#####################
deets=myDetails.SetITk()
myClient=infra.AuthenticateUser(deets.ac1,deets.ac2)
user=myClient.get('getUser', json={'userIdentity': myClient.user.identity})
user['firstName']
myClient.user.expires_in


#####################
### checking PDB
#####################

### projects
projList = list(myClient.get('listProjects'))
# projList
df_proj= pd.DataFrame([{"name":x['name'],"code":x['code']} for x in projList])
df_proj

### sub-projects
myProjCode="P"
subprojList = myClient.get('listSubprojects', json={'project':myProjCode})
# subprojList
df_subproj= pd.DataFrame([{"name":x['name'],"code":x['code']} for x in subprojList])
df_subproj

### institutions
instList = list(myClient.get('listInstitutions'))
# instList
df_inst= pd.DataFrame([{"name":x['name'],"code":x['code']} for x in instList])
df_inst.query('name.str.contains("G")')

### component types
compTypesList = list(myClient.get('listComponentTypes', json={'project':myProjCode}))
# compTypesList
df_compType= pd.DataFrame([{"name":x['name'],"code":x['code'],"id":x['id']} for x in compTypesList])
df_compType


### components
myProjCode="P"
myCompTypeCode="PCB"
compList= list(myClient.get('listComponents',json={'componentType':myCompTypeCode, 'project':myProjCode }))
# sort groups by state
df_comps=pd.DataFrame([{'ASN':x['serialNumber'],'id':x['id'],'state':x['state'],'institution':x['institution']['code'],'stage':x['currentStage']['code']} for x in compList])
df_comps.head(3)
# sort
df_comps.pivot_table(index=['institution','stage','state'], aggfunc='size')

### access test info
# get component
retVal=myClient.get('getComponent', json={'component':"20UPGPQ0021158"})
# get test IDs of component
testIds=[y['id'] for x in retVal['tests'] for y in x['testRuns']]
# get test info for IDs, in bulk
bulkRuns=myClient.get('getTestRunBulk', json={'testRun':testIds})
bulkRuns[0]['results']
[{x['code']:x['value']} for x in bulkRuns[0]['results']]
# select info.
df_testInfo=pd.DataFrame([{'testId':x['id'],'stage':[y['testedAtStage']['code'] for y in x['components']],'compId':[y['id'] for y in x['components']],'test':x['testType']['code'],'results':[{y['code']:y['value']} for y in x['results']]} for x in bulkRuns])
df_testInfo

#####################
### get PCB data per component test stage-test data
#####################

# define components of interest
myASNList=list(df_comps.query("institution=='GL' & state=='ready'")['ASN'].values)
len(myASNList)

### collect testRuns for components
testIds=[]
# loop o'er selection
for i,c in enumerate(myASNList):
    retVal=None
    print("ASN:",c,",",i,"of",len(myASNList))
    try:
        retVal=myClient.get('getComponent', json={'component':c})
        print("getComponent: found:",c)
    except infra.itkX.BadRequest as b:
        print("getComponent: went wrong for:",c)
        print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks
        continue
    testIds.extend([y['id'] for x in retVal['tests'] for y in x['testRuns']])

len(testIds)

### bulk retrieval of test info. (better performance from PDB)
testInfo=[]
chunk=300 # size of bulk
for i in range(0,len(testIds),chunk):
    print("retrieving:",i,"-",i+chunk,"of",len(testIds))
    try:
        bulkRuns=myClient.get('getTestRunBulk', json={'testRun':testIds[i:i+chunk]})
        print("getTestRunBulk: got bulk runs:",len(bulkRuns))
    except infra.itkX.BadRequest as b:
        print("getTestRunBulk: went wrong for:",len(bulkRuns))
        print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks
        continue
    # selected test info. to keep
    testInfo.extend([{'testId':x['id'],'stage':[y['testedAtStage']['code'] for y in x['components']],'compId':[y['id'] for y in x['components']],'test':x['testType']['code'],'results':[{y['code']:y['value']} for y in x['results']]} for x in bulkRuns])

len(testInfo)

### get testRun information of interest
# set-up stage and test map -- {stage:"", tests:[""]} ]
stageTestMap=[
            {'stage':"PCB_RECEPTION", 'tests':["COPPER_THICKNESS_RD53A","REPORT_POPULATION"]},
            {'stage':"PCB_QC", 'tests':["COPPER_THICKNESS_RD53A","SLDO_RESISTORS","LV_RAIL_TEST","HV_TEST","NTC_VERIFICATION_RD53A","METROLOGY"]}
            ]

# testInfo[0]
#'stageTest':st['stage']+":"+ti['test'],
resultsList=[]
for st in stageTestMap:
    for ti in testInfo:
        if st['stage'] in ti['stage'] and ti['test'] in st['tests']:
            resultsList.append({'compId':ti['compId'],'test':ti['test'],'stage':st['stage'],'testId':ti['testId'],'results':ti['results']})

### get stats info.
df_tests=pd.DataFrame(resultsList)
df_tests['stageTest']=df_tests[['stage','test']].apply(lambda row: ':'.join(row.values.astype(str)), axis=1)
# df_tests
df_tests.pivot_table(index=['test','stage'], aggfunc='size')

### pandas built-in plotting
df_tests.pivot_table(index=['test','stage'], aggfunc='size').plot.bar(title="tests")

### get subset of results for value check
stageName="PCB_QC"
testName="LV_RAIL_TEST"
df_sub=df_tests.query("stage=='"+stageName+"' & test=='"+testName+"'")[['test','results']].reset_index()
df_sub.head(3)


###################
### pandas plotting
###################

### split results into *columns*
df_res = pd.DataFrame(df_sub.results.tolist(), index= df_sub.index)
df_res.head(3)

cols=[list(x.keys())[0] for x in df_res.iloc[0].values]
for i in range(0,len(df_res.columns),1):
    df_res=df_res.rename({i:cols[i]}, axis=1)
    df_res[cols[i]]= df_res.apply(lambda x: list(x[cols[i]].values())[0],axis=1)

df_res

for c in list(df_res.columns):
    df_res[c]=pd.to_numeric(df_res[c].astype(str), errors='coerce')

df_res.plot.box(grid=True,title="results")


###################
### altair & plotly plotting
###################

### split results list into *rows*
s = df_sub.apply(lambda x: pd.Series(x['results']), axis=1).stack().reset_index(level=1, drop=True)
s.name = 'results'
# new dataframe for split list
df_alt = df_sub.drop('results', axis=1).join(s)
# split name from value
df_alt['resName']= df_alt.apply(lambda x: list(x['results'].keys())[0],axis=1)
df_alt['resVal']= df_alt.apply(lambda x: list(x['results'].values())[0],axis=1)
#df_alt

# df_alt['resVal'].value_counts()
def SortValues(x):
    try:
        return float(x)
    except ValueError:
        return float('NaN')
    except:
        return -1

df_alt['resVal']=df_alt['resVal'].apply(lambda x: SortValues(x), 1)
df_alt['resVal'].value_counts()

boxes=alt.Chart(df_alt).mark_boxplot().encode(
    x='resName:O',
    y='resVal:Q'
).properties(
    width=500,
    height=300
)
boxes.show()


fig = px.line_polar(df_alt, r='resVal', theta='resName', line_close=True)
fig.show()


bars=alt.Chart(df_tests).mark_bar().encode(
    y=alt.Y('test:O', title="component testType"),
    x=alt.X('count():Q', title="sum", scale=alt.Scale(domain=(0,550)) ),
    color=alt.Color('stage', legend=alt.Legend(title="component stage"), scale=alt.Scale(scheme='dark2'))
)
# annotate chart with values
text = bars.mark_text(
    align='left',
    baseline='middle',
    dx=3  # Nudges text to right so it doesn't appear on top of the bar
).encode(
    text='count():Q'
)
# open in notebook (problems with hydrogen)
bars
# open in browser - requires altair_viewer
(bars + text).properties(height=250).show()
