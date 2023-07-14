#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
#To use:
import GetComponentInfoFromDatabase
COMPONENTIDDICTLIST=GetComponentInfoFromDatabase.GetComponentInfoFromDatabase()


#To do queries for example get Serial Number given Batch and Wafer:
[i['Component'] for i in COMPONENTIDDICTLIST if (i['Batch']=='VPX30816' and i['Wafer']==163)]
"""
"""###Author: David Rousso"""
#import __path__
#import dbAccess
import itkdb
from CommonConfig import HMComponent2BatchWafer
from CommonConfig import ITK_COMPONENTTYPE
from CommonConfig import ITK_PROJECT

def GetComponentInfoFromDatabase():
    print('')
    print('')
    print('')
    print('')
    print('')
    print("Running GetComponentInfoFromDatabase.py: Importing Component Info from ITK Database:")
    
    
    
    """
    #Get Component List
    APIComponentList = dbAccess.extractList("listComponents", method = "GET",
                                  data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE},
                                  )
    
    
    ###############################################################################################
    #A bug on the ITK side seems to cap the length of the above at 1000 resulting in lost wafers. 
    #A temporary hard-coded sort of work-around is below
    APIComponentTypeList = dbAccess.extractList("listComponentTypes", method = "GET",
                                  data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE},
                                  )
    TypeList=[j['code'] for j in [i for i in APIComponentTypeList if i['code']==ITK_COMPONENTTYPE][0]['types']]
    APIComponentList=[]
    for ATLAStype in TypeList:
        APIComponentList.extend( dbAccess.extractList("listComponents", method = "GET",
                                  data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE,'type':ATLAStype},
                                  )
                               )
    ###############################################################################################
    """
    '''
    CheckLengths=dbAccess.doSomething("listComponents", method = "GET",
                                      data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE,
                                            "includeProperties": True,
                                            "pageInfo": {
                                            "pageIndex": 0,
                                            "pageSize": 10000
                                                }
                                             }
                                      )

    APIComponentList=dbAccess.extractList("listComponents", method = "GET",
                                      data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE,
                                            "includeProperties": True,
                                            "pageInfo": {
                                            "pageIndex": 0,
                                            "pageSize": CheckLengths['pageInfo']['total']
                                                }
                                             }
                                      )
    '''
    client = itkdb.Client()
    '''
    CheckLengths = client.get("listComponents",json = {"filterMap": {"project": ITK_PROJECT, 'componentType': [ITK_COMPONENTTYPE]},
                                            
                                            "pageInfo": {
                                            "pageIndex": 0,
                                            "pageSize": 2000
                                                },
                                           # "includeProperties":"true",
                                             }                                                 
                                        
                            
                                        )
    '''
    APIComponentList = client.get("listComponents",json={"filterMap": {"project": ITK_PROJECT, 'componentType': [ITK_COMPONENTTYPE]},
                                         #   "includeProperties":"true",
                                            "outputType": "full", 
                                            "pageInfo": {
                                            "pageIndex": 0,
                                            "pageSize": 1000000
                                                }
                                        } 
                                    )

    APIComponentList=[i for i in APIComponentList if i['state']=='ready']
    #print("APIComponentList,",APIComponentList) #plni se dobre
    
    #Compiling Dictionary for Component IDs!!

    COMPONENTIDDICTLIST=[]

    for Component in APIComponentList:
        ComponentID=Component['id']
        ComponentCode=Component['code']
        SerialNumber=Component['serialNumber']

        #TestType=Component['TestType']

        try:
            Type=Component['type']['code']
        except:
            Type=None
        #Name=Component['alternativeIdentifier']

        #Extracting Batch and Wafer from Name
        Batch=None
        Wafer=None
       # print("serial number,", SerialNumber)
        if Batch==None and Wafer == None:
            (Batch,Wafer)=HMComponent2BatchWafer(SerialNumber)
            
        #(Batch,Wafer)=string2BatchWafer(Name)
        try: 
            Wafer=int(Wafer)
        except:
            Wafer=Wafer
            #['Filename','Batch','Wafer','Shorthand','Manufacturer','Type','Component', 'Institute','Date','Time','TestType','Settings','Instrument','Temperature','OtherInfo','Segment','Humidity','RunNumber','numColumns','numRows', 'strFormat']
        COMPONENTIDDICT={'ComponentID':ComponentID,'ComponentCode':ComponentCode,'Batch':Batch, 'Wafer':Wafer,'Component':SerialNumber, 'Type':Type}
        #print('Output from the DB '+str(COMPONENTIDDICT['Batch'])+': '+str(COMPONENTIDDICT['Wafer'])+':'+str(COMPONENTIDDICT['ComponentID'])+': '+str(COMPONENTIDDICT['Type'])+":"+ str(COMPONENTIDDICT['Component'])+":"+ str(COMPONENTIDDICT['ComponentCode']))

        COMPONENTIDDICTLIST.append(COMPONENTIDDICT)
       
    print("GetComponentInfoFromDatabase.py Completed!")
    #print ("COMPONENTDICTLIST",COMPONENTIDDICTLIST)
    return COMPONENTIDDICTLIST
