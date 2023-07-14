#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
import RUNME_DirectImportAndUploadOfOtherTests

#To simply import and upload a list of tests without any analysis, specifically for tests that are not IV/CV/BOW/STAB/STRIP
querypath=["/var/clus/pc_backup/Cleanroom/data/sisensors/","/var/clus/pc_backup/Cleanroom/data/Sensor_QC_data_2019"]
RUNME_DirectImportAndUploadOfOtherTests.MAIN(querypath)

#

"""
import sys

import ImportData
import UploadDataToDatabase
from CommonConfig import extractRUNMEargsfromcmd

def MAIN(querypath):
    
    #Import Data
    CAMDBTESTLIST=ImportData.ImportData(querypath)
    
    for TEST in CAMDBTESTLIST:
        TEST['Decision']='Pass'
    
    UploadDataToDatabase.UploadDataToDatabase(CAMDBTESTLIST)

    return CAMDBTESTLIST


#Run from bash
if __name__=='__main__':
    querypath,outputfile,batch,wafers=extractRUNMEargsfromcmd(sys.argv)
    MAIN(querypath)
