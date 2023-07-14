#!/usr/bin/env python
#local_staveStatus_GUI.py
# a standalone GUI to check a local stave's assembly status (how many modules assembled, how many calibrations...)
# written by Jiayi Chen
# created 05/14/2019
# last update: 06/14/2019

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys, os
import numpy as np
#sys.path.append(os.path.abspath('../'))
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
        QDialog,
        QFileDialog,
        QVBoxLayout,
        QCheckBox,
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
    CORE,
    MountingInfoInStaveFolder,
    NoCalibrationFound,
)
from STAVEstatus_GUI import STAVEstatus__Header
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

class registerWindow(QDialog):
    def __init__(self,parent=None,ITkPDSession=None):
        super(registerWindow,self).__init__(parent)
        self.parent           =  parent
        self.setGeometry(100,100,200,200)
        #self.resize(850, 600)
        self.setObjectName("Dialog!!!")
        self.isRegistered = False
        self.ITkPDSession = ITkPDSession
        self.initRegisterUI()

    def __registerSTAVE(self):

        if "long" in self.core_type_input.text().lower() or "ls" in self.core_type_input.text().lower():
            core_type="LS"
        elif "short" in self.core_type_input.text().lower() or "ss" in self.core_type_input.text().lower():
            core_type="SS"
        else:
            QMessageBox.warning(self, 'Warning', 'Invalid input for Core type (LS/SS) or side (A/C)')
            return None

        if "A" in self.core_side_input.text().upper():
            core_side="A"
        elif "C" in self.core_side_input.text().upper():
            core_side="C"
        else:
            QMessageBox.warning(self, 'Warning', 'Invalid input for Core type (LS/SS) or side (A/C)')
            return None

        self.stave_localname =   self.stave_localname_input.text()

        if _DEBUG:
            print("recieved input (STAVE ID):", self.stave_localname)


        self.Stave = STAVE(LOCALNAME=self.stave_localname, assemblySite=self.assembly_site_input.currentText(), ITkPDSession=self.ITkPDSession)
        newCore=CORE(type=core_type,side=core_side)
        self.Stave.addCore(newCore)

        try:
            self.Stave.registerSTAVE()
        except RequestException as e:
            QMessageBox.warning(self, 'Error', ' Requests exception raised for registration:\n %s -- abort registration!' % (e))
            return None

        QMessageBox.information(self, 'Success', 'Registered STAVE with local name:'+self.stave_localname)
        self.isRegistered = True

    def initRegisterUI(self):
        core_id_label = QLabel("Core ID:")
        core_id_label.setStyleSheet('font-size: 13pt; color: black;')
        self.core_id_input  =   QLineEdit()
        self.core_id_input.setStyleSheet('font-size: 12pt; color: black;')

        self.find_core_btn = QPushButton("Find CORE")

        core_side_label = QLabel("Side (A/C):")
        core_side_label.setStyleSheet('font-size: 13pt; color: black;')
        self.core_side_input =  QLineEdit("")
        self.core_side_input.setStyleSheet('font-size: 12pt; color: blue;')

        core_type_label = QLabel("Type (LS/SS):")
        core_type_label.setStyleSheet('font-size: 13pt; color: black;')
        self.core_type_input =  QLineEdit("")
        self.core_type_input.setStyleSheet('font-size: 12pt; color: blue;')

        assembly_site_label = QLabel("Assembly site:")
        assembly_site_label.setStyleSheet('font-size: 13pt; color: black;')
        self.assembly_site_input= QComboBox()
        self.assembly_site_input.addItem('BU')
        self.assembly_site_input.addItem('BNL')
        #self.assembly_site_input.addItem('RAL')

        stave_localname_label = QLabel("Stave Local Name:")
        stave_localname_label.setStyleSheet('font-size: 13pt; color: black;')
        self.stave_localname_input  =   QLineEdit("")
        self.stave_localname_input.setStyleSheet('font-size: 12pt; color: blue;')

        self.confirm_register_btn = QPushButton('Register and Add Core')
        self.confirm_register_btn.setStyleSheet('font-size: 12pt; font: bold; color: blue;')

        #if self.stave_localname_input.text() != "" and self.core_type_input.text()!= "" and self.core_type_input.text()!= "":
        self.confirm_register_btn.clicked.connect(self.__registerSTAVE)

        self.grid = QGridLayout(self)
        #self.grid.setSpacing(10)

        self.grid.addWidget(    core_id_label,         0, 0, Qt.AlignLeft)
        self.grid.addWidget(    self.core_id_input,    1, 0, 1, 1)#,  Qt.AlignLeft)
        self.grid.addWidget(    self.find_core_btn,    1, 1, 1, 1, Qt.AlignLeft)
        self.grid.addWidget(    core_side_label,       2, 0, 1, 1,  Qt.AlignRight)
        self.grid.addWidget(    self.core_side_input,  2, 1, 1, 2, Qt.AlignLeft)
        self.grid.addWidget(    core_type_label,       3, 0, 1, 1,  Qt.AlignRight)
        self.grid.addWidget(    self.core_type_input,  3, 1, 1, 2, Qt.AlignLeft)
        self.grid.addWidget(    assembly_site_label,       4, 0, 1, 1,  Qt.AlignRight)
        self.grid.addWidget(    self.assembly_site_input,  4, 1, 1, 2, Qt.AlignLeft)
        self.grid.addWidget(    stave_localname_label,        5, 0, Qt.AlignLeft)
        self.grid.addWidget(    self.stave_localname_input,   6, 0, 1, 5, Qt.AlignLeft)
        self.grid.addWidget(    self.confirm_register_btn,   7, 0, 1, 1, Qt.AlignRight)

class staveStatus(QWidget):

        @DEBUG
        def __init__(self, parent=None,ITkPDSession=None):
            super(staveStatus,self).__init__(parent)
            self.parent           =  parent
            self.stave_folder     =  None
            self.ITkPDSession     = ITkPDSession
            self.registerDialog   = registerWindow(self,ITkPDSession)
            self.positions        = np.arange(0,14,1)
            self.selectable_positions = []
            self.isRegistered = self.registerDialog.isRegistered
            #self.setGeometry(100,100,1250,1200)
            self.initUI()

        def __select_highlighted(self):

            if self.selectable_positions == None:
                 return None

            positions = self.table.selectionModel().selectedRows()
            positions = [index.row() for index in sorted(positions)]

            correct_positions=[]

            for position in positions:
                if position in self.selectable_positions:
                    correct_positions.append(position)

            positions=[str(x) for x in correct_positions]
            positions=",".join(positions)
            self.selected_position.setText(positions)

            #current selected positions
            #selected_position = self.selected_position.text()
            #if selected_position != "" and selected_position != None:
            #    positions=[int(x) for x in selected_position.split(",")]
            #else:
        #        positons=[]

            #add selected position - i
        #    if i not in positions:
        #        positions.append(i)
        #        positions.sort()

            #remove??
        #    else:
        #        return None


        def __select_all_position(self):
            if self.selectable_positions == None:
                 return None

            selectable_positions=[str(x) for x in self.selectable_positions]
            selectable_positions=",".join(selectable_positions)
            self.selected_position.setText(selectable_positions)

        def __display_staveAssembly(self):
            if not os.path.exists(self.stave_folder_input.text()):
                QMessageBox.warning(self, 'Warning', 'Invaid path to stave folder (path does not exist), please try again.')
                self.isValidStaveFolder = False
                return None

            try:
                staveFolderInfo = MountingInfoInStaveFolder(self.stave_folder_input.text())
                self.isValidStaveFolder = True
            except NoCalibrationFound:
                QMessageBox.warning(self, 'Warning', 'Invaid path to stave folder (no calibration folder was found), please try again.')
                self.isValidStaveFolder = False
                return None
            #except FileNotFoundError:
            #    QMessageBox.warning(self, 'Warning', 'Invaid path to stave folder, please try again.')
            #    self.isValidStaveFolder = False
            #    return None

            self.stave_side = self.stave_side_input.currentText()
            self.MountingInfo = staveFolderInfo.MountingInfo
            #print(staveFolderInfo.MountingInfo)
            if self.stave_side not in self.MountingInfo.keys():
                self.selectable_positions = []
                QMessageBox.information(self, 'Information', 'No module was assembled on this stave side')
            else:
                self.selectable_positions = list(self.MountingInfo[self.stave_side].keys())
                #print("!!!!!!",self.selectable_positions)

            for position in self.positions:
                module_position = position
                if module_position not in self.selectable_positions:
                    isAssembled = QTableWidgetItem("No")
                    isAssembled.setBackground(QColor('red'))
                    isAssembled.setTextAlignment(Qt.AlignHCenter)
                    textFont = QFont("song", 12, QFont.Bold)
                    isAssembled.setFont(textFont)
                    self.table.setItem(module_position,1, isAssembled)

                    assembler = QTableWidgetItem("")
                    assembler.setTextAlignment(Qt.AlignHCenter)
                    assembler.setFont(textFont)
                    self.table.setItem(module_position,2, assembler)

                    GlueID = QTableWidgetItem("")
                    GlueID.setTextAlignment(Qt.AlignHCenter)
                    GlueID.setFont(textFont)
                    self.table.setItem(module_position,3, GlueID)

                else:
                    #time=MountingInfo[module_position]['CALIBRATION']
                    isAssembled = QTableWidgetItem("Yes")
                    isAssembled.setBackground(QColor('green'))
                    isAssembled.setTextAlignment(Qt.AlignHCenter)
                    textFont = QFont("song", 12, QFont.Bold)
                    isAssembled.setFont(textFont)
                    self.table.setItem(module_position, 1, isAssembled)

                    assembler = QTableWidgetItem(self.MountingInfo[self.stave_side][module_position]['ASSEMBLER'])
                    assembler.setTextAlignment(Qt.AlignHCenter)
                    assembler.setFont(textFont)
                    self.table.setItem(module_position,2, assembler)

                    GlueID = QTableWidgetItem(self.MountingInfo[self.stave_side][module_position]['GLUE-ID'])
                    GlueID.setTextAlignment(Qt.AlignHCenter)
                    GlueID.setFont(textFont)
                    self.table.setItem(module_position,3, GlueID)


                    #self.table.cellClicked(module_position,0).connect(__select_position(module_position))


        def __find_stave_folder(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            options |= QFileDialog.ShowDirsOnly
            path = QFileDialog.getExistingDirectory(parent = self, directory = '.', options = options)
            self.stave_folder = path+'/'
            self.stave_folder_input.setText(self.stave_folder)

        #def __select

        @DEBUG
        def initUI(self):

            #self.setWindowTitle("stave status")
            self.header = STAVEstatus__Header(self,title='Check local stave assembly status')

########add Widgets and set Grid Layout#########
    ##########fill in by users#######
            subtitle    =     QLabel('I. Fill in the following to find the status of one stave side')
            subtitle.setStyleSheet('font-size: 14pt; font: bold; color: black;')

            stave_folder_label=   QLabel('stave folder:')
            self.stave_folder_input  =   QLineEdit()
            #initiate stave folder input to be invalid
            self.isValidStaveFolder = False

            stave_folder_label.setStyleSheet('font-size: 13pt; color: black;')

            self.ExploreBtn=QPushButton('Explore')
            self.ExploreBtn.setStyleSheet('font-size: 12pt; font: bold; color: black;')
            self.ExploreBtn.clicked.connect(self.__find_stave_folder)

            stave_side_label= QLabel('STAVE SIDE:')
            self.stave_side_input= QComboBox()
            self.stave_side_input.addItem('L')
            self.stave_side_input.addItem('J')

            stave_side_label.setStyleSheet('font-size: 13pt; color: black;')

            self.confirm_find_stave = QPushButton('confirm')
            self.confirm_find_stave.setStyleSheet('font-size: 12pt; font: bold; color: black;')
            self.confirm_find_stave.clicked.connect(self.__display_staveAssembly)

            self.register_btn = QPushButton('Register new STAVE')
            self.register_btn.setStyleSheet('font-size: 14pt; font: bold; color: blue;')
            self.register_btn.clicked.connect(self.registerDialog.show)

            #set layout + grids
            self.layout = QVBoxLayout(self)
            self.grid = QGridLayout()
            self.grid.setSpacing(10)

            self.grid.addWidget(    self.header,         0, 0, 1, -1)
            self.grid.addWidget(    subtitle,            1, 0, 1, -1, Qt.AlignLeft)
            self.grid.addWidget(    stave_folder_label,      2, 0, 1, 1,Qt.AlignRight)
            self.grid.addWidget(    self.stave_folder_input,      2, 1, 1, 7)
            self.grid.addWidget(    self.ExploreBtn,      2, 8,1, 1, Qt.AlignLeft)
            self.grid.addWidget(    stave_side_label,    3, 0, 1, 1, Qt.AlignRight)
            self.grid.addWidget(    self.stave_side_input,    3, 1, 1, 1, Qt.AlignLeft)
            self.grid.addWidget(    self.confirm_find_stave,  3, 3, 1, 1)
            self.grid.addWidget(    self.register_btn,  3, 5, 1, 1)


    ##########fill in w/ info from stave folder#######
            subtitle2    =     QLabel('II. stave assembly status')
            subtitle2.setStyleSheet('font-size: 14pt; font: bold; color: black;')

            stave_properties_label=   QLabel('stave properties:')
            stave_properties_label.setStyleSheet('font-size: 13pt; color: black;')

            modules_label=   QLabel('Assembly Status (from position 0-13):')
            modules_label.setStyleSheet('font-size: 13pt; color: black;')

            #
            #self.grid2.setSpacing(10)
            self.grid.addWidget(subtitle2,                     4, 0, 1, -1, Qt.AlignLeft)
            #self.grid2.addWidget(stave_properties_label,        1, 0, 1, 1, Qt.AlignRight)
            #self.grid2.addWidget(self.stave_properties_display, 1, 1, 1, -1)
            self.grid.addWidget(modules_label,                 5, 0, 1, -1, Qt.AlignLeft)

            #table for assembled module
            self.table = QTableWidget()
            self.table.setColumnCount(4) # position, is Assembled, assembler, glue batch ID
            self.table.setRowCount(14)

            horizontalHeader = ["Position","is Assembled","Names of Assemblers", "GlueBatchID"]
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


            for position in self.positions:
                #some PD actions...fill in slot info
                input=QTableWidgetItem(str(position))
                #input.setBackgroundColor(QColor(0,60,10))
                input.setTextAlignment(Qt.AlignHCenter)
                textFont = QFont("song", 12, QFont.Bold)
                input.setFont(textFont)
                self.table.setItem(position,0,input)

                #this_slot=QLineEdit(str(position) + ":")
                #this_slot.setReadOnly(True)
                #this_slot.setStyleSheet('font-size: 11pt; color: black;')
                #self.grid2.addWidget(this_slot,    position+3, 0, 1, 15)
                #self.slots.append(this_slot)

                #select_btn = QPushButton("select")
                #select_btn.setStyleSheet('font-size: 11pt; color: blue;')
                #self.grid2.addWidget(select_btn,    position+3, 15, 1, 1,Qt.AlignLeft)
                #self.select_btns.append(select_btn)

            self.grid2 = QGridLayout()
            self.grid2.setSpacing(10)

            self.select_all_btn = QPushButton("upload ALL")
            self.select_all_btn.setStyleSheet('font-size: 12pt; font: bold; color: blue;')
            self.select_all_btn.clicked.connect(self.__select_all_position)

            self.select_highlighted_btn = QPushButton("upload the selected")
            self.select_highlighted_btn.setStyleSheet('font-size: 12pt; font: bold; color: blue;')
            self.select_highlighted_btn.clicked.connect(self.__select_highlighted)

            self.grid2.addWidget(self.select_all_btn,  0, 0, 1, 2)
            self.grid2.addWidget(self.select_highlighted_btn,  0, 2, 1, 2)

            selected_position_label = QLabel("Selected positions to be uploaded (ex. 1,5,6):")
            selected_position_label.setStyleSheet('font-size: 12pt; font: bold; color: black;')
            self.selected_position=QLineEdit()
            #self.selected_position.setReadOnly(True)

            additional_options_lable = QLabel("Additional upload options:")
            additional_options_lable.setStyleSheet('font-size: 11pt; font: bold; color: black;')


            self.link_child_parent = QCheckBox('link MODULEs with STAVE:', self)
            self.link_child_parent.setLayoutDirection(Qt.RightToLeft)
            self.link_child_parent.setStyleSheet('font-size: 11pt; color: black; margin-left: 50%; margin-right: 50%;')
            self.link_child_parent.setChecked(True)

            self.upload_only_calibration_files = QCheckBox('Upload calibration files:', self)
            self.upload_only_calibration_files.setLayoutDirection(Qt.RightToLeft)
            self.upload_only_calibration_files.setStyleSheet('font-size: 11pt; color: black; margin-left: 50%; margin-right: 50%;')
            self.upload_only_calibration_files.setChecked(True)

            self.assemble_btn = QPushButton("Upload to Database")
            self.assemble_btn.setStyleSheet('font-size: 12pt; font: bold; color: blue;')


            self.grid2.addWidget(selected_position_label,        1, 0, 1, 2)
            self.grid2.addWidget(self.selected_position,         1, 2, 1, 2)
            self.grid2.addWidget(additional_options_lable,       2, 0, 1, 1)
            self.grid2.addWidget(self.link_child_parent,  2, 1, 1, 1)
            self.grid2.addWidget(self.upload_only_calibration_files,  2, 2, 1, 2)
            self.grid2.addWidget(self.assemble_btn,  3, 0, 1, -1,Qt.AlignRight)

            #merge the upper, lower grid layouts, table
            self.layout.addLayout(self.grid)
            self.layout.addWidget(self.table)
            self.layout.addLayout(self.grid2)


            #try:
            #    ITkPDLoginGui(ITkPDSession = self.ITkPDSession, parent = self)
            #except RequestException as e:
                #QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting.' % e, QMessageBox.Ok)
                #sys.exit(1)


if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication

        session = ITkPDSession()
        app = QApplication(sys.argv)
        exe = staveStatus(parent=None,ITkPDSession=session)
        #exe.show()
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
