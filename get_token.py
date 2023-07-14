#!/usr/bin/env python
import platform

import itk_pdb.dbAccess as dbAccess

if __name__ == "__main__":
    token = dbAccess.authenticate()
    if platform.system() == "Windows":
        print("$env:ITK_DB_AUTH = '%s'" % token)
    else:
        print("export ITK_DB_AUTH=%s" % token)
