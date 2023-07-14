#Load_a_STAVE_auto.py     -- automatically load a STAVE in the PD
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#created 5/17/2019
#last update 6/12/2019
from __future__ import print_function  # import python3 printer if python2 is used

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys

# sys.path.append('../')
from itk_pdb.databaseUtilities import ERROR, INFO, WARNING
from itk_pdb.dbAccess import ITkPDSession, dbAccessError
from LoadedStave_class import (
    STAVE,
    MODULE,
    MountingInfoInStaveFolder,
    CORE,
    ComponentNotFound,
    MultipleComponentsFound,
)
import requests


def assembleModule(stave,StaveFolder,stave_folder_path):

    stave_side  = StaveFolder.side
    MountingInfo= StaveFolder.MountingInfo
    positions   = StaveFolder.positions

    print('\n')
    print('-------------Assembly INFO--------------')

    for position in positions:
        Calibration_TimeStamp = MountingInfo[stave_side][position]['CALIBRATION']
        Loader_Names          = MountingInfo[stave_side][position]['ASSEMBLER']

        try:
            module=MODULE(stave_folder_path, position, stave_side, Calibration_TimeStamp, Loader_Names, ITkPDsession=stave.ITkPDsession)
        except ComponentNotFound:
            ERROR("No module was found using the IDs given in the CSV file, please fix the error")
            continue
        except MultipleComponentsFound:
            ERROR("More than one module was found using the IDs given in the CSV file, please fix the error")
            continue

        ###------fill in more properties--------###
        child_properties=module.childProperties

        #find the slot to be assembled
        if 'LHS' in module.stave_side:
            child_slot=stave.slotIDs[position-1]
        else:
            child_slot=stave.slotIDs[14+position-1]

        stave.addModule(module,child_slot,child_properties)
        INFO('Assembled MODULE at '+ stave_side + str(position))
        print('childProperties are:', child_properties)

    print('----------Assembly INFO end------------')
    print('\n')


def main(stave_folder,ITkPDSession):
    stave_localname = os.path.basename(stave_folder[:-1])
    try:
        thisStave=STAVE(LOCALNAME=stave_localname,assemblySite='BU',ITkPDsession=session) #since day2 start with assembly stage
        #get Info for this STAVE
        INFO("successfully found STAVE with local name" + stave_localname)

    except ComponentNotFound:
        #needs to be changed to read CORE id then use CORE side&type to register STAVE
        INFO("No STAVE was found using local name: "+ stave_localname)
        newCore=CORE(type='SS',side='A')
        thisStave.addCore(newCore)
        thisStave.registerSTAVE()
        INFO('Successfully registered new STAVE')

    except MultipleComponentsFound:
        WARNING("multiple STAVEs were found using local name: %s" %stave_localname)
        print("Please fix this error in the ITk PD!")
        INFO("exiting program...")
        sys.exit()

    print('\n')
    print("-----------STAVE INFO------------")
    print("local name: "+ thisStave.localname)
    print("stave side: "+ thisStave.side)
    print("stave type: "+ thisStave.type)
    print("---------STAVE INFO end----------")
    print('\n')

    INFO("Proceeding to assemble MODULEs...")
    StaveFolder=MountingInfoInStaveFolder(stave_folder)

    #iterate through the sides of a stave
    for one_side in StaveFolder.MountingInfo.keys():
        INFO("assembling MODULEs on side: " + one_side)
        positions = StaveFolder.MountingInfo[one_side].keys()
        StaveFolder.side = one_side
        StaveFolder.positions = positions
        assembleModule(thisStave, StaveFolder, stave_folder)



    thisStave.StaveINFO()
    if thisStave.isFullyAssembled == True:
        INFO("This STAVE is fully assembled")
    else:
        INFO("There are " + str(thisStave.assembledModules) + " MODULEs assembled on this STAVE")

    INFO('')



if __name__ =='__main__':
    import os

    #in the future, read path from path file
    directory = './'
    stave_folder='./AUTO/Test6-4-3/'
    #find last update stave folder

    #authenticate ITkPDSession (long term token needed)
    session = ITkPDSession()
    session.authenticate()
    try:
        main(stave_folder,session)
        INFO('Finished assembling all MODULEs in stave folder: '+ stave_folder)

    except (dbAccessError,requests.exceptions.HTTPError):
        ERROR("Finished with error, see dbAccess returned error map")
    #rename/move stave folder --> indicate STAVE fully assembled
    #os.rename(stave_folder,stave_folder+"_PD")
