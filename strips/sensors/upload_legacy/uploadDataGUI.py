#Upload Generic Data with a GUI
#Created Jun 10 2019
#Written by Nashad Rahman rahman.176@osu.edu
#GoBucks

if __name__ == '__main__':
    from __path__ import updatePath

    updatePath()

from itk_pdb.dbAccess import ITkPDSession

import ast
import sys

from PyQt5 import QtCore

# Extra imports needed to display loge
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QMainWindow,
    QLabel,
    QCheckBox,
    QWidget,
    QApplication,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QTabWidget,
    QGridLayout,
    QPlainTextEdit,
)

import re
import json
import os
from itk_pdb.ITkPDLoginGui import ITkPDLoginGui


session = ITkPDSession()

class uploadDataOptions: # Stores options in one class to avoid being passed around individually
    def __init__(self):
        #self.session = ITkPDSession()
        self.ignoreBlanks = False
        self.makeJSON = False
        self.allowUpload = True
        self.delimiter = [":", ": ", "\t", "= "]
        self.dataTitleOpen = "%%"
        self.dataTitleClose = "/%"
        self.dataHeaderSymbol = "%"
        self.defaultValues = ""
        self.overrideValues = ""
        self.replacementValues = ""

    def toDict(self):

        return{"ignoreBlanks":self.ignoreBlanks,
               "delimiter":self.delimiter,
               "defaultValuesText":self.defaultValues,
               "overrideValues" :self.overrideValues,
               "replacementValues" :self.replacementValues}



##############GUI STUFF##############

class App(QMainWindow):

    def __init__(self):
        super(App, self).__init__()
        self.title = 'Upload Data to Database'
        self.left = 100
        self.top = 100
        self.width = 700
        self.height = 350

        # Add ITK logo to GUI
        label = QLabel(self)
        pixmap = QPixmap('../../media/logo.png')
        label.setPixmap(pixmap)
        label.setGeometry(700,50, 200, 100)

        self.initUI()

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)


    def initUI(self):
        ITkPDLoginGui(session, self)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)


# Makes Separate Tabs and objects within tabs
class MyTableWidget(QWidget):

    def __init__(self, parent):

        global delimiter

        self.currentOptions = uploadDataOptions()

        super(QWidget, self).__init__(parent)
        self.layout = QGridLayout()
        self.selectedFile = "No file or directory selected"

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Upload")
        self.tabs.addTab(self.tab2, "Options")

        ####Tab 1####

        # Layout Formatting
        self.tab1.layout = QGridLayout()

        self.tab1.layout.setColumnStretch(0, 1)
        self.tab1.layout.setColumnStretch(4, 1)
        self.tab1.layout.setColumnStretch(2, 10)
        self.tab1.layout.setRowStretch(0, 1)
        self.tab1.layout.setRowStretch(3, 1)

        # File Name Label (not input)
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('File or Directory Name:')
        self.tab1.layout.addWidget(self.nameLabel,1,1)
        self.nameLabel.setMaximumSize(150, 15)

        # File input text
        self.line = QLineEdit(self)
        self.line.setText(self.selectedFile)
        self.tab1.layout.addWidget(self.line,1,2)
        self.line.setMinimumSize(550, 30)

        # Select File Button
        self.fileSelect = QPushButton('Select File', self)
        self.fileSelect.setToolTip('Open window to select file location')
        self.fileSelect.clicked.connect(self.file_on_click)
        self.fileSelect.setMaximumSize(100, 30)
        self.tab1.layout.addWidget(self.fileSelect,1,3)
        self.tab1.setLayout(self.tab1.layout)

        # Final Upload Button
        self.uploadFiles = QPushButton('Upload', self)
        self.uploadFiles.setToolTip('Uploads selected file to database')
        self.uploadFiles.move(300, 170)
        self.uploadFiles.setMaximumSize(300, 30)
        self.uploadFiles.clicked.connect(self.upload_on_click)
        self.tab1.layout.addWidget(self.uploadFiles,3,2, QtCore.Qt.AlignCenter)


        ####Tab 2####
        self.tab2.layout = QGridLayout()

        # Ignore Blanks Checkbox
        self.ignoreBlanks = QCheckBox("Ignore Blanks", self)
        self.tab2.layout.addWidget(self.ignoreBlanks, 0, 2)

        # Save JSON Check Box
        self.JSONCheck = QCheckBox("Save a copy of .JSON file", self)
        self.JSONCheck.stateChanged.connect(self.whichAreChecked)
        self.tab2.layout.addWidget(self.JSONCheck, 0, 3)

        # Allow Upload Check Box
        self.stopUploadCheck = QCheckBox("Do not upload, but check values", self)
        self.stopUploadCheck.stateChanged.connect(self.whichAreChecked)
        self.tab2.layout.addWidget(self.stopUploadCheck, 0, 4)


        # Delimiter Label (not input)
        self.delimiterLabel = QLabel(self)
        self.delimiterLabel.setText('Delimiters:')
        self.tab2.layout.addWidget(self.delimiterLabel, 1, 1)

        # Set a delimiter
        self.delimiterText = QLineEdit(self)
        self.delimiterText.setText(str(self.currentOptions.delimiter)[1:-1])
        self.tab2.layout.addWidget(self.delimiterText, 1, 2)
        self.delimiterText.setMinimumSize(100, 30)


        # Data Title Open Label (not input)
        self.dataOpenLabel = QLabel(self)
        self.dataOpenLabel.setText('Data Header Open:')
        self.tab2.layout.addWidget(self.dataOpenLabel, 2, 1)


        # Set a Data Title Opener
        self.dataTitleOpenText = QLineEdit(self)
        self.dataTitleOpenText.setText(str(self.currentOptions.dataTitleOpen))
        self.tab2.layout.addWidget(self.dataTitleOpenText, 2, 2)
        self.dataTitleOpenText.setMinimumSize(50, 30)


        # Data Title Close Label (not input)
        self.dataCloseLabel = QLabel(self)
        self.dataCloseLabel.setText('Data Header Close:')
        self.tab2.layout.addWidget(self.dataCloseLabel, 3, 1)

        # Set a Data Title Closer
        self.dataTitleCloseText = QLineEdit(self)
        self.dataTitleCloseText.setText(str(self.currentOptions.dataTitleClose))
        self.tab2.layout.addWidget(self.dataTitleCloseText, 3, 2)
        self.dataTitleCloseText.setMinimumSize(50, 30)

        # Data Header Symbol Label (not input)
        self.dataCloseLabel = QLabel(self)
        self.dataCloseLabel.setText('Data Header First Symbol:')
        self.tab2.layout.addWidget(self.dataCloseLabel, 4, 1)

        # Set a Data Header Symbol
        self.dataHeaderSymbolText = QLineEdit(self)
        self.dataHeaderSymbolText.setText(str(self.currentOptions.dataHeaderSymbol))
        self.tab2.layout.addWidget(self.dataHeaderSymbolText, 4, 2)
        self.dataHeaderSymbolText.setMinimumSize(50, 30)

        # Default Values Label (not input)
        self.defaultValuesText = QLabel(self)
        self.defaultValuesText.setText('Default Values:')
        self.tab2.layout.addWidget(self.defaultValuesText, 5, 2)

        # Set Default Values Text
        self.defaultValuesText = QPlainTextEdit(self)
        self.tab2.layout.addWidget(self.defaultValuesText, 6, 2)
        self.defaultValuesText.setMinimumSize(150, 30)

        # Override Values Label (not input)
        self.overrideValues = QLabel(self)
        self.overrideValues.setText('Override Values:')
        self.tab2.layout.addWidget(self.overrideValues, 5, 3)

        # Set override values
        self.overrideValues = QPlainTextEdit(self)
        self.tab2.layout.addWidget(self.overrideValues, 6, 3)
        self.overrideValues.setMinimumSize(150, 30)

        # Replace Keys Label (not input)
        self.replacementLabel = QLabel(self)
        self.replacementLabel.setText('Replacement Keys:')
        self.tab2.layout.addWidget(self.replacementLabel, 5, 4)

        # Set Replacement Keys
        self.replacementValues = QPlainTextEdit(self)
        self.tab2.layout.addWidget(self.replacementValues, 6, 4)
        self.replacementValues.setMinimumSize(150, 30)


        # Add tabs to widget
        self.tab1.setLayout(self.tab1.layout)
        self.tab2.setLayout(self.tab2.layout)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def whichAreChecked(self): # Changes the label of the upload button to make sure people are aware if it will not upload

        if self.JSONCheck.isChecked() and self.stopUploadCheck.isChecked():
            self.uploadFiles.setText("Create JSON (No Upload)")

        if self.JSONCheck.isChecked() and not self.stopUploadCheck.isChecked():
            self.uploadFiles.setText("Create JSON and Upload")

        if not self.JSONCheck.isChecked() and not self.stopUploadCheck.isChecked():
            self.uploadFiles.setText("Upload")

        if not self.JSONCheck.isChecked() and  self.stopUploadCheck.isChecked():
            self.uploadFiles.setText("Check Values (No Upload)")



    def file_on_click(self): # Changes the data entry to file name

        self.selectedFile = self.openFileNameDialog()

        self.line.setText(str(self.selectedFile))

        self.show()

    def openFileNameDialog(self):   # opens a QT5 file dialogue
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Data Files (*.dat)", options=options)

        return (fileName)

    def upload_on_click(self): # Updates all the options and passes it

        self.currentOptions.ignoreBlanks = self.ignoreBlanks.isChecked()
        self.currentOptions.makeJSON = self.JSONCheck.isChecked()
        self.currentOptions.allowUpload = not self.stopUploadCheck.isChecked()
        self.currentOptions.delimiter = ast.literal_eval(
            "[" + str(self.delimiterText.text()) + "]"
        )
        self.currentOptions.defaultValues = self.defaultValuesText.toPlainText()
        self.currentOptions.overrideValues = self.overrideValues.toPlainText()
        self.currentOptions.replacementValues = self.replacementValues.toPlainText()
        self.currentOptions.dataTitleOpen = self.dataTitleOpenText.text()
        self.currentOptions.dataTitleClose = self.dataTitleCloseText.text()
        self.currentOptions.dataHeaderSymbol = self.dataHeaderSymbolText.text()

        passFileOrFolder(str(self.line.text()), self.currentOptions)


def YesOrNo(text):  # Easily calls and returns y/n

    dec = YesNo()
    dec.initUI(text)
    dec2 = dec.getDec()

    if dec2:
        return True
    else:
        return False


class YesNo(QWidget):   # Recycled for every y/n prompt

    def __init__(self):
        super(YesNo, self).__init__()
        self.title = "Prompt"
        self.left = 100
        self.top = 100
        self.width = 320
        self.height = 200
        self.decision = False

    def initUI(self, text):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        buttonReply = QMessageBox.question(self, 'PyQt5 message', text,
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.decision =  True

        else:
            self.decision = False


        self.show()

    def getDec(self):
        return self.decision

    def __repr__(self):
        return repr(self.decision)

    def __str__(self):
        return self.decision


def textInput(text):                 # Easily calls and returns text

    dec = TextInput()
    dec.initUI(text)
    dec2 = dec.userInput

    return dec2


class TextInput(QWidget):            # Recycled for every text prompt

    def __init__(self):
        super(TextInput, self).__init__()
        self.title = 'Request input'
        self.userInput = "notset"
        self.left = 100
        self.top = 100

    def initUI(self, text):
        self.setWindowTitle(self.title)
        self.setGeometry(10, 10, 640, 480)
        self.getText(text)
        self.show()

    def getText(self, propmtText):
        text, okPressed = QInputDialog.getText(self, "Get text", propmtText, QLineEdit.Normal, "")
        if okPressed and text != '':
            self.userInput = text


class Prompt(QWidget):

    def __init__(self):
        super(Prompt, self).__init__()
        self.title = 'Upload Data to Database'
        self.left = 100
        self.top = 100
        self.width = 500
        self.height = 250
        self.selectedFile = 0
        self.initUI()


def passFileOrFolder(inputLocation, currentOptions):

    if os.path.isdir(inputLocation):

        dec = False
        dec = YesOrNo("\nInput is a directory, please be sure only data files are present."
                      "\n\nWould you like to continue? (y/n) ")

        if not dec:
            return

        elif dec:

            for filename in os.listdir(inputLocation):  # Cycles through all files in the directory

                DataToPass(inputLocation, currentOptions)

    elif os.path.isfile(inputLocation):

        DataToPass(inputLocation, currentOptions)

    else:
        dec = False
        dec = YesOrNo("Invalid input location.\n\n Would you like to try again?")

        if dec:
            return
        if not dec:
            return


####################Object which stores and uploads data####################

class DataToPass:

    def __init__(self,inputLocation, currentOptions):     # Initializes data with empty dictionary
        self.py_dict = {}
        self.inputLocation = inputLocation
        self.currentOptions = currentOptions

        self.extractInfoFromFile(inputLocation, currentOptions)

    def getDto(self, session, code, componentType, project):        # Gets a sample Dto

        try:
            dtoString = session.doSomething('generateTestTypeDtoSample', 'GET',{'code': code,
                                                                                'componentType': componentType,
                                                                                'project': project,
                                                                                'requiredOnly': False})

        except:
            dec = True
            dec = YesOrNo("INVALID INFORMATION TO GET DTO!\n\nWould you like to try again?")
            if dec:
                return
            else:
                return


        self.py_dict = dtoString["dtoSample"]

    def clearDict(self, dictionary):                # Clear the Dto sample acquired from the database
                                                    # (First step after getting Dto)
        for key, value in dictionary.items():

            if isinstance(value, list):
                dictionary[key] = []

            elif isinstance(value, dict):
                self.clearDict(value)

            else:
                dictionary[key] = "notset"

    def setInfo(self, dicti, gkey, ginfo):          # Loops through an input dictionary, finding keys that match gkey,
                                                    # replacing its value with ginfo (Second step)
        for key, value in dicti.items():

            if isinstance(value, dict):
                self.setInfo(value, gkey, ginfo)

            else:
                if key.upper() == gkey.upper():
                    dicti[key] = ginfo

    def search_notset(self, info, inputLocation):   # Searches to see if any spaces have not been filled in,
                                                    # prompts user to manually input (Final step before upload)

        for key, value in info.items():

            if "notset" == info[key] or info[key] == [] or info[key] == None or info[key] == "":
                dec = False
                dec = YesOrNo("WARNING: No value for \"" + key + "\" found in \n\n" + inputLocation +
                              "\n\nWould you like to continue?")

                if not dec:
                    exit()
                elif dec:
                    dec = False
                    dec = YesOrNo("Would you like to manually input a value?")

                    if not dec:
                        continue
                    elif dec:

                        manualInput = textInput("Enter value for " + key + ": ")

                        if str(manualInput).upper() == "TRUE":
                            manualInput = True
                        if str(manualInput).upper() == "FALSE":
                            manualInput = False

                        info[key] = manualInput
                        # GoBucks

            elif isinstance(value, dict):
                self.search_notset(value, inputLocation)

    # Allow function to easily set values in dictionary, can be reused by other code
    def setBasic(self, pName, pValue):
        self.py_dict[pName] = pValue

    def setProperties(self, pName, pValue):
        self.py_dict["properties"][pName] = pValue

    def setResults(self, pName, pValue):
        self.py_dict["results"][pName] = pValue

    def addData(self, dName, dValue):
        self.py_dict["results"][dName].append(dValue)

    # Uploads data to Itk DB
    def upload(self, session, inputLocation):

        ex.statusBar().showMessage("Uploading... ")
        ex.show()

        if self.currentOptions.allowUpload:
            try:

                session.doSomething('uploadTestRunResults', 'POST', data=self.py_dict)

                if len(inputLocation) >= 100:
                    ex.statusBar().showMessage("Successfully uploaded: ..." + inputLocation[-100:])
                    ex.show()
                else:
                    ex.statusBar().showMessage("Successfully uploaded: " + inputLocation)
                    ex.show()

            except:
                dec = False
                dec = YesOrNo("UPLOAD FAILED \n\n Would you like to try again?")
                if dec:
                    self.upload(session, inputLocation)

                if not dec:
                    return

                ex.statusBar().showMessage("Upload Failed")
                ex.show()

        if self.currentOptions.makeJSON:
            with open(inputLocation+".JSON", "w+") as saveJSON:
                saveJSON.write(str(json.dumps(self.py_dict)))

    def extractInfoFromFile(self, inputLocation, currentOptions):

        # Dear Future Coder, I apologize for making this a bit part a bit confusing so here's how it works
        # It takes in the input file location and checks if it is a JSON file
        # If it is a JSON file, it looks for override values it can replace in the JSON file
        # If it is not a JSON file, it reads through every line and searches for every delimiter that was entered
        # If the delimiter is found along with project, component, or test type,
        # then it stores the information that follows
        # If project, component, and test type are found, a sample Dto is retrieved from the database
        # If any are missing, it will prompt the user
        # The program then goes through every line in the default list and the file and searches for every delimiter
        # If a delimiter is found it will split the data into two pieces and try to add it to the sample DTo
        # If a % is found the program sees a data header
        # At the end it tries to upload

        replaceKeys = {}

        defList = currentOptions.defaultValues.split("\n")
        ovrList = currentOptions.overrideValues.split("\n")
        repList = currentOptions.replacementValues.split("\n")
        delimiter = currentOptions.delimiter
        dataTitles = []

        for line in repList:

            for delim in delimiter:

                pos = line.find(delim)

                if (pos != -1):
                    keyInFile = line[:(pos)]
                    keyInDTo = line[(pos + len(delim)):]

                    replaceKeys.update({keyInFile : keyInDTo})

        if inputLocation[-4:].upper() == "JSON": # Checks to see if the Data is already a JSON file

            try: # Try to open file and load it as a JSON
                with open(inputLocation) as js:
                    self.py_dict = json.load(js)

            except:
                dec = False
                dec = YesOrNo("INVALID INPUT LOCATION OR IMPROPER JSON FORMAT \n\n Would you like to try again?")
                if not dec:
                    return
                elif dec:
                    return

            for line in ovrList:

                for delim in delimiter:

                    pos = line.find(delim)         # Information will be extracted if a delimiter is present

                    if (pos != -1):
                        info_desc = line[:(pos)]
                        extracted = line[(pos + len(delim)):]


                    try:
                        self.setInfo(self.py_dict, info_desc, extracted)
                    except ValueError:
                        continue


        else:   # If not a JSON file, will parse through and get info and fill in a sample dto

            try:
                with open(inputLocation) as f:
                    fileData = f.read().splitlines()
            except:
                dec = False
                dec = YesOrNo("COULD NOT READ IN FILE:\n"+ inputLocation +"\n\n Would you like to try again?")
                if not dec:
                    return
                elif dec:
                    return


            all = defList + fileData + ovrList  # Combines all data values
            allExceptOvr = defList + fileData   # Combines all except override values, so they can be used last

            reqForDto = {"project": "", "componentType": "", "testType": ""}

            for line in all:                    # Checks through every line using every delimitter
                                                # for the information required to get a Dto sample

                for delim in delimiter:

                    for label in reqForDto:

                        if label + delim in line:

                            reqForDto[label] = line[len(label + delim):]

            try:                                # Checks if all values present
                inputLocation + reqForDto["project"] + reqForDto["componentType"] + reqForDto["testType"]

            except:

                dec = False
                dec = YesOrNo("Not enough info to get Dto for " + inputLocation +
                              "\n\nWould you like to manually input values?")

                if not dec:
                    return
                elif dec:                       # Manually fill in info that is missing
                    try: reqForDto["project"]
                    except: reqForDto["project"] = textInput("Enter project (S or P): ")

                    try: reqForDto["componentType"]
                    except: reqForDto["componentType"] = textInput("Enter component type (e.g. SENSOR): ")

                    try: reqForDto["testType"]
                    except: reqForDto["testType"] = textInput("Enter test type (e.g. SENSOR_STRIP_TEST): ")

            # Once enough info, get DTo Sample
            try:
                self.getDto(session, reqForDto["testType"], reqForDto["componentType"], reqForDto["project"])
            except:
                dec = False
                dec = YesOrNo("Unable to get Dto from Itk PDB, please check that PROJECT, COMPONENT TYPE, and"
                              " TEST TYPE match database exactly.\n\nWould you like to try again?")
                if not dec:
                    return

            # Then Clear the dictionary
            self.clearDict(self.py_dict)

            ##### Look through every line and try to fill in dictionary ######

            lineIsData = False                              # Changes to true once data is detected

            for line in allExceptOvr:                       # Go through every line

                for delim in delimiter:                     # Search for every Delimiter

                    pos = line.find(delim)                  # Information will be extracted if a delimiter is present

                    if (pos != -1) :

                        info_desc = line[:(pos)]
                        extracted = line[(pos + len(delim)):]

                        if info_desc in replaceKeys.keys():  # Change the Key if any change Keys are present
                            info_desc = replaceKeys[info_desc]

                        self.setInfo(self.py_dict, info_desc, extracted)

                # Add data to array once data header is reached
                if lineIsData:

                    lineData = line.split()

                    for m , title in enumerate(dataTitles):

                       self.addData(str(title), lineData[m])

                # Check if line is a data header and if so add data titles
                try:
                    if line[0] == currentOptions.dataHeaderSymbol:      # Indicates that the following lines are data and the current one is data

                        lineData = line.split()

                        dataTitles = []

                        for string in lineData:

                            try:
                                dataTitles.append((re.findall(currentOptions.dataTitleOpen+"(.*)"+currentOptions.dataTitleClose, string)[0]))
                            except AttributeError:
                                continue

                        lineIsData = True
                except ValueError:
                    continue

            for line in ovrList:

                for delim in delimiter:

                    pos = line.find(delim)  # Information will be extracted if a colon is present

                    if (pos != -1):
                        info_desc = line[:(pos)]
                        extracted = line[(pos + 2):]

                        self.setInfo(self.py_dict, info_desc, extracted)

            if not currentOptions.ignoreBlanks:
                try:
                    self.search_notset(self.py_dict, inputLocation)
                    self.upload(session, inputLocation)
                except: None
            else:
                self.upload(session, inputLocation)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()

    sys.exit(app.exec_())
