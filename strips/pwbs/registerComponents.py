#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import argparse
import itk_pdb.dbAccess as dbAccess
from datetime import date

def create_serial(version,batch,pwb_num):
    batch = batch.zfill(2)
    pwb_num = pwb_num.zfill(4)

    return"20USBP0"+version+batch+pwb_num


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Register specified number of components to production database.")

    parser.add_argument("component", help="Component (general) you wish to register. (Must be the code as specified by the database: AMAC Chip=AMAC, bPOL12V=BPOL12V, HVMux=HVMUX, linPOL12V=PWB_LINPOL, Powerboard Coil=PWB_COIL, Shieldbox=PWB_SHIELDBOX")

    parser.add_argument("type", help="Type (subtype) of component you wish to register. (Must be the code as specified by the database.)")

    parser.add_argument("num_of_components", type=int, help="Number of components you wish to register.")

    parser.add_argument("-v", "--version", help="PWB version number.")

    parser.add_argument("-b", "--batch", help="PWB batch number.")

    parser.add_argument("-n", "--number", help="PWB number. If num_of_components is more than 1, that number of powerboards will be registered starting at the one given for this argument.")

    args = parser.parse_args()

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    if args.component=='PWB':
        for i in range (0, args.num_of_components):
            print(create_serial(args.version,args.batch,str(int(args.number) + i)))
            dbAccess.doSomething("registerComponent", {'project':'S', 'subproject':'SB', 'institution':'LBL', 'componentType':args.component, 'type':args.type, 'serialNumber':create_serial(args.version,args.batch,str(int(args.number) + i)), 'properties':{'VERSION':args.version, 'BATCH':int(args.batch), 'PB_NUMBWE':int(args.number) + i}}, method='POST')

    elif args.component=='AMAC':
        if args.type=='2':
            version = '2'
        if args.type=='TEST':
            version = '2a'
        for i in range (0, args.num_of_components):
            dbAccess.doSomething("registerComponent", {'project':'S', 'subproject':'SG', 'institution':'LBL', 'componentType':args.component, 'type':args.type, 'properties':{'VERSION':version}}, method = 'POST')
    else:
        for i in range (0, args.num_of_components):
            dbAccess.doSomething("registerComponent", {'project':'S', 'subproject':'SG', 'institution':'LBL', 'componentType':args.component, 'type':args.type, 'properties':{'BATCH':str(date.today())}}, method = 'POST')
