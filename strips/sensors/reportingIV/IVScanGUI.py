#!/usr/bin/python3
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

from math import exp
import sys,os

# Database access
from itk_pdb.ITkPDLoginGui import ITkPDLoginGui
from itk_pdb.dbAccess import ITkPDSession

# Qt5 for GUI
from PyQt5.QtWidgets import (QWidget, QLabel, 
                             QComboBox, QApplication, QPushButton, QSizePolicy,
                             QCalendarWidget,QLineEdit)
from PyQt5.QtCore import QDate

# matplotlib for figures
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# For saving ROOT output
RootOk = True
try:
    from ROOT import TFile,TGraph
    from array import array
except ImportError:
    RootOk = False

# For tracking timing
from datetime import datetime

# line styles
stylelist = ["bo-","ro-","go-","mo-","ko-"]

def scaleCurrentWithTemperature(I,T,TRef=0.):
    T += 273.15
    TRef += 273.15
    Eg = 1.21 #eV 
    kB = 8.617333262e-5 #eV K^-1
    ITRef = I*((TRef/T)**2)*exp(-1*(Eg/(2*kB))*((1./TRef) - (1./T)))
    return ITRef

def scaleCurrentWithArea(I,sensorType):
    if sensorType == "LS" or sensorType == "SS" or sensorType == "SL":
        area = 9.7621*9.7950 # Barrel LS/SS (cm^2)
    elif sensorType == "R0":
        area = 89.9031 # cm^2
    elif sensorType == "R1":
        area = 89.0575 # cm^2
    elif sensorType == "R2":
        area = 74.1855 # cm^2
    elif sensorType == "R3":
        area = 80.1679 # cm^2
    elif sensorType == "R4":
        area = 87.4507 # cm^2
    elif sensorType == "R5":
        area = 91.1268 # cm^2
    else:
        raise Exception("Unknown sensor type: %s" % sensorType)
    return (I/area) # uA/cm^2
    

class Example(QWidget):
    
    def __init__(self):
        super().__init__()
        self.startDate = QDate(-9999,9,9)
        self.endDate = QDate(9999,9,9)
        self.session = ITkPDSession()
        self.debug = False
        self.initUI()
        
    def initUI(self):      

        self.setGeometry(200, 50, 600, 720)
        self.setWindowTitle('IV Scan GUI')

        self.startCal = QCalendarWidget(self)
        self.startCal.move(20,100)
        self.startCal.clicked.connect(self.startCalClicked)
        self.startCalTitle = QLabel("Start Date",self)
        self.startCalTitle.move(40,80)
        self.startCal.setSelectedDate(QDate(2018,1,1))

        self.endCal = QCalendarWidget(self)
        self.endCal.move(310,100)
        self.endCal.clicked.connect(self.endCalClicked)
        self.endCalTitle = QLabel("End Date",self)
        self.endCalTitle.move(340,80)

        self.l0 = QLabel("To start, set date range:                     ",self)
        self.l0.move(30,20)

        self.continueButton = QPushButton("All Dates",self)
        self.continueButton.move(450,15)
        self.continueButton.clicked.connect(self.selectionGui)

        self.clearStartButton = QPushButton("Clear Start",self)
        self.clearStartButton.move(200,75)
        self.clearStartButton.hide()
        self.clearStartButton.clicked.connect(self.clearStart)

        self.clearEndButton = QPushButton("Clear End",self)
        self.clearEndButton.move(490,75)
        self.clearEndButton.hide()
        self.clearEndButton.clicked.connect(self.clearEnd)

        if os.environ.get("ITK_DB_AUTH"):
            self.session.authenticate()
            self.show()
        else:
            ITkPDLoginGui(self.session, self)

    def updateDateLabel(self):
        if self.endDate.year() > 2100:
            if self.startDate.year() < 1900:
                self.l0.setText("Date range: All")
                self.continueButton.setText("All Dates")
            else:
                self.l0.setText("Date range: %i-%02d-%02d to ****-**-**" % (self.startDate.year(),self.startDate.month(),self.startDate.day()))
                self.continueButton.setText("Continue")
        else:
            self.continueButton.setText("Continue")
            if self.startDate.year() < 1900:
                self.l0.setText("Date range: ****-**-** to %i-%02d-%02d" % (self.endDate.year(),self.endDate.month(),self.endDate.day()))
            else:
                self.l0.setText("Date range: %i-%02d-%02d to %i-%02d-%02d" % (self.startDate.year(),self.startDate.month(),self.startDate.day(),
                                                                      self.endDate.year(),self.endDate.month(),self.endDate.day()))
        self.l0.update()

    def startCalClicked(self,date):
        if self.debug: print("Clicked start calendar, date is:",date)
        self.startDate = date
        self.clearStartButton.show()
        self.updateDateLabel()

    def endCalClicked(self,date):
        if self.debug: print("Clicked end calendar, date is:",date)
        self.endDate = date
        self.clearEndButton.show()
        self.updateDateLabel()

    def clearStart(self):
        self.startDate = QDate(-9999,9,9)
        self.clearStartButton.hide()
        self.updateDateLabel()

    def clearEnd(self):
        self.endDate = QDate(9999,9,9)
        self.clearEndButton.hide()
        self.updateDateLabel()

    def selectionGui(self):
        self.updateDateLabel()
        self.startCal.hide()
        self.startCalTitle.hide()
        self.continueButton.hide()
        self.endCal.hide()
        self.endCalTitle.hide()
        self.clearStartButton.hide()
        self.clearEndButton.hide()
        if self.debug: print("In selectionGui about to access database")
#        components = self.session.doSomething('listComponents','GET',data={'project':"S",'componentType':'SENSOR'})
#        testList = sorted([c["serialNumber"] for c in components if c and "serialNumber" in c and c["serialNumber"]])
#        self.codeLookup = dict([(c["serialNumber"],c["code"]) for c in components if c["serialNumber"] in testList])
        if self.debug: before_testList = datetime.now()
        if self.debug: print("before_testList=%s"%before_testList)
        testList = self.session.doSomething('listTestRunsByTestType','GET',data={'project':"S",'componentType':'SENSOR','testType':"IV"})
        if self.debug: after_testList = datetime.now()
        if self.debug: print("after_testList=%s"%after_testList)

        self.instituteList = ["All Institutions"]
        self.batchList = ["Any batch value","Defined batch"]
        self.typeList = ["All sensor types"]
        test_run_ids = []
        
        for t in testList:
            theDateString = t["date"].split(" ")[0]
            #25.05.2019 01:05
            #28.08.2018
            day,month,year = [int(x) for x in theDateString.split(".")]
            theQDate = QDate(year,day,month)
            if theQDate >= self.startDate and theQDate <= self.endDate:
                test_run_ids.append(t["id"])

        if self.debug: test_runs_bulk = self.session.doSomething(action = 'getTestRunBulk', method = 'GET', data = {'testRun': test_run_ids})
        if self.debug: after_testRunsBulk = datetime.now()
        if self.debug: print("after_testRunsBulk=%s (n=%i)"%(after_testRunsBulk,len(test_runs_bulk)))
        test_runs = []
        for tid in test_run_ids:
            t = self.session.doSomething(action = 'getTestRun', method = 'GET', data = {'testRun': tid})
            test_runs.append(t)
            if self.debug: print(t["properties"])
        after_testRuns = datetime.now()
        if self.debug: print("after_testRuns=%s (n=%i)"%(after_testRuns,len(test_runs)))

        self.components = self.session.doSomething('listComponents','GET',data={'project':"S",'componentType':'SENSOR'})
        after_listComponents = datetime.now()
        if self.debug: print("after_listComponents=%s (n=%i)"%(after_listComponents,len(self.components)))

        n_notlist = 0
        n_exception = 0
        n_empty = 0
        n_ok = 0
        self.testRuns = []

        for t in test_runs:
#            assert(len(t["components"])==1)
#            print(t["components"][0])
            cid = t["components"][0]["serialNumber"]
            if self.debug: print(t["id"])
            if not cid in [c["serialNumber"] for c in self.components]:
                if self.debug: print("Skipping test %s because component %s is not on the list of sensors" % (t["id"],cid))
                n_notlist += 1
                continue
#            component = self.session.doSomething(action = 'getComponent', method = 'GET', data={'component':cid})
#            print(cid)
            ok = True
            try:
                batch = self.session.doSomething(action = 'listBatchesByComponent',method="GET",data={'component':cid})
            except Exception:
                if self.debug: print("Skipping test %s because of exception when calling listBatchesByComponent" % t["id"])
                n_exception += 1
                ok = False
            if not ok:
                continue
#            assert(len(batch) <= 1)
            if len(batch) == 0:
                if self.debug: print("Noting that for %s listBatchesByComponent returns an empty list, so putting in 'None'" % t["id"])
                n_empty += 1
                t["IVScanGui_batchNames"] = ["Any batch value","None defined"]
            else:
                n_ok += 1
                t["IVScanGui_batchNames"] = ["Any batch value",batch[0]["number"],"Defined batch"]
                if not batch[0]["number"] in self.batchList:
                    self.batchList.append(batch[0]["number"])
            if self.debug: print("OK or empty so we continue!")
            t["IVScanGui_types"] = ["All sensor types",cid[5:7]]
            if not cid[5:7] in self.typeList:
                self.typeList.append(cid[5:7])
            t["IVScanGui_institutes"] = ["All Institutions",t["institution"]["code"]]
            if not t["institution"]["code"] in self.instituteList:
                self.instituteList.append(t["institution"]["code"])
            self.testRuns.append(t)

        self.batchList.append("None defined")
            
        if self.debug: print("n_notlist=%i" % n_notlist)
        if self.debug: print("n_exception=%i" % n_exception)
        if self.debug: print("n_empty=%i" % n_empty)
        if self.debug: print("n_ok=%i" % n_ok)
        

        for t in self.testRuns:
            if self.debug: print("%s %s %s" % (t["IVScanGui_institutes"],t["IVScanGui_types"],t["IVScanGui_batchNames"]))

#        batches = self.session.doSomething('listBatches','GET',data={'project':"S",'componentType':'SENSOR'})
#        print (batches)
#        raise Exception("SETH STOP HERE NOW")

        if self.debug: print("Have succeeded so far!")

        offset = 170
        self.selInst = QLabel(self.shortForm(self.instituteList[0]), self)
        self.comboInst = QComboBox(self)
        for l in self.instituteList:
            self.comboInst.addItem(l)
        self.labelInst1 = QLabel("Site List:",self)
        self.labelInst2 = QLabel("Selected Site:",self)
        self.labelInst1.move(30,50)
        self.labelInst2.move(30,100)
        self.comboInst.move(50, 70)
        self.selInst.move(130, 100)

        self.selType = QLabel(self.shortForm(self.typeList[0]), self)
        self.comboType = QComboBox(self)
        for l in self.typeList:
            self.comboType.addItem(l)
        self.labelType1 = QLabel("Type List:",self)
        self.labelType2 = QLabel("Selected Type:",self)
        self.labelType1.move(30+offset,50)
        self.labelType2.move(30+offset,100)
        self.comboType.move(50+offset, 70)
        self.selType.move(130+offset, 100)

        self.selBatch = QLabel(self.shortForm(self.batchList[0]), self)
        self.comboBatch = QComboBox(self)
        for l in self.batchList:
            self.comboBatch.addItem(l)
        self.labelBatch1 = QLabel("Batch List:",self)
        self.labelBatch2 = QLabel("Selected Batch:",self)
        self.labelBatch1.move(30+2*offset,50)
        self.labelBatch2.move(30+2*offset,100)
        self.comboBatch.move(50+2*offset, 70)
        self.selBatch.move(130+2*offset, 100)

#        self.nr = QLabel("",self)
#        self.nr.move(400,130)

        self.l3 = QLabel("IV Scan List:",self)
        self.l3.hide()
        self.l3.move(30,125)
        
        self.combo2 = QComboBox(self)
        self.combo2.move(180,120)
        self.combo2.hide()

        self.plotButtonInst = QPushButton("Plot by Institute",self)
        self.plotButtonInst.move(50,150)
        self.plotButtonInst.hide()

        self.plotButtonType = QPushButton("Plot by Type",self)
        self.plotButtonType.move(170,150)
        self.plotButtonType.hide()

        self.plotButtonBatch = QPushButton("Plot by Batch",self)
        self.plotButtonBatch.move(275,150)
        self.plotButtonBatch.hide()

        self.plotButtonHist = QPushButton("Plot histogram",self)
        self.plotButtonHist.move(385,150)
        self.plotButtonHist.hide()

        self.clearButton = QPushButton("Clear",self)
        self.clearButton.move(500,150)
        self.clearButton.hide()

        self.comboInst.activated[str].connect(self.onInstActivated)
        self.comboType.activated[str].connect(self.onTypeActivated)
        self.comboBatch.activated[str].connect(self.onBatchActivated)
        self.plotButtonInst.clicked.connect(self.plotButtonInstClick)
        self.plotButtonType.clicked.connect(self.plotButtonTypeClick)
        self.plotButtonBatch.clicked.connect(self.plotButtonBatchClick)
        self.plotButtonHist.clicked.connect(self.plotButtonHistClick)
        self.clearButton.clicked.connect(self.clearButtonClick)

        self.logLabel = QLabel("Log?",self)
        self.logLabel.move(30,560)
        self.logLabel.hide()
        self.comboLog = QComboBox(self)
        self.comboLog.addItem("Auto",self)
        self.comboLog.addItem("Log",self)
        self.comboLog.addItem("Linear",self)
        self.comboLog.move(70,555)
        self.comboLog.hide()
        self.logMode = "Auto"
        self.comboLog.activated[str].connect(self.setLog)

        self.outlierLabel = QLabel("Outlier removal?",self)
        self.outlierLabel.move(150,560)
        self.outlierLabel.hide()
        self.comboOutlier = QComboBox(self)
        self.comboOutlier.addItem("No",self)
        self.comboOutlier.addItem("Yes, factor 1e8",self)
        self.comboOutlier.addItem("Yes, factor 1e6",self)
        self.comboOutlier.addItem("Yes, factor 1e4",self)
        self.comboOutlier.addItem("Yes, factor 1e2",self)
        self.comboOutlier.move(270,555)
        self.comboOutlier.hide()
        self.outlierFactor = None
        self.comboOutlier.activated[str].connect(self.setOutlier)
        
        self.replotButton = QPushButton("Replot",self)
        self.replotButton.move(530,555)
        self.replotButton.setFixedSize(50.,100.)
        self.replotButton.hide()
        self.replotButton.clicked.connect(self.replotButtonClick)

        self.xRangeMode = QComboBox(self)
        self.xRangeMode.move(30,595)
        self.xRangeMode.addItem("V range auto")
        self.xRangeMode.addItem("V range manual")
        self.xRangeMode.hide()
        self.xRangeMin = QLineEdit("-50.",self)
        self.xRangeMin.move(170,595)
        self.xRangeMin.setFixedWidth(40)
        self.xRangeMax = QLineEdit("1050.",self)
        self.xRangeMax.move(220,595)
        self.xRangeMax.setFixedWidth(40)
        self.xRangeMin.hide()
        self.xRangeMax.hide()
        self.xRangeMode.activated[str].connect(self.changeXRangeMode)

        self.yRangeMode = QComboBox(self)
        self.yRangeMode.move(290,595)
        self.yRangeMode.addItem("I range auto")
        self.yRangeMode.addItem("I range manual")
        self.yRangeMode.hide()
        self.yRangeMin = QLineEdit("0.005",self)
        self.yRangeMin.move(430,595)
        self.yRangeMin.setFixedWidth(40)
        self.yRangeMax = QLineEdit("1.050",self)
        self.yRangeMax.move(480,595)
        self.yRangeMax.setFixedWidth(40)
        self.yRangeMin.hide()
        self.yRangeMax.hide()
        self.yRangeMode.activated[str].connect(self.changeYRangeMode)

        self.temperatureLabel = QLabel("Scale I by temperature?",self)
        self.temperatureLabel.move(30,640)
        self.temperatureLabel.hide()
        self.comboTemperature = QComboBox(self)
        self.comboTemperature.addItem("No",self)
        self.comboTemperature.addItem("Yes, to 0°C")
        self.comboTemperature.addItem("Yes, to 20°C")
        self.comboTemperature.move(180,635)
        self.comboTemperature.hide()
        self.temperatureFactor = None
        self.comboTemperature.activated[str].connect(self.setTemperatureScaling)
        self.scaleCurrentByTemperature = False
        self.scaleCurrentTo = 0. # Celsius

        self.areaLabel = QLabel("By area?",self)
        self.areaLabel.move(320,640)
        self.areaLabel.hide()
        self.comboArea = QComboBox(self)
        self.comboArea.addItem("No",self)
        self.comboArea.addItem("Yes, to uA/cm^2")
        self.comboArea.move(380,635)
        self.comboArea.hide()
        self.scaleCurrentByArea = False
        self.comboArea.activated[str].connect(self.setAreaScaling)

        self.saveText =QLabel("Save as:",self)
        self.saveText.move(30,685)
        self.saveName = QLineEdit("IVScanGUI_output",self)
        self.saveName.move(90,680)
        if RootOk:
            self.saveAsRoot = QPushButton(".root",self)
            self.saveAsRoot.move(230,680)
            self.saveAsRoot.clicked.connect(self.saveAsRootClick)
        self.saveAsCsv = QPushButton(".csv",self)
        self.saveAsCsv.move(320,680)
        self.saveAsCsv.clicked.connect(self.saveAsCsvClick)
        self.saveAsPng = QPushButton(".png",self)
        self.saveAsPng.move(410,680)
        self.saveAsPng.clicked.connect(self.saveAsPngClick)
        self.saveAsPdf = QPushButton(".pdf",self)
        self.saveAsPdf.move(500,680)
        self.saveAsPdf.clicked.connect(self.saveAsPdfClick)


#        self.c = PlotCanvas(self, width=5, height=4)
#        self.c.move(30,130)
#        self.c.hide()
        
        self.figure  = Figure(figsize=(5.4,3.6),dpi=100)
        self.drawing = self.figure.add_subplot (111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.canvas.move(30,180)
        self.figure.tight_layout()
        self.canvas.hide()

        self.show()
        self.labelInst1.show()
        self.labelInst2.show()
        self.comboInst.show()
        self.labelType1.show()
        self.labelType2.show()
        self.comboType.show()
        self.labelBatch1.show()
        self.labelBatch2.show()
        self.comboBatch.show()
#        self.nr.show()

        self.plotData = []

        if self.debug: print("End of selectionGui")
#        ITkPDLoginGui(self.session, self)
        
    def shortForm(self,text):
        if text.count("All"):
            return "All"
        else:
            return text
        
    def onInstActivated(self, text):
        self.selInst.show()
        self.selInst.setText(self.shortForm(text))
        self.selInst.adjustSize()
        self.selType.show()
        self.selBatch.show()
        self.updateRunList()

    def onTypeActivated(self, text):
        self.selType.show()
        self.selType.setText(self.shortForm(text))
        self.selType.adjustSize()
        self.selInst.show()
        self.selBatch.show()
        self.updateRunList()

    def onBatchActivated(self, text):
        self.selBatch.show()
        self.selBatch.setText(self.shortForm(text))
        self.selBatch.adjustSize()
        self.selInst.show()
        self.selType.show()
        self.updateRunList()


    def updateRunList(self):

        validRuns = []
#        code = self.codeLookup[text]
#        testRuns = self.session.doSomething("listTestRunsByComponent", 'GET',data={'component':code})
#        testRuns = self.instituteDict[text]
        testRuns = [t for t in self.testRuns if t["IVScanGui_institutes"].count(str(self.comboInst.currentText())) and t["IVScanGui_types"].count(str(self.comboType.currentText())) and t["IVScanGui_batchNames"].count(str(self.comboBatch.currentText()))]
        if self.debug: print("Size of testRuns is %i" % len(testRuns))
        for t in testRuns:
            if self.debug: print(t["testType"]["code"])
            if (t["testType"]["code"] == "IV" or t["testType"]["code"] == "MANUFACTURING"):
                validRuns.append(t)
        if self.debug: print("Size of validRuns is %i" % len(validRuns))
#        self.nr.setText("Number of IV tests: %i"%len(validRuns))
#        self.nr.adjustSize()
        self.l3.setText("IV Scan List (%i total):" %len(validRuns))
        self.l3.adjustSize()

        if len(validRuns) > 0:
            self.combo2.clear()
            self.lookupTestId = {}
            if len(validRuns) > 1:
                self.combo2.addItem("All Runs")
            for t in validRuns:
                if self.debug: print(t)
                myname = t["testType"]["code"]+" "+t["date"]+" "+str(t["components"][0]["serialNumber"])
                self.combo2.addItem(myname)
                self.lookupTestId[myname] = t["id"]
            self.l3.show()
            self.combo2.show()
            self.plotButtonInst.show()
            self.plotButtonBatch.show()
            self.plotButtonType.show()
            self.plotButtonHist.show()
            self.clearButton.show()
        else:
            self.l3.hide()
            self.combo2.hide()
            self.plotButtonInst.hide()
            self.plotButtonBatch.hide()
            self.plotButtonType.hide()
            self.plotButtonHist.hide()
            self.clearButton.hide()

    def changeXRangeMode(self,text):
        if text == "X range auto":
            self.xRangeMin.hide()
            self.xRangeMax.hide()
        else:
            self.xRangeMin.show()
            self.xRangeMax.show()

    def changeYRangeMode(self,text):
        if text == "Y range auto":
            self.yRangeMin.hide()
            self.yRangeMax.hide()
        else:
            self.yRangeMin.show()
            self.yRangeMax.show()


    def plotButtonInstClick(self):
        self.plotBy = "Inst"
        self.doPlotButton()

    def plotButtonTypeClick(self):
        self.plotBy = "Type"
        self.doPlotButton()  

    def plotButtonBatchClick(self):
        self.plotBy = "Batch"
        self.doPlotButton()  

    def plotButtonHistClick(self):
        self.plotBy = "Hist"
        self.doPlotButton()

    def replotButtonClick(self):
        self.doPlotButton()

    def doPlotButton(self,forceKey=None):
        if self.debug: print("In doPlotButton with forceKey=%s and currentText()=%s and plotBy=%s" %(forceKey,self.combo2.currentText(),self.plotBy))
        if forceKey:
            testId = self.lookupTestId[forceKey]
        elif self.combo2.currentText() == "All Runs":
            for key in self.lookupTestId.keys():
                self.doPlotButton(key)
            self.plotMe()
            return
        else:
            testId = self.lookupTestId[self.combo2.currentText()]
        if self.debug: print(testId)
#        tr = self.session.doSomething('getTestRun','GET',data={'testRun':testId})
        tr = [t for t in self.testRuns if t["id"] == testId][0]
        if self.debug: print(tr)
        voltages = None
        currents = None
        tempstring = ""

#        print("NEW CODE %s" % tr["id"])
#        print(self.componentCodeByTest[tr["id"]])
#        batch = self.session.doSomething('listBatchesByComponent','GET',data={'component':self.componentCodeByTest[tr["id"]]})
#        print(batch)
#        raise Exception("SETH STOP NOW")

#{'code': 'TEMPERATURE', 'name': 'Temperature (°C)', 'dataType': 'integer', 'valueType': 'single', 'required': True, 'value': 25}

        if tr["testType"]["code"] == "IV":
            for res in tr["results"]:
                if res["code"] == "VOLTAGE":
                    voltages = res
                if res["code"] == "CURRENT":
                    currents = res
 
                # Code for old format
#                if res["code"] == "TEMPERATURE":
#                    try:
#                        deg = res["name"].split("(")[1].split(")")[0]
#                    except Exception:
#                        deg = "º"
#                    tempstring += ", %.1f %s" % (res["value"],deg)

            for prop in tr["properties"]:
                if prop["code"] == "TEMPERATURE":
#                    assert(prop["name"].count("°C"))
                    temperature = prop["value"]
                    tempstring += ", %.1f °C" % temperature

            if not voltages or not currents or len(voltages["value"]) != len(currents["value"]):
                if self.debug: print(tr["results"])
                raise Exception("Voltage and current keys not as expected, see above!")
            
            if self.debug: print(voltages)
            if self.debug: print(currents)
            xy = []
            for k in range(len(voltages["value"])):
                theCurrent = currents["value"][k]
                if self.scaleCurrentByTemperature: theCurrent = scaleCurrentWithTemperature(theCurrent,temperature,self.scaleCurrentTo)
                if self.scaleCurrentByArea: theCurrent = scaleCurrentWithArea(theCurrent,tr["IVScanGui_types"][1])
                xy.append((voltages["value"][k],theCurrent))
            v_name = voltages["name"]
            i_name = currents["name"]
            
        elif tr["testType"]["code"] == "MANUFACTURING":
            xy = []
            v_name = "???"
            i_name = "???"

            vfd = None
            for res in tr["results"]:
                if res["code"] == "LEAKAGE_CURRENT_VFD":
                    i_vfd = res["value"]
                    try:
                        i_name_split = res["name"].split(" ")
                        i_name = i_name_split[0] + " " + i_name_split[1] + " " + i_name_split[-1]
                    except Exception:
                        if self.debug: print("i_name didn't work:%s"%res["name"])
                        i_name = "Current (microA)"
                    v_name = "Voltage (V)"
                elif res["code"].count("LEAKAGE_CURRENT_"):
                    v = float(res["code"].split("_")[-1])
                    i = res["value"]
                    if i > -0.5:
                        xy.append((v,i))
                    else:
                        if self.debug: print("ignoring current for %swith negative value %s"%(res["code"],i))
                elif res["code"] == "DEPLETION_VOLTS":
                    try:
                        vfd = res["value"] + 50.
                    except Exception:
                        if self.debug: print("ignoring VFD with value:",res["value"])
                elif res["code"] == "IV_TEMPERATURE":
                    try:
                        deg = res["name"].split("(")[1].split(")")[0]
                    except Exception:
                        deg = "º"
                        tempstring += ", %.1f %s" % (res["value"],deg)
            if vfd:
                if i_vfd > -0.5:
                    xy.append((vfd,i_vfd))
                else:
                    if self.debug: print("ignoring i_vfd with negative value %s"%i_vfd)
                
        else:
            raise Exception("Unsupported testType code: %s"%tr["testType"]["code"])

        if i_name.count("(A)"):
            xyuA = []
            for iv in xy:
                xyuA.append((iv[0],iv[1]*1e6))
            i_name = i_name.replace("(A)","(µA)")
        else:
            xyuA = xy
        i_name = i_name.replace("micro","µ")
        if self.scaleCurrentByArea:
            i_name = i_name.replace("µA","µA/cm^2")
            i_name = i_name.replace("Current","Current/Area")

        x = [p[0] for p in sorted(xyuA)]
        y = [p[1] for p in sorted(xyuA)]

#        print(xy)
        if self.debug: print(xyuA)
#        print(x)
#        print( y)

        resultTuple = (x,y,v_name,i_name,
                       tr["components"][0]["componentType"]["name"],
                       tr["components"][0]["serialNumber"],
                       tr["date"],
                       tempstring, #temperature (if available)
                       tr["testType"]["code"], # IV
                       tr["IVScanGui_institutes"][1],
                       tr["IVScanGui_types"][1],
                       tr["IVScanGui_batchNames"][1]
        )

        existingIndex = -1
        for i in range(len(self.plotData)):
            if resultTuple[5] == self.plotData[i][5] and resultTuple[6] == self.plotData[i][6]:
                existingIndex = i

        if existingIndex >= 0:
            if self.debug: print("plotData already contains",resultTuple)
            self.plotData[existingIndex] = resultTuple
        else:
            self.plotData.append(resultTuple)

        if self.debug: print(self.plotData)
        if self.debug: print(forceKey)
        if not forceKey:
            self.plotMe()

    def plotHist(self):
        if self.debug: print("in plotHist")
        currentsAt500 = []
        for pd in self.plotData:
            for i in range(len(pd[0])):
                already = False
                if not already and abs(pd[0][i]-500.) < 0.1:
                    already = True
                    currentsAt500.append(pd[1][i])
        if self.debug: print(len(currentsAt500),len(self.plotData))
        if self.debug: print(currentsAt500)
#        assert(len(currentsAt500) == len(self.plotData))
        self.figure.clf()
        self.drawing = self.figure.add_subplot (111)
        self.drawing.hist(currentsAt500)
        self.drawing.set_xlabel(pd[3])
        self.drawing.set_ylabel("Sensors / bin")
        self.drawing.set_title("Current @ 500V")
        if self.scaleCurrentByTemperature:
            self.drawing.set_title("Current @ 500V (scaled to %.1fºC)"%self.scaleCurrentTo)
        if self.yRangeMode.currentText().count("manual"):
            self.drawing.set_xlim(auto=False,xmin=float(self.yRangeMin.text()),xmax=float(self.yRangeMax.text()))
        else:
            self.drawing.set_xlim(auto=True)

        self.showCanvasAndOptions()


    def plotMe(self):
        if self.debug: print("in plotMe")
        if self.plotBy == "Hist":
            self.plotHist()
            return
        if self.plotBy == "Inst":
            labelIndex = -3
            multiScanText = "Multiple scans at %s"
            multiLabelText = "Comparing scans at multiple sites"
        elif self.plotBy == "Type":
            labelIndex = -2
            multiScanText = "Multiple scans of type %s"
            multiLabelText = "Comparing scans on multiple types"
        elif self.plotBy == "Batch":
            labelIndex = -1
            multiScanText = "Multiple scans at %s"
            multiLabelText = "Comparing scans on multiple batches"
        else:
            raise Exception("plotBy not recognised: %s" % self.plotBy)

        minyval = 999000.
        maxyval = 0.
        for pd in self.plotData:
            for yval in pd[1]:
                if yval < minyval:
                    minyval = yval
                if yval > maxyval:
                    maxyval = yval
        if minyval < 0.01:
            minyval = 0.01

        if self.outlierFactor and maxyval > minyval*self.outlierFactor:
            nremoved = 0
            maxyval = 0. # this will be the maximum kept value at the end
            if self.debug: print("outlier computation with factor %.1f" % self.outlierFactor)
            pdtemp = []
            for pd in self.plotData:
                xnew = []
                ynew = []
                for i in range(len(pd[0])):
                    if pd[1][i] < minyval*self.outlierFactor:
                        xnew.append(pd[0][i])
                        ynew.append(pd[1][i])
                        if pd[1][i] > maxyval:
                            maxyval = pd[1][i]
                    else:
                        nremoved += 1
                pdtemp.append( (xnew,ynew,pd[2],pd[3],pd[4],pd[5],pd[6],pd[7],pd[8],pd[9],pd[10],pd[11]) )
#                assert(len(pdtemp[-1]) == len(pd))
                if self.debug: print("Total points removed: %i"%nremoved)
        else:
            pdtemp = self.plotData

        v_name = pdtemp[0][2]
        i_name = pdtemp[0][3]
        plots = []
        if len(pdtemp) == 1:
            plotstyle = "ro-"
            plots.append(self.drawing.plot(pdtemp[0][0],pdtemp[0][1],plotstyle))
            self.drawing.set_xlabel(v_name)
            self.drawing.set_ylabel(i_name)
            self.drawing.set_title(" ".join(pdtemp[0][4:6]) + ", " + pdtemp[0][6] + pdtemp[0][7])
        else:
            self.figure.clf()
            self.drawing = self.figure.add_subplot (111)
            labelList = []
            for pd in pdtemp:
                label = pd[labelIndex]
                if not label in labelList:
                    labelList.append(label)
            nlabels = len(labelList)
            if self.debug: print("%i labels:"%nlabels,labelList)
            if len(labelList) == 1:
                for i in range(len(pdtemp)):
                    plotstyle = stylelist[min(i,len(stylelist)-1)]
                    pd = pdtemp[i]
                    plots.append(self.drawing.plot(pd[0],pd[1],plotstyle))
                    plots[-1][0].set_label(" ".join(pd[4:6]))
                self.drawing.set_xlabel(v_name)
                self.drawing.set_ylabel(i_name)
                self.drawing.set_title(multiScanText%labelList[0]) 
                if len(pdtemp) <= len(stylelist):
                    self.drawing.legend()
            else:
                labelAlready = []
                for pd in pdtemp:
                    label = pd[labelIndex]
                    i = labelList.index(label)
                    plotstyle = stylelist[min(i,len(stylelist)-1)]
                    plots.append(self.drawing.plot(pd[0],pd[1],plotstyle))
                    if not labelAlready.count(label):
                        labelAlready.append(label)
                        plots[-1][0].set_label(label)
                self.drawing.set_xlabel(v_name)
                self.drawing.set_ylabel(i_name)
                self.drawing.set_title(multiLabelText)
                if len(labelList) <= len(stylelist):
                    self.drawing.legend()
        if self.logMode == "Auto":
            if maxyval > 1000.*minyval:
                if self.debug: print("Scale before:",self.drawing.get_yscale())
                self.drawing.set_yscale('log')
                if self.debug: print("Scale after:",self.drawing.get_yscale())
            else:
                if self.debug: print("Scale before:",self.drawing.get_yscale())
                self.drawing.set_yscale('linear')
                if self.debug: print("Scale after:",self.drawing.get_yscale())
        else:
            self.drawing.set_yscale(self.logMode.lower())
        if self.xRangeMode.currentText().count("manual"):
            self.drawing.set_xlim(auto=False,xmin=float(self.xRangeMin.text()),xmax=float(self.xRangeMax.text()))
        else:
            self.drawing.set_xlim(auto=True)
        if self.yRangeMode.currentText().count("manual"):
            self.drawing.set_ylim(auto=False,ymin=float(self.yRangeMin.text()),ymax=float(self.yRangeMax.text()))
        else:
            self.drawing.set_ylim(auto=True)
        self.showCanvasAndOptions()

    def showCanvasAndOptions(self):
        self.figure.tight_layout()
        self.canvas.show()
        self.canvas.draw()
        self.saveText.show()
        self.saveName.show()
        if RootOk: self.saveAsRoot.show()
        self.saveAsCsv.show()
        self.saveAsPng.show()
        self.saveAsPdf.show()
        self.logLabel.show()
        self.comboLog.show()
        self.outlierLabel.show()
        self.comboOutlier.show()
        self.replotButton.show()
        self.xRangeMode.show()
        if self.xRangeMode.currentText().count("manual"):
            self.xRangeMin.show()
            self.xRangeMax.show()
        else:
            self.xRangeMin.hide()
            self.xRangeMax.hide()
        self.yRangeMode.show()
        if self.yRangeMode.currentText().count("manual"):
            self.yRangeMin.show()
            self.yRangeMax.show()
        else:
            self.yRangeMin.hide()
            self.yRangeMax.hide()
        self.temperatureLabel.show()
        self.comboTemperature.show()
        self.areaLabel.show()
        self.comboArea.show()

    def setLog(self,text):
        self.logMode = text

    def setOutlier(self,text):
        if text.count("No"):
            self.outlierFactor = None
        else:
            self.outlierFactor = float(text.split(" ")[-1])
       
    def setTemperatureScaling(self,text):
        if text.lower().count("no"):
            self.scaleCurrentByTemperature = False
        else:
            self.scaleCurrentByTemperature = True
            self.scaleCurrentTo = float(text.split(" ")[2].split("°")[0])

    def setAreaScaling(self,text):
        if text.lower().count("no"):
            self.scaleCurrentByArea = False
        else:
            self.scaleCurrentByArea = True

    def clearButtonClick(self):
        self.figure.clf()
        self.plotData.clear()
        self.drawing = self.figure.add_subplot (111)
        self.canvas.hide()
        self.saveText.hide()
        self.saveName.hide()
        if RootOk: self.saveAsRoot.hide()
        self.saveAsCsv.hide()
        self.saveAsPng.hide()
        self.saveAsPdf.hide()
#        self.logLabel.hide()
#        self.comboLog.hide()
        self.replotButton.hide()
#        self.xRangeMode.hide()
        if self.xRangeMode.currentText().count("manual"):
            self.xRangeMin.hide()
            self.xRangeMax.hide()
#        self.yRangeMode.hide()
        if self.yRangeMode.currentText().count("manual"):
            self.yRangeMin.hide()
            self.yRangeMax.hide()

    def saveAsRootClick(self):
        fn = self.saveName.text() + ".root"
        if self.debug: print(fn)
        tgf = TFile(fn,"RECREATE")
        tgf.cd()
        for pd in self.plotData:
            if self.debug: print(len(pd[0]),pd[0],pd[1])
            tg = TGraph(len(pd[0]),array('d',pd[0]),array('d',pd[1]))
            tgn = "_".join(pd[8:10]+pd[4:7]).replace(" ","_").replace(".","_").replace(":","h")
            if self.debug: print(tgn)
            tg.SetName(tgn)
            tg.SetTitle(tgn)
            tg.GetXaxis().SetTitle(pd[2])
            tg.GetYaxis().SetTitle(pd[3])
            if self.debug: print(tg)
            tg.Write()
        tgf.Close()

    def saveAsCsvClick(self):
        fn = self.saveName.text() + ".csv"
        if self.debug: print(fn)
        f = open(fn,'w')
        for pd in self.plotData:
            f.write(" ".join(pd[8:10]+pd[4:7])+"\n")
            f.write(pd[2]+",")
            for x in pd[0]:
                f.write("%.1f," % x)
            f.write("\n"+pd[3]+",")
            for y in pd[1]:
                f.write("%.3f," % y)
            f.write("\n\n")
        f.close()

    def saveAsPngClick(self):
        fn = self.saveName.text() + ".png"
        if self.debug: print(fn)
        self.figure.savefig(fn)

    def saveAsPdfClick(self):
        fn = self.saveName.text() + ".pdf"
        if self.debug: print(fn)
        self.figure.savefig(fn)
                
if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
