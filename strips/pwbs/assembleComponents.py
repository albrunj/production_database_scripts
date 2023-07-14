#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import sys
import argparse
import itk_pdb.dbAccess as dbAccess
from itk_pdb.dbAccess import ITkPDSession
global session
session = ITkPDSession()
session.authenticate()

def create_serial(version,batch,pwb_num):
  batch = batch.zfill(2)
  pwb_num = pwb_num.zfill(4)

  return"20USBP0"+version+batch+pwb_num

def get_components(comp_type, sub_type, itemCount):
  if sub_type is not None:
      try:
        unassembled = []
        i = 0
        page = 0
        pageSize = 200
        while i == 0:
            comp_list = session.doSomething(action = "listComponents", data = {'project':'S', 'subproject':'SG', 'componentType':comp_type, 'type':sub_type, 'institution':['LBL'], 'assembled': False, 'pageInfo':{'pageSize':pageSize, 'pageIndex':page}}, method='GET')

            if len(comp_list) < pageSize:                  
              i = 1

            for component in comp_list:
                get_component = session.doSomething(action = "getComponent", data = {'component':component['code']}, method='GET')
                if get_component['trashed'] == False:
                    unassembled.append(get_component)
                if len(unassembled) == itemCount:                  
                  i = 1
                  break

            page = page+1

        if len(unassembled) < itemCount:
            raise Exception('Not enough components of type: ' + comp_type + ', ' + sub_type + ' registered in the database.')

        return iter(unassembled)

      except Exception as e:
        print('Problem finding '+ comp_type + ', ' + sub_type +' in database. Received the following error: ')
        print(e)
        sys.exit()

def assemble_single_component(parent, child, sub_type):
    try:
      session.doSomething(action = "assembleComponent", data = {'parent':parent, 'child':child['code']}, method = 'POST')
    except Exception as e:
        print('Problem assembling '+ sub_type +' onto powerboard number: ' + parent + '. Received the following error: ')
        print(e)


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Assemble Components.")

  parser.add_argument("version", help="PWB version number.")
  parser.add_argument("batch",  help="PWB batch number.")
  parser.add_argument("-a","--AMAC", help="Assembles AMAC. Argument given is AMAC type.")
  parser.add_argument("-b","--BPOL12V", help="Assembles bPOL12V. Argument given is bPOL12V type.")
  parser.add_argument("-hv","--HVMUX", nargs='?', const="HVMUX1", help="Assembles HVMux. Argument given is HVMux type.")
  parser.add_argument("-l","--PWB_LINPOL", nargs='?', const="LINPOL12V", help="Assembles linPOL12V. Argument given is linPOL12V type.")
  parser.add_argument("-c","--PWB_COIL", nargs='?', const="COILV3A", help="Assembles Powerboard Coil. Argument given is coil type.")
  parser.add_argument("-s","--PWB_SHIELDBOX", nargs='?', const="BARRELSHIELDBOX3A", help="Assembles Powerboard Shieldbox. Argument given is shieldbox type.")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-p","--parent", nargs='*', help="Parent PWB numbers.")
  group.add_argument("-r","--range", help="Range of components to register in the form num1-num2.")

  args = parser.parse_args()

  if os.getenv("ITK_DB_AUTH"):
    dbAccess.token = os.getenv("ITK_DB_AUTH")

  if args.parent is not None:
    pb_nums = args.parent
  else:
    pb_nums = range(int(args.range.split("-")[0]),int(args.range.split("-")[1])+1)
    pb_nums = list(map(str, pb_nums))

  itemCount = len(pb_nums)

  amac = get_components('AMAC',args.AMAC, itemCount)
  bpol = get_components('BPOL12V',args.BPOL12V, itemCount)
  hvmux = get_components('HVMUX',args.HVMUX, itemCount)
  linpol = get_components('PWB_LINPOL',args.PWB_LINPOL, itemCount)
  coil = get_components('PWB_COIL',args.PWB_COIL, itemCount)
  shield = get_components('PWB_SHIELDBOX',args.PWB_SHIELDBOX, itemCount)

  for pb in pb_nums:
    parent_id = create_serial(args.version,args.batch,pb)
    if(args.AMAC is not None):
      assemble_single_component(parent_id, next(amac), args.AMAC)
    if(args.BPOL12V is not None):
      assemble_single_component(parent_id, next(bpol),args.BPOL12V)
    if(args.HVMUX is not None):
      assemble_single_component(parent_id, next(hvmux), args.HVMUX)
    if(args.PWB_LINPOL is not None):
      assemble_single_component(parent_id, next(linpol), args.PWB_LINPOL)
    if(args.PWB_COIL is not None):
      assemble_single_component(parent_id, next(coil), args.PWB_COIL)
    if(args.PWB_SHIELDBOX is not None):
      assemble_single_component(parent_id, next(shield), args.PWB_SHIELDBOX)
