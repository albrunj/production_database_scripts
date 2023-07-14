#!/usr/bin/env python
import os
import sys
from pprint import PrettyPrinter

try:
    from PyQt5.QtCore import QSize
    from PyQt5.QtGui import QIcon
    from PyQt5.QtGui import QKeySequence
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWidgets import QDesktopWidget
    from PyQt5.QtWidgets import QGridLayout
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtWidgets import QLineEdit
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtWidgets import QPushButton
    from PyQt5.QtWidgets import QShortcut
    from PyQt5.QtWidgets import QTextBrowser
    from PyQt5.QtWidgets import QTextEdit
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.QtWidgets import QWidget
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
from itk_pdb.identifiers import get_component
from itk_pdb.identifiers import get_localname_codes
from itk_pdb.identifiers import get_rfid_codes
from itk_pdb.ITkPDLoginGui import ITkPDLoginGui

pp = PrettyPrinter(indent = 1, width = 200)

_LOCALNAME_CODES = get_localname_codes()
_RFID_CODES      = get_rfid_codes()

class ComponentLookupGui(QMainWindow):

    def __init__(self, parent = None, session = None):
        super(ComponentLookupGui, self).__init__(parent)
        self.parent = parent
        if not isinstance(session, ITkPDSession):
            raise TypeError('Argument \'session\' must be of type \'%s\': type(session) = %s' % (type(ITkPDSession), type(session)))
        self.session = session
        if self.session is not None:
            self.session.enable_printing = False
        self._initUI()

    def _find_and_fill(self, identifier):
        component = get_component(self.session, identifier)
        if not component:
            QMessageBox.warning(self, 'Error', 'Could not find component \'%s\'!' % identifier)
            url = ''
        else:
            url = 'https://itkpd-test.unicorncollege.cz/componentView?code=%s' % component['code']
        self.code.setText(component.get('code', ''))
        if component.get('serialNumber', '') is not None:
            self.sn.setText(component.get('serialNumber', ''))
        else:
            self.sn.setText('')
        if component.get('alternativeIdentifier') is not None:
            self.altid.setText(component.get('alternativeIdentifier', ''))
        else:
            self.altid.setText('')
        localname = ''
        rfid = ''
        for p in component.get('properties', []):
            if p.get('code') in _LOCALNAME_CODES:
                localname = p.get('value', '')
            elif p.get('code') in _RFID_CODES:
                rfid = p.get('value', '')
        self.localname.setText(localname)
        self.rfid.setText(rfid)
        self.type.setText(component.get('componentType', {}).get('name', ''))
        if component.get('type') is not None:
            self.subtype.setText(component.get('type', {}).get('name', ''))
        else:
            self.subtype.setText('')
        self.institution.setText(component.get('institution', {}).get('name', ''))
        self.location.setText(component.get('currentLocation', {}).get('name', ''))
        self.url.setText('<a href=\"%s\">%s</a>' % (url, url))
        self.json.setText(pp.pformat(component))
        return

    def _initUI(self):

        # Set size/position of the main window
        self.setWindowTitle('ATLAS ITkPD Component Lookup')
        self.setGeometry(0, 0, 900, 900)

        # Let's allow the window size to be adjusted (for different operating systems)
        # self.setFixedSize(self.size())
        icon = QIcon()
        icon.addFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'ATLAS-Logo-Square-B&W-RGB.png'), QSize(64, 64))
        self.setWindowIcon(icon)

        # Move window to the center of the screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        # Make CTRL+Q an escape
        close = QShortcut(QKeySequence('Ctrl+Q'), self)
        close.activated.connect(lambda: sys.exit(0))

        self.setStyleSheet('QMessageBox QPushButton { font-size: 16pt; color: black; }')
        self.setStyleSheet('QMessageBox { font-size: 16pt; color: black; }')

        title = QLabel('ATLAS ITk Production Database Component Lookup', self)
        title.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        quit = QPushButton('Quit', self)
        quit.setStyleSheet('font-size: 16pt; font: bold; color: black;')
        quit.clicked.connect(lambda: sys.exit(0))

        description = QLabel('Enter a component identifier (code, SN, alternative ID, local name, or RFID):', self)
        description.setStyleSheet('font-size: 16pt; color: black; qproperty-alignment: AlignLeft;')

        prompt = QLineEdit(self)
        prompt.setStyleSheet('font-size: 16pt; color: black;')
        prompt.setFocus()

        results_header = QLabel('Results:')
        results_header.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignLeft; text-decoration: underline;')

        code_header = QLabel('Component code:')
        code_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.code = QLineEdit(self)
        self.code.setReadOnly(True)
        self.code.setFocus()
        self.code.setStyleSheet('font-size: 16pt; color: black;')        

        sn_header = QLabel('Serial number:')
        sn_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.sn = QLineEdit(self)
        self.sn.setReadOnly(True)
        self.sn.setStyleSheet('font-size: 16pt; color: black;')

        altid_header = QLabel('Alternative ID:')
        altid_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.altid = QLineEdit(self)
        self.altid.setReadOnly(True)
        self.altid.setStyleSheet('font-size: 16pt; color: black;')

        localname_header = QLabel('Local object name:')
        localname_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.localname = QLineEdit(self)
        self.localname.setReadOnly(True)
        self.localname.setStyleSheet('font-size: 16pt; color: black;')

        rfid_header = QLabel('RFID:')
        rfid_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.rfid = QLineEdit(self)
        self.rfid.setReadOnly(True)
        self.rfid.setStyleSheet('font-size: 16pt; color: black;')

        type_header = QLabel('Component type:')
        type_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.type = QLineEdit(self)
        self.type.setReadOnly(True)
        self.type.setStyleSheet('font-size: 16pt; color: black;')

        subtype_header = QLabel('Subtype:')
        subtype_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.subtype = QLineEdit(self)
        self.subtype.setReadOnly(True)
        self.subtype.setStyleSheet('font-size: 16pt; color: black;')

        institution_header = QLabel('Institution:')
        institution_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.institution = QLineEdit(self)
        self.institution.setReadOnly(True)
        self.institution.setStyleSheet('font-size: 16pt; color: black;')

        location_header = QLabel('Current location:')
        location_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.location = QLineEdit(self)
        self.location.setReadOnly(True)
        self.location.setStyleSheet('font-size: 16pt; color: black;')

        url_header = QLabel('URL:')
        url_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.url = QTextBrowser(self)
        self.url.setReadOnly(True)
        self.url.setAcceptRichText(True)
        self.url.setOpenExternalLinks(True)
        self.url.setFixedHeight(2 * self.location.geometry().height())
        self.url.setStyleSheet('font-size: 16pt; color: black;')

        json_header = QLabel('JSON:')
        json_header.setStyleSheet('font-size: 16pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        self.json = QTextEdit(self)
        self.json.setReadOnly(True)
        self.json.setStyleSheet('font-size: 14pt; color: black;')

        find = QPushButton('Find', self)
        find.setStyleSheet('font-size: 16pt; font: bold; color: black;')
        find.clicked.connect(lambda: self._find_and_fill(prompt.text().strip()))
        prompt.returnPressed.connect(find.click)

        head = QWidget(self)
        head_layout = QGridLayout(head)
        head_layout.addWidget(title,       0, 0,  1,  5)
        head_layout.addWidget(quit,        0, 5,  1,  1)
        head_layout.addWidget(description, 1, 0,  1, -1)
        head_layout.addWidget(prompt,      2, 0,  1,  5)
        head_layout.addWidget(find,        2, 5,  1,  1)

        body = QWidget(self)
        body_layout = QGridLayout(body)
        body_layout.addWidget(results_header,       0, 0,  1, -1)
        body_layout.addWidget(code_header,          1, 0,  1,  1)
        body_layout.addWidget(self.code,            1, 1,  1, -1)
        body_layout.addWidget(sn_header,            2, 0,  1,  1)
        body_layout.addWidget(self.sn,              2, 1,  1, -1)
        body_layout.addWidget(altid_header,         3, 0,  1,  1)
        body_layout.addWidget(self.altid,           3, 1,  1, -1)
        body_layout.addWidget(localname_header,     4, 0,  1,  1)
        body_layout.addWidget(self.localname,       4, 1,  1, -1)
        body_layout.addWidget(rfid_header,          5, 0,  1,  1)
        body_layout.addWidget(self.rfid,            5, 1,  1, -1)
        body_layout.addWidget(type_header,          6, 0,  1,  1)
        body_layout.addWidget(self.type,            6, 1,  1, -1)
        body_layout.addWidget(subtype_header,       7, 0,  1,  1)
        body_layout.addWidget(self.subtype,         7, 1,  1, -1)
        body_layout.addWidget(institution_header,   8, 0,  1,  1)
        body_layout.addWidget(self.institution,     8, 1,  1, -1)
        body_layout.addWidget(location_header,      9, 0,  1,  1)
        body_layout.addWidget(self.location,        9, 1,  1, -1)
        body_layout.addWidget(url_header,          10, 0,  1,  1)
        body_layout.addWidget(self.url,            10, 1,  1, -1)

        tail = QWidget(self)
        tail_layout = QVBoxLayout(tail)
        tail_layout.addWidget(json_header)
        tail_layout.addWidget(self.json)

        main = QWidget(self)
        layout = QGridLayout(main)
        layout.addWidget(head,  0, 0,  5, -1)
        layout.addWidget(body,  5, 0, 25, -1)
        layout.addWidget(tail, 30, 0, 50, -1)

        self.setCentralWidget(main)

        try:
            ITkPDLoginGui(self.session, self)
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting. See the console for details.' % e, QMessageBox.Ok)
            sys.exit(1)

if __name__ == '__main__':

    try:

        session = ITkPDSession()

        app = QApplication(sys.argv)
        exe = ComponentLookupGui(None, session)
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
