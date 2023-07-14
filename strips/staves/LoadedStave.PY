
#LoadedStave.PY -- initiate a STAVE component in database
        ##      -- or update a current STAVE component by assemble more modules
       ##       -- need args: directory to stave file + positions to assemble
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#last update 3/21/2019

from __future__ import print_function #import python3 printer if python2 is used

import  os,sys
#sys.path.append('../') #doesn't work out for python3.6
path=os.path.abspath(os.path.join('./../', os.pardir))
sys.path.append(path)
import argparse, json, time


import numpy as np
import ReadSurvey as RS
from utilities.databaseUtilities import commands
from utilities.databaseUtilities import Colours, INFO, PROMPT, WARNING, ERROR, STATUS
from utilities.dbAccess import ITkPDSession


class STAVE(object):
    def __init__(self, LOCALNAME=None, dir='./', assemblySite='BNL', STAGE='reception',PDsession=None):
        self.component='STAVE'
        self.directory=dir
        self.type=None #from addCore
        self.side=None #from addCore
        self.localname=LOCALNAME
        self.site=assemblySite
        self.code=None #get from registerSTAVE or StaveINFO
        self.stage=STAGE
        self.modules={}#from addModule
        self.slotIDs=[]
        self.EoS={}
        self.core={}
        self.PDsession=PDsession

    #registerSTAVE called when 'initiate' command used
    def registerSTAVE(self):

        JSON={} #initiate DTOin for STAVE registration
        #fill in JSON
        JSON['institution']=self.site
        JSON['componentType']=self.component
        JSON['project']='S' #strip
        JSON['subproject']='SB' #strip barrel
        staveProperties={}
        staveProperties['SIDE']=self.type
        staveProperties['LOCALNAME']=self.localname

        #need to self.addCore first, core determines Stave type (SS/LS) and side (A/C)
        if self.type=='LS' or self.type =='Long': ##uncertain how the type is gonna be called for core yet
            type='LS'

        else:
            type='SS'

        JSON['type']=type
        JSON['properties']=staveProperties
        #finished filling in JSON
        print(JSON)

        new_stave=self.PDsession.doSomething(action='registerComponent',method='POST',data=JSON)
        print('finished registering new STAVE')

        #save a local json of
        #with open(self.directory+'STAVEinfo.json','w') as outfile:
        #    json.dump(new_stave,outfile)


        self.code=new_stave['component']['code'] #save STAVE component code

        #use component code to get the most complete STAVE info
        STAVE=self.PDsession.doSomething(action='getComponent',method='GET',data={'component':self.code})
        self.childrenSlots(STAVE) #save slot id to assemble MODULEs in a desired order
        return STAVE

    #STAVEinfo called when 'update' command used
    def StaveINFO(self):

        #use local name to find STAVE in PD
        stave=FindComp(LOCALNAME=self.localname,comp_type=self.component,PDsession=self.PDsession)
        self.code = stave['code'] #save STAVE component code
        STAVE = self.PDsession.doSomething(action='getComponent',method='GET',data={'component':self.code})

        self.type=STAVE['type']['name']
        STAVE_properties=STAVE['properties']
        for property in STAVE_properties:
            if property['code']=='SIDE':
                self.side=property['value']

        #a good cross check whether this STAVE is the one we are looking for
        print('Stave type:', self.type)
        print('Stave side:', self.side)

        self.childrenSlots(STAVE) #save slot id to assemble MODULEs in a desired order
        return STAVE

    #save slot id to assemble MODULEs in a desired order
    def childrenSlots(self,STAVE):
        children=STAVE['children']
        slotid=[]
        for component in children:
            if component['componentType']['code']=='MODULE': #check if the slot is for module
                id=component['id']
                slotid.append(id)
        self.slotIDs=slotid

    #fisrt step for registering a STAVE --> core determines Stave type (SS/LS) and side (A/C)
    def addCore(self, core):
        #in the future, input should be an ID to find core, read type and side from there
        self.type=core.type
        self.side=core.side
        self.core['name']=core.name
        #assemble core and stave

    def addModule(self,module): #add module according to its position on the stave
        dir=self.directory
        position=module.position
        if self.stage=='reception':
            #setstage to assembly for this stave
            self.stage='assembly'
            self.PDsession.doSomething(action='setComponentStage',method='POST',data={'component':self.code,'stage':'MODULE_LOADING'})
            print('changed STAVE stage to be assembly!')

        #----find module code and fill in properties from cali file-----#
        module.readCSV(dir) #read modulesID.csv to update local ID (RFID/LOCALNAME) according to position
        module_code=module.code #code is updated as soon as local ID is found
        module.Calibration(dir) #update calibration timestamp and SIDE
        #module.Survey() #update survey timestamp

        #if module.pass_reception==False:
            #print 'module did not pass tests at reception! Check for defects!'

        ###------fill in more properties--------###
        child_properties=module.childProperties
        child_properties['SITE']=self.site
        if 'LHS' in self.side:
            child_slot=self.slotIDs[position-1]
        else:
            child_slot=self.slotIDs[14+position-1]
        #if self.code==None:
            #self.code=FindComp(LOCALNAME=self.localname,comp_type=self.component)['code']
        #print 'getting ready to assemble...'
        #print 'assemble Stave:',self.code
        #print 'and module:', module_code
        print('childProperties are:', child_properties)
        print('about to assemble module at position', position)
        if getYesOrNo('are you sure you want to assemble? (inset \'y\' or\'n\')'):
            #commands['assembleComponent'].run(parent=self.code,child=module_code,properties=child_properties)
            self.PDsession.doSomething(action='assembleComponentBySlot',method='POST',
                data={'parent':self.code,'child':module_code,'slot':child_slot,'properties':child_properties})
            print('assembled successfully')


            ###----update module object for cross checking later (prevent assemble same module again)---##
            module.stage='assembly'
            module.assembled=True
            #commands['assembleComponent'].run(parent = self.code , child=module['code'] , properties=)
            #print self.modules
            ###------finished assembly this module--------###
        else:
            print('Canceled module %i assembly' % position)
        ##---save assembled module information locally at this stave object--------##

#Module Object
class MODULE(object):

    def __init__(self, name, ID=None, position=None, STAGE='reception',PDsession=None):
        self.component='MODULE'
        self.name=name
        self.id=ID #assume RFID; but test with local name
        self.code=None
        self.position=position #1-14, should be given by the user
        self.directory=None #this module's calibration directory path
        self.stage=STAGE
        self.pass_reception = False
        self.assembled = False
        self.childProperties={}
        self.PDsession=PDsession

    #find module in database using the local name from the excel
    def findMODULE(self):
        module = FindComp(LOCALNAME=self.id,comp_type=self.component,PDsession=self.PDsession)
        self.code=module['code']
        return module

    #read the CSV file of the modules' fake 'RFID'
    #-- assuming in the future, after modules are already glued on the core, then scan the RFID --> each module position is associated with a RFID
    def readCSV(self,dir):
        #read csv
        csv = np.genfromtxt(dir+'modulesID.csv',delimiter=",",dtype=str)

        IDs=csv[1:,0] #first column is the RFIDs
        Positions=csv[1:,1] #second column is the module position 1-14

        #if module position given, find the RFID of the module at this position
        if self.position!=None:
            self.id=IDs[Positions.tolist().index(str(self.position))]
            self.findMODULE() #find module

        #if RFID is given, find the module position for this RFID
        elif self.id!=None:
            self.position=Positions[IDs.tolist().index(str(self.id))]

    #find out the module is assembled using which calibration
    def modulesInCali(self,dir):
        import os
        dir += 'ModulePlacement/'
        module_num=[]

        total=len([file for file in os.listdir(dir)])
        for i in range(1,total+1):
            checkFolder=dir+str(i)+'/'
            Survey= checkFolder+'/Module_'+str(i)+'.txt'
            input=open(Survey,"r")
            lines=input.readlines()
            input.close()
            if len(lines) > 26:
                #print('module %i is loaded using calibration in %s' %(i,dir))
                module_num.append(i)
        if len(module_num)==0:
            print('no module loading in this file; only a testing calibration')
        return module_num

    #find out which calibration directory has the info to module at a certain position
    def Calibration(self,dir):
        calibrations=[] #paths to each calibration folder

        for file in os.listdir(dir):
            if os.path.isdir(dir+file):
                calibrations.append(dir+file+'/') # all calibrations folders
        print('there are %i calibrations' %len(calibrations))
        cali_mod={}
        #self.childProperties['CALIBRATION']=None
        self.childProperties['SIDE']=None
        self.childProperties['POSITION']=str(self.position) #must be string
        for calibration in calibrations:
            module_num=self.modulesInCali(calibration)#array of the modules' POSITIONS in this calibration
            if self.position in module_num:
                self.directory=calibration
                print('module at position %i is in calibration:%s' %(self.position,calibration))
                #find properties in calibration file
                input=open(calibration+'CalibrationResults.ini',"r")
                lines=input.readlines()
                input.close()
                for line in lines:
                    if 'StaveOrientation' in line:
                        ind=line.index('=')+3
                        self.childProperties['SIDE']=line[ind:-3]
                    if 'Date' in line:
                        ind=line.index('=')+3
                        cali_timestamp=line[ind:-3]
                        if 'EST' not in line:
                            cali_timestamp+=' EST'
                        self.childProperties['CALIBRATION']=cali_timestamp
                print('updated Calibration timestamp and SIDE for module', self.name)
                return calibration
        if self.childProperties['CALIBRATION']==None:
            print('no module at this position; or calibration is saved in a different directory')
            print('please check the position of the module you want to assemble')
            print('exiting LoadedStave.PY')
            exit()

    def Survey(self):
        dir=self.directory+"ModulePlacement/"+str(self.position)+"/"
        survey=RS.TheSurveys("Module"+str(self.position),"Module_"+str(self.position)+".txt",dir)
        print(survey.timestamps)
        if 'AG' in survey.GetAllTime().keys():
            GlueTime=survey.GetAllTime()['AG']
            if 'EST' not in GlueTime:
                GlueTime+=' EST'
            self.childProperties['SURVEY']=GlueTime
            return GlueTime
        else:
            print('no After Glue timestamp, left survey timestamp in child properties blank...')

class CORE(object):
    def __init__(self,name='coreName',type='LS',side='A'):
        self.component='CORE'
        #self.id=ID
        self.name=name
        self.side=side
        self.type=type

#EOS object
class EoS(object):
    def __init__(self,ID):
        self.component='EoS'
        self.id=ID

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

#return DTOout of 'listComponents'
# FindComp(args)['code'] return the component code
def FindComp(LOCALNAME=None, RFID=None,comp_type=None,PDsession=None):

    #needs either Local Name or ID to find the component type
    if LOCALNAME==None and RFID==None:
        PROMPT("Please insert a local name or RFID:")
        ID=input()
        while ID==None:
            WARNING("Invalid input. Please insert a local name or RFID:")
            ID=input()
    elif LOCALNAME!=None:
        ID = LOCALNAME
    elif RFID!=None:
        ID = RFID

    #need component type to find component
    if comp_type==None:
        PROMPT("Please insert the component type (STAVE/MODULE/EOS):")
        comp_type=input()
        while comp_type==None:
            WARNING("Invalid input. Please insert component type (STAVE/MODULE/EOS):")
            comp_type=input()

    #need a ITkPD sesion
    if PDsession==None:
        PDsession=ITkPDSession()
        PDsession.authenticate()

    #find component
    while True:
        try:
            property_filter = [{'code': 'LOCALNAME', 'operator': '=', 'value': ID}, {'code': 'LOCAL_NAME', 'operator': '=', 'value': ID},
                                {'code': 'RFID', 'operator': '=', 'value': ID},{'code': 'ID', 'operator': '=', 'value': ID}]
            component_list=PDsession.doSomething(action='listComponentsByProperty',method='POST',data={'project':'S',
                                                'componentType':comp_type,'propertyFilter': property_filter})
            component=component_list[0]

            #if found only one component
            if len(component_list)==1:
                return component



    #need a ITkPD sesion
    if PDsession==None:
        PDsession=ITkPDSession()
        PDsession.authenticate()

    #find component
    while True:
        try:
            property_filter = [{'code': 'LOCALNAME', 'operator': '=', 'value': ID}, {'code': 'LOCAL_NAME', 'operator': '=', 'value': ID},
                                {'code': 'RFID', 'operator': '=', 'value': ID},{'code': 'ID', 'operator': '=', 'value': ID}]
            component_list=PDsession.doSomething(action='listComponentsByProperty',method='POST',data={'project':'S',
                                                'componentType':comp_type,'propertyFilter': property_filter})
            component=component_list[0]

            #if found only one component
            if len(component_list)==1:
                return component


        #if no component found, keep asking for correct local name till found at least one (exit by keyboard error, ex. ^C)
        except IndexError:
            ERROR('No %s was found using ID: %s'%(comp_type, ID))
            PROMPT("Please reenter the ID for this %s:" %comp_type)
            ID=input()

        #in the case PD has multiple components with the same Local Name
        if len(component_list)>1:
            INFO("found more than 1 %s with ID %s" %(comp_type,ID))
            for ind, component in enumerate(component_list):
                print(ind+1,'.   type:',component['type']['name'], ',  institution:',component['institution']['name'],',  current localtion:',component['currentLocation']['name'])
            while True:
                try:
                    PROMPT('please give the index of the component:')
                    i=input()
                    i=int(i.strip())
                    component = component_list[i-1]
                    return component
                except IndexError:
                    ERROR('Invalid index, try again')

##main function##
def main(args):
    print('')
    print('*************************************************************************')
    print('* *                                                                 *   *')
    print('*                            LoadedStave.py --JiayiChen                 *')
    print('* *                                                                 *   *')
    print('*************************************************************************')
    print('')

    #stave file
    directory=args.directory

    #check if path exists
    while not os.path.exists(directory):
        print('calibration path (%s) not found' %directory)
        directory=input("Please enter the path to calibtration again:")

    #path has to end with '/'
    if directory[-1]!='/':
        directory+='/'

    #put the given positions by the user into array
    if args.positions!='all':

        #if given ex. 2-7 change to --> [2,3,4,5,6,7]
        if '-' in args.positions:
            ind=args.positions.index('-')
            positions=np.arange(int(args.positions[:ind]),int(args.positions[ind+1:])+1,1)
            #print(positions)

        #if given 1,4,6, change to --> [1,4,6]
        else:
            positions=[int(x) for x in args.positions.split(",")]

        #check if module position is allowed (1-14); if invalid, exit program
        if max(positions)>14 or min(positions)<1:
            print('Invalid module position. Position has to be in range of 1-14.')
            print('exiting LoadedStave.PY ...')
            exit()

    #if user want to assemble all
    else:
        positions=np.arange(1,15,1)

    #initiate a ITkPD session
    session = ITkPDSession()
    session.authenticate()

    #initiate STAVE in database
    if args.command=='initiate':
        print('Welcome to ITk PD STAVE assembly DAY1!')

        #need to give a local name as the identifier at the test stage of ITk PD
        localname=input('please give the new STAVE a local name: ')

        #initiate a fake 'CORE' object, as core determines stave type and stave side
        newCore=CORE(type='SS',side='A')

        #initiate a new STAVE
        newStave=STAVE(LOCALNAME=localname,dir=directory,PDsession=session) #default stage reception

        #assemble the fake 'CORE'
        newStave.addCore(newCore)

        #have the local name + stave type + stave side -->register
        newStave.registerSTAVE()

        for position in positions:
            #initiate a new MODULE object
            module=MODULE('Module'+str(position), position=position,PDsession=session)

            #assemble MODULE with STAVE
            newStave.addModule(module)

    #update a STAVE in the PD
    if args.command=='update':

        print('Welcome back to ITk PD STAVE assembly!!')

        #use local name as the identifier to find the STAVE
        localname=input('please give the stave local name to find this STAVE: ')
        thisStave=STAVE(LOCALNAME=localname,dir=directory,STAGE='assembly',PDsession=session) #since day2 start with assembly stage

        #get Info for this STAVE
        component=thisStave.StaveINFO()

        #print STAVE info
        print('Found the following stave using local name',localname)
        print('type(LS/SS):',component['type']['name'])
        print('institution:',component['institution']['name'])
        print('current localtion:',component['currentLocation']['name'])

        #confirm if this is the Stave wanted
        if getYesOrNo('Is this the stave you are looking for? (insert \'y\' or \'n\')'):

            for position in positions:

                #initiate a new MODULE object
                module=MODULE('Module'+str(position), position=position,PDsession=session)

                #assemble MODULE with STAVE
                thisStave.addModule(module)

        #did not find the STAVE wanted --> exit
        else:
            print('Wrong STAVE. Exiting program.')
            exit()


if __name__ =='__main__':
    parser=argparse.ArgumentParser(description='Load A STAVE in the ITk PD')
    parser.add_argument('command',type=str,choices=['initiate','update'],help='initiate: register new STAVE and assemble modules; update: find STAVE and assemble more modules')
    parser.add_argument('--directory',type=str, help='path to the stave folder(./Calibrations/)')
    parser.add_argument('--positions',type=str,help='enter module positions (ex. 2,3,4 or 2-4); enter \'all\' for all module 1-14')
    args=parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        print('')
        print('Exectution terminated.')
        print('Finished with error.')
        exit()
