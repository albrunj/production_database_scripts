#!/usr/bin/env python
# Creates Plot Using a GUI
# Created Jun 18 2019
# Written by Nashad Rahman rahman.176@osu.edu
# GoBucks
import os
import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QWidget

import generatePlots
from itk_pdb.dbAccess import ITkPDSession
from itk_pdb.ITkPDLoginGui import ITkPDLoginGui


session = ITkPDSession() #Change this to be within the class Later


from datetime import datetime


def str2date(datestr):
    try:
        datetime.strptime(datestr, '%Y-%m-%d')
        return datestr
    except ValueError:
        try:
            datetime.strptime(datestr, '%Y/%m/%d')
            return '-'.join(datestr.split('/'))
        except ValueError:
            try:
                datetime.strptime(datestr, '%Y.%m.%d')
                return '-'.join(datestr.split('.'))
            except ValueError:
                try:
                    datetime.strptime(datestr, '%Y%m%d')
                    return datestr[0:4] + '-' + datestr[4:6] + '-' + datestr[6:8]
                except ValueError:
                    print('Date must be formatted one of [\'YYYY-MM-DD\'|\'YYYY/MM/DD\'|\'YYYY.MM.DD\'|\'YYYYMMDD\'].')


##############GUI STUFF##############

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Upload Data to Database'
        self.left = 100
        self.top = 100
        self.width = 700
        self.height = 350

        self.session = session

        self.initUI()

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

    def initUI(self):


        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        ITkPDLoginGui(self.session, self)

        #self.show()

    def getToken(self):
        return self.session.token


# Makes Seperate Tabs and objects within tabs
class MyTableWidget(QWidget):

    def __init__(self, parent):


        global delimiter

        super(QWidget, self).__init__(parent)
        self.layout = QGridLayout()
        self.selectedFile = "No file or directory selected"

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Type")
        self.tabs.addTab(self.tab2, "Component Type")
        self.tabs.addTab(self.tab3, "Stage")
        self.tabs.addTab(self.tab4, "Plot")


        # (1) Project Tab =====================================================================================

        # (1) Layout Formatting
        self.tab1.layout = QGridLayout()

        self.tab1.layout.setColumnStretch(0, 1)
        self.tab1.layout.setColumnStretch(1, 10)
        self.tab1.layout.setColumnStretch(2, 1)
        self.tab1.layout.setRowStretch(0, 1)
        self.tab1.layout.setRowStretch(3, 1)



        # (1) Type Label
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Project: ')
        self.tab1.layout.addWidget(self.nameLabel, 1, 1)
        self.nameLabel.setMaximumSize(150, 15)

        # (1) Create combobox and add items.
        self.typeChoice = QComboBox(QWidget(self))
        self.typeChoice.setObjectName("Sensor")
        self.typeChoice.addItem("Strip")
        self.typeChoice.addItem("Pixel")
        self.typeChoice.setMinimumWidth(500)
        self.tab1.layout.addWidget(self.typeChoice, 2, 1)

        # (1) Next Button
        self.next = QPushButton('Next', self)
        self.next.setToolTip('next')
        self.next.setMaximumSize(100, 30)
        self.next.clicked.connect(lambda: self.next_tab2())
        self.tab1.layout.addWidget(self.next, 3, 2, QtCore.Qt.AlignCenter)


        ## (2) Component Type Tab =====================================================================================

        self.tab2.layout = QGridLayout()

        self.tab2.layout.setColumnStretch(0, 1)
        self.tab2.layout.setColumnStretch(1, 10)
        self.tab2.layout.setColumnStretch(2, 1)
        self.tab2.layout.setRowStretch(0, 1)
        self.tab2.layout.setRowStretch(3, 1)

        # (2) Component Type Label
        self.typeLabel = QLabel(self)
        self.typeLabel.setText('Component Type:')
        self.tab2.layout.addWidget(self.typeLabel, 1, 1)
        self.typeLabel.setMaximumSize(150, 15)

        # (2) Create combobox and add items.
        self.compTyChoice = QComboBox(QWidget(self))
        self.compTyChoice.setObjectName(("Sensor"))

        self.compTyChoice.addItem("*All*")

        self.compTyChoice.setMinimumWidth(500)
        self.tab2.layout.addWidget(self.compTyChoice, 2, 1)

        # (2) Next Button
        self.next = QPushButton('Next', self)
        self.next.setToolTip('next')
        self.next.move(300, 170)
        self.next.setMaximumSize(100, 30)
        self.next.clicked.connect(lambda: self.next_tab3())
        self.tab2.layout.addWidget(self.next, 3, 2, QtCore.Qt.AlignCenter)


        ## (3) Current Stage =====================================================================================


        # (3) Layout formatting
        self.tab3.layout = QGridLayout()
        self.tab3.layout.setColumnStretch(0, 1)
        self.tab3.layout.setColumnStretch(1, 10)
        self.tab3.layout.setColumnStretch(2, 1)
        self.tab3.layout.setRowStretch(0, 1)
        self.tab3.layout.setRowStretch(3, 1)

        # (3) Stage Label
        self.stageLabel = QLabel(self)
        self.stageLabel.setText('Stage:')
        self.stageLabel.setMaximumSize(150, 15)
        self.tab3.layout.addWidget(self.stageLabel, 1, 1)


        # (3) Create combobox and add items.
        self.stageChoice = QComboBox(QWidget(self))
        self.stageChoice.setObjectName(("Stage"))

        self.stageChoice.addItem("*All*")

        self.stageChoice.setMinimumWidth(500)
        self.tab3.layout.addWidget(self.stageChoice, 2, 1)

        # (3) Next Button
        self.next = QPushButton('Next', self)
        self.next.setToolTip('next')
        self.next.move(300, 170)
        self.next.setMaximumSize(100, 30)
        self.next.clicked.connect(lambda: self.next_tab4())
        self.tab3.layout.addWidget(self.next, 3, 2, QtCore.Qt.AlignCenter)


        ## (4) Last Tab =====================================================================================

        # Formatting Layout
        self.tab4.layout = QGridLayout()
        self.tab4.layout.setColumnStretch(0, 1)
        self.tab4.layout.setColumnStretch(1, 1)
        self.tab4.layout.setColumnStretch(2, 10)
        self.tab4.layout.setColumnStretch(3, 1)

        self.tab4.layout.setRowStretch(5, 1)

        # (4) Institution Label
        self.instLabel = QLabel(self)
        self.instLabel.setText('Institution')
        self.tab4.layout.addWidget(self.instLabel, 1, 1)

        # (4) Create Institution Dropdown Menu
        self.instChoice = QComboBox(QWidget(self))
        self.instChoice.setObjectName(("inst"))
        self.instChoice.addItem("*All*")

        self.instChoice.setMinimumWidth(500)
        self.tab4.layout.addWidget(self.instChoice, 1, 2)

        # (4) Lower Date Label
        self.ldLabel = QLabel(self)
        self.ldLabel.setText('Lower Date Range (YYYY-MM-DD)')
        self.tab4.layout.addWidget(self.ldLabel, 2, 1)

        # (4) Lower Date Range
        self.lowDate = QLineEdit(self)
        self.lowDate.setText("*All*")
        self.lowDate.setMinimumWidth(100)
        self.tab4.layout.addWidget(self.lowDate,2,2)

        # (4) Upper Date Label
        self.udLabel = QLabel(self)
        self.udLabel.setText('Upper Date Range (YYYY-MM-DD)')
        self.tab4.layout.addWidget(self.udLabel, 3, 1)

        # (4) Upper Date Range
        self.highDate = QLineEdit(self)
        self.highDate.setText("*All*")
        self.highDate.setMinimumWidth(100)
        self.tab4.layout.addWidget(self.highDate,3,2)


        # (4) Axis Frequency Label
        self.AxFreqLabel = QLabel(self)
        self.AxFreqLabel.setText('Axis Label Frequency')
        self.tab4.layout.addWidget(self.AxFreqLabel, 4, 1)

        # (4) Axis Frequency Dropdown
        self.axisFreqChoice = QComboBox(QWidget(self))
        self.axisFreqChoice.setObjectName(("freq"))
        self.axisFreqChoice.addItem("Yearly")
        self.axisFreqChoice.addItem("Monthly")
        self.axisFreqChoice.addItem("Daily")
        self.axisFreqChoice.setMinimumWidth(500)
        self.tab4.layout.addWidget(self.axisFreqChoice, 4, 2)

        # (4) Save Path Text (Add Later)

        # (4) Rolling avg and Stat options (Add Later after functionality in generatePlots.py)

        # (4) File Name Label
        self.fileNameLabel = QLabel(self)
        self.fileNameLabel.setText('File Name')
        self.tab4.layout.addWidget(self.fileNameLabel, 5, 1)

        # (4) File Name Text
        self.fileName = QLineEdit(self)
        self.fileName.setText("ITkPDProdPlot.pdf")
        self.fileName.setMinimumWidth(100)
        self.tab4.layout.addWidget(self.fileName, 5, 2)

        # (4) Final Create Button
        self.plot = QPushButton('Create Plots', self)
        self.plot.setToolTip('Create Plots')
        self.plot.setMaximumSize(100, 30)
        self.plot.clicked.connect(lambda: self.createPlotButton())
        self.tab4.layout.addWidget(self.plot, 6, 1)


        # Add tabs to widget
        self.tab1.setLayout(self.tab1.layout)
        self.tab2.setLayout(self.tab2.layout)
        self.tab3.setLayout(self.tab3.layout)
        self.tab4.setLayout(self.tab4.layout)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)


    def next_tab(self, i):

        self.tabs.setCurrentIndex(i)

    def next_tab2(self):

        self.tabs.setCurrentIndex(1)
        self.compTyChoice.clear()
        projectCode = self.typeChoice.currentText()[0]
        x = session.doSomething('listComponentTypes', 'GET',
                                {'project': projectCode})  # Gets list of components for proj

        for item in x:
            y = item["name"]
            self.compTyChoice.addItem((y)) # Add all components to choices



    def next_tab3(self):

        self.tabs.setCurrentIndex(2)
        stages = ["Bare", "ASIC Stuffed", "Wire Bonded", "Completed", "SMD Stuffed"] # THIS IS FAKE CHANGE LATER




        self.stageChoice.clear()
        self.stageChoice.addItem("*All*")
        self.stageChoice.addItems(stages)


    def next_tab4(self):

        institutions = session.doSomething('listInstitutions', 'GET', data={}) #Gets list of all institutions from db

        for institution in institutions:
            self.instChoice.addItem(institution["code"])

        self.tabs.setCurrentIndex(3)





    def createPlotButton(self):

        #print("plot button pressed, " + self.compTyChoice.currentText().upper())

        if self.stageChoice.currentText() == "*All*":
            currentStage = None
        else: currentStage = self.stageChoice.currentText()

        if self.lowDate.text() == "*All*":
            lowerDate = None
        else: lowerDate = str2date(self.lowDate.text())

        if self.highDate.text() == "*All*" :
            upperDate = None
        else: upperDate = str2date(self.highDate.text())

        if self.instChoice.currentText() == "*All*" :
            institution = None
        else: institution = str(self.instChoice.currentText())


        from time import strftime
        startTime = strftime('%Y/%m/%d-%H:%M:%S')


        kwargs = {'startTime': startTime,
                  'project': "S",
                  'savePath': os.getcwd() + "/" + self.fileName.text(),
                  'componentType': self.compTyChoice.currentText().upper(),
                  'type': None,
                  'currentStage':  currentStage,
                  'currentLocation': None,
                  'institution': str(institution),
                  'currentGrade': None,
                  'qaState': None,
                  'lowerDate': lowerDate,
                  'upperDate': upperDate,
                  'trashed': None,
                  'dummy': None,
                  'assembled': None,
                  'reworked': None,
                  'qaTested': None,
                  'split': None,
                  'rrulewrapperFrequency': self.axisFreqChoice.currentText().upper(),
                  'rrulewrapperInterval': 2,
                  'includeTotal': None,
                  'saveJson': None
                  }

        token = session.token

        #print(kwargs["institution"])

        generatePlots.generatePlotsFromKwargs(kwargs, token)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()

    sys.exit(app.exec_())
