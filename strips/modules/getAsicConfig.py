#!/usr/bin/env python3
### Author: Ian Dyckes, with help from Matthew Gignac, API update by Craig Sawyer
###
### Pulls the ABC configuration used during probe tests from the production DB, then writes an ITSDAQ config.
### Finds hybrid in DB, iterates through children, finds ABCSTARV1 serials, pulls their info, and writes the itsdaq config.
###
### Can give hybrid assembly's local name OR serial number.
###
### Example usage:
### python getAsicConfig.py --serial 20USBHX2000791
### python getAsicConfig.py --local GPC1938_X_002_B_H2

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import argparse
import os
import pathlib
import sys

import itk_pdb.dbAccess as dbAccess

############################################    
############################################    
############################################    

def main():

    ### arguements
    parser = argparse.ArgumentParser(description='For pulling ABC configuration during probe testing from DB and writing itsdaq config.')
    parser.add_argument('--local', default=None, help='Local name (e.g. GPC1938_X_009_A_H1).')
    parser.add_argument('--serial', default=None, help='Serial name of STAR Hybrid Assemble.')
    parser.add_argument('--verbose', default=False, action='store_true', help='Increase verbosity of DB interactions.')
    parser.add_argument('--outDir', default='./hybrid_configs/', help='Output directory for configs.')
    args = parser.parse_args()

    ### DB verbosity.
    if args.verbose:
        dbAccess.verbose = True
        
    ### Get DB token
    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    ### Can provide the serial of a single hybrid
    if args.serial:
        hybridSerial = args.serial
        
    ### Can provide the local name of a single hybrid.
    elif args.local: 
        ### Find the STAR Hybrid Assembly matching this local name and type.
        matchingList = getHybridAssemblyByLocalName(args.local)
        if len(matchingList)==0:
            print("Found no STAR Hybrid Assembly in the database matching local name:", args.local)
            sys.exit("Exiting!")
        elif len(matchingList)>1:
            print("Found multiple STAR Hybrid Assemblies in the database matching local name:", args.local,". Maybe provide the serial instead!")
            print("Or maybe add a check here of the institute to see if only one is yours.")
            sys.exit("Exiting")
        matching = matchingList[0]
        hybridSerial = matching['serialNumber'] # serial of STAR Hybrid Assembly matching this local name.
        print("Found exactly one STAR Hybrid Assembly matching this local name with serial:", hybridSerial)

    ### Not enough info provided
    else:
        sys.exit("Must provide either a --serial or --local of a single STAR Hybrid Assembly!  Exiting!")

    ### Get test results for all ABCs on the hybrid
    testType = "DAC_TEST"
    testResults = getAsicTestResults(hybridSerial, testType) # list of dictionaries.  Includes position on hybrid and all config info.

    testType = "IMUX_TEST"
    imuxResults = getAsicTestResults(hybridSerial, testType)

    ### Careful about maintaining order! Should be 9 to 0!  Sort.
    testResults = sorted(testResults, key=lambda d: d['position'], reverse=True)

    positions = [d['position'] for d in testResults]

    ### Get number of ABCs for this hybrid type
    nABCs = len(testResults)

    ### Now write itsdaq config
    hybridConfig = hybrid_header(nABCs, positions)
    for abc in testResults: #abc is a dictionary.
        location = abc['position']
        results = {result["code"]:result["value"] for result in abc['testJSON']['results']} # get just the vital info.

        imuxChipResult = {res["code"]:res["value"]
                          for iabc in imuxResults
                          for res in iabc['testJSON']['results']
                          if iabc['position'] == location}

        chip = "###### \n"
        chip =  f"Chip {location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
        chip += "            1    0     0       0      4     1  1  134\n"
        chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
        chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
        chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

        dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
        dacs = [int(results[d_n]) for d_n in dac_names]
        # BIFEED, BIPRE, ADC_BIAS
        dacs[4:4] = [15, 6, int(imuxChipResult['ADC_RANGE_BEST'])]
        chip += "       " + "\t".join("%d" % d for d in dacs) + "\n"
        chip += "######\n"
        hybridConfig+=chip

    ### Save the config
    outDir = pathlib.Path(args.outDir)
    if not os.path.exists(outDir):
        os.mkdir(outDir)
    if args.local:
        outFile = outDir / (args.local+'.det')
    else:
        outFile = outDir / (hybridSerial+'.det')
    # Current itsdaq doesn't like module name starting with 2
    # Also useful to let it know it's a serial number
    outFile = outDir / ('SN'+hybridSerial+'.det')
    print("Saving itsdaq config to", outFile)
    with open(outFile,"w") as f:
        f.write(hybridConfig)
        
##########################################
##########################################
##########################################

### Looks up hybrid assemblies in the database with given local name.
### Returns list of matching elements.  Hopefully only ever of length 0 or 1.
def getHybridAssemblyByLocalName(local):
  
    try:
            d = {
                "project": "S",
                #"subproject": "SB",
                "componentType": "HYBRID_ASSEMBLY",
                # "type": hybridType,
                "propertyFilter": [
                    {
                	"code": "LOCAL_NAME",
                	"operator": "=",
                	"value": local
                    }
                ]
            }
            result = dbAccess.doSomething("listComponentsByProperty",method='GET',data=d)
    except:
        sys.exit("\nFailed when looking for existing hybrid with local name", local, " in database.  Exiting.")

    matching = result["pageItemList"]
    
    return matching # this is a list of matching components.


############################################    
############################################    
############################################    
        
### Get results for <testType> test for all ASICs on hybrid with serial <hybridSerial>.
### Returns a list of dictionaries.  Each element is of the form {'serial':<ABC serial>, 'position':<ABC position>, 'testType':<testType>, "testJSON": <full test JSON>}
def getAsicTestResults(hybridSerial, testType):
        
    ### Get complete info on this STAR Hybrid Assembly.
    try:
        hybridJSON = dbAccess.doSomething(action='getComponent',method='GET',data={"component":hybridSerial})
    except:
        print("Failed when trying to get STAR Hybrid Assembly info from the DB.  Serial:", hybridSerial)
        sys.exit("Exiting!")

    ### Check if all ABCSTARV1 are assembled to the hybrid
    if not allChildrenAssembled(hybridJSON, 'ABCSTARV1'):
        print("Not all ABCSTARV1 chips were assembled in the database.  Fix this first!.")
        # continue
        sys.exit("Exiting!")

    ### Declare output list (use list instead of dict b/c order matters.  Could use an orderedDict I guess...).
    abcConfigList = []
    
    ### Go through ABCSTARV1 children and get info on each.
    for child in hybridJSON['children']:
        thisType = child['type']['code']
        if not thisType=="ABCSTARV1":
            continue
        if child['component']: # already assembled a chip here, else it's null.  Should be true due to check earlier.
            existingChipSerial = child['component']['serialNumber']
            existingChipPosition = [prop["value"] for prop in child['properties'] if prop['code']=="ABC_POSITION"][0]
            existingChipWafer = [prop["value"] for prop in child['properties'] if prop['code']=="WAFER_NUMBER"][0]
            print(f"Found ABCStarV1: {existingChipSerial}, position: {existingChipPosition}, wafer: {existingChipWafer}")
            
            ### Get all runs matching testType.
            try:
                #update from Craig for new API
                #testRuns = dbAccess.doSomething(action="listTestRunsByComponent",method='GET', data={'component': existingChipSerial, "testType":testType} )
                testRuns = dbAccess.doSomething(action="listTestRunsByComponent",method='GET', data={"filterMap": {"serialNumber": existingChipSerial, "state": ["ready", "requestedToDelete"], "testType": testType}} )
            except:
                print("Failed when trying to get test info from the DB for ABCSTARV1 with serial:", existingChipSerial, "and test type:", testType)
                sys.exit("Should not happen, so exiting.")

            ### Now get all the info from a particular run.
            ### Not sure how to handle multiple runs of the same test.  Maybe just pull the latest one (highest run number)?  Sort first?
            #update from Craig for new API
            #run =  testRuns['pageItemList'][-1] # get latest run if multiple?
            run =  testRuns['itemList'][-1] # get latest run if multiple?
            runNumber, runID = run["runNumber"], run['id']
            try:
                runInfo = dbAccess.doSomething(action="getTestRun",method='GET', data={'testRun': runID} )
            except:
                print("Failed to get results for following test. Test code/type:", testType, ", Run:", runNumber, ", ID:", runID)
                sys.exit("Exiting.")

            ### Convert existingChipPostion to an integer if necessary.  Some may use this format: ABC_<hybrid_type>_<chip_number>
            try:
                existingChipPosition = int(existingChipPosition)
            except:
                try:
                    existingChipPosition = int(existingChipPosition.split('_')[-1])
                except:
                    print("Cannot parse this chip's position property:", existingChipPosition)
                    print("Not an integer or in the ABC_<hybrid_type>_<chip_number> format.")
                    sys.exit("Exiting!")
            
            ### Return everything.
            resultsDict =  {'serial':existingChipSerial, 'position':existingChipPosition, 'testType':testType, "testJSON": runInfo}
            
            abcConfigList.append( resultsDict )
            
            
    return abcConfigList

################################
################################
################################

def allChildrenAssembled(hybridJSON, childType): # Use 'type' instead of component type to differentiate ASIC versions.
        
    ### First get the number of slots for this child type.
    nChildSlots = len([child['type']['code'] for child in hybridJSON['children'] if child['type']['code']==childType])
    print("Number of", childType, "child slots:", nChildSlots)
    if nChildSlots==0:
        print("No child slots of type:", childType)
        sys.exit("Exiting!")
    
    nAssembled = 0
    for child in hybridJSON['children']:
        if not child['type']['code']==childType: # skip any child that doesn't match the desired child type.
            continue
        if child['component']: # None if nothing assembled in this slot.
            if not child['component']['serialNumber']: # somehow someone assembled a chip without a serial somehow??? So add this check
                continue
            if childType=="ABCSTARV1": # then position of chip matters.
                position = [prop['value'] for prop in child['properties'] if prop['code']=='ABC_POSITION'][0]
                print("Already an ABCStarV1 assembled to position", position )
            nAssembled += 1
            
    if childType=="ABCSTARV1":                
        if not nAssembled == nChildSlots:
            print("Only found", nAssembled, childType, "already assembled.  Expect ", nChildSlots, ". Please assemble more first.")
            return False
        else:
            print("Found", nAssembled, childType, "already assembled.")
            return True
    else: # only expect 1 of these.
        if nAssembled==0:
            print("Did not find any", childType, "already assembled.  Please assemble more first.")
            return False
        else:
            print("Found", nAssembled, childType, "already assembled.")
            return True
    
####################
####################
####################

def hybrid_header(nABCs, positions):
  chipMask = 0
  for p in positions:
      chipMask |= 1 << p

  header  = "Module : Chipset \n"
  header +="           9 \n \n"

  header += "# Speed of readout from HCC \n"
  header += "Speed 320 \n \n"

  header += "HCC 15 auto \n \n"

  header += "#   R32        R33        R34        R35 \n"
  header += "    0x02400000 0x44444444 0x00000444 0x00ff3b05 \n"
  header += "#   R36        R37        R38        R39 \n"
  header += "    0x00000000 0x00000004 0x0fffffff 0x00000014 \n"
  header += "#   R40        R41        R42        R43 \n"
  header += "    0x%08x 0x00010001 0x00010001 0x00000000 \n" % chipMask
  header += "#   R44        R45        R46        R47 \n"
  header += "    0x0000018e 0x00710003 0x00710003 0x00000000 \n"
  header += "#   R48 \n"
  header += "    0x00406600 \n \n"

  header += "Order " + ' '.join([str(i) for i in reversed(range(nABCs))]) + " \n \n"
  
  return header


################################
################################
################################

if __name__ == "__main__":
    main()
