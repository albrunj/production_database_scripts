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
### checking PDB
#####################

### projects
projList = list(myClient.get('listProjects'))
projList
df_proj= pd.DataFrame([{"name":x['name'],"code":x['code']} for x in projList])
df_proj

### sub-projects
myProjCode="P"
subprojList = myClient.get('listSubprojects', json={'project':myProjCode})
subprojList
df_subproj= pd.DataFrame([{"name":x['name'],"code":x['code']} for x in subprojList])
df_subproj

### institutions
instList = list(myClient.get('listInstitutions'))
instList
df_inst= pd.DataFrame([{"name":x['name'],"code":x['code']} for x in instList])
df_inst.query('name.str.contains("G")')

### component types
compTypesList = list(myClient.get('listComponentTypes', json={'project':myProjCode}))
compTypesList
df_compType= pd.DataFrame([{"name":x['name'],"code":x['code'],"id":x['id']} for x in compTypesList])
df_compType


#####################
### deletion
#####################

# get my components (ready + requestedToDelete + deleted)
myComps= myClient.get('listMyComponents')
# myComps.page_size
# myComps.page_info
# myComps.page_index

df_myComps= pd.DataFrame([{"type":x['componentType']['code'],"state":x['state'],"code":x['code']} for x in myComps.data])
df_myComps.describe()
df_myComps.pivot_table(index=['type','state'], aggfunc='size')

# subset if required
theseComps=[x for x in myComps.data if x['componentType']['code']=="SENSOR_TILE"]
len(theseComps)

# loop to approve delete requests
for mc in theseComps:
    if mc['state']=="requestedToDelete":
        try:
        #print(mc['code'])
            print(myClient.post('approveDeleteComponent',json={'component':mc['code'], 'approve':"true"}))
        except:
            print("issue with:",mc['code'])
