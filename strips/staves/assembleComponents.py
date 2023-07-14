#!/usr/bin/env python
# -*- coding: utf-8 -*-
#assembleComponents.py
#interface for assemble one or more 'parent' components with appropriate 'child' components
    #in the ITk Production Database from the command line
#Created: 2019/03/22, Last Update: 2019/03/28
#Written by Jiayi Chen
#reference: '../registerComponent.py', written by Matt Basso
from __future__ import print_function #import python3 printer if python2 is used

import sys
sys.path.append('../')
from utilities.databaseUtilities import Colours, INFO, input, PROMPT, WARNING, ERROR, STATUS
from requests.exceptions import RequestException
from utilities.dbAccess import ITkPDSession
from pprint import PrettyPrinter
from LoadedStave import FindComp
pp = PrettyPrinter(indent = 1, width = 200)

class Cancel(Exception):
    pass

class GoBack(Exception):
    pass

class AssembleComponents(object):

    def __init__(self,ITkPDSession):
        self.PDSession = ITkPDSession
        self.json={}
        #self.always_print = False

    ##from registerComponent.py -- modified:doesn't have to have options
    def __askForSomething(self,prompt=None,options=None):
        PROMPT(prompt)

        #if options are given...
        if options != None:
            for ind,item in enumerate(options):
                print(ind, '.  ', item)
            PROMPT('Please enter a index:')

            while True:
                #get user input
                response=input().strip()

                # If nothing, do nothing
                if response == '':
                    continue

                # Escape code &JSON -- print JSON to show what has already been selected
                elif response == '&JSON':
                    INFO('Printing JSON:\n')
                    pp.pprint(self.json)
                    print('')
                    PROMPT('Please enter a code:')

                elif response == '&CANCEL':
                    WARNING('Cancled ')
                    raise Cancel

                #CHNAGE (add) Jiayi
                elif response == '&BACK':
                    WARNING('Going Back')
                    raise GoBack

                #assume valid input
                else:
                    try:
                        selected_ind=int(response)
                        print('You have selected ', options[selected_ind])
                        return selected_ind
                    except IndexError:
                        WARNING('Invalid index!')
                        continue
        #if no options are given
        else:

            while True:
                #get user input
                response=input().strip()

                # If nothing, do nothing
                if response == '':
                    continue

                # Escape code &JSON -- print JSON to show what has already been selected
                elif response == '&JSON':
                    INFO('Printing JSON:\n')
                    pp.pprint(self.json)
                    print('')
                    PROMPT('Please enter a code:')

                elif response == '&CANCEL':
                    WARNING('Cancled ')
                    raise Cancel

                #CHNAGE (add) Jiayi
                elif response == '&BACK':
                    WARNING('Going Back')
                    raise GoBack

                #assume valid input
                else:
                    return response

    #from registerComponent.py
    def __getYesOrNo(self, prompt):
        PROMPT(prompt)
        while True:

            # Get our input
            response = input().strip().lower()

            # Skip empty inputs
            if response == '':
                continue

            # If yes, return True
            elif response in ['y', 'yes', '1']:
                return True

            # If no, return False
            elif response in ['n', 'no', '0']:
                return False

            # Else the input is invalid and ask again
            else:
                del response
                PROMPT('Invalid input. Please enter \'y/Y\', or \'n/N\':')
                continue

    #ask for identifier and find the parent/child component using the identifier
    def getParentChild(self,comp_type,isParent=False):
        while True:
            try:
                #ask for which identifier type to use and insert the indentifier
                Identifiers=['Local Name', 'serial number']
                INFO('You need to provide one of the following identifiers to find this %s' %comp_type)

                #get identifier type
                ID_type=self.__askForSomething(prompt='which one do you want to use:',options=['Local Name', 'serial number'])
                INFO('If you want to change your selection, enter &BACK')

                #get identifier
                identifier=self.__askForSomething(prompt='Please provide the '+ comp_type + '\'s '+ Identifiers[ID_type])

                #given identifier is local name/RFID
                if ID_type == 0:
                    component = Parent_Child(comp_type,LOCALNAME=identifier,ID=None,PDSession=self.PDSession,isParent=isParent)

                #given identifier is serial number
                else:
                    component = Parent_Child(comp_type,LOCALNAME=None,ID=identifier,PDSession=self.PDSession,isParent=isParent)
                return component
            except ValueError:
                WARNING('invid input, try again')
                continue
            except GoBack:
                WARNING('you have asked to reenter the identifier')
                continue

    # Convert reponse to specific type
    #from registerComponent.py
    def __convertToType(self, response, type):

        # If the wrong input is provided, the code will throw a ValueError
        if type == 'string':
            return str(response)
        elif type == 'float':
            return float(response)
        elif type == 'integer':
            return int(response)

        # For boolean, we'll require specific inputs or else throw a ValueError
        elif type == 'boolean':
            if response.lower() in ['1', 'true', 't']:
                return True

            elif response.lower() in ['0', 'false', 'f']:
                return False
            else:
                raise ValueError

        # For a code table, we'll require keys or values to be enter or else throw a ValueError
        elif type[0] == 'codeTable':
            code_table = {item['code']: item['value'] for item in type[1]}
            if response in code_table.keys():
                return response
            else:
                raise ValueError
        return None

    # Give the user a prompt to enter a value for a property indexed by i
    #from registerComponent.py
    def __getProperty(self, prompt, property, i):

        # Print the relevant info for that property
        self.__printProperty(property)
        PROMPT(prompt)

        while True:

            # Get our input
            response = input().strip()

            # If nothng, do nothing
            if response == '':
                continue

            # Escape code &JSON -- print JSON to show what has already been selected
            elif response.upper() == '&JSON':
                INFO('Printing JSON:\n')
                pp.pprint(self.json)
                print('')
                PROMPT('Please enter a value for the property:')

            # Escape code &SKIP -- skip the current property if it's not required
            elif response.upper() == '&SKIP':

                # Check if it's required
                if property['required']:
                    WARNING('Property is required and cannot be skipped.')
                    INFO('Please enter a value:')
                    continue
                else:
                    INFO('Skipping property: {0} ({1}).'.format(property['code'], property['name']))

                    # Increment i to move onto the next property, and return None for the current property's value
                    return i + 1, None

            # Escape code &BACK -- go back to edit the previous property by raising Back exception
            elif response.upper() == '&BACK':
                INFO('Going back.')
                raise GoBack

            # Escape code &CANCEL -- raise our Cancel exception
            elif response.upper() == '&CANCEL':
                WARNING('Component Assembly cancelled.')
                raise Cancel

            # Else, we assume the user enter a property value
            else:
                try:

                    # Try to convert the input string to its correct data type
                    if property['dataType'] == 'codeTable':
                        property['dataType'] = ['codeTable', property['codeTable']]
                    response_converted = self.__convertToType(response, property['dataType'])
                    INFO('Using property: {0} ({1}) = {2}'.format(property['code'], property['name'], response))

                    # Return i + 1 to move onto the next property and return our converted property value
                    return i + 1, response_converted

                # Catch our ValueErrors for invalid input
                except ValueError:
                    PROMPT('Invalid input, please try again:')
                    continue

    #from registerComponent.py
    def __printProperty(self, property):
        keys = property.keys()
        print('')
        if 'code' in keys:
            print('    {0}{1}Code{2}:        '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['code'])
        if 'name' in keys:
            print('    {0}{1}Name{2}:        '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['name'])
        if 'dataType' in keys:
            print('    {0}{1}Data Type{2}:   '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['dataType'])
        if 'required' in keys:
            print('    {0}{1}Required{2}:    '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['required'])
        if 'default' in keys:
            print('    {0}{1}Default{2}:     '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['default'])
        if 'unique' in keys:
            print('    {0}{1}Unique{2}:      '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['unique'])
        if 'snPosition' in keys:
            print('    {0}{1}SN Positon{2}:  '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['snPosition'])
        if 'description' in keys:
            print('    {0}{1}Description{2}: '.format(Colours.WHITE, Colours.BOLD, Colours.ENDC) + '%s' % property['description'])
        if property['dataType'] == 'codeTable':
            print('    {0}{1}Code Table{2}:'.format(Colours.WHITE, Colours.BOLD, Colours.ENDC))
            row_format = '        {:<15}{:<15}'
            header = ['Code', 'Value']
            print(Colours.WHITE + Colours.BOLD + row_format.format(*header) + Colours.ENDC)
            code_table = {item['code']: item['value'] for item in property['codeTable']}
            for code in code_table.keys():
                row = [code, code_table[code]]
                print(row_format.format(*row))
        print('')

    def openInterface(self):

        #iterate over multiple parent components one wants to assemble
        while True:

            #ask for the parent component type
            parent_type=self.__askForSomething(prompt='Enter the code to the component type of the \'Parent\'(ex. STAVE, MODULE):')

            #find parent component
            parent=self.getParentChild(parent_type,isParent=True)

            #fill in parent code
            self.json['parent']=parent.code

            #iterate through all child components () one want to assemble to the parent
            while True:
                #find what type of child one wants to assemble
                INFO('A '+ parent_type + ' has the following children types:')
                child_ind=self.__askForSomething(prompt='Please give the child component type:',options=parent.children_types)
                child_type=parent.children_types[child_ind]

                #find child component
                child=self.getParentChild(child_type)
                self.json['child']=child.code

                #insert child-parent property
                self.json['properties']={}
                INFO('Successfully find both parent and child')
                INFO('Now you need to fill in the child-parent properties...')
                INFO('Use escape codes &JSON to print the current JSON, &SKIP to skip a property which is not required, &BACK to make a correction, or &CANCEL to cancel component assembly.')

                # If not properties to add, skip
                child_properties=parent.children_properties[child_ind]
                if  child_properties==None or child_properties==[]:
                    WARNING('No properties for this parent-child --skipping')

                # Else iterate over our properties
                else:
                    i=0
                    try:

                        #iterate through all child-parent properties
                        while True:

                            # If i reaches the end of the length of properties, we know we have added all and can break
                            if i==len(child_properties):
                                INFO('All properties added.')
                                break

                            # If we try to go &BACK below 0, set i to 0
                            elif i < 0:
                                WARNING('Can\'t go back any further.')
                                i = 0
                                continue

                            else:
                                try:
                                    property=child_properties[i]
                                    print(property)
                                    i, value = self.__getProperty('Please entry an appropriate value for the above property:', property, i)
                                    self.json['properties'][property['code']] = value
                                except GoBack:
                                    i -= 1
                                    continue

                    # Catch our Cancels in the case of &CANCEL
                    except Cancel:
                        break

                # Show the user what is to be registered
                INFO('Your component will be registered using JSON:\n')
                pp.pprint(self.json)
                print('')

                #does the user want to assemble by slot?
                if self.__getYesOrNo('Do you want to assemble the component to a specific slot? (y/n)'):
                    slots=parent.children_slots[child_type]
                    empty_slots=[]
                    for ind,slot in enumerate(slots):
                        if not slot['assembled']:
                            empty_slots.append(str(ind))

                    if empty_slots==[]:
                        WARNING('All the slots are taken for this child type: %s' %child_type)
                        break

                    else:
                        response=self.__askForSomething(prompt='Please select one of the following slot indices',options=empty_slots)
                        slot_index=int(empty_slots[int(response)])
                        self.json['slot']=slots[slot_index]['id']

                    #confirm assembly
                    if self.__getYesOrNo('Please confirm you want to assemble the ' + parent_type + ' and the ' + child_type + ' (y/n)'):
                        self.PDSession.doSomething(action = 'assembleComponentBySlot',method = 'POST',data = self.json)
                        INFO('Finished assembly!')

                    #cancel assembly of this child
                    else:
                        INFO('You have canceled the assembly of this %s with the %s' %(child_type, parent_type))

                #assemble without choosing a particular slot
                else:
                    #confirm assembly
                    if self.__getYesOrNo('Please confirm you want to assemble the ' + parent_type + ' and the ' + child_type + ' (y/n)'):
                        self.PDSession.doSomething(action = 'assembleComponent',method = 'POST',data = self.json)
                        INFO('Finished assembly!')

                    #cancel assembly of this child
                    else:
                        INFO('You have canceled the assembly of this %s with the %s' %(child_type, parent_type))

                #continue assembly with the same parent
                if self.__getYesOrNo('Do you want to assemble another child component with this ' + parent_type + ' (y/n)'):

                    #re-initialize json
                    self.json={}
                    self.json['parent']=parent.code #same parent
                    continue

                #done with this parent
                else:
                    INFO('You have finished assembly with the parent component, %s' %parent_type)
                    break

            #continue with another parent
            if self.__getYesOrNo('Do you want to assemle more parent and child components (y/n)?'):

                #re-initialize json
                self.json={}
                continue

            #exit program
            else:
                INFO('Exiting Program...')
                INFO('Have a wonderful rest of your day~')
                break



#find either a Parent or Child component
class Parent_Child(object):
    #use either local name or a unique ID to find the component
    def __init__(self,component_type,LOCALNAME=None,ID=None,PDSession=None,isParent=True):
        self.PDSession = PDSession
        self.type = component_type
        self.localname = LOCALNAME
        self.id = ID
        self.code = self.GetComponentCode() #return component code
        if isParent:
            #lists
            self.children_types=[] #list of child types ex. for a STAVE it will be ['MODULE','EOS']
            #self.num_assembled_children=[] #array of the amount of children that are already assembled for each child type
            self.children_properties=[]
            #dictionary
            self.children_slots={} #put slot info (assembled? + slot id) in each child type category
            #fill in the above lists and dictionary
            self.GetChildren()

    def GetComponentCode(self):
        component= FindComp(LOCALNAME=self.localname, RFID=self.id,comp_type=self.type,PDsession=self.PDSession)
        return component['code']

    def GetChildren(self):
        parent=self.PDSession.doSomething(action='getComponent',method='GET',data={'component':self.code})
        #print(parent)
        #child_type=None
        #count_assembled_comp=0
        #count_comp=0 #count for each child type

        #iterate through all child components of
        for child in parent['children']:
            child_type=child['componentType']['code']
            #initialize for a new child type
            if child_type not in self.children_types:
                self.children_types.append(child_type)
                self.children_slots[child_type]=[] #a list of slots info
                self.children_properties.append(child['properties'])

                #count_assembled_comp=0

            #initialize for a new child component slot
            new_child_slot={}
            new_child_slot['assembled']=False

            #attach slot id to each child type
            new_child_slot['id']=child['id']
            self.children_slots[child_type].append(new_child_slot)

            #if the slot is not empty, change 'assembled' to True
            if child['component']!=None:
                #count_assembled_comp+=1
                self.children_slots[child_type][-1]['assembled']=True

            #if the child is the last child, append the last type of child's count_assembled_comp
            #if child==parent['children'][-1]:
                #self.num_assembled_children.append(count_assembled_comp)
            #count_comp+=1


    #print the child parent properties of an assembled slot
    # a good cross check if the slot is taken by mistake / the child component is already assembled
    #def printAssembledSlot(self):
        #print('')

if __name__ == '__main__':

    try:
        print('')
        print('*************************************************************************')
        print('* *                                                                 *   *')
        print('*           assemblyComponents.py -- Jiayi Chen & Matt Basso            *')
        print('* *                                                                 *   *')
        print('*************************************************************************')
        print('')

        # Instantiate our ITkPDSession
        session = ITkPDSession()
        session.authenticate()

        # Open registration interface and run it
        interface = AssembleComponents(session)
        interface.openInterface()

        #######commands for testing##########
        #parent=Parent_Child('MODULE',LOCALNAME='testModuleJiayi',ID=None,PDSession=session,isParent=True)
        #parent=Parent_Child('STAVE',LOCALNAME='PracticeJiayi',ID=None,PDSession=session,isParent=True)
        #parent.GetChildren()
        #print(parent.children_types)
        #print(parent.children_slots)
        #print('')
        #print(parent.children_properties)

        ####################################

    # In the case of a keyboard interrupt, quit with error
    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        STATUS('Finished with error.', False)
        sys.exit(1)

    except RequestException as e:
        ERROR('Request exception raised: %s' % e)
        STATUS('Finished with error.', False)
        sys.exit(1)
