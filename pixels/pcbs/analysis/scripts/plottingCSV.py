import sys

import pandas as pd
## common PDB access
pdsDir = globals()['_dh'][0]
sys.path.insert(1, pdsDir+'/pixels/pcbs/analysis')
import PDBinfrastructure as infra
import myDetails
## plotting
import altair as alt

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
fileName=dataPath+"RD53A Quad Hybrid QC register - Sheet1.csv"
#fileName=dataPath+"TestSheet1.csv"
df_raw = pd.read_csv(fileName)
df_raw=df_raw.convert_dtypes()
df_raw.columns

# format input data for upload - map booleans
df_raw['Shorts on capacitors?']=df_raw['Shorts on capacitors?'].map({'no':False,'not tested':False,'No':False,'reworked':True,'yes':True,'Yes':True})
df_raw['Shorts on capacitors?'].value_counts()

df_raw['Scans taken?']=df_raw['Scans taken?'].map({'no':False,'not tested':False,'No':False,'reworked':True,'yes':True,'Yes':True})
df_raw['Scans taken?'].value_counts()

df_raw.dtypes
df_raw.head(5)

# mapping values
def repFunc(x):
    if 'not tested' in str(x).lower():
        return -1
    else:
        return x
df_raw['HV leakage (mV on readout card)']=df_raw['HV leakage (mV on readout card)'].apply(lambda x:repFunc(x))
df_raw['HV leakage (mV on readout card)'].value_counts()
df_raw['HV leakage (mV on readout card)'].describe()
df_raw['HV leakage (mV on readout card)']=pd.to_numeric(df_raw['HV leakage (mV on readout card)'],errors='coerce')
df_raw['HV leakage (mV on readout card)'].plot.hist(bins=100, alpha=0.5,title="HVLEAKAGE")

df_raw['Temp (°C) (@HV test)'].describe()
df_raw['humidity (%) (@HV test)'].describe()
df_raw['HV leakage (mV on readout card)'].describe()
#####################
### plot csv data
#####################

### define comparison sets
cu_set=['top cu thickness (microns)','bot cu thickness (microns)']
sldo_set=['SLDO 1 (kOhms)','SLDO 2','SLDO3','SLDO4']
height_set=['hv cap height (mm)','connector height (mm)']
drop_set=['Vin drop with jig compensation','GND drop with jig compensation']
cond_set=['Temp (°C) (@HV test)','humidity (%) (@HV test)']


### pandas in-built plotting
for c in cu_set:
    df_raw[c]=pd.to_numeric(df_raw[c],errors='coerce')
    df_raw[c].plot.hist(bins=12, alpha=0.5,title=c)

for c in sldo_set:
    df_raw[c]=pd.to_numeric(df_raw[c],errors='coerce')
    df_raw[c].plot.hist(bins=12, alpha=0.5,title=c)

for c in height_set:
    df_raw[c]=pd.to_numeric(df_raw[c],errors='coerce')
    df_raw[c].plot.hist(bins=12, alpha=0.5,title=c)

for c in drop_set:
    df_raw[c]=pd.to_numeric(df_raw[c],errors='coerce')
    df_raw[c].plot.hist(bins=12, alpha=0.5,title=c)

for c in cond_set:
    df_raw[c]=pd.to_numeric(df_raw[c],errors='coerce')
    df_raw[c].plot.hist(bins=12, alpha=0.5,title=c)


### altair plotting
histo=alt.Chart(df_raw).transform_fold(
    cond_set,
    as_=['name', 'value']
).mark_area(
    opacity=0.3,
    interpolate='step'
).encode(
    alt.X('value:Q', bin=alt.Bin(maxbins=100)),
    alt.Y('count()', stack=None),
    alt.Color('name:N')
).interactive()
alt.renderers.enable('mimetype')
histo.height=300
histo.width=500

histo

histo.show()
