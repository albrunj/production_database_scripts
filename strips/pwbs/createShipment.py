#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import argparse
import itk_pdb.dbAccess as dbAccess

def create_serial(version,batch,pwb_num):
	batch = batch.zfill(2)
	pwb_num = pwb_num.zfill(4)

	return"20USBP0"+version+batch+pwb_num

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Creates shippment of items given their serial numbers.")

	parser.add_argument("name", help="Name of shipment")
	parser.add_argument("recipient", help="Code for recipient institution.")
	parser.add_argument("globe", help="One of domestic, intraContinental, or continental.")
	parser.add_argument("version", help="Powerboard version.")
	parser.add_argument("batch", help="Powerboard batch.")
	parser.add_argument("-i","--items", nargs='*', help="Powerboard numbers of items in shipment.")

	args = parser.parse_args()

	args.items = [create_serial(args.version,args.batch,pwb_num) for pwb_num in args.items]

	if os.getenv("ITK_DB_AUTH"):
        	dbAccess.token = os.getenv("ITK_DB_AUTH")
	
	component_codes = []
	for i in args.items:
		component = dbAccess.doSomething("getComponent", {'component':i}, method='GET')
		code = component['code']
		component_codes.append(code)

	dbAccess.doSomething("createShipment", {'name':args.name, 'sender':'LBL', 'recipient':args.recipient, 'type':args.globe, 'status':'inTransit','shipmentItems':component_codes}, method='POST')
