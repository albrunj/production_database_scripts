#!/usr/bin/python
import json
from pathlib import Path

from __path__ import updatePath
updatePath()



# VF, 2021-06-24: to write a json file with the test setup, using an input control file
#
#


def main(args,aTemplate):
    inputControlFile = args.inputControlFile
    outputJSONFile   = args.outputJSONFile
    printTemplate    = args.printTemplate
    print(" Got input: ")
    print("   inputControlFile = " + inputControlFile )
    print("   outputJSONFile   = " + outputJSONFile   )
    print("   printTemplate    = " + str(printTemplate) )

    if printTemplate:
        oFile = "ControlFile_example.txt"
        print("\nWill write the Control File template to file <" + oFile + "> and exit.\n")
        with open(oFile,'w') as oF:
            oF.write(aTemplate)
        return

    # check the existence of the input
    if len(inputControlFile) ==0 or len(outputJSONFile) == 0 :
        print(" wrong intput parameters, exiting...")
        return

    fAbsPath = Path(inputControlFile)
    if not fAbsPath.is_file():
        print(" don't really see the file, exiting..." )
        return

    # read the input
    with open(inputControlFile,'r') as iFile:
        myLines = iFile.readlines()


    # initialize
    Proj      = ""
    CompType  = ""
    Code      = ""
    Name      = ""
    Descr     = ""
    AutoGrade = ""
    listProps  = []
    listParams = []

    # read it all in
    for aLine in myLines:
        # remove the comment lines, which start with "#" symbol
        if aLine.startswith("#") :
            continue
        # remove the comments from the other lines
        listWords = aLine.split("#") # presume it could be a comma-separated list
        myRealData = listWords[0]
        # presume the keyword and the value are separated by ":"
        listKeyValue = myRealData.split(":")
        if len(listKeyValue) != 2:
            print("wrong Control File Syntax: expect only 1 Key and 1 Value in a line. Exiting...")
            print("got:")
            print(listKeyValue)
            return 
        # assign the key and its value
        rawKey = listKeyValue[0]
        rawVal = listKeyValue[1]
        # remove spaces
        aKey = rawKey.strip()
        aVal = rawVal.strip()
        # clean them
        aKey.strip()
        aVal.strip()
        # find the key
        if   aKey == "project"         : 
            Proj      = aVal
        elif aKey == "componentType"   : 
            CompType  = aVal
        elif aKey == "code"            : 
            Code  = aVal
        elif aKey == "name"            : 
            Name  = aVal
        elif aKey == "description"     : 
            Descr  = aVal
        elif aKey == "automaticGrading": 
            AutoGrade  = aVal
        elif aKey == "property"        : 
            listProps.append(aVal)
        elif aKey == "parameter"       : 
            listParams.append(aVal)
        else:
            print("wrong Control File Syntax: found an unexpected line:")
            print(" Key   = " + aKey )
            print(" Value = " + aVal )
            print(" ...exiting.")
            return 

    # declare the JSON structure
    theJSON = { "project"         : Proj,
                "componentType"   : CompType,
                "code"            : Code,
                "name"            : Name,
                "description"     : Descr,
                "automaticGrading": (AutoGrade=="True"),
                "properties": [],
                "parameters": [],
                "plots": None }

    # process the properties and add the the json file
    for aProp in listProps:
        listVals = aProp.split(',')

        # expect exactly 7 values! This is HARD-CODED!
        if len(listVals) != 7:
            print(" wrong format of the <property> line in the ASCII file: ")
            print(listVals)
            print("...exiting")
            return

            # clean them
        washedVals = []
        for eachVal in listVals:
            cleanVal = eachVal.strip()
            washedVals.append(cleanVal)

        # for a jasonlet
        aJsonlet = { "code"       : washedVals[0],
                     "name"       : washedVals[1],
                     "order"      : int(washedVals[2]), # this is an integer
                     "description": washedVals[3],
                     "dataType"   : washedVals[4],
                     "valueType"  : washedVals[5],
                     "required"   : (washedVals[6]=="True") } # this is a boolean
        theJSON['properties'].append(aJsonlet)

    
    # process the properties and add the the json file
    # firstTime = True
    for aParam in listParams:
        listVals = aParam.split(',')
        # expect exactly 8 values! This is HARD-CODED!
        if len(listVals) != 8:
            print(" wrong format of the <property> line in the ASCII file: ")
            print(listVals)
            print("...exiting")
            return
        # clean them
        washedVals = []
        for eachVal in listVals:
            cleanVal = eachVal.strip()
            washedVals.append(cleanVal)

        # # DBG:
        # bReq = washedVals[7] == "True"
        # print(" the required state = " + washedVals[7] + " = " + str(bReq) )

        # for a jasonlet
        # <code,name,order,description,dataType,valueType,arrayDimensions,required> \n"
        #  - for parameters: keys <additional,allAssociatedChildrenIsRequired,objectDefinition,thresholds>  are <None> \n"
        #  - for parameters: key  <associateChildren> is <[]> \n"

        # if "None" string -> It's <None>, otherwise an integer to decipher
        useDim = ""
        if washedVals[6] == "None" :
            useDim = None
        else:
            useDim = int(washedVals[6])
        bReq = ( washedVals[7] == "True" )
        # VF, 2021-06-26:
        # not sure if this actually intended behavior -- seems too weird.
        # Will assume this is a bug.
        # it seem the 1st "additional"/"required" parameter is <null>, and the rest are False
        # vAddit = ""
        # vReqed = ""
        # if firstTime :
        #     firstTime = False
        #     vAddit = None
        #     vReqed = None
        # else:
        #     vAddit = False
        #     vReqed = False
        # if bReq : # this means true value is set -> reset it
        #     vReqed = True
        vReqed = bReq
        vAddit = False
        aJsonlet = { "code"       : washedVals[0],
                     "name"       : washedVals[1],
                     "order"      : int(washedVals[2]), # this is an integer
                     "description": washedVals[3],
                     "dataType"   : washedVals[4],
                     "valueType"  : washedVals[5],
                     "arrayDimensions": useDim,
                     "required"       : vReqed,               # this is a boolean
                     "additional"     : vAddit,
                     "allAssociatedChildrenIsRequired": None, # this is BS
                     "objectDefinition"               : None, # this is BS
                     "thresholds"                     : None, # this is BS
                     "associateChildren"              : [] }  # this is BS
        theJSON['parameters'].append(aJsonlet)

    # write it all out
    with open( outputJSONFile, 'w') as oF:
        json.dump( theJSON, oF, indent=2 )



if __name__ == '__main__':
    import argparse
    aTemplate  = " project          : <S/P/etc>                                                     \n"
    aTemplate += " componentType    : <component type handle/code>                                  \n"
    aTemplate += " code             : <test type handle/code to be created, e.g. MAH_TESTA_SUPERBO >\n"
    aTemplate += " name             : <Test name visible to a user>                                 \n"
    aTemplate += " description      : <Test description less visible to a user>                     \n"
    aTemplate += " automaticGrading : <True/False>                                                  \n"
    aTemplate += " property   : <code,name,order,description,dataType,valueType,required>           \n"
    aTemplate += " ... \n"
    aTemplate += " parameter: <code,name,order,description,dataType,valueType,arrayDimensions,required> \n"
    aTemplate += " ... \n"
    aTemplate += " will assume that: \n"
    aTemplate += "    - key <plots> is None for the test \n" 
    aTemplate += "    - for parameters: keys <additional,allAssociatedChildrenIsRequired,objectDefinition,thresholds>  are <None> \n"
    aTemplate += "    - for parameters: key  <associateChildren> is <[]> \n"

    strDescription = "Converting an input Control File (ASCII) into an test data structure\n\n"
    strDescription += " A Control File content example (between \"-------\" lines):\n\n"
    strDescription += " ----------------------------------------\n"
    strDescription += aTemplate
    strDescription += " ----------------------------------------\n"
    strDescription += "\n"

    parser = argparse.ArgumentParser(
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = strDescription )
    parser.add_argument('-i', '--inputControlFile', dest = 'inputControlFile', type = str, default = '', help = 'Control File name/path')
    parser.add_argument('-o', '--outputJSONFile',   dest = 'outputJSONFile',   type = str, default = '', help = 'output JSON file name/path')
    parser.add_argument('-p', '--printTemplate',    dest = 'printTemplate',action="store_true", help = 'To print Control File template and exit')
    args = parser.parse_args()

    main(args,aTemplate)
