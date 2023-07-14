# %%
# %% codecell
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
print(user['firstName'])

# %%
projCode="P"
compTypeCode="BARE_MODULE"
# new module
bareObj = myClient.get('generateComponentTypeDtoSample', json={'project':projCode, 'code': compTypeCode, 'requiredOnly' : False})

### add basic info.
bareObj['subproject']="PG"
bareObj['type']="DIGITAL_QUAD_BARE_MODULE"
bareObj['institution']="GL"
bareObj['properties'] = {'SENSOR_TYPE' : '0', 'FECHIP_VERSION': '0'}
bareObj

# %%
### register component
new_bare = myClient.post('registerComponent', json=bareObj)
newCode=new_bare['component']['code']

# %%
### get component
compCode=newCode
compObj = myClient.get('getComponent',json={'component':compCode})

# %%
# what tests are appropriate?
compTypeCode=compObj['componentType']['code']
compTestList=list(myClient.get('listTestTypes',json={'project':projCode, 'componentType':compTypeCode}))
compTestMap=[{"name":w['name'], "code":w['code']} for w in compTestList]
df_compTest=pd.DataFrame(compTestMap)
df_compTest.drop_duplicates()

# %%
# test format
testCode="BARE_MODULE_METROLOGY"
testObj=myClient.get('generateTestTypeDtoSample',json={'project':projCode, 'code': testCode, 'componentType':compTypeCode, 'requiredOnly' : False})
testObj

# %%
### delete component
myClient.post('deleteComponent', json={'component':newCode})

checkObj=myClient.get('getComponent',json={'component':newCode})
checkObj['state']

# %%
