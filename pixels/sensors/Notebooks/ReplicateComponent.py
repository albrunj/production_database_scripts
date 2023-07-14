# %%
#!/usr/bin/python3
### get general libraries
import copy
import os
import sys
from datetime import datetime

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
print(user['firstName'])

# %%
### start with code of component to be copied
compCode="6ede3d5f7af65cef9bb9214ccc6e3a80"
compObj=myClient.get('getComponent',json={'component':compCode})
compObj['state']

# %%
# get basic template of componentType
comp_template = myClient.get('generateComponentTypeDtoSample', json={'project':compObj['project']['code'], 'code': compObj['componentType']['code'], 'requiredOnly' : False})
comp_template

# %%
# make replicant by copying basic template of componentType
repObj=copy.deepcopy(comp_template)

# copy basics to replicant
basic_list=['subproject','institution','type']
for k in basic_list:
    repObj[k]=compObj[k]['code']
repObj

# %%
# copy rest -- basically there is nothing else supported in registration
# avoid=['id','code','serialNumber','state','user','cts']
# # cern-itkpd-main/registerComponent/unsupportedKeys: {'type': 'warning', 'message': 'DtoIn contains unsupported keys.', 'paramMap': {'unsupportedKeyList': ['$.alternativeIdentifier', '$.stateTs', '$.stateUserIdentity', '$.dummy', '$.completed', '$.assembled', '$.trashed', '$.reworked', '$.sys', '$.currentLocation', '$.currentStage', '$.parents', '$.stages', '$.tests']}}
# unsupportedKeys= ['alternativeIdentifier', 'stateTs', 'stateUserIdentity', 'dummy', 'completed', 'assembled', 'trashed', 'reworked', 'sys', 'currentLocation', 'currentStage', 'parents', 'stages', 'tests']
# for k,v in compObj.items():
#     #print(type(v))
#     if k in repObj.keys(): continue
#     if k in unsupportedKeys: continue
#     if k in avoid: continue
#     if v==None: continue
#     if "list" in str(type(v)) and len(v)==0: continue
#     if "dict" in str(type(v)) and len(v.keys())==0: continue
#     repObj[k]=compObj[k]
# repObj

# %%
# copy properties to replicant
# compObj['properties']
for p in compObj['properties']:
    for rp in repObj['properties'].keys():
        if p['code']==rp:
            print(p)
            if p['value']==None: continue
            repObj['properties'][rp]=p['value']
# MAN_SNO must be unique so flag change with time
now=datetime.now()
nowStr=now.strftime("%d.%m.%Y_%H:%M")
repObj['properties']['MAN_SNO']+="_copied_"+nowStr

# %%
### check what's there
repObj

# %%
### register component
new_sensor = myClient.post('registerComponent', json=repObj)

### checking not the same!
print(compObj['serialNumber'])
print(new_sensor['component']['serialNumber'])

# %%
# a couple of useful functions
def FormatProperties(inDict):
    outDict={}
    for i in inDict:
        outDict[i['code']]=i['value']
    return outDict

def GetResult(inDict,testCode):
    #outDict={}
    for i in inDict:
        if i['code']==testCode:
            #outDict[i['code']]=i['value']
            return i['value']

# %%
# upload test results from original to replicant
uploadDict={}
uploadDict['component']=new_sensor['component']['code']
for t in compObj['tests']:
    print(t)
    uploadDict['testType']=t['code']
    for rt in t['testRuns']:
        if rt['state']=="requestedToDelete": continue
        uploadDict['institution']=rt['institution']['code']
        uploadDict['runNumber']=rt['runNumber']
        uploadDict['date']=rt['date']
        uploadDict['passed']=rt['passed']
        uploadDict['problems']=rt['problems']
        testObj=myClient.get('getTestRun',json={'testRun':rt['id']})
        uploadDict['properties']=FormatProperties(testObj['properties'])
        uploadDict['results']={}
        if "IV" in t['code']:
            uploadDict['results']['IV_ARRAY']=GetResult(testObj['results'],"IV_ARRAY")
            uploadDict['results']['BREAKDOWN_VOLTAGE']=GetResult(testObj['results'],"BREAKDOWN_VOLTAGE")
            uploadDict['results']['LEAK_CURRENT']=GetResult(testObj['results'],"LEAK_PLANAR")
            uploadDict['results']['IV_IMG']=GetResult(testObj['results'],"IV_IMG")
        uploadDict['comments']=testObj['comments']
        uploadDict['defects']=testObj['defects']
        updateReturn = myClient.post('uploadTestRunResults', json={**uploadDict})
        ### check return value
        print(updateReturn)

# %%
### checking new component in PDB
newObj=myClient.get('getComponent',json={'component':new_sensor['component']['code']})
newObj['tests']

# %%
### delete component if required
myClient.post('deleteComponent', json={'component':new_sensor['component']['code']})

### component is flagged for deletion
checkObj=myClient.get('getComponent',json={'component':new_sensor['component']['code']})
print(checkObj['state'])


# %%
