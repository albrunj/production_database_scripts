#!/usr/bin/env python
#LoadedStave_class.py
        ##           -- class of STAVE, and all of its children comp: MODULEs, CORE, EOS
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#last update 7/15/2019
from __future__ import print_function #import python3 printer if python2 is used

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

# sys.path.append('../')
import os
import numpy as np
import surveyZachTodd as RS
from itk_pdb.databaseUtilities import INFO, PROMPT, WARNING
from requests_toolbelt.multipart.encoder import MultipartEncoder
# ComponentNotFound := component could not be identified in the ITkPD
class ComponentNotFound(Exception):
    pass

class MultipleComponentsFound(Exception):
    pass

class NoCalibrationFound(Exception):
    pass

##------------------------------------------------------------##

#########################----STAVE----####################################
class STAVE(object):

    """
    this class represent a STAVE in the process of module loading...
    """
    # a STAVE in the PD  <--> returned by registerSTAVE or StaveINFO
    def __init__(self, LOCALNAME=None, assemblySite='BNL', STAGE='Components Reception',ITkPDSession=None):

        """
        initiate STAVE

        :type LOCALNAME: string
        :param LOCALNAME: the local name of the STAVE to be registered or already registered in the database

        :type assemblySite: string
        :param assemblySite: the stave assembly site code in the PD (ex. BNL, BU, RAL...)

        :type STAGE: string
        :param STAGE: stage of the STAVE

        :type ITkPDSession: requests.Session
        :param ITkPDSession: dbAccess.ITkPDSession

        """

        self.component='STAVE'
        self.stave_type=None #from addCore
        #self.side=None #from addCore
        self.localname=LOCALNAME
        self.site=assemblySite
        self.code=None #get from registerSTAVE or StaveINFO
        self.stage=STAGE
        self.getComponentSTAVE = None

        #from childrenSlots()
        self.slotIDs=[]
        self.module_info=[]
        self.module_codes=[] #list of module codes, if MODULE assembled; if not assembled: None
        self.assembledModules=0
        self.isFullyAssembled = False

        #other children
        self.EoS={}
        self.core={}

        self.ITkPDSession=ITkPDSession

    #registerSTAVE called when 'initiate' command used
    def registerSTAVE(self):

        JSON={} #initiate DTOin for STAVE registration
        #fill in JSON
        JSON['institution']=self.site
        JSON['componentType']=self.component
        JSON['project']='S' #strip
        JSON['subproject']='SB' #strip barrel
        staveProperties={}
        #staveProperties['SIDE']=self.type
        staveProperties['LOCALNAME']=self.localname


        JSON['type']=self.stave_type
        JSON['properties']=staveProperties
        #finished filling in JSON

        new_stave=self.ITkPDSession.doSomething(action='registerComponent',method='POST',data=JSON)
        self.code=new_stave['component']['code'] #save STAVE component code

        #use component code to get the most complete STAVE info
        STAVE=self.ITkPDSession.doSomething(action='getComponent',method='GET',data={'component':self.code})
        self.getComponentSTAVE=STAVE
        self.childrenSlots(STAVE) #save slot id to assemble MODULEs in a desired order
        return STAVE

    #STAVEinfo called when 'update' command used
    def StaveINFO(self):

        #use local name to find STAVE in PD
        stave=FindComp(LOCALNAME=self.localname,comp_type=self.component,ITkPDSession=self.ITkPDSession)
        self.code = stave['code'] #save STAVE component code
        STAVE = self.ITkPDSession.doSomething(action='getComponent',method='GET',data={'component':self.code})
        self.getComponentSTAVE=STAVE
        self.stage=STAVE['currentStage']['name']
        self.stave_type=STAVE['type']['name']
        STAVE_properties=STAVE['properties']
        for property in STAVE_properties:
            if property['code']=='SIDE':
                self.side=property['value']

        self.childrenSlots(STAVE) #save slot id to assemble MODULEs in a desired order

        #check if STAVE is fully assembled
        if None not in self.module_codes:
            self.isFullyAssembled=True
            self.assembledModules=28

        #if not fully assembled, count how many modules are assembled
        else:
            for code in self.module_codes:
                if code!=None:
                    self.assembledModules+=1

        return STAVE

    #save slot id to assemble MODULEs in a desired order
    def childrenSlots(self,STAVE):
        children=STAVE['children']

        #loop over all children
        for child in children:

            #find modules in the children
            if child['componentType']['code']=='MODULE': #check if the slot is for module
                self.slotIDs.append(child['id'])

                #if slot is not empty --> check if properties correctly saved position
                if child['component']!=None:
                    properties=[]

                    #find SIDE and POSITION in properties
                    for property in child['properties']:
                        if property['code']=='SIDE':
                            side = property['value']
                        elif property['code']=='POSITION':
                            posi = property['value']
                        elif property['code']=='CALIBRATION':
                            cali = property['value']

                    #append module codes
                    self.module_codes.append(child['component']['code'])

                    #append to module_info
                    properties.append(side)
                    properties.append(posi)
                    properties.append(cali)
                    self.module_info.append(properties)

                #if slot is empty
                else:
                    self.module_codes.append(None)
                    self.module_info.append('empty')

    #fisrt step for registering a STAVE --> core determines Stave type (SS/LS) and side (A/C)
    def addCore(self, core):
        #in the future, input should be an ID to find core, read type and side from there
        self.stave_type=core.type+'-'+core.side
        #self.side=core.side
        self.core['name']=core.name
        #assemble core and stave

    def addModule(self,module,child_slot,child_properties): #add module according to its position on the stave
        #if is the first module assembled --> set stage to Module Loading
        if self.stage=='Components Reception':
            #setstage to assembly for this stave
            self.stage='Assembly'
            self.ITkPDSession.doSomething(action='setComponentStage',method='POST',data={'component':self.code,'stage':'MODULE_LOADING'})

        #assemble
        print(child_properties)
        self.ITkPDSession.doSomething(action='assembleComponentBySlot',method='POST',
            data={'parent':self.code,'child':module.code,'slot':child_slot,'properties':child_properties})

        ###----update module object for cross checking later (prevent assemble same module again)---##
        module.assembled=True

            ###------finished assembly this module--------###

    def uploadCalibrationFiles(self, calibration_folder_path,files):

        stave_side, cali_timestamp = readCalibrationFile(calibration_folder_path+"CalibrationResults.ini")

        for attachment in self.getComponentSTAVE["attachments"]:
            if attachment["description"] == cali_timestamp:
                INFO("calibration files previously uploaded to database! skipping")
                return True

        INFO("calibration files to be uploaded:")
        print(files)
        invalidFilePath=[]
        for file in files:
            try:

                fields = {  'data': (file, open(calibration_folder_path+file, 'rb')),
                             'type': 'file',
                             'component': self.code,
                             'title': file+"-"+stave_side,
                             'description': cali_timestamp  }
            except IOError:
                invalidFilePath.append(calibration_folder_path+file)
                continue

            data = MultipartEncoder(fields = fields)
            self.ITkPDSession.doSomething(action ='createComponentAttachment', method = 'POST', data = data)
        return invalidFilePath

    def disassembleChild(self,child_code):

        self.ITkPDSession.doSomething(action='disassembleComponent',method='POST',
            data={'parent':self.code,'child':child_code})

#read FileToUploadPerCalibration to find which calibration file to upload
def getCalibrationFileList(fileList="FileToUploadPerCalibration.txt"):

    input = open(fileList,"r")
    lines = input.readlines()
    input.close()
    files=[]
    for line in lines:
        file=line.rstrip().strip('\n')
        if file != None and file != "" and "#" not in file:
            files.append(file)

    files.append("CalibrationResults.ini")
    return files

#########################----STAVE end----####################################

##------------------------------------------------------------##

############Module Related Functions BEGIN!######################

#Module Object
class MODULE(object):

    def __init__(self, stave_folder, position=None, stave_side=None, Calibration_TimeStamp=None, Loader_Names=None,
                    Glue_Time=None, Glue_Batch_ID=None, ITkPDSession=None):
        self.component    = 'MODULE'
        self.directory    = stave_folder #stave directory
        self.code         = None
        self.assembled    = False
        self.ITkPDSession = ITkPDSession
        self.stave_side   = stave_side
        self.position     = position
        self.id           = None   # RFID

        #fill in children properties
        self.childProperties={}
        self.childProperties['SIDE']        = stave_side
        self.childProperties['POSITION']    = str(position)
        self.childProperties['CALIBRATION'] = Calibration_TimeStamp
        self.childProperties['ASSEMBLER']   = Loader_Names
        self.childProperties['GLUE-TIME']   = Glue_Time
        self.childProperties['GLUE-ID']     = Glue_Batch_ID

        #get MODULE code in database
        self.findMODULE()

    #find module in database using the local name from the excel
    def findMODULE(self):
        self.getRFIDs()
        module = FindComp(LOCALNAME=self.id,comp_type=self.component,ITkPDSession=self.ITkPDSession)
        self.code =module['code']
        return module

    #read the CSV file of the modules' fake 'RFID'
    #2 csv for the two sides of Stave 'LmodulesID.csv'& 'JmodulesID.csv'
    #-- assuming in the future, after modules are already glued on the core, then scan the RFID
    #--> each module position is associated with a RFID
    def getRFIDs(self):

        #read csv
        csv = np.genfromtxt(self.directory + 'modulesID-'+ self.stave_side + '.csv',delimiter=",",dtype=str)

        IDs=csv[1:,0]       #first column is the RFIDs
        Positions=csv[1:,1] #second column is the module position 1-14

        #find the RFID of the module at this position
        self.id = IDs[Positions.tolist().index(str(self.position))]

### find which modules are in which calibration folders ###
#function hierarchy: 'Calibrations' calls 'modulesInCali'
#modulesInCali--> return module positions loaded in this calibration
class MountingInfoInStaveFolder(object):

    def __init__(self,stave_folder, STAVE_childrenInfo=None):
        self.stave_folder = stave_folder
        self.STAVE_childrenInfo = STAVE_childrenInfo
        self.MountingInfo = self.Calibrations()
        self.side = None
        self.positions = None

    #interface to get the position user what to assemble MODULE with STAVE in the PD
    def openInterface(self):

        #get stave side first
        #if stave folder has both sides
        if len(list(self.MountingInfo.keys())) >1:
            while True:
                PROMPT('Give the stave side you want to assemble (J/L):')
                side = input()
                if side in self.MountingInfo.keys():
                    break
                else:
                    WARNING('invlid input!')
                    continue

        #if in stave folder only one side has been loaded
        else:
            side=list(self.MountingInfo.keys())[0]

        #get positions next
        while True:
            INFO('the positions you can choose are')
            print(list(self.MountingInfo[side].keys()))
            PROMPT('Please give the positions in one of the formats: 1,2,5 OR 2-5 OR all:')
            positions = input()

            #put the given positions by the user into array
            if positions!='all':

                #if given ex. 2-7 change to --> [2,3,4,5,6,7]
                if '-' in positions:
                    ind=positions.index('-')
                    positions=np.arange(int(positions[:ind]),int(positions[ind+1:])+1,1)

                #if given 1,4,6, change to --> [1,4,6]
                else:
                    positions=[int(x) for x in positions.split(",")]


                #check if the chosen positions are allowed
                for position in positions:

                    if position in self.MountingInfo[side]:

                        #finished checking the last one position, return side and positions
                        if position == positions[-1]:
                            self.side, self.positions = side, positions
                            return None

                        #continue with other selected positions
                        else:
                            continue

                    #found selected positions not allowed, reenter!
                    else:
                        WARNING('Wrong positions, please try again')
                        break

                #if all positions are allowed
                continue


            #if user want to assemble all
            else:
                positions = self.MountingInfo[side].keys()
                self.side, self.positions = side, positions
                return None


    def modulesInCali(self,calibration_folder):
        dir = calibration_folder + 'ModulePlacement/'
        module_posi=[]

        total=len([file for file in os.listdir(dir)])

        #module survey file labeled from 0 - total-1
        for i in range(0,total):
            checkFolder=dir+str(i)+'/'
            Survey= checkFolder+'/Module_'+str(i)+'.txt'
            input=open(Survey,"r")
            lines=input.readlines()
            input.close()

            #survey is conducted
            if len(lines) > 26:
                #INFO('module %i is loaded using calibration in %s' %(i,dir))
                module_posi.append(i)

        return module_posi


    #iterate through a stave folder and find which module is in which calibrations folder
    def Calibrations(self,folderToIgnore = "./CalibrationFoldersToIgnore.txt"):

        dir=self.stave_folder #rename

        input = open(folderToIgnore,"r")
        lines = input.readlines()
        input.close()
        words=[]
        for line in lines:
            word=line.rstrip().strip('\n')
            if word != None and word != "" and "#" not in word:
                words.append(word)

        calibrations=[] #initiate array for paths to each calibration folder

        for file in os.listdir(dir):
            if os.path.isdir(dir+file):
            #file is a directory and it's not the final survey directory

            #if (os.path.isdir(dir+file) and os.path.basename(dir+file)!='FinalSurvey'
            #    and "Recali" not in os.path.basename(dir+file) and "recali" not in os.path.basename(dir+file)):
                for word in words:
                    if word in os.path.basename(dir+file):
                        INFO("ignored calibration folder: "+file)
                        break
                    else:
                        calibrations.append(dir+file+'/') # all calibrations folders


        if len(calibrations) == 0 :
            raise NoCalibrationFound
            #ERROR('No calibration folders found in this stave folder')
            #INFO('exiting program...')
            #exit()

        #INFO('there are %i calibration folder' %len(calibrations))
        ModuleMountingInfo={} #initiate dict for modules

        #initiate list of empty calibration folder
        empty_calibrations=[]

        #iterate through all calibration folders for this stave
        for calibration in calibrations:

            try:
                module_posi=self.modulesInCali(calibration)

            #if folder doesn't have ModulePlacement, pass this folder
            except FileNotFoundError:
                empty_calibrations.append(calibration)

                #if all folders are empty, raise no Calibration was found
                if calibration == calibrations[-1] and empty_calibrations == calibrations:
                    raise NoCalibrationFound
                continue

            if module_posi != []:

                #find calibration timestamp in calibration file
                stave_side, cali_timestamp = readCalibrationFile(calibration+'CalibrationResults.ini')

                #ModuleMountingInfo divided into sub-dict: 'L' + 'J'
                if stave_side not in ModuleMountingInfo.keys():
                    ModuleMountingInfo[stave_side]={}

                for position in module_posi:

                    surveyFile = calibration+'ModulePlacement/'+str(position)+'/'+"Module_"+str(position) +".txt"
                    survey = RS.TheSurvey("Module"+str(position), "this stave",surveyFile)
                    stages = [stage for stage in survey.dates.keys()]
                    glue_timestamp = survey.dates
                    assembler_name = survey.assembler_name
                    glue_batch_ID  = survey.GlueBatchID
                    #if module after glue info is recorded in this calibration, meaning the module is placed using this calibration
                    for stage in stages:
                        if "ag" in stage.strip().strip('_').lower() or "after glu" in stage.strip().strip('_').lower()or "afterglu" in stage.strip().strip('_').lower():
                            ModuleMountingInfo[stave_side][position]={}
                            ModuleMountingInfo[stave_side][position]['GLUE-TIME']  = glue_timestamp[stage]
                            ModuleMountingInfo[stave_side][position]['ASSEMBLER']  = assembler_name #'(*assembler name)'
                            ModuleMountingInfo[stave_side][position]['GLUE-ID']    = glue_batch_ID #'(*assembler name)'
                            ModuleMountingInfo[stave_side][position]['CALIBRATION']= cali_timestamp
                            ModuleMountingInfo[stave_side][position]['calibration_folder_path'] = calibration
                            break


        return ModuleMountingInfo

def readCalibrationFile(pathToCalibration):
    input=open(pathToCalibration,"r")
    lines=input.readlines()
    input.close()

    for line in lines:
        if 'Orientation' in line:
            ind=line.index('Side-')+5
            stave_side=line[ind:-1].strip().strip('\"').strip("-").strip("\'")
            stave_side=stave_side.upper()

        if 'Date =' in line:
            ind=line.index('=')+1
            cali_timestamp=line[ind:-1].strip().strip('\"').strip("\'")
            #if 'EST' not in line:
                #cali_timestamp+=' EST' #time zone, needs to be changed for RAL
        if 'DateFormat' in line:
            ind=line.index('=')+1
            cali_timestamp+=" ("+line[ind:-1].strip().strip('\"').strip("\'")+")"


    return stave_side, cali_timestamp

############Module Related Functions END!######################

##------------------------------------------------------------##

############Other Children of STAVE#########################
class CORE(object):
    def __init__(self,name='coreName',type='LS',side='A'):
        self.component='CORE'
        #self.id=ID
        self.code=None
        self.name=name
        self.side=side
        self.type=type

#EOS object
class EoS(object):
    def __init__(self,ID):
        self.component='EoS'
        self.code=None
        self.id=ID

############Other Children of STAVE END#########################


############   General Functions  ###############

#return DTOout of 'listComponents'
# FindComp(args)['code'] return the component code
def FindComp(LOCALNAME=None,comp_type=None,ITkPDSession=None):

    #needs either Local Name or ID to find the component type
    ID = LOCALNAME

    #find component

    property_filter = [{'code': 'LOCALNAME', 'operator': '=', 'value': ID}, {'code': 'LOCAL_NAME', 'operator': '=', 'value': ID},
                        {'code': 'RFID', 'operator': '=', 'value': ID},{'code': 'ID', 'operator': '=', 'value': ID}]
    component_list=ITkPDSession.doSomething(action='listComponentsByProperty',method='POST',data={'project':'S',
                                        'componentType':comp_type,'propertyFilter': property_filter})

    #if found only one component
    if len(component_list)==1:
        return component_list[0]
    elif len(component_list)==0:
        raise ComponentNotFound
    else:
        INFO("local name: "+ID)
        raise MultipleComponentsFound

#from Matth Basso's registerComponent.py
def getYesOrNo(prompt):
    print(prompt)
    while True:
        # Get our input
        response = input().strip()
        # Skip empty inputs
        if response == '':
            continue
        # If yes, return True
        elif response in ['y', 'Y', 'yes', 'Yes', 'YES', '1','true','True']:
            return True
        # If no, return False
        elif response in ['n', 'N', 'no', 'No', 'NO', '0','false','False']:
            return False
        # Else the input is invalid and ask again
        else:
            del response
            print('Invalid input. Please enter \'y/Y\', or \'n/N\':')
            continue

############   General Functions END  ###############
