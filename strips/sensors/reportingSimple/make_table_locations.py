#!/usr/bin/env python
import csv
import datetime
import logging

from __path__ import updatePath
from tabulate import tabulate
#import json
updatePath()


from strips.sensors.SensorSNUtils import setup_logging
from strips.sensors.SensorSNUtils import checkSN_BWNo_type

#----------------------------------------------------------------
# A code to parse a standard CSV file (created by "reportingGlobal" code, and make a table with type/locations per site
# V1, 2021-09-29, VF
#----------------------------------------------------------------

scriptVersion = "1"

html_pref_obj_  = "https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/dcb3f6d1f130482581ba1e7bbe34413c/componentView?code="
legalSites = ['CERN','KEK','CAM','QMUL','UCSC_STRIP_SENSORS','FZU','SFU','TRIUMF','CU','Total']
legalTypes = ["ATLAS18SS", "ATLAS18LS", "ATLAS18R0", "ATLAS18R1", "ATLAS18R2", "ATLAS18R3", "ATLAS18R4", "ATLAS18R5", "ATLASDUMMY18"]

# nicer site names
SITE_MAP = { 'CAM'   : 'Cambridge', 
             'UCSC_STRIP_SENSORS': 'SCIPP',
             'FZU'   : 'Prague', 
             'SFU'   : 'Vancouver', 
             'TRIUMF':'Vancouver', 
             'CU'    : 'Carleton'}

def main(args):
    inputCSV       = args.inputCSV
    outputBasename = args.outputBasename

    log_base_file = "SensorLocations_"
    logFile = setup_logging(log_base_file)
    logMAIN = logging.getLogger('LOG-MAIN')
    logMAIN.info(" starting the log file for DB : " + logFile )
    logMAIN.info('\n *** make_table_locations.py ***')
    logMAIN.info(" scriptVersion = " + str(scriptVersion) + "\n" )
    logMAIN.info(" Got input: ")
    logMAIN.info("  inputCSV       = " + inputCSV       )
    logMAIN.info("  outputBasename = " + outputBasename )

    with open(inputCSV, 'r') as iF:
        lines = [l.strip() for l in iF.readlines()]

    dictData = {}
    nS = 0
    for L in lines:
        iL = L.strip()
        # these are initial comments
        if iL.startswith("#"):
            continue
    
        items = iL.split(",")
        if len(items) != 10:
            #logMAIN.info(" weird input line: <" + iL + ">")
            continue

        code  = items[0]
        SN    = items[1]
        #oType = items[2]
        sType = items[3]
        #stage = items[4]
        loc   = items[5]
        #orig  = items[6]
        #logi  = items[7]
        #rDate = items[8]
        BWNo  = items[9]
        if not checkSN_BWNo_type( SN, BWNo, sType ):
            logMAIN.info(" illegal sensor line: <" + iL + ">")
            sLink = html_pref_obj_ + code
            logMAIN.info(" link = " + sLink)
            continue

        if loc not in legalSites:
            continue

        # this should not really happen at this point
        if sType not in legalTypes:
            logMAIN.info(" illegal type is showing up illegally: " + sType)
            continue


        # assume we are left with correct objects at this point
        # remap to nicer names
        if loc in SITE_MAP:
            loc = SITE_MAP[loc]
        # count and fill in
        nS += 1
        dictData[SN] = {}
        dictData[SN]["site"] = loc
        dictData[SN]["type"] = sType

    # end of parsing the input
    cntFill = len(dictData)
    logMAIN.info(" got " + str(cntFill) + " sensors to consider")

    # make a nicer list of sites
    niceSites = []
    for aSite in legalSites:
        if aSite in SITE_MAP:
            aSite = SITE_MAP[aSite]
        if aSite in niceSites:
            continue
        niceSites.append(aSite)
    logMAIN.info(" will continue with the following site list:")
    logMAIN.info(str(niceSites))

    # now, count them ------------------------------------
    # initialization
    Cnt = {}
    for t in legalTypes:
        Cnt[t] = {}
        for s in niceSites:
            Cnt[t][s] = 0

    # actually, count
    cntTotal = 0
    for SN in dictData:
        s = dictData[SN]["site"]
        t = dictData[SN]["type"]
        Cnt[t][s] += 1
        cntTotal += 1
        '''
        should only have the known "legal" items lists due to the cuts above
        if s not in lSites:
            lSites.append(s)
        if t not in lTypes:
            lTypes.append(t)
        '''
    if cntTotal != cntFill:
        logMAIN.error(" now got " + str(cntTotal) + " sensors counted")
        logMAIN.error(" error! Will exit.")
        return

    #print( json.dumps( Cnt, indent=2) )


    # make the list of lists
    table = []
    l1 = [" "] + niceSites
    table.append(l1)
    cntFinal = 0
    for t in legalTypes:
        # the type name
        li = [t]
        cntLine = 0
        # array per site
        for s in niceSites:
            if s != 'Total':
                li.append( Cnt[t][s] )
                cntFinal += Cnt[t][s]
                cntLine  += Cnt[t][s]
            else:
                li.append( cntLine )
        # the total for a type
        table.append(li)

    if cntFinal != cntFill:
        logMAIN.error(" now got " + str(cntFinal) + " sensors counted")
        logMAIN.error(" error! Will exit.")
        return

    logMAIN.info(tabulate(table, headers="firstrow", tablefmt = "psql"))
    
    startT = datetime.datetime.now()
    cDate = startT.strftime("%Y-%m-%d")
    basename = "table_sensor_loc_" + cDate
    oCSV  = basename + ".csv"
    oHTML = basename + ".html"
    oTXT  = basename + ".txt"

    with open( oCSV, 'w') as fCSV:
        oW = csv.writer( fCSV, delimiter=',')
        for aLine in table:
            oW.writerow(aLine)

    with open( oHTML, 'w') as fHTML:
        fHTML.write( tabulate(table, headers="firstrow", tablefmt = "html") )
    
    with open( oTXT, 'w') as fTXT:
        fTXT.write( tabulate(table, headers="firstrow", tablefmt = "psql") )
    
    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Script for creating list of SNs from directory of HPK files')
    parser.add_argument('-i', '--inputCSV', dest = 'inputCSV', type = str,required=True,help = 'CSV file with sensor list')
    parser.add_argument('-o', '--outputBasename', dest = 'outputBasename', type = str,required=True,help = 'output file basename')

    args = parser.parse_args()
    main(args)
