#!/usr/bin/env python
#STAVEstatus_GUI.py
# a standalone GUI to check STAVE status in the database
# written by Jiayi Chen
# created 04/17/2019
# last update: 07/15/2019

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys, os
import numpy as np
sys.path.append(os.path.abspath('../'))
try:
    from PyQt5.QtWidgets import (
        QWidget,
        QLabel,
        QGridLayout,
        QPushButton,
        QLineEdit,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QMessageBox,
        QAbstractItemView,
        QComboBox,
        QVBoxLayout,
        QScrollArea,
    )
    from PyQt5.QtGui import QColor, QFont
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
from itk_pdb.dbAccess import ITkPDSession
from LoadedStave_class import (
    STAVE,
    ComponentNotFound,
    MultipleComponentsFound,
    getCalibrationFileList,
)
from functools import wraps

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

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## HEADER WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class STAVEstatus__Header(QWidget):

    @DEBUG
    def __init__(self, parent = None,title=''):
        super(STAVEstatus__Header, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.title=title
        self.__initUI()
        self.scroll = QScrollArea()
        self.scroll.setWidget(self)

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __quit(self):
        sys.exit(0)

    @DEBUG
    def __initUI(self):

        title = QLabel(self.title, self)
        title.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')
        #quit = QPushButton('Quit', self)
        #quit.clicked.connect(lambda: self.__quit())
        #quit.setAutoDefault(True)
        #quit.setToolTip('Quit the GUI')
        #quit.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        self.layout.addWidget(title,    0, 0, 1, 5)
        #self.layout.addWidget(quit,     0, 5, 1, 5)

class STAVEStatus(QWidget):

        @DEBUG
        def __init__(self, parent=None, ITkPDSession=None):
            super(STAVEStatus,self).__init__(parent)
            self.parent           =  parent
            self.ITkPDSession     =  ITkPDSession
            self.stave_id         =  None
            self.stave_side       =  None #module loaded side (L/J)
            self.stave_properties =  None
            self.wrong_slots      =  []
            self.Stave            = None
            #self.setGeometry(100,100,1170,1300)
            self.initUI()


        def __display_STAVE(self):

            #get stave id from the textbox
            self.stave_id =   self.stave_id_input.text()
            if _DEBUG:
                print("recieved input (STAVE ID):", self.stave_id)


            while True:

                try:
                    self.Stave = STAVE(LOCALNAME=self.stave_id,ITkPDSession=self.ITkPDSession)
                    stave_info = self.Stave.StaveINFO()
                    self.isRegistered = True
                    break

                #if STAVE not found, prompt up warning and do nothing
                except ComponentNotFound:
                    if _DEBUG:
                        print('no component found')
                    QMessageBox.warning(self, 'Warning', 'No STAVE was found using the given stave ID, please register first!')
                    self.isRegistered = False
                    return None

                #if multiple STAVEs were found, prompt up warning and do nothing
                except MultipleComponentsFound:
                    if _DEBUG:
                        print('more than one component was found using the ID')
                    QMessageBox.warning(self, 'Warning', 'More than one STAVE was found using the given stave ID! Please correct this in the ITk PD')
                    return None

                except RequestException as e:
                    QMessageBox.warning(self, 'Error', ' Requests exception raised for STAVE with ID %s:\n %s -- abort upload!' % (self.stave_id, e))
                    return None

            #get the PD STAVE's stave properties and display properties
            self.stave_properties = 'stave type (' + self.Stave.stave_type + '); stage ('+self.Stave.stage +')'
            self.stave_properties_display.setText(self.stave_properties)

            #read the selected stave side (L/J)
            self.stave_side = self.stave_side_input.currentText()
            if _DEBUG:
                print("selected stave side:", self.stave_side)

            #if chosen RHS, slots15-28
            isJ=0
            if self.stave_side == 'J':
                isJ=14

            slot_num=np.arange(0,14,1)

            for ind,slot in enumerate(slot_num):

                #start from 0, not 1
                module_position = slot
                ind+=isJ #change to index of the children slots (28 total)

                this_slot = QTableWidgetItem(str(module_position))
                this_slot.setTextAlignment(Qt.AlignHCenter)
                textFont = QFont("song", 12, QFont.Bold)
                this_slot.setFont(textFont)
                self.table.setItem(module_position, 0, this_slot)

                #PD STAVE slot if not empty
                module_info=self.Stave.module_info[ind]
                if module_info != 'empty':
                    #module_info=self.Stave.module_info[ind]
                    #time=MountingInfo[module_position]['CALIBRATION']
                    isAssembled = QTableWidgetItem("Yes")
                    isAssembled.setBackground(QColor('green'))
                    isAssembled.setTextAlignment(Qt.AlignHCenter)
                    isAssembled.setFont(textFont)
                    self.table.setItem(module_position, 1, isAssembled)

                    stave_side = QTableWidgetItem(module_info[0])
                    stave_side.setTextAlignment(Qt.AlignHCenter)
                    stave_side.setFont(textFont)
                    if module_info[0] != self.stave_side:
                        stave_side.setBackground(QColor('red'))
                    self.table.setItem(module_position,2, stave_side)

                    position = QTableWidgetItem(str(module_info[1]))
                    position.setTextAlignment(Qt.AlignHCenter)
                    position.setFont(textFont)
                    if str(module_position) != module_info[1]:
                        position.setBackground(QColor('red'))
                    self.table.setItem(module_position,3, position)

                    #get the list of calibration files that should be uploaded
                    files=getCalibrationFileList()
                    isUploaded = "Uploaded"

                    #get the uploaded files with the same calibration timestamp
                    uploadedFiles = []
                    for attachment in stave_info["attachments"]:
                        if attachment["description"] == str(module_info[2]):
                            uploadedFiles.append(attachment["filename"])

                    #check if file is uploaded
                    for file in files:
                        if not (file in uploadedFiles):
                            isUploaded = "Not Uploaded"

                    caliUploaded = QTableWidgetItem(isUploaded)
                    if caliUploaded == "Not Uploaded":
                        caliUploaded.setBackground(QColor('red'))
                    caliUploaded.setTextAlignment(Qt.AlignHCenter)
                    caliUploaded.setFont(textFont)
                    self.table.setItem(module_position,4, caliUploaded)

                else:
                    isAssembled = QTableWidgetItem("No")
                    isAssembled.setTextAlignment(Qt.AlignHCenter)
                    isAssembled.setFont(textFont)
                    self.table.setItem(module_position, 1, isAssembled)

                    stave_side = QTableWidgetItem("")
                    stave_side.setTextAlignment(Qt.AlignHCenter)
                    stave_side.setFont(textFont)
                    self.table.setItem(module_position,2, stave_side)

                    position = QTableWidgetItem("")
                    position.setTextAlignment(Qt.AlignHCenter)
                    position.setFont(textFont)
                    self.table.setItem(module_position,3, position)

                    caliUploaded = QTableWidgetItem("")
                    caliUploaded.setTextAlignment(Qt.AlignHCenter)
                    caliUploaded.setFont(textFont)
                    self.table.setItem(module_position,4, caliUploaded)

                        #enable the fix button
                        #self.fix_btn.setStyleSheet('font-size: 14pt;font: bold; color: red;')

                        #attach the module position
                        #self.wrong_slots.append(ind)
                    #else:
                        #slot.setStyleSheet('font-size: 12pt; font: bold;color: green;')


        def __fix_Error(self):

            #if wrong slots array is empty
            if self.wrong_slots==[]:
                return None

            #if there is an issue with a slot
            else:
                for slot in self.wrong_slots:
                    child_code=self.Stave.module_codes[slot]
                    print(child_code)
                    self.Stave.disassembleChild(child_code)

                QMessageBox.information(self,'Success', 'Modules at slot %s are disassembled' %(str(self.wrong_slots)))
                self.fix_btn.setStyleSheet('font-size: 13pt; color: grey;')
        @DEBUG
        def initUI(self):

            self.setWindowTitle("STAVE status")
            self.header = STAVEstatus__Header(self,title='Check STAVE status in ITk PD')

########add Widgets and set Grid Layout#########
    ##########fill in by users#######
            subtitle    =     QLabel('I. Fill in the following to find the status of one STAVE side')
            subtitle.setStyleSheet('font-size: 13pt; font: bold; color: black;')

            stave_id_label=   QLabel('STAVE ID:')
            self.stave_id_input  =   QLineEdit()

            stave_id_label.setStyleSheet('font-size: 13pt; color: black;')

            stave_side_label= QLabel('STAVE SIDE:')
            self.stave_side_input= QComboBox()
            self.stave_side_input.addItem('L')
            self.stave_side_input.addItem('J')

            stave_side_label.setStyleSheet('font-size: 13pt; color: black;')

            self.confirm_find_stave = QPushButton('Find in Database')
            self.confirm_find_stave.setStyleSheet('font-size: 12pt; font: bold; color: blue;')
            self.confirm_find_stave.clicked.connect(self.__display_STAVE)

            #set layout + grids
            self.layout = QVBoxLayout(self)

            self.grid = QGridLayout()
            self.grid.setSpacing(10)

            self.grid.addWidget(    self.header,         0, 0, 1, -1,Qt.AlignLeft)
            self.grid.addWidget(    subtitle,            1, 0, 1, -1, Qt.AlignLeft)
            self.grid.addWidget(    stave_id_label,      2, 0, 1, 1,Qt.AlignRight)
            self.grid.addWidget(    self.stave_id_input,      2, 1, 1, 2, Qt.AlignLeft)
            self.grid.addWidget(    stave_side_label,    2, 4, 1, 1, Qt.AlignRight)
            self.grid.addWidget(    self.stave_side_input,    2, 5, 1, 1, Qt.AlignLeft)
            self.grid.addWidget(    self.confirm_find_stave,  2, 6, 1, 1)


            #self.layout.setContentMargins(50,50,50,50)



    ##########fill in w/ info from PD#######
            subtitle2    =     QLabel('II. STAVE info in database')
            subtitle2.setStyleSheet('font-size: 14pt; font: bold; color: black;')

            stave_properties_label=   QLabel('STAVE properties:')
            stave_properties_label.setStyleSheet('font-size: 13pt; color: black;')

            #PD returned properties:
            self.stave_properties_display =   QLineEdit()
            self.stave_properties_display.setReadOnly(True)
            self.stave_properties_display.setStyleSheet('font-size: 10pt; color: black;')

            modules_label=   QLabel('Assembly Status:')
            modules_label.setStyleSheet('font-size: 13pt; color: black;')

            self.grid2 = QGridLayout()
            self.grid2.setSpacing(10)
            self.grid2.addWidget(subtitle2,                     0, 0, 1, -1, Qt.AlignLeft)
            self.grid2.addWidget(stave_properties_label,        1, 0, 1, 1, Qt.AlignRight)
            self.grid2.addWidget(self.stave_properties_display, 1, 1, 1, -1)
            self.grid2.addWidget(modules_label,                 2, 0, 1, -1, Qt.AlignLeft)

            #table for assembled module
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setRowCount(14)

            horizontalHeader = ["slot#","is Assembled","stave side","position","Calibration Files"]
            self.table.setHorizontalHeaderLabels(horizontalHeader)

            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            #disable edit for now
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setSelectionMode(QTableWidget.MultiSelection)

            header_horizontal = self.table.horizontalHeader()
            header_horizontal.setStyleSheet('font-size: 11pt; font: bold;')
            header_horizontal.setDefaultAlignment(Qt.AlignHCenter)
            header_horizontal.setSectionResizeMode(QHeaderView.ResizeToContents)
            header_horizontal.setStretchLastSection(True)

            header_vertical = self.table.verticalHeader()
            header_vertical.setVisible(False)

            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()


            #merge the upper and lower grid layouts
            self.layout.addLayout(self.grid)
            self.layout.addLayout(self.grid2)
            self.layout.addWidget(self.table)

            # self.setFixedSize(self.size())
            # try:
            #     ITkPDLoginGui(ITkPDSession = self.ITkPDSession, parent = self)
            # except RequestException as e:
            #     QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting.' % e, QMessageBox.Ok)
            #     sys.exit(1)



if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication

        session = ITkPDSession()
        app = QApplication(sys.argv)
        #exe = STAVEStatus(parent=None, ITkPDSession=session)
        #exe.show()
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
