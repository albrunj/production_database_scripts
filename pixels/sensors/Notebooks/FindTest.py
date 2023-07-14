# %%
#!/usr/bin/python3
### get general libraries
import os
import sys

import pandas as pd

# %%
### get PDB credentials
cwd = os.getcwd()
# check where this is:
#cwd
sys.path.insert(1, cwd+"/Notebooks")
import setEnv
setEnv.SetEnv()

# import API and check authentication
import itkdb
myClient = itkdb.Client()
myClient.user.authenticate()
user=myClient.get('getUser', json={'userIdentity': myClient.user.identity})
user['firstName']

# %%
# Check available component names and codes
instCode="GL"
projCode="P"

compTypeList=list(myClient.get('listComponents',json={'institution':instCode, 'project':projCode }))
compTypeMap=[{"name":w['componentType']['name'], "code":w['componentType']['code']} for w in compTypeList]
df_compType=pd.DataFrame(compTypeMap)
df_compType.drop_duplicates()

# %%
# Check available tests for componentType
compTypeCode="SENSOR_TILE"
compTestList=list(myClient.get('listTestTypes',json={'project':projCode, 'componentType':compTypeCode}))
compTestMap=[{"name":w['name'], "code":w['code']} for w in compTestList]
df_compTest=pd.DataFrame(compTestMap)
df_compTest.drop_duplicates()

# %%
# make list of components of type (if status ready)
compTypeCode="SENSOR_TILE"
compList=list(myClient.get('listComponents',json={'institution':instCode, 'project':projCode, 'componentType':compTypeCode }))
compMap=[{"ASN":w['serialNumber'], "altID":w['alternativeIdentifier'], "code":w['code']} for w in compList if w['state']=="ready"]
df_comp=pd.DataFrame(compMap)
df_comp

# %%
# find tests of type for selected components
testType="CV_MEASURE"
for c in compMap:
    print(c['altID'])
    compObj=myClient.get('getComponent',json={'component':c['code']})
    for i in compObj['tests']:
        #print(i)
        if i['code']==testType:
            for r in i['testRuns']:
                print(r['id'])
                #if r['state']!="ready": continue
                try:
                    c[testType].append(r['id'])
                except KeyError:
                    c[testType]=[r['id']]

# %%
df_compAug=pd.DataFrame(compMap)
### nifty filter out NaN trick:
df_compAug.query(testType+" == "+testType)

# %%
# edit tests
for c in compMap:
    try:
        for r in c[testType]:
            testObj=myClient.get('getTestRun',json={'testRun':r})
            for v in testObj['results']:
                ### edits here
                if v['code']=="V_FULLDEPL":
                    print("code:",c['code'],", testRun:",r,", value:",v['value'])
    except KeyError:
        continue

# %%
