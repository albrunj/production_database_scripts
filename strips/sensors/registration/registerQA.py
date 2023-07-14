#!/usr/bin/env python
import argparse
import os
import re

from __path__ import updatePath
updatePath()
from strips.sensors.SensorSNUtils import makeSN
	
from pprint import PrettyPrinter
import itk_pdb.dbAccess as dbAccess
from itk_pdb.dbAccess import ITkPDSession


qa_ctypes = {'dummy':['SENSOR_QCHIP_TEST','SENSOR_QAMINI_TEST'],
	     'real':['SENSOR_TESTCHIP_MD8','SENSOR_MINI_MD8']}
chip_ctype = {'dummy':'SENSOR_QCHIP_TEST','real':'SENSOR_TESTCHIP_MD8'}
mini_ctype = {'dummy':'SENSOR_QAMINI_TEST','real':'SENSOR_MINI_MD8'}
parent_ctype = {'dummy':'SENSOR_W_TEST','real':'SENSOR_WAFER'}

acceptable_sensor_types = ['ATLASDUMMY18','ATLAS18LS', 'ATLAS18SS', 'ATLAS18R0', 'ATLAS18R1', 'ATLAS18R2', 'ATLAS18R3', 'ATLAS18R4', 'ATLAS18R5']
acceptable_component_type_names = ['Sensor Testchip&MD8','Sensor Mini&MD8','Sensor QAchip test','Sensor QAmini test']
component_code = {'Sensor QAchip test':'SENSOR_QCHIP_TEST',
		  'Sensor QAmini test':'SENSOR_QAMINI_TEST',
		  'Sensor Testchip&MD8':'SENSOR_TESTCHIP_MD8',
		  'Sensor Mini&MD8':'SENSOR_MINI_MD8'}
acceptable_subprojects = ['SE','SB']


def get_parent_exists(subproject,component_type,sensor_type,wafer_number,dummy=False):	
	#check if parent exists
	print("Checking if parent exists in DB...")
	parent_SN = get_parentSN(component_type,sensor_type,
					wafer_number,dummy=dummy,subproject=subproject)
	parent_data = getData(parent_SN)
	if parent_data != None:
		print("Parent (SN: {}) is registered.".format(parent_SN))
		return True
	
	print("Parent (SN: {}) is not registered.".format(parent_SN))
	return False

def get_qa_parent_component_type(dummy=False):
	test_type = 'dummy' if dummy else 'real'
	return parent_ctype[test_type]

def get_parentSN(component_type, sensor_type, wafer_number,dummy=False,subproject=None):
	#subproject is not necessary if not a dummy
	parent_ctype = get_qa_parent_component_type(dummy=dummy)
	subproject = None if not dummy else subproject
	parentSN = makeSN(parent_ctype,sensor_type,
                          wafer_number,dummy=dummy,subproject=subproject)
	return parentSN

def getData(SN):
	try:
		data = dbAccess.extractList("getComponent",
				method = "GET",
				data = {'component':SN})
	except:
		print("Request failed:")
		import traceback
		traceback.print_exc()

		return None
	
	return data

def get_batch_and_wafer_numbers(vpx):
	#always 5 digits '#####'
	vpx_split = vpx.split('-')
	batch_number = vpx_split[0]
	wafer_number = vpx_split[1][1:]
	if len(wafer_number) < 5:
		wafer_number = "0"*(5-len(wafer_number)) + wafer_number
	return batch_number,wafer_number

def parse_line(line):
	#comma separated: "ATLAS18SS,VPX99999-W102,Sensor Testchip&MD8,ATLAS test chip 2 - A6"
	stripped_line = [s.strip() for s in line.split(',')]
	if len(stripped_line) != 4: 
		print("Line in invalid format: '{}'".format(line))
		return None
	
	sensor_type,vpx,component_type_name,wafer_pos_label = stripped_line
	#check if each value is acceptable
        # VF, 2021-10-20: have to allow for VPA now, in addition to VPX
	if sensor_type not in acceptable_sensor_types or \
			component_type_name not in acceptable_component_type_names or \
			not bool(re.search(r'VP(X|A)\d{5}-W\d{1,}$',vpx)) or \
			not bool(re.search(r'[A,M]\d{1,}$',wafer_pos_label)):
		return None	

	component_type_code = component_code[component_type_name]
	return sensor_type,vpx,component_type_code,wafer_pos_label

def getAllowedComponents(session,institution):
	#ex. allowed_components = ['SENSOR','SENSOR_WAFER',etc.]
	allowed_components = []
	response_json = session.doSomething(action = 'listInstitutions', method = 'GET', data = {})
	for inst_data in response_json:
		inst_code = inst_data['code']
		if inst_code != institution:
			continue
		for project in inst_data['componentType']:
			for comp in project['itemList']:
				allowed_components.append(comp['code'])
	return allowed_components
 
def get_institution(line):
	institution = line.strip().split()[1]
	return institution

def get_subproject_from_line(line):
	splitline = line.strip().split()
	if len(splitline) > 2:
		#this means it is a "real" file (not dummy)
		return None
	subproject = splitline[1]
	if subproject in acceptable_subprojects:
		return subproject
	raise Exception("Invalid subproject: {}".format(subproject))

def get_subproject_from_sensor_type(sensor_type):
	#only used for real components. For dummy's, subproject must
	# be listed in the file.
	if bool(re.search(r'R\d{1}$',sensor_type)):
		return 'SE'
	elif bool(re.search(r'S$',sensor_type)):
		return 'SB'
	else:
		#shouldn't ever get here...
		raise Exception("Invalid sensor type")

def register_and_assembleQA(session,sensor_type,vpx,component_type,wpl,subproject,institution,dummy):
	batch_number,wafer_number = get_batch_and_wafer_numbers(vpx)
	SN = makeSN(component_type, sensor_type, wafer_number, dummy=dummy, qa_piece=True,subproject=subproject)
	dto = {
	  "project": 'S',
	  "subproject": subproject,
	  "institution": institution,
	  "componentType": component_type,
	  "serialNumber": SN,
	  "batches": {'SENSORS_PROD_BATCH': batch_number},
	  "properties": { 'WAFER_POSITION_LABEL': wpl }
	  }	
	
	pp = PrettyPrinter(indent = 1,width=200)
	print("PRINTING dto")
	pp.pprint(dto)

	#register QA piece
	response = session.doSomething(action = 'registerComponent', method = 'POST',
					data = dto)

	print("Successfully registered QA piece with SN {}!".format(SN))
	#check if parent is registered	
	parent_exists = get_parent_exists(subproject,component_type,sensor_type,wafer_number,dummy=dummy)
	if parent_exists: #assemble QA piece
		wafer_code = get_parentSN(component_type,sensor_type,wafer_number,dummy=dummy,subproject=subproject)
		print("Assembling to parent...")
		assembly_data = {'parent': wafer_code, 'child': response['component']['code']}#, 'properties': { 'WAFER_POSITION_LABEL': wpl }}
		print("assembly dto =",assembly_data)
		session.doSomething(action='assembleComponent', method = 'POST', data = assembly_data)
		print("Successfully assembled to parent (Parent SN:{})".format(wafer_code))
	else:
		print("QA piece was not assembled since parent wasn't found")

	print("View this QA piece component at this URL: itkpd-test.unicorncollege.cz/componentView?code={}".format(response['component']['code']))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = 'Register (and assemble if parent exists) QA pieces (dummy or real)', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
	required = parser.add_argument_group('required arguments')
	required.add_argument('-fp', '--fpath', dest = 'fpath', type = str, required = True, help = 'Location of text file with list of QA pieces to register')
	args = parser.parse_args()
	
	##############
	if os.getenv("ITK_DB_AUTH"):
		dbAccess.token = os.getenv("ITK_DB_AUTH")
	else:
		print("Token expired.")

	session = ITkPDSession()
	session.authenticate()
	os.environ['ITK_DB_AUTH'] = session.token['token']
	#print("session.token = ",session.token)
	#example input	
	#TODO: read from "ATLAS18SS   VPX99999-W1001    ATLAS test chip 1 - A3"
	#		<sensor_type>   <vpx>              <wafer_pos_label>
	#######
	#dummy = True
	#institution = "UCSC"
	#subproject = "SE" 
	#######
	with open(args.fpath,"r") as f:
		lines = f.readlines()
	
	institution = get_institution(lines[0])
	allowed_components = getAllowedComponents(session,institution)
	subproject = get_subproject_from_line(lines[1])
	if subproject == None:
		#means this is a "real" file (not dummy components)
		#subproject not yet defined! (is None)
		dummy = False
		component_list_start_line = 1
	else:
		#Note: subproject is this value for whole file
		dummy = True
		component_list_start_line = 2

	#now each line should be in format:
	#ATLAS18SS,\tVPX99999-W1001,\tATLAS test chip 1 - A3
	#or ATLASDUMMY18, ...etc
	
	for line in lines[component_list_start_line:]:
		if line.startswith('#'): 
			#allow for commented lines
			continue
		rv = parse_line(line)
		if rv == None:
			#error reading line
			raise Exception("Error reading line: '{}'".format(line))
		sensor_type,vpx,component_type,wafer_pos_label = rv		
		if component_type not in allowed_components: 
			continue

		if not dummy:
			#extract subproject from sensor type
			subproject = get_subproject_from_sensor_type(sensor_type)
		args = [session,sensor_type,vpx,component_type,wafer_pos_label,subproject,institution,dummy]
		register_and_assembleQA(*args)
