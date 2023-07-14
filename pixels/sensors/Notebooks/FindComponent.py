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
print(user['firstName'])

# %%
# Check available component names and codes
instCode="GL"
projCode="P"
compList=list(myClient.get('listComponents',json={'institution':instCode, 'project':projCode }))
compMap=[{"code":w['code'], "ASN":w['serialNumber'], "altID":w['alternativeIdentifier'], "typeCode":w['componentType']['code'],"instCode":w['institution']['code'],"locCode":w['currentLocation']['code'],"state":w['state']} for w in compList]
df_comp=pd.DataFrame(compMap)
# display top 5 rows only
df_comp.head(5)

# %%
df_comp.query('ASN=="20UPGS93500001"')

# %%
df_comp.query('ASN=="20UPGS91700001"')

# %%
