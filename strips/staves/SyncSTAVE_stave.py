#3/5/2019 by Jiayi Chen
#Check if PD STAVE and real-world stave are synchronized
#In the future might use this to call LoadedStave directly to assembled any un-assembled components of a stave
#printPDOBject should be able to print info for any PD Object ('MODULE', 'EOS'...) -->need to check
from __future__ import print_function  # whole script consistently used python3 print()

import sys
# import collections, argparse, os,json,

# import ReadSurvey as RS
sys.path.append("../")
from LoadedStave import FindComp

# from datetime import date
from utilities.dbAccess import ITkPDSession
#import pandas as pd

#myobject = ITkPDSession.doSomething(action='getComponent',method='GET',data={'component':comp_code})
def printPDObject(myobject):
    obj=myobject
    print("Printing information for a",obj['componentType']['name'])
    print("type:",obj['type']['name'])
    print("code:",obj['code'])
    print("serialNumber:",obj['serialNumber'])
    print("current stage:",obj['currentStage']['name'])
    print("properties:")
    for property in obj['properties']:
        print('   ',property['name'],": ", property['value'])
    print("assembled children:")

    module_slot=1 #initiate module slot num, this goes from 1-28
    empty_slots={} #initiate a dict for all empty child slots

    for child in obj['children']:
        #print for modules
        if child['componentType']['code']=='MODULE':
            #first 14 modules is on LHS stave side; other 14 on RHS
            if module_slot<15:
                position='LHS'+str(module_slot)
            else:
                position='RHS'+str(module_slot-14)

            #print out assembled child components info
            if child['component']!=None:
                print("   Slot",module_slot, '(',position,')', child['type']['name'], " ", child['componentType']['name'])
                for property in child['properties']:
                    if property['code']=='SITE':
                        print("     ",property['name'],' :  ', property['value'])
                    elif property['code']=='SIDE':
                        side=property['value']
                    elif property['code']=='POSITION':
                        posi=property['value']
                #check if the module is assembled at the right slot
                #ex.module at stave side LHS position7, slot=7
                #   module at stave side RHS position7, slot=14+7=21
                print("      MODULE position saved correctly:", position==side+str(posi), "(",side+str(posi),")")
            else:
                if 'Module' not in empty_slots.keys():
                    empty_slots['Module']=[]
                empty_slots['Module'].append(position)
            module_slot+=1 #increment slot num


        #print all other children other than module
        else:
            if child['component']!=None:
                print("   ", child['componentType']['name'])
                #for property in child['properties']:
                    #print(property['name'],': ', property['value'])
            else:
                if child['componentType']['name'] not in empty_slots.keys():
                    empty_slots[child['componentType']['name']]=[]
                empty_slots[child['componentType']['name']].append(child['type']['name'])
    print("the following child components are not assembled:")
    for key in empty_slots.keys():
        print(key,":",empty_slots[key])


def ReportSTAVE(mystave):
    stave=mystave.StaveINFO()
    printPDObject(stave)
    #print(stave)

#start a ITk session
session= ITkPDSession()
session.authenticate()
#find component code (input local name, comp_type)
comp_code=FindComp(LOCALNAME='component local name',comp_type='MODULE',PDsession=session)['code']
component = session.doSomething(action='getComponent',method='GET',data={'component':comp_code})
printPDObject(component)


#stave=STAVE(LOCALNAME='US-Electrical-Prototype', dir='./', assemblySite='BU', STAGE='reception',PDsession=session)
#m=MODULE('module name', ID='testModuleJiayi', position=1, STAGE='reception',PDsession=session)
#m.findMODULE()
#module = session.doSomething(action='getComponent',method='GET',data={'component':m.code})
#printPDObject(module)
