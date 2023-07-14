#!/usr/bin/env python
# ComponentAssemblyGui.py
# Created: 2019/02/19, Updated: 2020/04/06
# Written by Matthew Basso

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys
import time

try:
    from PyQt5.QtWidgets import (
        QWidget,
        QMainWindow,
        QDesktopWidget,
        QLabel,
        QShortcut,
        QGridLayout,
        QPushButton,
        QLineEdit,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QMessageBox,
        QAbstractItemView,
        QComboBox,
        QStackedWidget,
        QTabWidget,
    )
    from PyQt5.QtGui import QIcon, QKeySequence
    from PyQt5.QtCore import QThread, Qt, pyqtSignal
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

# https://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
class ITkPDThread(QThread):

    def __init__(self, ITkPDSession, command = {'action': '', 'method': '', 'data': {}}, parent = None):
        super(ITkPDThread, self).__init__(parent)
        self.ITkPDSession   = ITkPDSession
        self.command        = command
        self.parent         = parent
        self.data           = None

    def __del__(self):
        del self.ITkPDSession
        self.ITkPDSession = None
        self.data         = None

    def run(self):
        self.data = self.ITkPDSession.doSomething(**self.command)

class QComponentTableWidget(QTableWidget):

    def __init__(self, parent = None):
        super(QComponentTableWidget, self).__init__(parent)
        self.parent = parent
        self.labels = ['Serial (Component) #', 'Type', 'Stage']
        self.thread = None
        self.setColumnCount(len(self.labels))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalHeaderLabels(self.labels)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setStyleSheet('font-size: 12pt; color: black;')
        header_horizonal = self.horizontalHeader()
        header_horizonal.setStyleSheet('font: bold;')
        header_horizonal.setDefaultAlignment(Qt.AlignHCenter)
        header_horizonal.setSectionResizeMode(QHeaderView.Stretch)
        header_vertical = self.verticalHeader()
        header_vertical.setSectionResizeMode(QHeaderView.Fixed)

    def __len__(self):
        return self.rowCount()

    def __del__(self):
        del self.thread
        self.thread = None

    def setThread(self, ITkPDSession, command):
        self.thread = ITkPDThread(ITkPDSession, command, self)
        self.thread.finished.connect(lambda: self.fillTable(self.thread.data))

    def startThread(self):
        self.thread.start()

    def fillTable(self, components, cuts = {'dummy': False, 'assembled': False}):
        self.clearContents()
        self.setRowCount(len(components))
        for i, component in enumerate(components):
            fail_cuts = False
            for var in cuts.keys():
                if component[var] != cuts[var]:
                    break
            if fail_cuts:
                continue
            try:
                serial_number = component['serialNumber']
                if serial_number is not None:
                    pass
                else:
                    serial_number = component['code']
            except KeyError:
                serial_number = component['code']
            self.setItem(i, 0, QTableWidgetItem(serial_number))
            try:
                type0 = component['type']['code']
            except KeyError:
                type0 = 'None'
            self.setItem(i, 1, QTableWidgetItem(type0))
            try:
                stage = component['currentStage']['code']
            except KeyError:
                stage = 'None'
            self.setItem(i, 2, QTableWidgetItem(stage))

class QTabComponentTableWidget(QTabWidget):

    def __init__(self, parent = None):
        super(QTabComponentTableWidget, self).__init__(parent)
        self.parent = parent
        self.tables = []
        self.iter_index = 0
        self.setMovable(False)
        self.setTabBarAutoHide(False)
        self.setTabsClosable(False)
        self.setStyleSheet('color: black;')
        self.__applyDecorators()

    def __call__(self):
        i = self.currentIndex()
        return self.tables[i]

    def __getitem__(self, i):
        return self.tables[i]

    def __len__(self):
        return self.count()

    def __iter__(self):
        self.iter_index = 0
        return self

    def __next__(self):
        if self.iter_index <= (len(self.tables) - 1):
            table = self.tables[self.iter_index]
            self.iter_index += 1
            return table
        else:
            raise StopIteration

    # Python 2 iterator fix, see: https://stackoverflow.com/questions/29578469/how-to-make-an-object-both-a-python2-and-python3-iterator
    next = __next__

    def __del__(self):
        for table in self.tables:
            del table
        self.tables = []

    def __addOrInsertTab_decorate(self, func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            if func == super(QTabComponentTableWidget, self).addTab:
                self.tables.append(args[0])
            elif func == super(QTabComponentTableWidget, self).insertTab:
                self.tables.insert(args[0], args[1])
            return func(*args, **kwargs)
        return func_wrapper

    def __removeTab_decorate(self, func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            i = args[0]
            del self.tables[i]
            return func(*args, **kwargs)
        return func_wrapper

    def __applyDecorators(self):
        self.addTab = self.__addOrInsertTab_decorate(super(QTabComponentTableWidget, self).addTab)
        self.insertTab = self.__addOrInsertTab_decorate(super(QTabComponentTableWidget, self).insertTab)
        self.removeTab = self.__removeTab_decorate(super(QTabComponentTableWidget, self).removeTab)

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## HEADER WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ComponentAssemblyGui__Header(QWidget):

    @DEBUG
    def __init__(self, parent = None):
        super(ComponentAssemblyGui__Header, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.__initUI()

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

        title = QLabel('ATLAS ITk Production Database -- Component Assembly GUI', self)
        title.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignLeft;')
        quit = QPushButton('Quit', self)
        quit.clicked.connect(lambda: self.__quit())
        quit.setAutoDefault(True)
        quit.setToolTip('Quit the GUI')
        quit.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        self.layout.addWidget(title,    0, 0, 1, 7)
        self.layout.addWidget(quit,     0, 7, 1, 1)

class ComponentAssemblyGui__Step1(QWidget):

    @DEBUG
    def __init__(self, parent = None, ITkPDSession = None):
        super(ComponentAssemblyGui__Step1, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.layout = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __setDefaults(self):
        self.institutions               = []
        self.componentTypes_detailed    = {}
        self.institution                = ('', -1)
        self.project                    = ('', -1)
        self.componentType              = ('', -1)
        self.type                       = ('', -1)

    @DEBUG
    def __getInput__institution(self):
        i = self.input__institution.currentIndex()
        if i != -1:
            self.institution = self.institutions[i]['code'], i
            projects = self.institutions[self.institution[1]]['componentType']
        else:
            self.institution = ('', -1)
            projects = []
        self.__fillQComboBox(self.input__project, [project['name'] for project in projects])
        self.__getInput__project()

    @DEBUG
    def __getInput__project(self):
        i = self.input__project.currentIndex()
        if i != -1:
            self.project = self.institutions[self.institution[1]]['componentType'][i]['code'], i
            componentTypes = self.institutions[self.institution[1]]['componentType'][self.project[1]]['itemList']
        else:
            self.project = ('', -1)
            componentTypes = []
        self.__fillQComboBox(self.input__componentType, [componentType['name'] for componentType in componentTypes])
        self.__getInput__componentType()

    @DEBUG
    def __getInput__componentType(self):
        i = self.input__componentType.currentIndex()
        if i != -1:
            self.componentType = self.institutions[self.institution[1]]['componentType'][self.project[1]]['itemList'][i]['code'], i
            if self.componentType[0] in self.componentTypes_detailed.keys():
                pass
            else:
                self.componentTypes_detailed[self.componentType[0]] = self.ITkPDSession.doSomething(action = 'getComponentType', method = 'GET', data = {'id': self.institutions[self.institution[1]]['componentType'][self.project[1]]['itemList'][self.componentType[1]]['id']})
            types = self.componentTypes_detailed[self.componentType[0]]['types']
            if types is None:
                types = []
        else:
            self.componentType != ('', -1)
            types = []
        self.__fillQComboBox(self.input__type, [type0['name'] for type0 in types])
        self.__getInput__type()

    @DEBUG
    def __getInput__type(self):
        i = self.input__type.currentIndex()
        if self.componentTypes_detailed[self.componentType[0]]['types'] is not None:
            if i != -1:
                type_code = self.componentTypes_detailed[self.componentType[0]]['types'][i]['code']
            else:
                type_code = ''
        else:
            type_code = ''
        self.type = type_code, i
        if self.institution != ('', -1) and self.project != ('', -1) and self.componentType != ('', -1):
            self.confirm.setEnabled(True)
        else:
            self.confirm.setEnabled(False)

    @DEBUG
    def __confirm(self):
        if self.componentTypes_detailed[self.componentType[0]]['category'] == 'assembly':
            self.signal_done.emit()
        else:
            QMessageBox.warning(self, 'Error', 'Component type \"%s\" is not in category \"assembly\".' % self.componentTypes_detailed[self.componentType[0]]['name'])
            return

    @DEBUG
    def __fillQComboBox(self, member_QComboBox, items):
        member_QComboBox.clear()
        member_QComboBox.addItems(items)

    @DEBUG
    def __initUI(self):

        title = QLabel('Step #1: Select the component type to be assembled and then click \"Confirm\".')
        title.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        description = QLabel('Note: the selected component type must be in category \"assembled\".')
        description.setStyleSheet('font-size: 12pt; color: black;')

        label__institution = QLabel('Institution:')
        label__institution.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        label__institution.setAlignment(Qt.AlignCenter)
        label__project = QLabel('Project:')
        label__project.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        label__project.setAlignment(Qt.AlignCenter)
        label__componentType = QLabel('Component Type:')
        label__componentType.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        label__componentType.setAlignment(Qt.AlignCenter)
        label__type = QLabel('Type:')
        label__type.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        label__type.setAlignment(Qt.AlignCenter)

        # See: https://pythonprogramming.net/drop-down-button-window-styles-pyqt-tutorial/
        self.input__institution = QComboBox(self)
        self.input__institution.activated[str].connect(lambda: self.__getInput__institution())
        self.input__institution.setStyleSheet('font-size: 12pt;')
        self.input__project = QComboBox(self)
        self.input__project.currentIndexChanged[str].connect(lambda: self.__getInput__project())
        self.input__project.setStyleSheet('font-size: 12pt;')
        self.input__componentType = QComboBox(self)
        self.input__componentType.currentIndexChanged[str].connect(lambda: self.__getInput__componentType())
        self.input__componentType.setStyleSheet('font-size: 12pt;')
        self.input__type = QComboBox(self)
        self.input__type.currentIndexChanged[str].connect(lambda: self.__getInput__type())
        self.input__type.setStyleSheet('font-size: 12pt;')

        label__cuts = QLabel('Common cuts:')
        label__cuts.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        self.cuts = QLineEdit(self)
        self.cuts.setStyleSheet('font-size: 12pt; color: black;')

        self.confirm = QPushButton('Confirm', self)
        self.confirm.clicked.connect(lambda: self.__confirm())
        self.confirm.setAutoDefault(True)
        self.confirm.setToolTip('Confirm selected component type')
        self.confirm.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        self.layout.addWidget(title,                        0, 0, 1, -1)
        self.layout.addWidget(description,                  1, 0, 1, -1)
        self.layout.addWidget(label__institution,           2, 0, 1, 3)
        self.layout.addWidget(label__project,               2, 3, 1, 3)
        self.layout.addWidget(label__componentType,         2, 6, 1, 3)
        self.layout.addWidget(label__type,                  2, 9, 1, 3)
        self.layout.addWidget(self.input__institution,      3, 0, 1, 3)
        self.layout.addWidget(self.input__project,          3, 3, 1, 3)
        self.layout.addWidget(self.input__componentType,    3, 6, 1, 3)
        self.layout.addWidget(self.input__type,             3, 9, 1, 3)
        self.layout.addWidget(label__cuts,                  4, 0, 1, 1)
        self.layout.addWidget(self.cuts,                    4, 1, 1, -1)
        self.layout.addWidget(self.confirm,                 5, 10, 1, 2)

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

    @DEBUG
    def updateInstitutions(self):
        self.institutions = self.ITkPDSession.doSomething(action = 'listInstitutions', method = 'GET')

    @DEBUG
    def get__componentType_detailed(self):
        return self.componentTypes_detailed[self.componentType[0]]

    @DEBUG
    def get__institution(self):
        return self.institution

    @DEBUG
    def get__type(self):
        return self.type

    @DEBUG
    def initialize(self):
        self.__fillQComboBox(self.input__institution, [institution['name'] for institution in self.institutions])
        self.confirm.setEnabled(False)

    @DEBUG
    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## STEP 2 WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ComponentAssemblyGui__Step2(QWidget):

    @DEBUG
    def __init__(self, parent = None, ITkPDSession = None):
        super(ComponentAssemblyGui__Step2, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.layout = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __setDefaults(self):
        self.componentType_detailed = {}
        self.institution            = ('', -1)
        self.type                   = ('', -1)
        self.components             = []

    @DEBUG
    def __add(self):
        self.table__comps.currentIndex()
        rows = self.table__comps().selectionModel().selectedRows()
        for row0 in rows:
            self.table__comps().setRowHidden(row0.row(), True)

    @DEBUG
    def __remove(self):
        self.table__assemble.currentIndex()
        self.table__assemble().selectionModel().selectedRows()

    @DEBUG
    def __assemble(self):
        self.signal_done.emit()

    @DEBUG
    def __initUI(self):

        title = QLabel('Step #2: Select components from the tabs in the LH table and add them to the assembly in the RH table.')
        title.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        self.status = QLineEdit(self)
        self.status.setStyleSheet('font-size: 12pt; color: black;')

        self.table__comps = QTabComponentTableWidget(self)
        self.table__assemble = QTabComponentTableWidget(self)

        label__buttons = QLabel('--> Manually select rows of components from the above table(s) (using CTRL to deselect).\n--> Press \"Add\" to add the selected rows from the LH table to the assembly, \"Remove\" to remove the selected rows from the assembly, and \"Assemble\" to assemble.')
        label__buttons.setStyleSheet('font-size: 12pt; color: black;')

        self.add = QPushButton('Add', self)
        self.add.clicked.connect(lambda: self.__add())
        self.add.setAutoDefault(True)
        self.add.setToolTip('Add the selected components to the assembly')
        self.add.setStyleSheet('font-size: 12pt; color: black;')
        self.remove = QPushButton('Remove', self)
        self.remove.clicked.connect(lambda: self.__remove())
        self.remove.setAutoDefault(True)
        self.remove.setToolTip('Remove the selected components from the assembly')
        self.remove.setStyleSheet('font-size: 12pt; color: black;')
        self.assemble = QPushButton('Assemble', self)
        self.assemble.clicked.connect(lambda: self.__assemble())
        self.assemble.setAutoDefault(True)
        self.assemble.setToolTip('Assemble the selected components')
        self.assemble.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        self.layout.addWidget(title,                    0, 0, 1, -1)
        self.layout.addWidget(self.status,              1, 0, 1, -1)
        self.layout.addWidget(self.table__comps,        2, 0, 1, 4)
        self.layout.addWidget(self.table__assemble,     2, 4, 1, 4)
        self.layout.addWidget(label__buttons,           3, 0, 1, -1)
        self.layout.addWidget(self.add,                 4, 3, 1, 1)
        self.layout.addWidget(self.remove,              4, 4, 1, 1)
        self.layout.addWidget(self.assemble,            4, 5, 1, 1)

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

    @DEBUG
    def get__componentType_detailed(self):
        return self.componentType_detailed

    @DEBUG
    def get__institution(self):
        return self.institution

    @DEBUG
    def get__type(self):
        return self.type

    @DEBUG
    def set__componentType_detailed(self, componentType_detailed):
        self.componentType_detailed = componentType_detailed

    @DEBUG
    def set__institution(self, institution):
        self.institution = institution

    @DEBUG
    def set__type(self, type0):
        self.type = type0

    @DEBUG
    def initialize(self):
        if self.componentType_detailed != {}:
            self.add.setEnabled(True)
            self.remove.setEnabled(True)
            self.assemble.setEnabled(True)
            children = self.componentType_detailed['children']['*']
            if self.type != ('', -1):
                default_children_codes = [child['code'] for child in children]
                for child in self.componentType_detailed['children'][self.type[0]]:
                    if child['code'] in default_children_codes:
                        i = default_children_codes.index(child['code'])
                        children[i] = child
                    else:
                        children.append(child)
            if children != []:
                # Check if the selected componentType has a type ('' := no type as determined by Step 1)
                if self.type[0] != '':
                    self.table__comps.addTab(QComponentTableWidget(self.table__comps), self.componentType_detailed['name'] + ' (' + self.componentType_detailed['types'][self.type[1]]['name'] + ')')
                    self.table__assemble.addTab(QComponentTableWidget(self.table__assemble), self.componentType_detailed['name'] + ' (' + self.componentType_detailed['types'][self.type[1]]['name'] + ')')
                    self.table__comps[0].setThread(self.ITkPDSession, {'action': 'listComponents', 'method': 'GET', 'data': {'project': self.componentType_detailed['project']['code'], 'componentType': [self.componentType_detailed['code']], 'type': [self.type[0]]}})
                else:
                    self.table__comps.addTab(QComponentTableWidget(self.table__comps), self.componentType_detailed['name'])
                    self.table__assemble.addTab(QComponentTableWidget(self.table__assemble), self.componentType_detailed['code'])
                    self.table__comps[0].setThread(self.ITkPDSession, {'action': 'listComponents', 'method': 'GET', 'data': {'project': self.componentType_detailed['project']['code'], 'componentType': [self.componentType_detailed['code']]}})
                for i, child in enumerate(children):
                    temp_session = ITkPDSession()
                    temp_session.setToken(self.ITkPDSession.token)
                    # Check if a given child component has a type (None := no type from getComponentTypeByCode)
                    if child['type'] is not None:
                        self.table__comps.addTab(QComponentTableWidget(self.table__comps), child['name'] + ' (' + child['type']['name'] + ')')
                        self.table__assemble.addTab(QComponentTableWidget(self.table__assemble), child['name'] + ' (' + child['type']['name'] + ')')
                        self.table__comps[i+1].setThread(temp_session, {'action': 'listComponents', 'method': 'GET', 'data': {'project': self.componentType_detailed['project']['code'], 'componentType': [child['code']], 'type': [child['type']['code']]}})
                    else:
                        self.table__comps.addTab(QComponentTableWidget(self.table__comps), child['name'])
                        self.table__assemble.addTab(QComponentTableWidget(self.table__assemble), child['name'])
                        self.table__comps[i+1].setThread(temp_session, {'action': 'listComponents', 'method': 'GET', 'data': {'project': self.componentType_detailed['project']['code'], 'componentType': [child['code']]}})
                for table in self.table__comps:
                    table.startThread()
                    time.sleep(0.1)
        else:
            self.add.setEnabled(False)
            self.remove.setEnabled(False)
            self.assemble.setEnabled(False)

    @DEBUG
    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## STEP 3 WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ComponentAssemblyGui__Step3(QWidget):

    @DEBUG
    def __init__(self, parent = None, ITkPDSession = None):
        super(ComponentAssemblyGui__Step3, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.layout = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    def __setDefaults(self):
        pass

    def __initUI(self):

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

    def initialize(self):
        pass

    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## MAIN WIDGET ---------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ComponentAssemblyGui(QMainWindow):

    def __init__(self, ITkPDSession = None, parent = None):
        super(ComponentAssemblyGui, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.title = 'ATLAS ITkPD Component Assembly'
        self.geometry = (0, 0, 1500, 900)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __loginDone(self):
        self.step1.updateInstitutions()
        self.step1.initialize()
        self.show()

    @DEBUG
    def __step1Done(self):
        self.step2.set__componentType_detailed(self.step1.get__componentType_detailed())
        self.step2.set__institution(self.step1.get__institution())
        self.step2.set__type(self.step1.get__type())
        self.step2.initialize()

    @DEBUG
    def __step2Done(self):
        pass

    @DEBUG
    def __tieTogetherSignals(self):
        self.login.signal_done.connect(lambda: self.__loginDone())
        self.step1.signal_done.connect(lambda: self.__step1Done())
        self.step2.signal_done.connect(lambda: self.__step2Done())

    ##################################################################
    ############################## MAIN ##############################
    ##################################################################

    @DEBUG
    def __initUI(self):

        ###########################################################
        ### Set size/position of the main window -------------- ###
        ###########################################################

        self.setWindowTitle(self.title)
        self.setGeometry(*self.geometry)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon('./media/ATLAS-Logo-Square-B&W-RGB.png'))

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        close = QShortcut(QKeySequence('Ctrl+Q'), self)
        close.activated.connect(lambda: sys.exit(0))

        self.setStyleSheet('QMessageBox QPushButton { font-size: 12pt; color: black; }')
        self.setStyleSheet('QMessageBox { font-size: 12pt; color: black; }')

        ###########################################################
        ### Instatiate individual pieces ---------------------- ###
        ###########################################################

        self.header = ComponentAssemblyGui__Header(self)
        self.step1  = ComponentAssemblyGui__Step1(self, self.ITkPDSession)
        self.step2  = ComponentAssemblyGui__Step2(self, self.ITkPDSession)

        ###########################################################
        ### Position individual widgets ----------------------- ###
        ###########################################################

        self.main = QWidget(self)
        self.layout = QGridLayout(self.main)
        self.layout.setAlignment(Qt.AlignTop)
        self.setCentralWidget(self.main)

        self.step12 = QWidget(self)
        self.layout__step12 = QGridLayout(self.step12)
        self.layout__step12.addWidget(self.step1,   0, 0)
        self.layout__step12.addWidget(self.step2,   1, 0)

        self.body = QStackedWidget(self)
        self.body.addWidget(self.step12)

        self.layout.addWidget(self.header,          0, 0)
        self.layout.addWidget(self.body,            1, 0)

        ###########################################################
        ### Connect all of our signals and run ---------------- ###
        ###########################################################

        self.login = ITkPDLoginGui(self.ITkPDSession, parent = self, show_immediately = False)

        self.__tieTogetherSignals()

        self.body.setCurrentWidget(self.step12)

        try:
            self.login.show()
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting.' % e, QMessageBox.Ok)
            sys.exit(1)

if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication
        from itk_pdb.dbAccess import ITkPDSession

        session = ITkPDSession(enable_printing = False)

        app = QApplication(sys.argv)
        exe = ComponentAssemblyGui(session)
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
