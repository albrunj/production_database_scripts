#!/usr/bin/env python
import time

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import strips.libs.Mercury as Mercury

class ExtendedCombo( QtWidgets.QComboBox ):
    def __init__( self,  parent = None):
        super( ExtendedCombo, self ).__init__( parent )

        self.setFocusPolicy( QtCore.Qt.StrongFocus )
        self.setEditable( True )
        self.completer = QtWidgets.QCompleter( self )

        # always show all completions
        self.completer.setCompletionMode( QtWidgets.QCompleter.UnfilteredPopupCompletion )
        self.pFilterModel = QtCore.QSortFilterProxyModel( self )
        self.pFilterModel.setFilterCaseSensitivity( QtCore.Qt.CaseInsensitive )

        self.completer.setPopup( self.view() )

        self.setCompleter( self.completer )

        self.lineEdit().textEdited.connect( self.pFilterModel.setFilterFixedString )
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def setModel( self, model ):
        super(ExtendedCombo, self).setModel( model )
        self.pFilterModel.setSourceModel( model )
        self.completer.setModel(self.pFilterModel)

    def setModelColumn( self, column ):
        self.completer.setCompletionColumn( column )
        self.pFilterModel.setFilterKeyColumn( column )
        super(ExtendedCombo, self).setModelColumn( column )

    def view( self ):
        return self.completer.popup()

    def index( self ):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
      if text:
        index = self.findText(text)
        self.setCurrentIndex(index)

class ScanForRFID(QtCore.QThread):
    colorSetter = QtCore.pyqtSignal(QtGui.QPalette,QtWidgets.QLineEdit )
    received_RFID = QtCore.pyqtSignal(str,QtWidgets.QLineEdit,int )
    skip_RFID = QtCore.pyqtSignal(bool)
#    stopped = QtCore.pyqtSignal()

    def __init__(self, ComboBox,CheckBox):
        QtCore.QThread.__init__(self)
        self.ComboBoxList = ComboBox
        self.checkBoxes = CheckBox
        self.skipBool = False

    def changeBool(self,boolV):
        self.skipBool = boolV

    def run(self ):
        print("Thread is running!")
        green = QtGui.QPalette()
        green.setColor(QtGui.QPalette.Window, QtCore.Qt.green)
        red = QtGui.QPalette()
        red.setColor(QtGui.QPalette.Window, QtCore.Qt.red)
        yellow = QtGui.QPalette()
        yellow.setColor(QtGui.QPalette.Window, QtCore.Qt.yellow)

        for x,pos in enumerate(self.ComboBoxList):
            if self.checkBoxes[x].isChecked():
                self.received_RFID.emit(str("Scanning for Tags"),pos, x)
        usedTags = []
        for currentIndex,tag in enumerate(self.ComboBoxList):
            RFID = []
            #self.colorSetter.emit(red, tag)
            self.colorSetter.emit(yellow, tag)
            # QtCore.QCoreApplication.processEvents()
            #self.skip_RFID.emit(False)
            self.skipBool = False
            if self.checkBoxes[currentIndex].isChecked():
                temp = []
                i=0
                while temp == "" or temp == [] and not self.skipBool:
                    if i > 50:
                        break
                    RFID, RSSI = Mercury.read(usedTags,RFID)
                    if temp == []:
                        self.received_RFID.emit("Scanning for RFID!", tag, currentIndex)
                    i += 1
                    if RSSI == "404":
                        continue
                    else:
                        temp = RFID
                    if temp == "":
                        self.received_RFID.emit("Tag already scanned!", tag, currentIndex)
                        RFID = []
                if self.skipBool:
                    self.received_RFID.emit("Skipped", tag, currentIndex)
                    self.colorSetter.emit(green, tag)
                    continue
                elif temp == "" or temp == []:
                    self.received_RFID.emit("Could not find tag!", tag, currentIndex)
                    self.colorSetter.emit(red, tag)
                    continue
            else:
                RFID = "Skipped"
                self.colorSetter.emit(green, tag)
                self.received_RFID.emit(str(RFID), tag, currentIndex)
                # self.skip_RFID.emit(False)
                self.skipBool = False
                Mercury.read([], [])
                continue
            self.colorSetter.emit(green, tag)
            self.received_RFID.emit(str(RFID),tag, currentIndex)
            #self.skip_RFID.emit(False)
            self.skipBool = False
            usedTags.append(RFID)
            Mercury.read([],[])
            time.sleep(0.1)
        #lock.lock()
        #waitForRFID.wakeAll()
        #lock.unlock()
        print("All RFIDs read!")
