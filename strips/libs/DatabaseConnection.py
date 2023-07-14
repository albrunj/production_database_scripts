#!/usr/bin/env python
from PyQt5 import QtCore

import itk_pdb.dbAccess as dbAccess

class DataBaseCommunication():

    def __init__(self,user,allow_auth_from_file=False):
        self.dBSession = dbAccess.ITkPDSession()
        if allow_auth_from_file:
            self.token = self.dBSession.authenticate(accessCode1=user[0], accessCode2=user[1])
        else:
            self.token = self.dBSession.authenticate()
        self.tags = []
        self.enabled = []

    def update(self,tag,enable,sheet):
        self.tags = tag
        self.enabled = enable
        self.sheet = sheet

    def getHybrids(self):
        self.TopItem = self.dBSession.doSomething("getComponentType",
                                                  method="GET",
                                                  data={"id": "5d10e3dd5f865b00092c5481"})
        self.types = [x for x in self.TopItem["children"] if x != "*"]
        self.number = []
        self.hybridtypes = []
        for x in self.types:
            for y in range(len(self.TopItem["children"][x])):
                if self.TopItem["children"][x][y]["code"] == 'HYBRID':

                    self.hybridtypes.append(self.TopItem["children"][x][y]['type']['code'])
                    self.number.append(self.TopItem["children"][x][y]['quantity'])

        #self.TopItem = self.dBSession.doSomething("searchComponentTypeByName",
        #                                          method="GET",
        #                                          data={"project": "S",
        #                                                "componentType": "HYBRID_FLEX_SHEET"})
        #for item in self.TopItem["itemList"]:
        #    print(item)
        #{'id': '5d10e3dd5f865b00092c5481', 'code': 'HYBRID-FLEX-ARRAY', 'name': 'Hybrid Flex Array', 'state': 'active',
        #{'id': '59f8846a7fff1a0005d9751b', 'code': 'HYBRID_FLEX_PANEL', 'name': 'Hybrid Flex Panel', 'state': 'active',
        return self.types ,self.number ,self.hybridtypes

    def getComponentList(self):
        TopItem = self.dBSession.doSomething("listComponents",
                                             method="GET",
                                             data={"project": "S",
                                                   "componentType": "HYBRID-FLEX-ARRAY",
                                                   "currentStage":"BARE",
                                                   "includeProperties": "true"
                                                   })

        #TopItem = np.asarray(TopItem)
        Arrays = [i["properties"][0]["value"] for i in TopItem]
        TypePerSensor = [i["type"]["code"] for i in TopItem]
        NumberType = []
        for i in TypePerSensor:
            for number,type in enumerate(self.types):
                if type == i:
                    NumberType.append(number)
        #for i in TopItem:
        #    print(i)
        #    print(i["properties"][0]["value"])
        #    print(i["properties"][0])
        #    print(i["type"]["code"])
        return Arrays, NumberType

class DataBaseThread(QtCore.QThread):
    def __init__(self,db):
        QtCore.QThread.__init__(self)
        self.dBSession = db.dBSession
        self.db = db

    def refreshToken(self):
        self.dBSession.refreshToken()

    def getItems3(self):
        try:
            self.TopItem = self.dBSession.doSomething("listComponentsByProperty",
                                 method="POST",
                                 data={"project": "S",
                                       "componentType": "HYBRID-FLEX-ARRAY",
                                       "propertyFilter": [{"code": "UNIQUE-ID", "operator": "=", "value": self.db.sheet[1].text()}]})[0]
           # print(self.TopItem["type"]["code"])
           # if self.TopItem["type"]["code"] =!
            self.TopItem = self.TopItem["code"]
            self.SubItem = self.dBSession.doSomething("getComponent", method="GET",
                                                            data={"component": self.TopItem})["children"]
            print(self.SubItem)
        except Exception as error:
            print(error)

    def updateRFID(self):
        try:
            for itemNr, item in enumerate(self.SubItem):
                if len(self.db.enabled)>itemNr:
                    if self.db.enabled[itemNr].isChecked():
                        if item["component"]["serialNumber"]:
                            self.dBSession.doSomething("setComponentProperty", method="POST",
                                                   data={"component": item["component"]["code"], "code":"RFID","value":self.db.tags[itemNr].text()})
        except Exception as error:
            print(error)

    def run(self):
        self.getItems3()
        self.updateRFID()

class DataBaseTestPanel(DataBaseCommunication):

    def update(self,tag,enable,sheet,frameTag,frameEnable):
        self.tags = tag
        self.enabled = enable
        self.sheet = sheet
        self.frameTag = frameTag
        self.frameEnable = frameEnable

    def getTestpanel(self):
        self.TopItem = self.dBSession.doSomething("getComponentType",
                                                  method="GET",
                                                  data={"id": "5db1c48e2dc69e000af1bdf9"})
        self.types = [x for x in self.TopItem["children"] if x != "*"]
        self.project = [x["subprojects"][0]["code"] for x in self.TopItem["types"] if x["code"] in self.types]
        self.typeNames = [x["name"] for x in self.TopItem["types"] if x["code"] in self.types]


        number = []
        hybridtypes = []
        nrhybridtypes = []
        for x in self.types:
            temp = False
            for y in range(len(self.TopItem["children"][x])):
                if self.TopItem["children"][x][y]["code"] == 'HYBRID':
                    if temp == False:
                        nrhybridtypes.append(1)
                        number.append(self.TopItem["children"][x][y]['quantity'])
                    else:
                        nrhybridtypes[-1] += 1
                        number[-1] += self.TopItem["children"][x][y]['quantity']
                    if self.TopItem["children"][x][y]['type'] == None:
                        hybridtypes.append('HY')
                    else:
                        hybridtypes.append(self.TopItem["children"][x][y]['type']['code'])
                    temp = True
       # print(self.types ,number ,hybridtypes, nrhybridtypes)
       # self.TopItem = self.dBSession.doSomething("searchComponentTypeByName",
       #                                           method="GET",
       #                                           data={"project": "S",
       #                                                 "componentType": "TESTPANEL"})
       # for item in self.TopItem["itemList"]:
       #     print(item)
        #{'id': '5db1c48e2dc69e000af1bdf9', 'code': 'TESTPANEL', 'name': 'Hybrid Testpanel', 'state': 'active', 'project': 'S', 'subprojects': ['SB', 'SE'], 'category': 'panel', 'snRequired': False, 'snAutomatically': False, 'snComponentIdentifier': '', 'properties': [{'code': 'CYCLES USED', 'name': 'cycles Used', 'description': 'How often whas this panel used for bonding hybrids', 'dataType': 'integer', 'order': 0, 'required': True, 'default': False, 'unique': False, 'snPosition': None, 'codeTable': [{'code': '', 'value': ''}]}, {'code': 'LOCALNAME', 'name': 'Local name', 'description': '', 'dataType': 'string', 'order': 0, 'required': False, 'default': False, 'unique': False, 'snPosition': None, 'codeTable': [{'code': '', 'value': ''}]}, {'code': 'BATCH', 'name': 'Batch', 'description': '', 'dataType': 'string', 'order': 0, 'required': True, 'default': False, 'unique': False, 'snPosition': None, 'codeTable': [{'code': '', 'value': ''}]}, {'code': 'NUMBER', 'name': 'Number', 'description': '', 'dataType': 'integer', 'order': 0, 'required': True, 'default': False, 'unique': False, 'snPosition': None, 'codeTable': [{'code': '', 'value': ''}]}, {'code': 'RFID', 'name': 'RFID Tag', 'description': '', 'dataType': 'string', 'order': 0, 'required': True, 'default': False, 'unique': True, 'snPosition': None, 'codeTable': [{'code': '', 'value': ''}]}], 'types': [{'code': 'R0 TESTPANEL', 'name': 'R0 Testpanel', 'version': 'prototype', 'subprojects': ['SE'], 'snComponentIdentifier': '', 'existing': True, 'cddNumber': ''}, {'code': 'TESTPANEL', 'name': 'R1 Testpanel', 'version': 'prototype', 'subprojects': ['SE'], 'snComponentIdentifier': '', 'existing': True, 'cddNumber': ''}, {'code': 'TESTPANELR2', 'name': 'R2 Testpanel', 'version': 'prototype', 'subprojects': ['SE'], 'snComponentIdentifier': '', 'existing': True, 'cddNumber': ''}, {'code': 'R3 TESTPANEL', 'name': 'R3 Testpanel', 'version': 'prototype', 'subprojects': ['SE'], 'snComponentIdentifier': '', 'existing': True, 'cddNumber': ''}, {'code': 'R4 TESTPANEL', 'name': 'R4 Testpanel', 'version': 'prototype', 'subprojects': ['SE'], 'snComponentIdentifier': '', 'existing': True, 'cddNumber': ''}, {'code': 'R5 TESTPANEL', 'name': 'R5 Testpanel', 'version': 'prototype', 'subprojects': ['SE'], 'snComponentIdentifier': '', 'existing': True, 'cddNumber': ''}], 'stages': [{'code': 'EMPTY', 'name': 'Empty', 'order': 0, 'initial': True, 'final': True}, {'code': 'HYBRIDS LOADED', 'name': 'Hybrids Loaded', 'order': 1, 'initial': False, 'final': False}, {'code': 'HYBRIDS BONDED', 'name': 'Hybrids Bonded', 'order': 3, 'initial': False, 'final': False}, {'code': 'HYBRIDS TESTED', 'name': 'Hybrids Tested', 'order': 4, 'initial': False, 'final': False}, {'code': 'HYBRIDS BURNED', 'name': 'Hybrids burned', 'order': 5, 'initial': False, 'final': False}, {'code': 'HYBRIDS METROLOGY', 'name': 'Hybrids Metrology', 'order': 2, 'initial': False, 'final': False}], 'parents': None, 'children': {'*': [{'child': '5ce3f29291f5f40009849035', 'childType': None, 'quantity': 1, 'properties': []}], 'R0 TESTPANEL': [{'child': '59d608c6ed67730005160cd6', 'childType': 'R0H0', 'quantity': 2, 'properties': []}, {'child': '59d608c6ed67730005160cd6', 'childType': 'R0H1', 'quantity': 2, 'properties': []}, {'child': '59d6089ced67730005160cd5', 'childType': 'ECPANELPB', 'quantity': 2, 'properties': []}]}, 'testTypes': None, 'awid': 'dcb3f6d1f130482581ba1e7bbe34413c', 'sys': {'cts': '2019-10-24T15:34:38.974Z', 'mts': '2019-10-25T08:53:33.731Z', 'rev': 35}}
        return self.types ,number ,hybridtypes, nrhybridtypes

    def getComponentList(self):
        TopItem = self.dBSession.doSomething("listComponents",
                                                  method="GET",
                                                  data={"project":"S",
                                                        "componentType":"TESTPANEL",
                                                        "includeProperties": "true"
                                                        })

        #TopItem = np.asarray(TopItem)
        Panels = [i["properties"][0]["value"] for i in TopItem]
        #for i in TopItem:
        #    print(i)
        #    print(i["properties"][0]["value"])
        return Panels

class TestPanelThread(DataBaseThread):

    def registerRFID(self):
        if self.OmitRFID:
            try:
                self.dBSession.doSomething("registerComponent", method="POST",
                                           data={"project": "S", "subproject": self.db.project[self.db.sheet[1].currentIndex()], \
                                                 "institution": self.Institute, \
                                                 # "componentType":"5db1c48e2dc69e000af1bdf9",
                                                 "componentType": "TESTPANEL",
                                                 "type": self.db.types[self.db.sheet[1].currentIndex()],
                                                 "properties": {
                                                     "CYCLES_USED": 1,
                                                     "BATCH": self.db.sheet[0][0].text(),
                                                     "NUMBER": int(self.db.sheet[0][1].text())
                                                 }
                                                 # "children":[{"parentType":"TESTPANEL", "childType":"R0 TESTPANEL","quantity":"1"}]
                                                 # "children": { "TESTPANEL", "R0 TESTPANEL", "1"}
                                                 }
                                           )
            except Exception as error:
                print(error)
        else:
            try:
                if self.db.frameEnable.isChecked():
                    self.dBSession.doSomething("registerComponent", method="POST",
                                           data={"project":"S","subproject": self.db.project[self.db.sheet[1].currentIndex()], \
                                                 "institution": self.Institute, \
                                                # "componentType":"5db1c48e2dc69e000af1bdf9",
                                                 "componentType":"TESTPANEL",
                                                 "type": self.db.types[self.db.sheet[1].currentIndex()],
                                                 "properties":{
                                                     "RFID": self.db.frameTag.text(),
                                                    "CYCLES_USED": 1,
                                                     "BATCH":self.db.sheet[0][0].text(),
                                                     "NUMBER":int(self.db.sheet[0][1].text())
                                                 }
                                               # "children":[{"parentType":"TESTPANEL", "childType":"R0 TESTPANEL","quantity":"1"}]
                                                # "children": { "TESTPANEL", "R0 TESTPANEL", "1"}
                                                 }
                                            )
            except Exception as error:
                print(error)

    def test(self):
        self.dBSession.doSomething("addInstitutionComponentType", method="POST",
                                   data={"code": "UNIFREIBURG","project":"S", \
                                         # "componentType":"5db1c48e2dc69e000af1bdf9",
                                         "componentType": "TESTPANEL",
                                         }
                                   )

    def withOrWithoutRFID(self, truth):
        self.OmitRFID = truth
    def setInstitution(self,Institute):
        self.Institute = str(Institute)


    def run(self):
        self.registerRFID()
