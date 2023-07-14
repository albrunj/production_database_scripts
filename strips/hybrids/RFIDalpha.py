#!/usr/bin/env python
# Cedric Hoenig
import configparser as cf
import sys

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtSvg
from PyQt5 import QtWidgets

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import strips.libs.DatabaseConnection as db
import strips.libs.ExtendedQtClasses as ExtendedQtClasses

_ALLOW_AUTH_FROM_CFG = False

skipBool = False

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,dataBase, flexSheet, usedArrays, parent= None):
        #self.MainWindow = QtWidgets.QMainWindow()
        super().__init__(parent)
        self.form_widget = FormWidget(self,dataBase,flexSheet=flexSheet,usedArrays=usedArrays)
        self.setCentralWidget(self.form_widget)
        self.setMenuBar(self.createMenubar())
        self.resize(780, 400)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(self.sizePolicy)

        #self.setWindowIcon(QtGui.QIcon('Bilder/Uni-Logo.png'))

        self.setWindowTitle(u"Hybrids register - by Jan Cedric Hönig")
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.branding = QtSvg.QSvgWidget("../../media/Branding2.svg")
        self.statusbar.addPermanentWidget(self.branding)

    def heightForWidth(self, width):
        return width * 2

    def createMenubar(self):
        self.menubar = QtWidgets.QMenuBar()
        #self.menubar.setGeometry(QtCore.QRect(0, 0, 220, 21))

        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        self.menubar.addAction(self.menuFile.menuAction())
        return self.menubar

class FormWidget(QtWidgets.QWidget):
    colorSetterForm = QtCore.pyqtSignal(QtGui.QPalette, QtWidgets.QLineEdit)
    changeRFIDBool = QtCore.pyqtSignal(bool)

    def __init__(self, parent,dataBase, flexSheet,usedArrays):
        super().__init__(parent)
        self.flexSheet = flexSheet
        self.usedArrays = usedArrays

        self.setLayoutandContent()

        self.dataBase = dataBase
        self.dataBase.update(self.lineEdit, self.checkBoxes,self.BatchSheet)
        self.dataBThread = db.DataBaseThread(self.dataBase)

        self.skipBool = False
        self.rfidThread = ExtendedQtClasses.ScanForRFID(self.lineEdit,self.checkBoxes)
        #self.rfidThread.started.connect(self.rfidThread.changeColor, QtCore.Qt.DirectConnection)
        #self.rfidThread.started.connect(self.rfidThread.changeColor, QtCore.Qt.DirectConnection)

        self.rfidThread.colorSetter.connect(self.updateColor, QtCore.Qt.DirectConnection)
        self.rfidThread.received_RFID.connect(self.updateRFID, QtCore.Qt.DirectConnection)
        self.rfidThread.skip_RFID.connect(self.skipRFID, QtCore.Qt.DirectConnection)
        self.changeRFIDBool.connect(self.rfidThread.changeBool, QtCore.Qt.DirectConnection)
  #      self.rfidThread.stopped.connect(self.rfidThread.quit, QtCore.Qt.DirectConnection)
        """bkgnd = QtGui.QPixmap("Bilder/r0h0panel.png")
        bkgnd = bkgnd.scaled(self.size(), QtCore.Qt.IgnoreAspectRatio);
        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Background, bkgnd)
        self.setPalette(palette)"""
        #self.setStyleSheet(open('RFID-Alpha.css').read())

    def setLayoutandContent(self):
        self.layout =  MyBoxLayout(self)
        self.layout.setSpacing(10)

        self.addConstantComponents()
        self.addLabelsAndLineEdit()
        self.addButtons()
        self.connectButtons()

        self.setLayout(self.layout)

    def addConstantComponents(self):
        BatchSheet = ["Batch", "Sheet"]

        self.BatchSheet = [QtWidgets.QLineEdit(x) for x in BatchSheet]
        self.BatchSheet[1] = ExtendedQtClasses.ExtendedCombo()

        #create the selection for selected Array type and set starting value

        self.combobox = QtWidgets.QComboBox()

        self.combobox.addItems(self.flexSheet[0])
        self.combobox.setCurrentIndex(self.usedArrays[1][0])

        # position all the elements within the window

        self.layout.addWidget(self.combobox, 1, 4, 1, 2)

        self.layout.addWidget(self.BatchSheet[0], 1, 0, 1, 2)
        self.layout.addWidget(self.BatchSheet[1], 1, 2, 1, 2)

        model = QtGui.QStandardItemModel()

        #create tthe suggestion window and index the elements

        for i, word in enumerate(self.usedArrays[0]):
            item = QtGui.QStandardItem(word)
            model.setItem(i, 0, item)

        self.BatchSheet[1].setModel(model)
        self.BatchSheet[1].setModelColumn(0)
        self.BatchSheet[1].currentIndexChanged.connect(self.currentlySelectedArrayType)


    def addLabelsAndLineEdit(self):
        projects = ["Tag 1", "Tag 2", "Tag 3", "Tag 4", "Tag 5", "Tag 6", "Tag 7", "Tag 8"]
        projects = ["Tag " +str(x+1) for x in range(self.flexSheet[1][self.combobox.currentIndex()]) ]
        projects2 = ["__________Tag 1__________", "Tag 2", "Tag 3", "Tag 4", "__________Tag 5__________", "Tag 6", \
                     "Tag 7", "Tag 8","Tag 9", "Tag 10", "Tag 11", "__________Tag 12_________"]
        projects2 = [x for x in projects2[0:self.flexSheet[1][self.combobox.currentIndex()]]]


       # self.Labels = [QtWidgets.QLabel(x) for x in projects]
        self.lineEdit = [QtWidgets.QLabel(x) for x in projects2]

        self.checkBoxes = [QtWidgets.QCheckBox(x) for x in projects]

        # Create the check uncheck all checkbox
        self.allCheckbox = QtWidgets.QCheckBox("Uncheck all")
        self.layout.addWidget(self.allCheckbox, 6, 2)

        #[self.checkBoxes[x].setAlignment(QtCore.Qt.AlignCenter) for x in range(4)]

        [self.lineEdit[x].setAlignment(QtCore.Qt.AlignCenter) for x in range(self.flexSheet[1][self.combobox.currentIndex()])]

        # position all the elements within the window

        for x in range(len(projects)):
            if x<self.flexSheet[1][self.combobox.currentIndex()]/2:
                self.layout.addWidget(self.lineEdit[x], x+2, 2, 1, 2)
            else:
                self.layout.addWidget(self.lineEdit[x], -1*(self.flexSheet[1][self.combobox.currentIndex()]/2-x)+2, 4, 1, 2)

        for x in range(len(projects)):
            if x < self.flexSheet[1][self.combobox.currentIndex()]/2:
                self.layout.addWidget(self.checkBoxes[x], x+2, 1)
            else:
                self.layout.addWidget(self.checkBoxes[x], -1*(self.flexSheet[1][self.combobox.currentIndex()]/2-x)+2, 6)

        # Set standard values for check boxes

        for x in self.checkBoxes:
            x.setChecked(True)
            x.stateChanged.connect(self.updateCheckUncheckAllFunc)
        self.allCheckbox.setChecked(True)
        self.allCheckbox.stateChanged.connect(self.checkUncheckAllFunc)
        # allow changes in background color for the labels
        for x in self.lineEdit:
            x.setAutoFillBackground(True)
           # x.linkActivated.connect(self.clickedOnRFID)
        
    def addButtons(self):
        self.pushButton_ScanRFID = QtWidgets.QPushButton()
        self.pushButton_ScanRFID.setText("Scan RFID")
        self.layout.addWidget(self.pushButton_ScanRFID , 6, 4)
        self.pushButton_Upload = QtWidgets.QPushButton()
        self.pushButton_Upload.setText("Upload")
        self.layout.addWidget(self.pushButton_Upload, 6, 5)
        self.pushButton_Skip = QtWidgets.QPushButton()
        self.pushButton_Skip.setText("Skip RFID")
        self.layout.addWidget(self.pushButton_Skip, 6, 3)

    def connectButtons(self):
        self.pushButton_ScanRFID.clicked.connect(self.scanForRFID)
        self.pushButton_Upload.clicked.connect(self.upload)
        self.combobox.currentIndexChanged.connect(self.changeHybrid)
        self.pushButton_Skip.clicked.connect(self.skipRFIDButton)

    def changeHybrid(self, index):
        if self.flexSheet[1][index] > len(self.checkBoxes):
            projects = ["Tag " + str(x+1) for x in range(len(self.checkBoxes),self.flexSheet[1][index])]
            projects2 = ["__________Tag 1__________", "Tag 2", "Tag 3", "Tag 4", "__________Tag 5__________", "Tag 6", \
                     "Tag 7", "Tag 8","Tag 9", "Tag 10", "Tag 11", "__________Tag 12_________"]
            projects2 = [x for x in projects2[len(self.lineEdit):self.flexSheet[1][index]]]

            # If the new flex sheet is larger than the previously selected one create additional GUI elements

            self.checkBoxes = self.checkBoxes+[QtWidgets.QCheckBox(x) for x in projects]
            self.lineEdit = self.lineEdit + [QtWidgets.QLabel(x) for x in projects2]
            [self.lineEdit[x].setAlignment(QtCore.Qt.AlignCenter) for x in range(self.flexSheet[1][index])]

            # position all the elements within the window

            for x in range(self.flexSheet[1][index] ):
                if x < self.flexSheet[1][index] / 2:
                    self.layout.addWidget(self.lineEdit[x], x + 2, 2, 1, 2)
                else:
                    self.layout.addWidget(self.lineEdit[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 2, 4, 1, 2)

            for x in range(self.flexSheet[1][index] ):
                if x < self.flexSheet[1][self.combobox.currentIndex()] / 2:
                    self.layout.addWidget(self.checkBoxes[x], x + 2, 1)
                else:
                    self.layout.addWidget(self.checkBoxes[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 2, 6)

                # Set standard values for check boxes

            for x in self.checkBoxes:
                x.setChecked(True)
                x.stateChanged.connect(self.updateCheckUncheckAllFunc)
            self.allCheckbox.setChecked(True)
            self.allCheckbox.setText("Uncheck all")
            self.allCheckbox.stateChanged.connect(self.checkUncheckAllFunc)
                # allow changes in background color for the labels
            for x in self.lineEdit:
                x.setAutoFillBackground(True)

            self.rfidThread = ExtendedQtClasses.ScanForRFID(self.lineEdit, self.checkBoxes)

            self.dataBase.update(self.lineEdit, self.checkBoxes, self.BatchSheet)
            self.rfidThread.colorSetter.connect(self.updateColor, QtCore.Qt.DirectConnection)
            self.rfidThread.received_RFID.connect(self.updateRFID, QtCore.Qt.DirectConnection)
            self.changeRFIDBool.connect(self.rfidThread.changeBool, QtCore.Qt.DirectConnection)

        elif self.flexSheet[1][index] < len(self.checkBoxes):

            # If the new flex sheet is smaller than the previously selected one delete not needed GUI elements

            for x in self.checkBoxes[self.flexSheet[1][index]:]:
                self.layout.removeWidget(x)
                self.checkBoxes.remove(x)
                x.deleteLater()
                x = None

            for x in self.lineEdit[self.flexSheet[1][index]:]:
                self.layout.removeWidget(x)
                self.lineEdit.remove(x)
                x.deleteLater()
                x = None

            # position all the elements within the window

            for x in range(self.flexSheet[1][index] ):
                if x < self.flexSheet[1][index] / 2:
                    self.layout.addWidget(self.lineEdit[x], x + 2, 2, 1, 2)
                else:
                    self.layout.addWidget(self.lineEdit[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 2, 4, 1, 2)

            for x in range(self.flexSheet[1][index] ):
                if x < self.flexSheet[1][self.combobox.currentIndex()] / 2:
                    self.layout.addWidget(self.checkBoxes[x], x + 2, 1)
                else:
                    self.layout.addWidget(self.checkBoxes[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 2, 6)

            # Set standard values for check boxes

            for x in self.checkBoxes:
                x.setChecked(True)
                x.stateChanged.connect(self.updateCheckUncheckAllFunc)
            self.allCheckbox.setChecked(True)
            self.allCheckbox.setText("Uncheck all")
            self.allCheckbox.stateChanged.connect(self.checkUncheckAllFunc)
                # allow changes in background color for the labels
            for x in self.lineEdit:
                x.setAutoFillBackground(True)

            self.rfidThread = ExtendedQtClasses.ScanForRFID(self.lineEdit, self.checkBoxes)
            self.dataBase.update(self.lineEdit, self.checkBoxes, self.BatchSheet)
            self.rfidThread.colorSetter.connect(self.updateColor, QtCore.Qt.DirectConnection)
            self.rfidThread.received_RFID.connect(self.updateRFID, QtCore.Qt.DirectConnection)
            self.changeRFIDBool.connect(self.rfidThread.changeBool, QtCore.Qt.DirectConnection)
        else:
            # If the two flex sheets have the same number of elements no need to change anything.
            pass

    @QtCore.pyqtSlot(int)
    def checkUncheckAllFunc(self, state):
        all_checkboxes = self.checkBoxes
        if all(x.isChecked() for x in all_checkboxes) and not self.allCheckbox.isChecked():
            [x.setChecked(0) for x in all_checkboxes]
        elif self.allCheckbox.isChecked():
            [x.setChecked(1) for x in all_checkboxes]
        else:
            pass

    @QtCore.pyqtSlot(int)
    def updateCheckUncheckAllFunc(self, state):
        all_checkboxes = self.checkBoxes
        if all(x.isChecked() for x in all_checkboxes):
            self.allCheckbox.setText("Uncheck all")
            self.allCheckbox.setChecked(1)
        else:
            self.allCheckbox.setText("Check all")
            self.allCheckbox.setChecked(0)

    """def clickedOnRFID(self, clicked_on):
        for i,x in enumerate(self.lineEdit):
            if x == clicked_on:
                self.checkBoxes[i].setChecked(True)
            else:
                self.checkBoxes[i].setChecked(False)"""

    @QtCore.pyqtSlot(int)
    def currentlySelectedArrayType(self,index):
        #When a different Array is selected change type to match that automatically
        self.combobox.setCurrentIndex(self.usedArrays[1][index])


    def scanForRFID(self):
        green = QtGui.QPalette()
        green.setColor(QtGui.QPalette.Base, QtCore.Qt.green)
        if not self.rfidThread.isRunning():
            self.rfidThread.quit()
        if not self.rfidThread.isRunning():
            self.rfidThread.start()

        #test.wait()

    def updateRFID(self, text,slot, tagNr):
        if self.checkBoxes[tagNr].isChecked():
            slot.setText(text)
            QtCore.QCoreApplication.processEvents()
        else:
            #slot.setText("Skipped tag")
            QtCore.QCoreApplication.processEvents()

    def updateColor(self,color,slot):
        slot.setPalette(color)
        QtCore.QCoreApplication.processEvents()

    def skipRFID(self,bool):
#        global skipBool
#        skipBool = bool
        self.changeRFIDBool.emit(bool)

    def skipRFIDButton(self):
        self.skipRFID(True)

    def upload(self):
        if not self.rfidThread.isRunning() and (not self.dataBThread.isRunning()):
            self.dataBThread.start()
        return 0

    def resizeEvent(self, event):
        f = self.font()
        temp = event.size().height()
        f.setPixelSize(temp / 20)
        self.setFont(f)
        return super().resizeEvent(event)

class MyBoxLayout(QtWidgets.QGridLayout):
    def __init__(self, parent):
        super().__init__(parent)

class GUIThread(QtCore.QThread):
    def __init__(self, name):
        QtCore.QThread.__init__(self)
        self.name = name

    def run(self):
        import sys
        app = QtWidgets.QApplication(sys.argv)

        w = MainWindow()
        w.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    if _ALLOW_AUTH_FROM_CFG:
        config = cf.ConfigParser()
        config.read("./User.txt")
        dataBaseCommunication = db.DataBaseCommunication([config.get("User", "Name1"), config.get("User","Name2")],True)
    else:
        dataBaseCommunication = db.DataBaseCommunication([None, None])

    flextypes ,number ,hybridtypes = dataBaseCommunication.getHybrids()
    usedArrays, typesOfTheArrays = dataBaseCommunication.getComponentList()

    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow(dataBaseCommunication, [flextypes ,number ,hybridtypes],[usedArrays,typesOfTheArrays])
    w.show()
    sys.exit(app.exec_())
