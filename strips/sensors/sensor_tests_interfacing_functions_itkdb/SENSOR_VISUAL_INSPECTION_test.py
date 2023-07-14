import copy
import os
from pathlib import Path

from __path__ import updatePath
from CommonConfig import TestType_Visual_Inspection
updatePath()

standardDamages = ["mark", "debris", "scuffing", "suction cup mark", "blotch", "pit", "deposit", "scratch", "deep scratch", "chip", "mismatched serial number", "metal short", "metal break"]         # the standard classification of damages
maxIMG = 4
maxDEFECT = 6
maxSIZE = 10_000_000

def Visual_Inspection(WAFERDICT):

    print('Starting Visual_Inspection for {}-W{}, file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']),str(WAFERDICT['Filename']) ))

    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
    NEWWAFERDICT['Decision']=None
    NEWWAFERDICT['Flags']=[]

    #MeasErr =  False
    #Check if it is a Visual Inspection Test
    if WAFERDICT['TestType'] in [TestType_Visual_Inspection]:
        Result=WAFERDICT['Result']
    else:
        print('*** {} is Not a Visual Inspection Test!'.format(str(WAFERDICT['Filename'])))
        NEWWAFERDICT['Flags'].append('File Not a Visual Inspection Test!')
        return NEWWAFERDICT
    
    #Check if Results exists
    print("WAFERDICT,", WAFERDICT)
    if Result=='Pass':
        print('The Visual Inspection test passed.')
        NEWWAFERDICT['Decision']=Result
        NEWWAFERDICT['Flags'].append('The Visual Inspection test passed.')
    elif  Result == 'Fail':  
        print('The Visual Inspection test failed.')
        NEWWAFERDICT['Decision']=Result
        NEWWAFERDICT['Flags'].append('The Visual Inspection test failed.')
    elif (WAFERDICT['DataFormat'] =='FromITKDatabase'):
        if WAFERDICT['Settings'] is not None:
            if (WAFERDICT['Settings'].find('failed') != -1):
                print('The Visual Inspection test failed.')
                NEWWAFERDICT['Decision']="Fail"
                NEWWAFERDICT['Flags'].append('The Visual Inspection test failed.')
            elif (WAFERDICT['Settings'].find('failed') != -1):
                print('The Visual Inspection test passed.')
                NEWWAFERDICT['Decision']='Pass'
                NEWWAFERDICT['Flags'].append('The Visual Inspection test passed.')
            else:
                if (WAFERDICT['DAMAGE_TYPE1']!=None):
                    print('The Visual Inspection test already in the DB. Some images uploaded.')
                    NEWWAFERDICT['Flags'].append('The Visual Inspection test already in the DB. Some images uploaded.')
                else:
                    print('The Visual Inspection test already in the DB. No image uploaded.')
                    NEWWAFERDICT['Flags'].append('The Visual Inspection test already in the DB. No image uploaded.')
        elif WAFERDICT['Settings'] is None:
            if (WAFERDICT['DAMAGE_TYPE1']!=None):
                    print('The Visual Inspection test already in the DB. Some images uploaded.')
                    NEWWAFERDICT['Flags'].append('The Visual Inspection test already in the DB. Some images uploaded.')
            else:
                print('The Visual Inspection test already in the DB. No image uploaded.')
                NEWWAFERDICT['Flags'].append('The Visual Inspection test already in the DB. No image uploaded.')
    elif ( Result != "Pass" and Result != "Fail" and WAFERDICT['Filename'] != None ):
        print('The test results is unclear. Should be either <Pass> or <Fail>')
        NEWWAFERDICT['Flags'].append('The test results is unclear. Should be either <Pass> or <Fail>')
        NEWWAFERDICT['Decision']='MeasErr'
    else:
        print('The test results is unclear.')
        NEWWAFERDICT['Flags'].append('The test results is unclear.')
        NEWWAFERDICT['Decision']='MeasErr'

   # to check the DamageType classification
    for Damage in [WAFERDICT["DamageType1"],
                     WAFERDICT["DamageType2"],
                     WAFERDICT["DamageType3"],
                     WAFERDICT["DamageType4"],
                     WAFERDICT["DamageType5"],
                     WAFERDICT["DamageType6"]] :
        if Damage != None :
            cmpDamage = Damage.lower()
            if cmpDamage not in standardDamages:
                print(" Got new/unknown damage type = <" + Damage + ">")
                print(" The authorized types are:")
                print(standardDamages)
                print(" Exiting.")
                NEWWAFERDICT['Flags'].append(" Got new/unknown damage type = <" + Damage + ">. Exiting.")
                return NEWWAFERDICT

   # check/add images
    totalSize = 0.0

    for k in range(1,maxDEFECT+1):
        aKey = "Images" + str(k)
        mImages = WAFERDICT[aKey]
        if mImages!= None and len(mImages) > 0 :
            # check the number of them
            listImages = mImages.split(",")
            cleanImages = []
            for anImage in listImages:
                clImage = anImage.strip()
                cleanImages.append(clImage)
            if len(cleanImages) > maxIMG:
                print(" see more than " + str(maxIMG) + " images for a defect:")
                print(cleanImages)
                print("Only up to " + str(maxIMG) + " are supported, exiting...")
                NEWWAFERDICT['Flags'].append(" More than " + str(maxIMG) + " images for a defect. Only up to " + str(maxIMG) + " are supported. Exiting.")
                return NEWWAFERDICT
            # Check their existence and size
            for n,anImage in enumerate(cleanImages):
                aPath = Path(anImage)
                if not aPath.is_file():
                    print(" file <" + anImage + "> does not exist, exiting")
                    NEWWAFERDICT['Flags'].append("File <" + anImage + "> does not exist. Exiting.")
                    return NEWWAFERDICT 
                chkName = anImage.lower()
                if not ( chkName.endswith('.png' ) or
                         chkName.endswith('.jpg' ) or
                         chkName.endswith('.jpeg') or
                         chkName.endswith('.bmp' ) or
                         chkName.endswith('.png' ) ) :
                    print(" incorrect file extension for <" + anImage + ">")
                    print(" expected png/jpg/jpeg/bmp/png, exiting...")
                    NEWWAFERDICT['Flags'].append("Incorrect file extension for <" + anImage + "> Exiting.")
                    return NEWWAFERDICT 
                totalSize += os.path.getsize(anImage)
                # Since we already parsed this, add the new key to the dict, to use in the JSON file
                newKey = "IMS" + str(k) + "_" + str(n+1)
                NEWWAFERDICT[newKey] = anImage
    if totalSize >= maxSIZE :
        print(" the input images are too large, expect maximum of 10 MB in total, exiting ")
        NEWWAFERDICT['Flags'].append("The input images are too large, expect maximum of 10 MB in total. Exiting.")
        return NEWWAFERDICT 

    print ("Decision = {}".format(NEWWAFERDICT['Decision']))
    print ('Finished Visual_Inspection for {}-W{}, file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']),str(WAFERDICT['Filename'])))
    return NEWWAFERDICT
