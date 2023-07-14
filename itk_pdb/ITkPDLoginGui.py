#!/usr/bin/env python
# ITkPDLoginGui.py -- class for logging into the ITk Production Database
# Created: 2019/02/13, Updated: 2022/01/25
# Written by Matthew Basso
import os
import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtWidgets import QWidget
from requests.exceptions import RequestException

class ITkPDLoginGui(QDialog):

    def __init__(self, ITkPDSession = None, parent = None, show_immediately = True):

        super(ITkPDLoginGui, self).__init__(parent)
        self.ITkPDSession = ITkPDSession
        if self.ITkPDSession is not None:
            self.ITkPDSession.enable_printing = False
        self.parent = parent
        self.show_immediately = show_immediately
        self.title = 'ATLAS ITkPD Login'
        # self.geometry = (0, 0, 480, 240)
        self._initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    # Check if token is available
    def _existingTokenAvailable(self):
        # NOTE: this is hacky for now, doesn't actually check if the token is still good
        if 'Authorization' in self.ITkPDSession.headers.keys() or self.ITkPDSession.getTokenFromEnv():
            QMessageBox.information(self, 'Success', 'Token already available!')
            self.signal_done.emit()
            self.close()
            if self.parent is not None:
                self.parent.show()
                return True
        return False

    # Wrap show function
    def show(self):
        if not self._existingTokenAvailable():
            super(ITkPDLoginGui, self).show()

    def _initUI(self):

        # Set size/position of the main window
        self.setWindowTitle(self.title)
        # self.setGeometry(*self.geometry)

        # Let's allow the window size to be adjusted (for different operating systems)
        # self.setFixedSize(self.size())
        icon = QIcon()
        icon.addFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'media', 'ATLAS-Logo-Square-B&W-RGB.png'), QSize(64, 64))
        self.setWindowIcon(icon)

        # Move window to the center of the screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        # Make CTRL+Q an escape
        shortcut__close = QShortcut(QKeySequence('Ctrl+Q'), self)
        shortcut__close.activated.connect(lambda: sys.exit(0))

        title = QLabel('ATLAS ITk Production Database Login', self)
        title.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignCenter;')

        title__accessCode1 = QLabel('Access Code 1:', self)
        title__accessCode1.setStyleSheet('font-size: 12pt; color: black;')
        self.line__accessCode1 = QLineEdit(self)
        self.line__accessCode1.setEchoMode(QLineEdit.Password)

        title__accessCode2 = QLabel('Access Code 2:', self)
        title__accessCode2.setStyleSheet('font-size: 12pt; color: black;')
        self.line__accessCode2 = QLineEdit(self)
        self.line__accessCode2.setEchoMode(QLineEdit.Password)

        login = QPushButton('Login', self)
        login.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        login.clicked.connect(lambda: self._login())
        quit = QPushButton('Quit', self)
        quit.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        quit.clicked.connect(lambda: sys.exit(0))

        buttons = QWidget(self)
        layout__buttons = QGridLayout(buttons)
        layout__buttons.addWidget(login,            0, 0, 1, 1)
        layout__buttons.addWidget(quit,             0, 1, 1, 1)

        layout = QGridLayout(self)
        layout.addWidget(title,                     0, 0, 1, -1)
        layout.addWidget(title__accessCode1,        1, 0, 1, 1)
        layout.addWidget(self.line__accessCode1,    1, 1, 1, 1)
        layout.addWidget(title__accessCode2,        2, 0, 1, 1)
        layout.addWidget(self.line__accessCode2,    2, 1, 1, 1)
        layout.addWidget(buttons,                   3, 0, 1, -1)

        if self.show_immediately:
            self.show()

    # Add support for checking if tokens are expired or not (?)
    # Keys: "expires_at", "issued_at", "expires_in"
    def _login(self):
        if self.ITkPDSession is not None:
            try:
                accessCode1 = self.line__accessCode1.text()
                accessCode2 = self.line__accessCode2.text()
                if accessCode1 == '' or accessCode2 == '':
                    QMessageBox.warning(self, 'Warning', 'Access code(s) left blank')
                else:
                    self.ITkPDSession.authenticate(accessCode1, accessCode2)
                    QMessageBox.information(self, 'Success', 'Authentication successful!')
                    self.signal_done.emit()
                    self.close()
                    if self.parent is not None:
                        self.parent.show()
            except RequestException as e:
                QMessageBox.warning(self, 'Error', 'requests exception raised: %s' % e)
        else:
            QMessageBox.warning(self, 'Error', 'No ITkPDSession available')

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication
        from itk_pdb.dbAccess import ITkPDSession

        session = ITkPDSession()

        app = QApplication(sys.argv)
        exe = ITkPDLoginGui(session)
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
