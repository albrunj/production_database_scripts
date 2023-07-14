#!/usr/bin/env python
# Cedric Hoenig
"""
Information for use:
You will have to place a User.txt file in the same folder.
This file will need to contain the database short for your institution.
For example my file looks like this:
[Institution]
Institution = UNIFREIBURG
"""

_ALLOW_AUTH_FROM_CFG = False

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
import sys
import strips.libs.DatabaseConnection as db
import configparser as cf
import strips.libs.ExtendedQtClasses as ExtendedQtClasses

skipBool = False

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, dataBase, flexSheet,usedPanels,institution, parent=None):
        # self.MainWindow = QtWidgets.QMainWindow()
        super().__init__(parent)
        self.form_widget = FormWidget(self, dataBase, flexSheet=flexSheet,usedPanels=usedPanels,institution=institution)
        self.setCentralWidget(self.form_widget)
        self.setMenuBar(self.createMenubar())
        self.resize(780, 400)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(self.sizePolicy)
        self.setWindowTitle(u"Testpannel register - by Jan Cedric Hönig")

        #self.setWindowIcon(QtGui.QIcon('Bilder/Uni-Logo.png'))

        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.branding = QtSvg.QSvgWidget("../../media/Branding2.svg")
        self.statusbar.addPermanentWidget(self.branding)

    def heightForWidth(self, width):
        return width * 2

    def createMenubar(self):
        self.menubar = QtWidgets.QMenuBar()
        # self.menubar.setGeometry(QtCore.QRect(0, 0, 220, 21))

        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        self.menubar.addAction(self.menuFile.menuAction())
        return self.menubar

class FormWidget(QtWidgets.QWidget):
    colorSetterForm = QtCore.pyqtSignal(QtGui.QPalette, QtWidgets.QLineEdit)
    changeRFIDBool = QtCore.pyqtSignal(bool)

    def __init__(self, parent, dataBase, flexSheet,usedPanels,institution):
        super().__init__(parent)
        self.flexSheet = flexSheet
        self.usedPanels = usedPanels
        self.setLayoutandContent()

        self.dataBase = dataBase
        self.dataBase.update(self.lineEdit, self.checkBoxes, [self.BatchSheet,self.combobox],self.labelSheet,self.checkboxSheet)
        self.dataBThread = db.TestPanelThread(self.dataBase)
        self.dataBThread.withOrWithoutRFID(True)
        self.dataBThread.setInstitution(institution)


        self.rfidThread = ExtendedQtClasses.ScanForRFID([self.labelSheet]+self.lineEdit, [self.checkboxSheet]+self.checkBoxes)
        # self.rfidThread.started.connect(self.rfidThread.changeColor, QtCore.Qt.DirectConnection)
        # self.rfidThread.started.connect(self.rfidThread.changeColor, QtCore.Qt.DirectConnection)

        self.rfidThread.colorSetter.connect(self.updateColor, QtCore.Qt.DirectConnection)
        self.rfidThread.received_RFID.connect(self.updateRFID, QtCore.Qt.DirectConnection)
        self.changeRFIDBool.connect(self.rfidThread.changeBool, QtCore.Qt.DirectConnection)
        self.hideBoxes(True)

    #      self.rfidThread.stopped.connect(self.rfidThread.quit, QtCore.Qt.DirectConnection)

    def setLayoutandContent(self):
        self.layout = MyBoxLayout(self)
        self.layout.setSpacing(10)

        self.addConstantComponents()
        self.addLabelsAndLineEdit()
        self.addButtons()
        self.connectButtons()

        self.setLayout(self.layout)
        #self.hideBoxes(True)

    def addConstantComponents(self):
        BatchSheet = ["Batch", "Sheet"]

        self.BatchSheet = [QtWidgets.QLineEdit(x) for x in BatchSheet]

        self.BatchSheet[1].textChanged.connect(self.ceckifSheetExists)

        self.combobox = QtWidgets.QComboBox()

        self.combobox.addItems(self.flexSheet[0])

        # position all the elements within the window

        self.layout.addWidget(self.combobox, 1, 4, 1, 2)

        self.layout.addWidget(self.BatchSheet[0], 1, 0, 1, 2)
        #self.layout.addWidget(self.BatchSheet[1], 1, 2, 1, 2)

        #Add figure to the sheet box which displays if sheet already exists
        self.label = QtWidgets.QLabel()
        self.PictureYes = QtGui.QPixmap("../../media/YesTick.png")
        self.PictureNo = QtGui.QPixmap("../../media/RedCross.png")
        self.BatchSheet[1].setFrame(0)
        self.NumberLayout = QtWidgets.QHBoxLayout()
        self.NumberLayout.setSpacing(0)
        self.NumberLayout.addWidget(self.label)
        self.NumberLayout.addWidget(self.BatchSheet[1])
        self.label.setPixmap(self.PictureYes.scaledToHeight(self.BatchSheet[1].height() / 17))
        self.label.setScaledContents(1)
        self.layout.addLayout(self.NumberLayout, 1, 2, 1, 2)


        self.showElementsCheckBox = QtWidgets.QCheckBox()
        self.layout.addWidget(self.showElementsCheckBox, 1,6,1,2)
        self.showElementsCheckBox.setText("No RFID present")
        self.showElementsCheckBox.setChecked(1)
        self.showElementsCheckBox.stateChanged.connect(self.hideBoxes)

    def addLabelsAndLineEdit(self):
        projects = ["Tag 1", "Tag 2", "Tag 3", "Tag 4", "Tag 5", "Tag 6", "Tag 7", "Tag 8"]
        projects = ["Tag " + str(x + 1) for x in range(self.flexSheet[1][self.combobox.currentIndex()])]
        projects2 = ["__________Tag 1__________", "Tag 2", "Tag 3", "Tag 4", "__________Tag 5__________", "Tag 6", \
                     "Tag 7", "Tag 8", "Tag 9", "Tag 10", "Tag 11", "__________Tag 12_________"]
        projects2 = [x for x in projects2[0:self.flexSheet[1][self.combobox.currentIndex()]]]

        # Create the check uncheck all checkbox
        self.allCheckbox = QtWidgets.QCheckBox("Check all")
        self.layout.addWidget(self.allCheckbox, 6, 2)

        # self.Labels = [QtWidgets.QLabel(x) for x in projects]
        self.lineEdit = [QtWidgets.QLabel(x) for x in projects2]

        self.checkBoxes = [QtWidgets.QCheckBox(x) for x in projects]

        # [self.checkBoxes[x].setAlignment(QtCore.Qt.AlignCenter) for x in range(4)]

        self.checkboxSheet = QtWidgets.QCheckBox("RFID Sheet (A1)")
        self.labelSheet = QtWidgets.QLabel("________RFID________")
        self.labelSheet.setAutoFillBackground(True)

        self.labelSheet.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.labelSheet, 2, 4, 1, 2)
        self.layout.addWidget(self.checkboxSheet, 2, 6, 1, 2)

        [self.lineEdit[x].setAlignment(QtCore.Qt.AlignCenter) for x in
         range(self.flexSheet[1][self.combobox.currentIndex()])]

        # position all the elements within the window

        for x in range(len(projects)):
            if x < self.flexSheet[1][self.combobox.currentIndex()] / 2:
                self.layout.addWidget(self.lineEdit[x], x + 3, 2, 1, 2)
            else:
                self.layout.addWidget(self.lineEdit[x],
                                      -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 3, 4, 1, 2)

        for x in range(len(projects)):
            if x < self.flexSheet[1][self.combobox.currentIndex()] / 2:
                self.layout.addWidget(self.checkBoxes[x], x + 3, 1)
            else:
                self.layout.addWidget(self.checkBoxes[x],
                                      -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 3, 6)

        # Set standard values for check boxes

        for x in self.checkBoxes:
            x.setChecked(False)
            x.stateChanged.connect(self.updateCheckUncheckAllFunc)
        self.checkboxSheet.setChecked(True)
        self.checkboxSheet.stateChanged.connect(self.updateCheckUncheckAllFunc)
        self.allCheckbox.stateChanged.connect(self.checkUncheckAllFunc)
        # allow changes in background color for the labels
        for x in self.lineEdit:
            x.setAutoFillBackground(True)

    def addButtons(self):
        self.pushButton_ScanRFID = QtWidgets.QPushButton()
        self.pushButton_ScanRFID.setText("Scan RFID")
        self.layout.addWidget(self.pushButton_ScanRFID, 6, 4)
        self.pushButton_Upload = QtWidgets.QPushButton()
        self.pushButton_Upload.setText("Upload")
        self.layout.addWidget(self.pushButton_Upload, 6, 5)
        self.pushButton_Skip = QtWidgets.QPushButton()
        self.pushButton_Skip.setText("Skip RFID")
        self.layout.addWidget(self.pushButton_Skip, 6, 3)

    def connectButtons(self):
        self.pushButton_ScanRFID.clicked.connect(self.scanForRFID)
        self.pushButton_Upload.clicked.connect(self.upload)
        self.combobox.currentIndexChanged.connect(self.changeHybridPlusHideBoxes)
        self.pushButton_Skip.clicked.connect(self.skipRFIDButton)

    def changeHybrid(self, index):
        if self.flexSheet[1][index] > len(self.checkBoxes):
            projects = ["Tag " + str(x + 1) for x in range(len(self.checkBoxes), self.flexSheet[1][index])]
            projects2 = ["__________Tag 1__________", "Tag 2", "Tag 3", "Tag 4", "__________Tag 5__________", "Tag 6", \
                         "Tag 7", "Tag 8", "Tag 9", "Tag 10", "Tag 11", "__________Tag 12_________"]
            projects2 = [x for x in projects2[len(self.lineEdit):self.flexSheet[1][index]]]

            # If the new flex sheet is larger than the previously selected one create additional GUI elements

            self.checkBoxes = self.checkBoxes + [QtWidgets.QCheckBox(x) for x in projects]
            self.lineEdit = self.lineEdit + [QtWidgets.QLabel(x) for x in projects2]
            [self.lineEdit[x].setAlignment(QtCore.Qt.AlignCenter) for x in range(self.flexSheet[1][index])]

            # position all the elements within the window

            for x in range(self.flexSheet[1][index]):
                if x < self.flexSheet[1][index] / 2:
                    self.layout.addWidget(self.lineEdit[x], x + 3, 2, 1, 2)
                else:
                    self.layout.addWidget(self.lineEdit[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 3, 4, 1, 2)

            for x in range(self.flexSheet[1][index]):
                if x < self.flexSheet[1][self.combobox.currentIndex()] / 2:
                    self.layout.addWidget(self.checkBoxes[x], x + 3, 1)
                else:
                    self.layout.addWidget(self.checkBoxes[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 3, 6)

                # Set standard values for check boxes

            for x in self.checkBoxes:
                x.setChecked(False)
                x.stateChanged.connect(self.updateCheckUncheckAllFunc)
                # allow changes in background color for the labels
            for x in self.lineEdit:
                x.setAutoFillBackground(True)
            self.rfidThread = ExtendedQtClasses.ScanForRFID([self.labelSheet]+self.lineEdit, [self.checkboxSheet]+self.checkBoxes)

            self.dataBase.update(self.lineEdit, self.checkBoxes, self.BatchSheet, self.labelSheet, self.checkboxSheet)
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

            for x in range(self.flexSheet[1][index]):
                if x < self.flexSheet[1][index] / 2:
                    self.layout.addWidget(self.lineEdit[x], x + 3, 2, 1, 2)
                else:
                    self.layout.addWidget(self.lineEdit[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 3, 4, 1, 2)

            for x in range(self.flexSheet[1][index]):
                if x < self.flexSheet[1][self.combobox.currentIndex()] / 2:
                    self.layout.addWidget(self.checkBoxes[x], x + 3, 1)
                else:
                    self.layout.addWidget(self.checkBoxes[x],
                                          -1 * (self.flexSheet[1][self.combobox.currentIndex()] / 2 - x) + 3, 6)

            # Set standard values for check boxes

            for x in self.checkBoxes:
                x.setChecked(False)
                x.stateChanged.connect(self.updateCheckUncheckAllFunc)
                # allow changes in background color for the labels
            for x in self.lineEdit:
                x.setAutoFillBackground(True)
            self.rfidThread = ExtendedQtClasses.ScanForRFID([self.labelSheet]+self.lineEdit, [self.checkboxSheet]+self.checkBoxes)
            self.dataBase.update(self.lineEdit, self.checkBoxes, self.BatchSheet, self.labelSheet, self.checkboxSheet)
            self.rfidThread.colorSetter.connect(self.updateColor, QtCore.Qt.DirectConnection)
            self.rfidThread.received_RFID.connect(self.updateRFID, QtCore.Qt.DirectConnection)
            self.changeRFIDBool.connect(self.rfidThread.changeBool, QtCore.Qt.DirectConnection)
        else:
            # If the two flex sheets have the same number of elements no need to change anything.
            pass

    @QtCore.pyqtSlot(int)
    def checkUncheckAllFunc(self, state):
        all_checkboxes = self.checkBoxes+[self.checkboxSheet]
        if all(x.isChecked() for x in all_checkboxes) and not self.allCheckbox.isChecked():
            [x.setChecked(0) for x in all_checkboxes]
        elif self.allCheckbox.isChecked():
            [x.setChecked(1) for x in all_checkboxes]
        else:
            pass

    @QtCore.pyqtSlot(int)
    def updateCheckUncheckAllFunc(self, state):
        all_checkboxes = self.checkBoxes + [self.checkboxSheet]
        if all(x.isChecked() for x in all_checkboxes):
            self.allCheckbox.setText("Uncheck all")
            self.allCheckbox.setChecked(1)
        else:
            self.allCheckbox.setText("Check all")
            self.allCheckbox.setChecked(0)

    @QtCore.pyqtSlot(str)
    def ceckifSheetExists(self,text):
        try:
            if int(text) in self.usedPanels:
                self.label.setScaledContents(0)
                self.label.setPixmap(self.PictureNo.scaledToHeight(self.BatchSheet[1].height() ))
                self.label.setScaledContents(1)
            else:
                self.label.setScaledContents(0)
                self.label.setPixmap(self.PictureYes.scaledToHeight(self.BatchSheet[1].height() ))
                self.label.setScaledContents(1)
        except:
            self.label.setScaledContents(0)
            self.label.setPixmap(self.PictureNo.scaledToHeight(self.BatchSheet[1].height() ))
            self.label.setScaledContents(1)

    def changeHybridPlusHideBoxes(self,index):
        if self.showElementsCheckBox.isChecked():
            pass
        else:
            self.hideBoxes(False)

    def hideBoxes(self,truthvalue):
        if truthvalue:
            try:
                self.dataBThread.withOrWithoutRFID(True)
                for x in self.checkBoxes:
                    self.layout.removeWidget(x)
                    x.deleteLater()
                    x = None
                for x in self.lineEdit:
                    self.layout.removeWidget(x)
                    x.deleteLater()
                    x = None
                self.checkBoxes =[]
                self.lineEdit = []
                self.layout.removeWidget(self.checkboxSheet)
                self.checkboxSheet.deleteLater()
                self.checkboxSheet = None
                self.checkboxSheet =[]
                self.labelSheet.setText("Argh Ich bin ewig ...")
                self.layout.removeWidget(self.labelSheet)
                self.labelSheet.deleteLater()
                self.labelSheet = None
                self.labelSheet = []
            except BaseException:
                pass
        else:
            self.dataBThread.withOrWithoutRFID(False)
            if self.checkboxSheet == []:
                self.checkboxSheet = QtWidgets.QCheckBox("RFID Sheet (A1)")
                self.labelSheet = QtWidgets.QLabel("________RFID________")
                self.labelSheet.setAutoFillBackground(True)

                self.labelSheet.setAlignment(QtCore.Qt.AlignCenter)
                self.layout.addWidget(self.labelSheet, 2, 4, 1, 2)
                self.layout.addWidget(self.checkboxSheet, 2, 6, 1, 2)
            self.changeHybrid(self.combobox.currentIndex())

    def skipRFID(self, bool):
        #        global skipBool
        #        skipBool = bool
        self.changeRFIDBool.emit(bool)

    def skipRFIDButton(self):
        self.skipRFID(True)

    def scanForRFID(self):
        if not self.rfidThread.isRunning():
            self.rfidThread.quit()
        if not self.rfidThread.isRunning():
            self.rfidThread.start()

        # test.wait()

    def updateRFID(self, text, slot, tagNr):
        tmp = [self.checkboxSheet]+self.checkBoxes
        if tagNr == 1337:
            slot.setText(text)
            QtCore.QCoreApplication.processEvents()
        elif tmp[tagNr].isChecked():
            slot.setText(text)
            QtCore.QCoreApplication.processEvents()
        else:
            slot.setText("Skipped tag")
            QtCore.QCoreApplication.processEvents()

    def updateColor(self, color, slot):
        slot.setPalette(color)
        QtCore.QCoreApplication.processEvents()

    def upload(self):
        if not self.rfidThread.isRunning() and (not self.dataBThread.isRunning()):
            self.dataBThread.start()
        return 0

    def resizeEvent(self, event):
        f = self.font()
        temp = event.size().height()
        f.setPixelSize(temp / 20)
        self.setFont(f)
        #self.label.setPixmap(self.Picture.scaledToHeight(self.BatchSheet[1].height() / 17))
        return super().resizeEvent(event)

class MyBoxLayout(QtWidgets.QGridLayout):
    def __init__(self, parent):
        super().__init__(parent)

class GUIThread(QtCore.QThread):
    def __init__(self, name):
        QtCore.QThread.__init__(self)
        self.name = name

    def run(self):
        app = QtWidgets.QApplication(sys.argv)

        w = MainWindow()
        w.show()
        sys.exit(app.exec_())

if __name__ == "__main__":

    config = cf.ConfigParser()
    config.read("./User.txt")

    if _ALLOW_AUTH_FROM_CFG:
        dataBaseCommuncation = db.DataBaseTestPanel([config.get("User", "Name1"), config.get("User","Name2")],True)
    else:
        dataBaseCommuncation = db.DataBaseTestPanel([None, None],False)

    flextypes ,number ,hybridtypes, nrhybrids= dataBaseCommuncation.getTestpanel()
    #print([flextypes ,number ,hybridtypes, nrhybrids])
    usedPanels = dataBaseCommuncation.getComponentList()

    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow(dataBaseCommuncation, [flextypes ,number ,hybridtypes],usedPanels, \
                   config.get("Institution","Institution"))
    w.show()
    sys.exit(app.exec_())
