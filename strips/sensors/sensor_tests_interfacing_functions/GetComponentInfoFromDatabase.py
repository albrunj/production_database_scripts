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
import dbAccess
from CommonConfig import ITK_COMPONENTTYPE
from CommonConfig import ITK_PROJECT
from CommonConfig import string2BatchWafer

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
    
    CheckLengths=dbAccess.doSomething("listComponents", method = "GET",
                                      data = {"project": ITK_PROJECT, 'componentType':ITK_COMPONENTTYPE,
                                            "includeProperties": True,
                                            "pageInfo": {
                                            "pageIndex": 0,
                                            "pageSize": 20
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
    APIComponentList=[i for i in APIComponentList if i['state']=='ready']

    
    #Compiling Dictionary for Component IDs!!

    COMPONENTIDDICTLIST=[]

    for Component in APIComponentList:
        ComponentID=Component['id']
        ComponentCode=Component['code']
        SerialNumber=Component['serialNumber']
        try:
            Type=Component['type']['code']
        except:
            Type=None
        Name=Component['alternativeIdentifier']

        #Extracting Batch and Wafer from Name
        Batch=None
        Wafer=None
        
        (Batch,Wafer)=string2BatchWafer(Name)
        try: 
            Wafer=int(Wafer)
        except:
            Wafer=Wafer
            #['Filename','Batch','Wafer','Shorthand','Manufacturer','Type','Component', 'Institute','Date','Time','TestType','Settings','Instrument','Temperature','OtherInfo','Segment','Humidity','RunNumber','numColumns','numRows', 'strFormat']
        COMPONENTIDDICT={'ComponentID':ComponentID,'ComponentCode':ComponentCode,'Batch':Batch, 'Wafer':Wafer,'Component':SerialNumber, 'Type':Type}
        COMPONENTIDDICTLIST.append(COMPONENTIDDICT)
       
    print("GetComponentInfoFromDatabase.py Completed!")

    return COMPONENTIDDICTLIST
