#LoadedStave.PY 2.0  -- initiate a STAVE component in database
        ##           -- or update a current STAVE component by assemble more modules
        ##           -- change: need only the directory args
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#created 05/08/2019
#last update 06/13/2019
from __future__ import print_function #import python3 printer if python2 is used

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys

# sys.path.append('../')
import argparse
import os
from itk_pdb.databaseUtilities import ERROR, INFO, input, WARNING
from itk_pdb.dbAccess import ITkPDSession
from LoadedStave_class import STAVE, MODULE, MountingInfoInStaveFolder, CORE, ComponentNotFound, MultipleComponentsFound,getCalibrationFileList,getYesOrNo

#assemble a MODULE with a STAVE
def assembleModule(stave,StaveFolder,stave_folder_path):

    stave_side  = StaveFolder.side
    MountingInfo= StaveFolder.MountingInfo
    positions   = StaveFolder.positions
    calibration_folder_path = []
    for position in positions:
        Calibration_TimeStamp = MountingInfo[stave_side][position]['CALIBRATION']
        Loader_Names          = MountingInfo[stave_side][position]['ASSEMBLER']
        cali_path = MountingInfo[stave_side][position]['calibration_folder_path']
        if cali_path not in calibration_folder_path:
            calibration_folder_path.append(cali_path)

        try:
            module=MODULE(stave_folder_path, position, stave_side, Calibration_TimeStamp, Loader_Names, ITkPDSession=stave.ITkPDSession)
        except ComponentNotFound:
            ERROR("No module was found using the IDs given in the CSV file, please fix the error")
            INFO("exiting program...")
            sys.exit()
        except MultipleComponentsFound:
            ERROR("More than one module was found using the IDs given in the CSV file, please fix the error")
            INFO("exiting program...")
            sys.exit()

        ###------fill in more properties--------###
        child_properties=module.childProperties

        #find the slot to be assembled, side L first 14 slots; side J the next 14 slots
        if 'L' in module.stave_side:
            child_slot=stave.slotIDs[position]
        else:
            child_slot=stave.slotIDs[14+position]

        print('childProperties are:', child_properties)
        print('about to assemble module at position', position)
        if getYesOrNo('are you sure you want to assemble? (inset \'y\' or\'n\')'):
            stave.addModule(module,child_slot,child_properties)
            INFO('assembled successfully')

            if getYesOrNo('do you want to upload calibration files associated with the modules you just assembled?'):

                files=getCalibrationFileList()
                for path in calibration_folder_path:

                    invalidFilePath = stave.uploadCalibrationFiles(path,files)

                    if invalidFilePath == True:
                        continue

                    if invalidFilePath!=[]:
                        WARNING("following file not found!")
                        print(invalidFilePath)

                INFO("finished uploading existing files...")

        else:
            INFO('Canceled module %s assembly' % module.stave_side + str(position))


##########main function########
def main(args):
    print('')
    print('*************************************************************************')
    print('* *                                                                 *   *')
    print('*                            LoadedStave.py --JiayiChen                 *')
    print('* *                                                                 *   *')
    print('*************************************************************************')
    print('')

    #stave file
    stave_folder=args.stave_folder

    insti=args.institute

    #check if path exists
    while not os.path.exists(stave_folder):
        ERROR('calibration path (%s) not found' %stave_folder)
        stave_folder=input("Please enter the path to calibtration again:")

    #path has to end with '/'
    if stave_folder[-1]=='/':
        #stave folder name is the local name
        localname = os.path.basename(stave_folder[:-1])
    else:
        localname = os.path.basename(stave_folder)
        stave_folder+='/'


    #initiate a ITkPD session
    session = ITkPDSession()
    session.authenticate()



    #initiate STAVE in database
    if args.command=='initiate':
        print('Welcome to ITk PD STAVE assembly DAY1!')

        type_choices = ["LS","SS"]
        side_choices = ["A","C"]

        core_type = args.core_type
        core_side = args.core_side

        try:
            core_type = core_type.upper()
            core_side = core_side.upper()

        except:
            while core_type not in type_choices:
                WARNING("invaid core type: ")
                print("please reenter core type ", type_choices, " : ")
                core_type = input().upper()

            while core_side not in side_choices:
                WARNING("invaid core side: ")
                print("please reenter core side ", side_choices, " : ")
                core_side = input().upper()

        #initiate a fake 'CORE' object, as core determines stave type and stave side
        newCore=CORE(type=core_type,side=core_side)

        #a chance to change local name
        while not getYesOrNo('Are you sure to use \' %s \' as the local name to register new STAVE? (insert \'y\' or \'n\')' % localname):
            localname=input('please give the new STAVE a local name: ')

        #initiate a new STAVE
        newStave=STAVE(LOCALNAME=localname, assemblySite=insti,ITkPDSession=session) #default stage reception

        #assemble the fake 'CORE'
        newStave.addCore(newCore)

        #register new STAVE
        INFO("ready to register a STAVE:")
        print("local name: ",localname,"  stave type: ", newCore.type + " side " + newCore.side)
        if getYesOrNo('Are you sure you want to register this STAVE? (y/n)'):
            newStave.registerSTAVE()
            INFO('Successfully registered new STAVE')
        else:
            INFO('canceled STAVE registration, exiting program...')
            sys.exit()

###Major changes here###
        #continue to assemble modules
        if getYesOrNo('Do you wish to assemble some MODULEs to this STAVE in the PD?(insert \'y\' or \'n\')'):

            #user select which module position to assemble
            StaveFolder=MountingInfoInStaveFolder(stave_folder)
            StaveFolder.openInterface()

            #get a PD MODULE comp for each module position the user selected & assemble away!
            assembleModule(newStave, StaveFolder,stave_folder)


        else:
            print('')
            INFO('Exiting program...')
            INFO('Summary: registered STAVE'+ localname)
            print('have a great rest of your day')
            exit()


    #update a STAVE in the PD
    if args.command=='update':

        print('Welcome back to ITk PD STAVE assembly!!')
        while True:
            try:
                thisStave=STAVE(LOCALNAME=localname,assemblySite=insti,STAGE='assembly',ITkPDSession=session) #since day2 start with assembly stage
                #get Info for this STAVE
                component = thisStave.StaveINFO()
                break

            except ComponentNotFound:
                ERROR("No stave was found using local name: " + localname)
                print("make sure you have registered this stave already using the \'initiate\' command")
                print("Or, try input the corrent local name")
                localname=input('please give the STAVE local name: ')
                continue

            except MultipleComponentsFound:
                WARNING("multiple STAVEs were found using local name: %s" %localname)
                print("please fix this error in the ITk PD!")
                INFO("exiting program...")
                sys.exit()

        #print STAVE info
        print('Found the following stave using local name',localname)
        print('type(LS/SS):',component['type']['name'])
        print('institution:',component['institution']['name'])
        print('current localtion:',component['currentLocation']['name'])

        #confirm if this is the Stave wanted
        if getYesOrNo('Is this the stave you are looking for? (insert \'y\' or \'n\')'):

            #user select which module position to assemble
            StaveFolder=MountingInfoInStaveFolder(stave_folder)
            StaveFolder.openInterface()

            #get a PD MODULE comp for each module position the user selected & assemble away!
            assembleModule(thisStave, StaveFolder, stave_folder)

            #check if STAVE is fully assembled


            INFO('finished assembling all selected modules')
            INFO('Exiting program.')
            print('have a great rest of your day')

        #did not find the STAVE wanted --> exit
        else:
            ERROR('did not find the right STAVE. Exiting program.')
            print('have a great rest of your day')
            exit()


if __name__ =='__main__':
    parser=argparse.ArgumentParser(description='Load A STAVE in the ITk PD')
    parser.add_argument('command',type=str,choices=['initiate','update'],help='initiate: register new STAVE and assemble modules; update: find STAVE and assemble more modules')
    parser.add_argument('--stave-folder',type=str, help='path to the stave folder(./US-Electrical-Prototype/) that has all calibrations')
    parser.add_argument('--institute',type=str, choices=['BU','BNL'],help='Brandeis/BNL')
    parser.add_argument('--core-type',type=str, choices=['SS','LS'],help='(required for initiate command) core type long/short strip')
    parser.add_argument('--core-side',type=str, choices=['A','C'],help='(required for initiate command) core side A/C')

    #parser.add_argument('--positions',type=str,help='enter module positions (ex. 2,3,4 or 2-4); enter \'all\' for all module 1-14')
    args=parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        INFO('Finished with error.')
        exit()
