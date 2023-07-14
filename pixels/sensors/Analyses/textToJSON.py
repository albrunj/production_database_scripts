#!/usr/bin/python
### short script to convert standardised text files to json format
import json
from datetime import datetime

import numpy as np


def ConvertCases(textToSplit, debug=False):
    arr=[]
    if "\t" in textToSplit:
        try:
            arr = textToSplit.rstrip('\n').split('\t')
        except ValueError:
            print("### split result:",textToSplit.rstrip('\n').split('\t'))
        if debug: print(">>> \"\\t\" >>>",arr)
    else:
        try:
            arr = textToSplit.rstrip('\n').split(' ')
        except ValueError:
            print("### split result:",textToSplit.rstrip('\n').split(' '))
        if debug: print(">>> \" \" >>>",arr)
    return arr


def Convert(data_file, debug=False):
    ### debugging toggled off
    jsonDict={}
    with open(data_file, 'r') as data:
        if debug: print(">>>","CONVERTING ...")
        ### ASN and test
        textToSplit=data.readline()
        caseArr=ConvertCases(textToSplit,debug)
        if len(caseArr)==2:
            jsonDict["component"]=caseArr[0]
            jsonDict["test"]=caseArr[1]
        else:
            print("Not enough elements returned!")
        ### institution and date
        textToSplit=data.readline()
        caseArr=ConvertCases(textToSplit,debug)
        if len(caseArr)==2:
            jsonDict["institution"]=caseArr[0]
            jsonDict["date"]=datetime.strptime(caseArr[1], '%Y-%m-%d_%H:%M').strftime("%d.%m.%Y %H:%M")
        else:
            print("Not enough elements returned!")
        ### prefix
        textToSplit=data.readline()
        caseArr=ConvertCases(textToSplit,debug)
        if len(caseArr)==2:
            jsonDict[caseArr[0]]=caseArr[1]
        else:
            print("Not enough elements returned")
        ### Vdep
        textToSplit=data.readline()
        caseArr=ConvertCases(textToSplit,debug)
        if len(caseArr)==2:
            jsonDict[caseArr[0]]=float(caseArr[1])
        else:
            print("Not enough elements returned")
        ### properties or data
        textToSplit=data.readline()
        caseArr=ConvertCases(textToSplit,debug)
        ### temp and humid (optional)
        header=[]
        if len(caseArr)==2:
            if debug: print("properties found")
            jsonDict["properties"]={"HUM":caseArr[0],"TEMP":caseArr[0]}
            textToSplit=data.readline()
            #print("header...:",textToSplit)
            caseArr=ConvertCases(textToSplit,debug)
            header = [x.split('/')[0] for x in caseArr]
        ### measurement data
        elif len(caseArr)>2:
            if debug: print("no properties found")
            header = [x.split('/')[0] for x in caseArr]
        else:
            print("Not enough elements returned")
        if debug: print(header)

    iv_data = np.genfromtxt(data_file, skip_header=6, names=header, delimiter='\t')
    if debug: print(">>> length:",len(iv_data))
    if debug: print(">>> >>>",iv_data)

    keyMap={"t":"time","U":"voltage","Iavg":"current","Istd":"sigma current","T":"temperature","RH":"humidity"}
    jsonDict["IV_ARRAY"]={}
    for c,h in enumerate(header):
        jsonDict["IV_ARRAY"][keyMap[h]]=[x[c] for x in iv_data]

    return jsonDict

def Write(jsonDict, jsonName):
    ### should be just about human readable
    j = json.dumps(jsonDict, indent=4)
    f = open(jsonName, 'w')
    print(j, file=f)
    f.close()

### debugging
# import os
# cwd = os.getcwd()
# fileName=cwd+"/data/"+"Example_IV_data_noProps.txt"
# myDict=Convert(fileName)
# Write(myDict,cwd+"/data/testResult_noProps.json")
