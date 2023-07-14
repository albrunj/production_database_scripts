#!/usr/bin/env python
# SyncSTAVE_GUI.py
# written by Jiayi Chen
# created 05/17/2019
# last update: 7/15/2019

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys, os
#sys.path.append(os.path.abspath('../'))
try:
    from PyQt5.QtWidgets import (
        QWidget,
        QGridLayout,
        QPushButton,
        QMessageBox,
        QMainWindow,
        QStackedWidget,
    )
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt
except ImportError:
    print('ERROR  : Python module \'PyQt5\' is not installed.')
    print('INFO   : To install, please type \'sudo apt-get install python-pyqt5\' for Python 2.')
    print('INFO   : For Python 3, type \'sudo apt-get install python3-pyqt5\'.')
    print('STATUS : Finished with error -- exitting!')
    sys.exit(1)
try:
    from requests.exceptions import RequestException
except ImportError:
    print('ERROR  : Python module \'requests\' is not installed.')
    print('INFO   : To install, please type \'sudo apt-get install python-requests\' for Python 2.')
    print('INFO   : For Python 3, type \'sudo apt-get install python3-requests\'.')
    print('STATUS : Finished with error -- exitting!')
    sys.exit(1)
from itk_pdb.ITkPDLoginGui import ITkPDLoginGui
from itk_pdb.dbAccess import ITkPDSession
from functools import wraps
from STAVEstatus_GUI import STAVEStatus as STAVE_status
from local_staveStatus_GUI import staveStatus
from LoadedStave_class import (
    MODULE,
    ComponentNotFound,
    MultipleComponentsFound,
    getCalibrationFileList,
)


def tip_decorate(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        args = list(args)
        args[1] = '<span style = \"background-color: black; color: white; font: normal; font-size: 12pt\">' + args[1] + '</span>'
        func(*args, **kwargs)
    return func_wrapper

QPushButton.setToolTip = tip_decorate(QPushButton.setToolTip)

#########################################
# ++++++++++++++ GLOBALS ++++++++++++++ #
#########################################
_DEBUG                 = True
_DEBUG_DEPTH           = 0
#########################################
# +++++++++++++++++++++++++++++++++++++ #
#########################################

def DEBUG(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if _DEBUG:
            global _DEBUG_DEPTH
            print(_DEBUG_DEPTH * ' ' + 'DEBUG : entering: %s.%s' % (args[0].__class__.__name__, func.__name__))
            _DEBUG_DEPTH += 1
            return_value = func(*args, **kwargs)
            _DEBUG_DEPTH -= 1
            print(_DEBUG_DEPTH * ' ' + 'DEBUG :  exiting: %s.%s' % (args[0].__class__.__name__, func.__name__))
            return return_value
        else:
            return func(*args, **kwargs)
    return func_wrapper



class SyncSTAVE_stave(QMainWindow):

    @DEBUG
    def __init__(self, parent=None, ITkPDSession=None):
        super(SyncSTAVE_stave,self).__init__(parent)
        self.parent         =  parent
        self.ITkPDSession   =  ITkPDSession
        self.title = 'ITkPD --- upload assembly info for a STAVE'
        #self.setGeometry(100,100,2500,1300)
        self.setWindowIcon(QIcon('../media/ATLAS-Logo-Square-B&W-RGB.png'))
        self.STAVE_status = STAVE_status(self,self.ITkPDSession)
        self.staveStatus = staveStatus(self,self.ITkPDSession)

        self.initMainUI()

    def __assembleModule(self):

        #find stave with this folder (in case the right panel has the search history of a different STAVE)
        self.__confirm_find_stave_clicked()

        #STAVE not registered yet
        if self.STAVE_status.isRegistered == False:
            if self.staveStatus.isRegistered == False:
                QMessageBox.warning(self, 'Warning', 'Please register the stave first')
                return None

        #if didn't select any modules
        if self.staveStatus.selected_position.text() == "" or self.staveStatus.selected_position.text() ==None:
            QMessageBox.warning(self, 'Warning', 'Please select a module first')
            return None

        #if insert non-integer
        try:
            positions = [int(x) for x in self.staveStatus.selected_position.text().split(',')]
        except ValueError:
            QMessageBox.warning(self, 'Warning', 'Invalid input. Please input \',\' deliminated integers only.')
            return None

        #if selected position is not allowed (not assembled)
        corrected_positions=[]
        for position in positions:
            if position in self.staveStatus.selectable_positions:
                corrected_positions.append(position)

        if corrected_positions==[]:
            QMessageBox.warning(self, 'Warning', 'Please select an assembled module positions to upload')
            return None

        MountingInfo = self.staveStatus.MountingInfo
        stave_folder_path = self.staveStatus.stave_folder
        stave_side = self.staveStatus.stave_side
        stave = self.STAVE_status.Stave

        calibration_folder_path = []
        assembled_positions=[]

        #iterate throu all selected modules
        for position in positions:
            position=int(position)
            Calibration_TimeStamp = MountingInfo[stave_side][position]['CALIBRATION']
            Loader_Names          = MountingInfo[stave_side][position]['ASSEMBLER']
            cali_path = MountingInfo[stave_side][position]['calibration_folder_path']
            Glue_Time = MountingInfo[stave_side][position]['GLUE-TIME']
            Glue_Batch_ID = MountingInfo[stave_side][position]['GLUE-ID']

            #this is for uploading calibration
            if cali_path not in calibration_folder_path:
                calibration_folder_path.append(cali_path)

            #if "upload only calibration file button" not checked, assemble modules
            if self.staveStatus.link_child_parent.isChecked():
                try:
                    module=MODULE(stave_folder_path, position, stave_side, Calibration_TimeStamp, Loader_Names,Glue_Time, Glue_Batch_ID,ITkPDSession=stave.ITkPDSession)
                except ComponentNotFound:
                    QMessageBox.warning(self,'Warning',"No module was found using the IDs given in the CSV file, please fix the error --skipping the module")
                    continue

                #in the terminal will print out the local name
                except MultipleComponentsFound:
                    QMessageBox.warning(self,'Warning',"Multiple modules were found using the Local Name given in the CSV file, please fix the error --skipping the module")
                    continue

                ###------fill in more properties--------###
                child_properties=module.childProperties

                #find the slot to be assembled, side L first 14 slots; side J the next 14 slots
                if 'L' in module.stave_side:
                    child_slot=stave.slotIDs[position]
                else:
                    child_slot=stave.slotIDs[14+position]

                try:
                    stave.addModule(module,child_slot,child_properties)
                    assembled_positions.append(position)

                except RequestException as e:
                    QMessageBox.warning(self, 'Error', ' Requests exception raised for module at position %i:\n %s -- abort upload!' % (position, e))
                    continue
                #finish assemble modules

        if assembled_positions !=[]:
            QMessageBox.information(self,'Information',"Successfully finished assembly at positions %s (press \'Find in Database\' button to check!)" %str(assembled_positions))

        if self.staveStatus.upload_only_calibration_files.isChecked():

            #read from FileToUploadPerCalibration.txt the list of files to upload
            files = getCalibrationFileList()

            #iterate through all calibration folders
            for path in calibration_folder_path:

                try:
                    invalidFilePath = stave.uploadCalibrationFiles(path,files)

                except RequestException as e:
                    QMessageBox.warning(self, 'Error', ' Requests exception raised for calibration files in %s:\n %s -- skipping!' % (path,e))
                    continue

                #calibration file was already uploaded
                if invalidFilePath == True:
                    QMessageBox.information(self, 'Information', 'calibration files in %s already uploaded to the database, skipping' %path)
                    continue

                #if found invalid file path, give warning, and continue
                if invalidFilePath!=[]:
                    paths_str="\n"
                    for path in invalidFilePath:
                        paths_str+=path
                        paths_str+="\n"
                    QMessageBox.warning(self,"Warning","following file not found!"+paths_str)

                #if successfully uploaded all files
                #else:
                #    QMessageBox.information(self,'Information',"Successfully uploaded all calibration files.")



    #use stave folder name as the local name and find stave on the right panel
    def __confirm_find_stave_clicked(self):

        if not self.staveStatus.isValidStaveFolder:
            return None

        #set local name
        stave_folder = self.staveStatus.stave_folder_input.text()

        if stave_folder[-1]=='/':
            stave_folder = stave_folder[:-1]

        #stave folder name is the local name
        localname = os.path.basename(stave_folder)

        #automatically set local name and confirm to find stave
        self.STAVE_status.stave_id_input.setText(localname)
        self.STAVE_status.confirm_find_stave.click()


    @DEBUG
    def initMainUI(self):
        self.setWindowTitle(self.title)

        self.main = QWidget(self)
        self.layout = QGridLayout(self.main)

        self.layout.setAlignment(Qt.AlignTop)
        self.setCentralWidget(self.main)

        self.compareStave = QWidget(self)
        self.grid_compareStave = QGridLayout(self.compareStave)
        self.grid_compareStave.setSpacing(30)
        self.grid_compareStave.addWidget(self.staveStatus, 0,0,Qt.AlignLeft)
        self.grid_compareStave.addWidget(self.STAVE_status, 0,1,Qt.AlignRight)


        self.body = QStackedWidget(self)
        self.body.addWidget(self.compareStave)
        #self.body.addWidget(self.step3)
        #self.body.addWidget(self.step4)

        #self.layout.addWidget(self.header,          0, 0)
        self.layout.addWidget(self.body,            0, 0)
        #self.setFixedSize(self.size())

        #add functions to buttons
        self.staveStatus.confirm_find_stave.clicked.connect(self.__confirm_find_stave_clicked)

        self.staveStatus.assemble_btn.clicked.connect(self.__assembleModule)

        try:
            ITkPDLoginGui(ITkPDSession = self.ITkPDSession, parent = self)
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting.' % e, QMessageBox.Ok)
            sys.exit(1)



if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication

        session = ITkPDSession()
        app = QApplication(sys.argv)
        #QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        exe = SyncSTAVE_stave(parent=None, ITkPDSession=session)
        #exe.show()
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
