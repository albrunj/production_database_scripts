#uploadModulePlacementAccuracy.py
#From the final survey directory, get the placement accuracy for all modules on one side of a stave
#attach the calibration file for the final survey
#written by Jiayi Chen, last update 4/3/2019
from __future__ import print_function #import python3 printer if python2 is used

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import numpy as np
import argparse
import os

# import ReadSurvey as RS
import surveyZachTodd as RS

# path=os.path.abspath(os.path.join('./../', os.pardir))
# sys.path.append(path)
# from utilities.databaseUtilities import commands
from itk_pdb.dbAccess import ITkPDSession
from LoadedStave_class import MountingInfoInStaveFolder, STAVE, getYesOrNo
from datetime import date

class MPAtest(object):
    def __init__(self,LOCALNAME=None,institution='BU',side="J",ITkPDSession=None):
        self.localname=LOCALNAME
        self.institution=institution
        self.stave_side=side #run number
        self.ITkPDSession=ITkPDSession
        self.stave_code,self.slotIDs=self.findStaveINFO()
        self.json=self.initiateSurvey()
        self.test_run_id=None

    def findStaveINFO(self):
        Stave=STAVE(LOCALNAME=self.localname,STAGE='assembly',ITkPDSession=self.ITkPDSession) #since day2 start with assembly stage
        return Stave.code,Stave.slotIDs


    #initialize the JSON (needs to be changed if the test format is changed) -- should try using CMD 'getTestType' or 'getTestTypeByCode'
    def initiateSurvey(self):
        DTO={
        "component": self.stave_code,
        "testType": "SURVEY-SUMMARY",
        "institution": self.institution,
        "runNumber":self.stave_side,
        "date": date.today().strftime("%d.%m.%Y"),
        "passed": False,
        "problems": False,
        "properties": {},
        "results":{"PASS":[],"FAIL-X":[],"FAIL-Y":[],"FAIL-XY":[]}}
        return DTO


    #fill in 'results' in the JSON
    def fillResults(self,dir=None):

        #check if properties if filled (only fill in once)
        fillFiducial=False

        #initiate test parameters
        Passed=True
        num_fail=0

        MountingInfo = MountingInfoInStaveFolder(dir).MountingInfo[self.stave_side]
        modules = [position for position in MountingInfo.keys()]

        CORNERS = 'ABCD'
        PLACEMENTS = {'X': [], 'Y': []}

        for module in modules:
            #open the module survey directory and find the module survey file at: 'ModulePlacement/13/Module_13.txt'
            path_to_cali = MountingInfo[module]['calibration_folder_path']
            infile=path_to_cali+'ModulePlacement/'+str(module)+'/'+"Module_"+str(module) +".txt"
            #print(infile)
            survey = RS.TheSurvey("Module"+str(module), "Stave8",infile)
            survey.Dump()
            positions,pass_fail=survey.GetFlags_database(tolerance=100.0)
            #print(x)
            #print(y)
            survey.PopulateHistograms(PLACEMENTS, survey.stages[-1], CORNERS)

            #fill fiducail property once (assume final survey uses the same fiducial)
            if not fillFiducial:
                for line in survey.lines:
                    if "FiducialMark" in line:
                        fiducial=line[line.find("=")+3:-3]
                        self.json["properties"]["FIDUCIAL"]=fiducial
                fillFiducial=True

            #initiate result {childrenproperties:***,value:{A:[x,y],B:[],C:[],D:[]}}
            result={}

            #find the slot_id for the MODULE
            slot=module
            if self.stave_side=='J':
                slot+=14
            #result["childParentRelation"]=self.slotIDs[slot]

            #use after bridge removal survey (but this should be changed, as we should upload Final Survey result)
            #if 'ABR' in survey.stages:

            #survey.DeltaXY already formated in the right way for database
            result["value"]=positions

            #fill in parameters (4 categories 'PASSED', 'FAIL-X','Y', 'X&Y')
            #fill in parameters (4 categories 'PASSED', 'FAIL-X','Y', 'X&Y'); find out which category this module falls into and fill in results

            if pass_fail['X'] and pass_fail['Y']:
                #self.json["results"]["PASS"].append(result)
                print("bhdjsk")
            else:
                Passed=False
                num_fail+=1
                #if not pass_fail['X'] and pass_fail['Y']:
                #    self.json["results"]["FAIL-X"].append(result)
                #elif not pass_fail['Y'] and pass_fail['X']:
            #        self.json["results"]["FAIL-Y"].append(result)
        #        else:
        #            self.json["results"]["FAIL-XY"].append(result)

        #loop over modules finished

        #fill in the rest of the properties
        self.json["passed"]=Passed
        #self.json["problem"]=not Passed
        #self.json["properties"]['FAILURE']=num_fail
        self.json["results"]['FAIL-NUM']=num_fail

        #fill in RMS in properties
        Delta_X,Delta_Y = PLACEMENTS['X'], PLACEMENTS['Y']
        self.json["results"]['RMS-X']=round(rms(Delta_X),1)
        self.json["results"]['RMS-Y']=round(rms(Delta_Y),1)
        #self.json["results"]['MIN-MAX-X']=[min(Delta_X),max(Delta_X)]
        #self.json["results"]['MIN-MAX-Y']=[min(Delta_Y),max(Delta_Y)]
        #self.json["results"]['DELTA-X']=Delta_X
        #self.json["results"]['DELTA-Y']=Delta_Y

    #upload JSON and the calibration file
    def uploadTest(self,directory):

        #upload and get the test run ID to attach calibration file
        self.test_run_id=self.ITkPDSession.doSomething(action='uploadTestRunResults',method='POST',data=self.json)['testRun']['id']

        #INFO('attaching the calibration file' + directory + 'CalibrationResults.ini')

        #upload attachment
        #fields = {  'data': ('CalibrationResults.ini', open(directory+'CalibrationResults.ini', 'rb')),
        #             'type': 'file',
        #             'testRun': self.test_run_id,
        #             'title': 'Calibration File', # Or you could give it a real title
        #             'description': 'sample description'  }
        #data = MultipartEncoder(fields = fields)
        #self.ITkPDSession.doSomething(action ='createTestRunAttachment', method = 'POST', data = data)


#calculate the RMS of an array
def rms(a):
    blah=0.
    for num in a:
        blah += num**2
    rms=np.sqrt(blah/float(len(a)))
    return rms



def main(args):
    print('')
    print('*************************************************************************')
    print('* *                                                                 *   *')
    print('*                            uploadMPA.py --JiayiChen                 *')
    print('* *                                                                 *   *')
    print('*************************************************************************')
    print('')


    directory=args.directory
    while not os.path.exists(directory):
        print('path (%s) not found' %directory)
        directory=input("Please enter the path to calibtration again:")
    if directory[-1]!='/':
        directory+='/'

    directory=args.directory #calibration file

    #check if directory exist
    while not os.path.exists(directory):
        print('path (%s) not found' %directory)
        directory=input("Please enter the path to calibtration again:")

    #needs directory string ends with a '/'
    if directory[-1]!='/':
        directory+='/'

    #get STAVE local name

    localname=input('please give the STAVE\'s local name:')

    #start a ITkPDsession
    session = ITkPDSession()
    session.authenticate()


    test=MPAtest(LOCALNAME=localname,side = "J",ITkPDSession=session)
    #upload final survay (which is supposed to have all module survey)
    #modu_positions=modu_positions=np.arange(2,14,1) #electrical stave 2-13
    test.fillResults(dir=directory)
    print('***Filled DTOin*****')
    print(test.json)
    if args.command=='upload':
        if getYesOrNo('Are you sure you want to upload the above test?(yes/no)'):
            test.uploadTest(directory)

    #if the command is to upload (not testing), upload!
    #if args.command=='upload':

        #confirm upload
        #getYesOrNo('Are you sure you want to upload the above test?(yes/no)')

        #needs the directory path to find the calibration file and upload the cali file too

        #test.uploadTest(directory)
        #print 'finished uploading'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='upload Module Placement Accuracy test to ITk PD')
    parser.add_argument('command',type=str,choices=['testing','upload'],help='testing: will show the json only; upload: will upload json to PD')
    parser.add_argument('--directory',type=str, help='directory that has the final survey results')
    args=parser.parse_args()
    try:
        main(args)

    except KeyboardInterrupt:
        print('')
        print('Exectution terminated.')
        print('Finished with error.')
        exit()
