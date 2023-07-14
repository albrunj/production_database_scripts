#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import argparse
import itk_pdb.dbAccess as dbAccess

def create_serial(version,batch,pwb_num):
    batch = +batch.zfill(2)
    pwb_num = pwb_num.zfill(4)

    return"20USBP0"+version+batch+pwb_num

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Creates shippment of items given their serial numbers.")

    parser.add_argument("stage", help="Code for component stage.")
    parser.add_argument("version", help="Powerboard version.")
    parser.add_argument("batch", help="Powerboard batch.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i","--items", nargs='*', help="Powerboard numbers of stages you wish to set.")
    group.add_argument("-r","--range", help="Range of powerboards for stages you wish to set. Given as n1-n2.")

    args = parser.parse_args()

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")
	
    if args.items is not None:
        args.items = [create_serial(args.version,args.batch,pwb_num) for pwb_num in args.items]
        for num in args.items:
            dbAccess.doSomething("setComponentStage", {'component':num, 'stage':args.stage}, method= 'POST')

    else:
        split = args.range.split("-")
        range_items = [create_serial(args.version,args.batch,str(pwb_num)) for pwb_num in range(int(split[0]),int(split[1])+1)]
        for num in range_items:
            dbAccess.doSomething("setComponentStage", {'component':num, 'stage':args.stage}, method= 'POST')
