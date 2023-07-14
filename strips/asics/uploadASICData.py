#!/usr/bin/env python
# uploadASICData.py -- look at JSON files stored locally, find wafer number, create ASICs using lookup table, upload JSON to right component
# Created: 2020/04/03
# Written by Mitch Norfolk, Matt Basso
#######Points regarding this script so I dont forget
#---> Works fine for fresh data not in the DB
#---> There is a bug with the DB which doesnt give the child properties when you do the API command 'getComponentBulk'- I think there is a temporary workaround
#---> We are having to manually loop over all the ASICs to set their fuse ID, we could do with fucntionality to do this at the time we create the children. E.g. pass a list with the same number of elements as children and it will assign the created children the fuse Ids?
#---> Its in a 'testing mode' for the time being as 'createComponentChildren' under normal circumstances would create around 400 ASICs in the DB. So this will need changing as we move to more ASICs being tested.
#--->createComponentChildren API call refers to children as 'dummyChildren' regardless of whether they are or not
#--> ASICs what cant be assigned a fuse ID are given -999, since we search for ASICs already in DB by fuse ID, this is not good

_DUMMY = True
if _DUMMY:
	abc_wafer_code = 'ABC_WAFER_TEST'
else:
	abc_wafer_code = 'ABC_WAFER'

if __name__ == '__main__':
	from __path__ import updatePath
	updatePath()

import argparse
import json
import os
import sys
from datetime import datetime

from itk_pdb.databaseUtilities import Colours
from itk_pdb.databaseUtilities import ERROR
from itk_pdb.databaseUtilities import INFO
from itk_pdb.databaseUtilities import STATUS
from itk_pdb.databaseUtilities import WARNING
from itk_pdb.dbAccess import ITkPDSession
from strips.asics.LookUpTable import DieType
from strips.asics.LookUpTable import LookUpTable
from strips.asics.LookUpTable import WaferSeries
from strips.modules.uploadITSDAQTests import getYesOrNo

class ParseUpload (ITkPDSession):

	# Guard against potentially setting extra member vars
	__slots__ = ['ASIC_JSON_folder_path', 'coreASICData', 'get_confirm', 'lut']

	#initialise main data list, path to JSONs and authenticate
	def __init__(self, ASIC_JSON_folder_path, get_confirm):
		super(ParseUpload, self).__init__()
		self.ASIC_JSON_folder_path = ASIC_JSON_folder_path
		self.coreASICData = []
		self.get_confirm = get_confirm
		self.lut = LookUpTable()

	#find files, open each one, save needed data to a list of dictionaries where each entry is a different ASIC
	def JSONParse(self):
		INFO ('Parsing JSON files in folder:' + os.path.abspath(self.ASIC_JSON_folder_path)) # print the absolute path? or the relative one?

		#initialise list of wafer names and ASIC number
		ASIC_number = 0
		waferNames =[]

		# get list of already parsed JSONs from uploaded.txt
		g = open(os.path.join(self.ASIC_JSON_folder_path, 'Uploaded.txt'), 'a+')
		uploadedJSONs = g.read().splitlines()

		filesToUpload = False
		for filename in os.listdir(self.ASIC_JSON_folder_path):
			#only open json files and ones not already uploaded
			if filename[-4:] == 'json' and filename not in uploadedJSONs:
				# if it enters this code block then there are files to be uploaded
				filesToUpload = True
				#open the file
				with open(os.path.join(self.ASIC_JSON_folder_path, filename), 'r') as f:
					# parse the json
					data = json.load(f)
					# firstly, get wafername and add to a seperate list, then get fuseID. I also need institution for the registration later
					waferName = data.get('properties', {}).get('WAFERNAME', None)
					waferNames.append(waferName)
					institution = data.get('institution', None)
					fuseID = data.get('properties', {}).get('FUSEID_DEC', None)

				# firstly check if the ASIC is not already in coreASICData, if its not add it to the list
				if not any(d['FUSEID_DEC'] == fuseID for d in self.coreASICData):
					# make the dictionary template for each ASIC
					# --> assign each ASIC with its properties given by the JSON
					# --> If I assume that for each ASIC, the tests being uploaded at this time are all from the same institution- this makes things simpler but could change if needed
					self.coreASICData.append({'FUSEID_DEC': fuseID, 'institution': institution, 'componentCode': None, 'inDB': False, 'waferName': waferName, 'waferComponentCode': None, 'associatedTestFiles': []})
					# add the file name to the ASIC
					self.coreASICData[ASIC_number]['associatedTestFiles'].append(filename)
					ASIC_number += 1
			
				# if the fuse ID is already in the core data then find the ASIC number and add the JSON to be uploaded
				else :
					for number, ASIC in enumerate(self.coreASICData):
						if ASIC['FUSEID_DEC'] == fuseID:
							self.coreASICData[number]['associatedTestFiles'].append(filename)
		# close the file of uploaded json files
		g.close()

		# stop here if no files to upload
		if filesToUpload == False:
			ERROR('No files to be uploaded. All files already in Uploaded.txt (already uploaded)')
			sys.exit(1)

		# list the wafer names and  get rid of duplicates in wafer list
		waferNames = list(set(waferNames))

		self.waferCheck(waferNames)

	# So far I have populated a list of ASICs under test with the neccessary information and also got a seperate list of the wafer names.

	# Function to check if the wafer is in the DB already (cant imagine this will often be the case) and deal with wafers not in DB
	def waferCheck(self, waferList):
		#Define a list of all wafers what are in the DB so I can do a getComponentBulk later
		wafersInDBCodes = []
		wafersInDBNames =[]

		#check if each wafer is in DB by searching for the wafer name  
		for wafer in waferList:
			waferInfo = self.doSomething('listComponentsByProperty', 'POST', data = {'project': 'S', 'componentType': abc_wafer_code, 'propertyFilter': [{'code': 'ABCWAFERNAME', 'operator': '=', 'value': wafer}]})

			#if waferInfo is not empty then the wafer exists, get the child component codes and fuseID
			if len(waferInfo) > 1: 
				WARNING('There is more than one wafer associated with this wafername, using the first one in the list (i.e., the most recent?)')

			elif len(waferInfo) != 0: 
				# add codes and names of InDB wafers to a list 
				wafersInDBCodes.append(waferInfo[0]['code'])
				wafersInDBNames.append(wafer)

				# change all the ASICs in self.coreASICData with this wafer name to inDB: True and log component code of wafer
				for number, ASIC in enumerate(self.coreASICData):
					if ASIC['waferName'] == wafer:
						self.coreASICData[number]['inDB'] = True
						self.coreASICData[number]['waferComponentCode'] = waferInfo[0]['code']

		# Now I have updated self.coreASICData with info for ASICs which have wafers in the DB

		# check the children of the wafers in the DB
		if len(wafersInDBCodes) != 0:
			# get the child information for each wafer
			waferChildrenBulk = [x['children'] for x in self.doSomething('getComponentBulk' , 'GET', data = {'component': wafersInDBCodes})]
			# Could have no mention of children or could say children are missing.

			# Case for no mention of children 
			if any(d == [] for d in waferChildrenBulk):
				for position, waferChildren in enumerate(waferChildrenBulk):
					if len(waferChildren) == 0:
						# Create children for wafer
						if self.get_confirm:
							self.getConfirm(0, wafersInDBNames[position])

						self.createWaferChildren(wafersInDBCodes[position], wafersInDBNames[position])

			# Case for mention of children	
			elif any(waferChildrenBulk) !=  0:
				# lists to help me distinguish which wafers have children but dont have children corresponding to the ASICS under test (as a check)
				wafersWithChildren =[]
				Dict_index = 0
			
				# loop over wafers what exist in the DB
				for number, waferChildren in enumerate(waferChildrenBulk):
					# if the wafer has no mention of children, this has been picked up, go to next wafer
					if len(waferChildren) == 0:
						continue

					# case for if there is mention of children but they are missing then loop through the children, if they are all missing create the children
					if any(d['component'] == None for d in waferChildren):
						# in this case I am expecting that if one of them is not registered, none of them will be so shoot an error.  otherwise, create all children
						if any(d['component'] != None for d in waferChildren):
							# Not expecting this to ever be the case
							ERROR('The wafer %s has children but some are registered and some are not, please consult DB' % wafersInDBNames[number])
							sys.exit(1)

						# if wafer has mention of children but they are all missing, create the children
						else:
							if self.getConfirm:
								self.getConfirm(0, wafersInDBNames[number])

							# if all children are missing, create them and go to next wafer
							self.createWaferChildren(wafersInDBCodes[number], wafersInDBNames[number])
							continue

					# case for if there are registered wafer children
					wafersWithChildren.append({'waferName': wafersInDBNames[number], 'IDChildren':[]})

					# Workaround:
					# H A C K Y
					waferChildrenBulk[number] = self.doSomething(action = 'getComponentBulk', method = 'GET', data = {'component': [c['component']['code'] for c in waferChildren]})
					for c in waferChildrenBulk[number]:
						for p in c.get('properties', []):
							if p['code'] == 'ID':
								wafersWithChildren[Dict_index]['IDChildren'].append(p['value'])

					# loop over children and append the propeties to a list
					for child in waferChildrenBulk[number]:
						# append to the dictionary list the fuse ID of the children
						###########################################################################################################################################################################
						#This line of code doesnt seem to be working, when I do a get component bulk the children seem to have 'properties' set to None regardless of whether they have properties#
						###########################################################################################################################################################################
						# --> Handled before this loop with a temporary workaround
						# wafersWithChildren[Dict_index]['IDChildren'].append([p['value'] for p in child['properties'] if p['code']  == 'ID'][0])

						# loop through the ASICs under test and see if any ID's match the child ID collected from DB, if they do get component code
						ID = None
						for p in child.get('properties', []):
							if p['code'] == 'ID':
								ID = p['value']
						for number, ASIC in enumerate(self.coreASICData):
							if ASIC['FUSEID_DEC'] == ID:
								self.coreASICData[number]['componentCode'] = child['code']

					Dict_index += 1

				# case for if the wafer has registered children but none correspond to the tested ASICs
				for ASIC in self.coreASICData:
					# if the test asic wafername is not in the wafers with children list then skip
					for wafer in wafersWithChildren:
						if ASIC['waferName'] == wafer['waferName']:
							if ASIC['FUSEID_DEC'] not in wafer['IDChildren']:
								WARNING('The wafer %s has children on DB but no child associated with fuse ID %s given from test data, check on DB if some children need deleting' % (ASIC['waferName'], ASIC['FUSEID_DEC']))
								sys.exit(1)

		# Deal with wafers not in DB
		if any(not d['inDB'] for d in self.coreASICData):
			# create a list to tell which wafers I have registered
			wafersDone = []
			#loop through ASICs not in DB and register wafers and children
			for ASIC in self.coreASICData:
				# if it is in DB skip
				if ASIC['inDB']:
					continue
				if ASIC['waferName'] not in wafersDone:

					if self.get_confirm:
						self.getConfirm(1, ASIC['waferName'])

					waferInfo = self.doSomething('registerComponent', 'POST', data = {'project': 'S', 'subproject': 'SG', 'institution': ASIC['institution'], 'componentType': abc_wafer_code, 'type':'ABCSTAR','properties':{'ABCWAFERNAME': ASIC['waferName'], 'HEIGHT': 0}})
					wafersDone.append(ASIC['waferName'])

					# I need to assign the new wafer code to the ASICS with the right wafername
					for EL_NUMBER, element in enumerate(self.coreASICData):
						if element['waferName'] == ASIC['waferName']:
							self.coreASICData[EL_NUMBER]['waferComponentCode'] = waferInfo['component']['code']

					# I now need to register the children
					self.createWaferChildren(waferInfo['component']['code'], ASIC['waferName'])

			if self.get_confirm:
				self.getConfirm(2, self.coreASICData)

			# and upload the JSONs
		print(self.coreASICData)
		self.uploadJSON(self.coreASICData)

	def createWaferChildren(self, waferCode, waferName):
		INFO('Creating wafer children for wafer name %s with code %s and assigning FuseID' % (waferName, waferCode))

		# create the children of the wafer
		childrenInfo = self.doSomething('createComponentChildren', 'POST', data = {'component': waferCode})

		#get Fuse IDs from the look up table.
		# --> The length of the fuse IDs list is 378, meaning there is this many children in a wafer? - yes, I think so -- MB
		fuseIDs = self.useLookUpTable(waferName)

		########################################################################################################################################################
		# When testing the script, I'm not wanting to create the 300+ ASICs in the DB, so I guess a good way to get around this is to split it up into modes ###
		########################################################################################################################################################

		full_production_mode = False

		# Code for full production
		#--> There doesnt seem to be an API call at the moment which will allow me to set the fuse IDs of the ASICs at once so I will have to loop through the set children
		#--> What if the number of children created by the DB is more/less than the amount of fuse_ids given?
		if full_production_mode:
			if len(childrenInfo['dummyChildren']) >= len(fuseIDs):
				if len(childrenInfo['dummyChildren']) > len(fuseIDs):
					WARNING('More Children created than fuse IDs given')

				for childNumber, child in enumerate(childrenInfo['dummyChildren']):
					# so index doesnt go out of range
					if childNumber == (len(fuseIDs)-1):
						break
					self.doSomething('setComponentProperty', 'POST', data = {'component': child['code'], 'code': 'ID', 'value': fuseIDs[childNumber]})
					# assign ASIC component code to ASIC
					for number, ASIC in enumerate(self.coreASICData):
						if ASIC['FUSEID_DEC'] == fuseIDs[childNumber]:
							self.coreASICData[number]['componentCode'] = child['code']

			#surely if there are less children than fuse IDs then you cant continue, because what fuse IDs do you miss out?
			elif len(childrenInfo['dummyChildren']) < len(fuseIDs):
				ERROR('Not enough fuse IDs given, this may mean that data can not be uploaded')
				sys.exit(1)

		# If not full production mode, create the max amount of children (value set at 5), only assign fuse ID to ones I have data for .
		# --> On the DB the max amount of children you can create for an ABC* wafer currently stands at 5, so you will have to change this if you have more (to protect against many being uploaded). 
		else:
			DB_Codes_Assigned = 0
			# What if you have more ASICs in your data then can be made in the DB under the current value (5)?			
			if len(self.coreASICData) > len(childrenInfo['dummyChildren']):
				WARNING('There are more ASICs tested in the data %s than children created in the DB, please adjust in the DB' % len(self.coreASICData))
				sys.exit(1)
 
			# we are only assigning the fuse IDs to the ones we have
			for ASICNumber, ASIC in enumerate(self.coreASICData):
				# If the ASIc belongs to this wafer or is -999 meaning a fuse Id couldnt be given
				if ASIC['FUSEID_DEC'] in fuseIDs or ASIC['FUSEID_DEC'] == -999:
					# associate the ASIC from data with component code fetched from DB
					self.coreASICData[ASICNumber]['componentCode'] = childrenInfo['dummyChildren'][DB_Codes_Assigned]['code']
					DB_Codes_Assigned += 1
					# This could be replaced with a feature request in future
					self.doSomething('setComponentProperty', 'POST', data = {'component': self.coreASICData[ASICNumber]['componentCode'], 'code': 'ID', 'value': self.coreASICData[ASICNumber]['FUSEID_DEC']})

	# A function to use the look up table and assign the fuse IDs depending on the waferName.
	def useLookUpTable(self, waferName):
		try:
			fuse_ids = self.lut.getFuseIDs(die_type = DieType.SC_ASIC_ABC, wafer_number = waferName, wafer_series = WaferSeries.SC_WAFER_PROTOTYPE)
			return fuse_ids
		except KeyError:
			ERROR('Likely due to %s not being in the look up table, please check it is in the look up table' % waferName) 

	def getConfirm(self, codePart, info):
		INFO('get confirm enabled')
		if codePart == 0:
			input = getYesOrNo('Wafer %s exists in DB but has no children, create children? (yes/no)' % info)

		elif codePart == 1:
			input = getYesOrNo('Wafer %s does not exist in DB register wafer and create children? (yes/no)' % info)

		elif codePart == 2:
			print (200*'-')
			row_format = '{:<5}{:<12}' + '{:<14}'
			header = ['ASIC', 'Wafer name ', 'Tests to upload']
			print(row_format.format(*header))
			for i, ASIC in enumerate(info):
				row = [str(i), ASIC['waferName'], ', '.join(ASIC['associatedTestFiles'])]
				print(row_format.format(*row))
			input = getYesOrNo('Upload files to ASICs? (yes/no?)')

		if not input:
			ERROR('User exits program')
			sys.exit(1)			

	# upload the associated tests
	def uploadJSON(self, ASICData):
		for ASIC in ASICData:
			for test_number, test in enumerate(ASIC['associatedTestFiles']):
				# open the files 
				with open(os.path.join(self.ASIC_JSON_folder_path, test), 'r') as h:
					# get in python dictionary format
					try:
						uploadData = json.load(h)
						#update with component code
						uploadData['component'] = ASIC['componentCode']

						self.doSomething('uploadTestRunResults', 'POST', data = (uploadData))
						# write the test to uploaded.txt

						g = open(os.path.join(self.ASIC_JSON_folder_path, 'Uploaded.txt'), 'a+')
						g.write('Uploaded on ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ":\n" + test + "\n\n")
						g.close()

					except ImportError:
						ERROR('Unable to upload test results, sometimes due to the JSON, make sure all entries are in double quotes rather than single')

		###########################################################################################################################################################################################
		### Warning needed here: with the recent updates of you needing to associate tests with stages, the tests have been associated with the bonding stage (because that was the only stage) ###
		### will need changing in future
		###########################################################################################################################################################################################

		INFO(Colours.BOLD+Colours.GREEN+ 'Tests successfully uploaded')

if __name__ == '__main__':

	try:
		# arguments for the function, just the required path to the folder and an option for verbosity?
		parser = argparse.ArgumentParser(description = 'Uploads results of ASIC wafer probing to the ITkPD', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
		parser._action_groups.pop()

		# Add required argument 
		required = parser.add_argument_group('required arguments')
		required.add_argument(dest = 'ASIC_JSON_folder_path', type = str, help = 'path to the folder containing the ASIC JSON file(s)')

		# Add optional requirements
		optional = parser.add_argument_group('optional arguments')
		optional.add_argument('-c', '--get-confirm', dest = 'get_confirm', action = 'store_true', help = 'Confirm what is to be uploaded')

		args = parser.parse_args()

		ASICUpload = ParseUpload(args.ASIC_JSON_folder_path, args.get_confirm)
		ASICUpload.authenticate()
		ASICUpload.JSONParse()
		STATUS('Finished successfully.', True)
		sys.exit(0)

	except KeyboardInterrupt:
		print('')
		ERROR('Exectution terminated.')
		STATUS('Finished with error.', False)
		sys.exit(1)
