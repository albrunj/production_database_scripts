#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import argparse
import itk_pdb.dbAccess as dbAccess
from itk_pdb.dbAccess import ITkPDSession

def getSerials(eFuse, pass1=None, pass2=None):
  global session
  session = ITkPDSession()
  session.authenticate()

  if pass1 == None and pass2 == None:
    if os.getenv("ITK_DB_AUTH"):
      dbAccess.token = os.getenv("ITK_DB_AUTH")

  else:
    os.environ["ITK_DB_AUTH"] = dbAccess.authenticate(pass1, pass2)

  pwbSN = []
  for ID in eFuse:
    try:
      amac = session.doSomething(action = "listComponentsByProperty", data = {'project':'S', 'componentType':'AMAC', 'propertyFilter':[{'code':'EFUSEID', 'operator':'=', 'value':ID}]}, method='POST')
      amacSN = amac[0]['serialNumber']

      pwb = session.doSomething(action = "getComponent", data = {'component':amacSN}, method='GET')
      pwbSN.append(pwb['parents'][0]['serialNumber'])

    except:
      pwbSN.append("Error retrieving powerboard for hex ID " + ID)

  return pwbSN


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Assemble Components.")

  parser.add_argument("eFuse", nargs='+', help="Hex AMAC eFuse ID (include 0x)")

  args = parser.parse_args()

  pwbSN = getSerials(args.eFuse)

  for pb in pwbSN:
    print(pb)
