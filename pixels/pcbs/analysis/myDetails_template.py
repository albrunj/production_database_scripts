## update and save as myDetails.py

class Credentials:
    def __init__(self, name, AC1, AC2):
        self.name = name
        self.ac1 = AC1
        self.ac2 = AC2


def SetITk():
    creds= Credentials("NAME", "YOUR_AUTHENTICATION_CODE_1","YOUR_AUTHENTICATION_CODE_2")
    return creds
