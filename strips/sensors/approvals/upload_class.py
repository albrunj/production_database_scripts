#!/usr/bin/python
import argparse
import json
import logging
import os
from datetime import datetime

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import check_batch_name
from strips.sensors.SensorSNUtils import setup_logging
from strips.sensors.SensorSNUtils import upload_testrun
from strips.sensors.SensorSNUtils import set_stage
from strips.sensors.SensorSNUtils import set_batch_prop
from strips.sensors.approvals.batch_sensor_tests import Batch
from strips.sensors.approvals.summary_data import DESIGN
from strips.sensors.approvals.clasify_batches import check_control_Json


### 
# 2021-10-18, VF: a code for updating the sensor FS and batch info based on the data from scanning
#
#----------------------------
#

scriptVersion = DESIGN


def query_if_ok(iLog):
    resp_ok = False
    while not resp_ok:
        txt = input('Is this batch info ok? (yes/no) >> ')
        iLog.info(' Received the batch confirmation response = <' + txt + '>')
        check_txt = txt.lower()
        if check_txt in ['yes','no']:
            resp_ok = True
            if check_txt == 'yes':
                return True
            else:
                return False
        else:
            iLog.info(" The response is not in the allowed values of <yes> and <no>, continuing.")

    # should not get here...
    return None


def findQA(iControl, aBatch, qaTC, qaCCE, iLog):
    CqaTC  = None
    CqaCCE = None
    if 'batches' in iControl:
        ctrlB = iControl['batches']
        if aBatch in ctrlB:
            if "QATC"  in ctrlB[aBatch]:
                CqaTC  = ctrlB[aBatch]["QATC" ]
            if "QACCE" in ctrlB[aBatch]:
                CqaCCE = ctrlB[aBatch]["QACCE"]

    use_qaTC  = None
    use_qaCCE = None
    if qaTC is None:
        use_qaTC = CqaTC
    else:
        # the run-time flag over-writes everything else
        use_qaTC = qaTC
        if qaTC != CqaTC:
            iLog.info(" over-writing QA-TC: the control-file value is <" + str(CqaTC) + ">, run-time flag = <" + str(qaTC) + ">")
            
    if qaCCE is None:
        use_qaCCE = CqaCCE
    else:
        # the run-time flag over-writes everything else
        use_qaCCE = qaCCE
        if qaCCE != CqaCCE:
            iLog.info(" over-writing QA-CCE: the control-file value is <" + str(CqaCCE) + ">, run-time flag = <" + str(qaCCE) + ">")

    return use_qaTC, use_qaCCE


def find_json_files(iLoc):
    all_files = list( filter( lambda x: x[-5:] == '.json', os.listdir(iLoc) ) )
    summary_files = []
    for aFile in all_files:
        if aFile.startswith("summary_"):
            summary_files.append(aFile)
    return summary_files


def batch_in_summary(sumFile): #,logFile):
    # assume we start with "summary_" => the batch name is [8:16]
    bName = sumFile[8:16]
    #logFile.info(" obtained the batch name " + bName)
    name_ok = check_batch_name(bName)
    return name_ok, bName


def suffix_in_summary(sumFile):
    suff = sumFile[-8:-5]
    #print(" suff = " + suff)
    statWord = ""
    if suff == "app":
        statWord = " It is intended to be approved => Can be processed!"
    elif suff == "run":
        statWord = " It is only a summary          => Should do nothing."
    elif suff == "fin":
        statWord = " It is alread finished         => Should do nothing."
    else:
        statWord = " Illegal suffix                => Should do nothing."
    return suff, statWord


def main(args):

    # TODO: an interactive check if proceed before the upload
    iBatches  = args.iBatches
    iLocation = args.iLocation
    iControl  = args.iControl
    iqaTC     = args.qaTC
    iqaCCE    = args.qaCCE
    bDBG      = args.debug

    log_base_file = "DB_batchClassUpload_"
    logFile = setup_logging(log_base_file)

    logMAIN = logging.getLogger('LOG-MAIN')
    logMAIN.info(" starting the log file for DB : " + logFile )
    logMAIN.info('\n *** upload_class.py ***')
    logMAIN.info(" scriptVersion = " + scriptVersion + "\n" )

    if len(iqaTC) == 0:
        qaTC = None
    elif iqaTC == "yes" or iqaTC == "Yes":
        qaTC = True
    elif iqaTC == "no"  or iqaTC == "No" :
        qaTC = False
    else:
        logMAIN.error(" wrong option for qaTC = <" + iqaTC + ">, exiting")
        return
    if len(iqaCCE) == 0:
        qaTC = None
    elif iqaCCE == "yes" or iqaCCE == "Yes":
        qaCCE = True
    elif iqaCCE == "no"  or iqaCCE == "No" :
        qaCCE = False
    else:
        logMAIN.error(" wrong option for qaCCE = <" + iqaCCE + ">, exiting")
        return
    
    logMAIN.info(" ------------------------------------- ")
    logMAIN.info(" Got input: "                           )
    logMAIN.info("   iBatches  = " + iBatches             )
    logMAIN.info("   iLocation = " + iLocation            )
    logMAIN.info("   iControl  = " + iControl             )
    logMAIN.info("   qaTC      = " + qaTC                 )
    logMAIN.info("   qaCCE     = " + qaCCE                )
    logMAIN.info("   bDBG      = " + str(bDBG)            )

    # find the control file with the directives, if available
    controlJson = {}
    try:
        with open(iControl, 'r') as iF:
            controlJson = json.load(iF)
    except Exception as e:
        controlJson = {}
        logMAIN.error(e)

    if len(controlJson) == 0:
        logMAIN.info("\n Do not have the over-writing control file to use.\n")
    else:
        logMAIN.info("\n Using control JSON file with " +
                     str(len(controlJson['batches'])) + " batches  and " +
                     str(len(controlJson['sensors'])) + " sensors. \n")
        if not check_control_Json(controlJson, logMAIN):
            return

    # batch list from the input
    lBinput = []
    if len(iBatches) > 0 :
        lBinput = iBatches.split(',')
        logMAIN.info("\n The allowed batches are: " + str(lBinput) + '\n')
    
    # batch list from the summary files
    listInputJsons = find_json_files(iLocation)
    logMAIN.info(" found the following input JSON files with the batch info:")
    logMAIN.info(listInputJsons)
    if len(listInputJsons) == 0:
        logMAIN.error(" no batch summary files => exiting!")
        return
    
    # check the action plan!
    actBatchFiles = []
    listBs = []
    for aF in listInputJsons:
        logMAIN.info("\n Looking at file " + aF + ":")

        use_name, aB = batch_in_summary(aF)  # ,logMAIN)
        if use_name:
            logMAIN.info(" found batch = " + aB  )
        else:
            logMAIN.error(" improper batch = " + aB )
            logMAIN.error(" exiting ")
            return
        
        # if the designated list of batches is provided, check if it's there
        if len(lBinput) > 0:
            if aB in lBinput:
                logMAIN.info(" in the designated list => can consider (if suffix = <app>)")
            else:
                logMAIN.info(" not in the designated list => will skip")
                continue

        suffix, explanation = suffix_in_summary( aF )
        logMAIN.info( explanation )
        
        if suffix == "app":
            actBatchFiles.append( aF )
            listBs.append( aB )

    logMAIN.info( "\n Found batches to upload/summarize: " + str(listBs) )

    lBuse = []
    lBbad = []
    # now, fill in the info
    for aF in actBatchFiles:
        with open( aF, "r" ) as inF:
            new_json = json.load(inF)
        nB = Batch.fromJD( new_json )

        # this will check the sensors present in the control file, then update their info
        nB.updateSensorControl(iControl)
        
        # The QA part: the run-time flags, if given, overwrite the control conditions
        use_qaTC, use_qaCCE = findQA(iControl, nB.bName(), qaTC, qaCCE, logMAIN)
        nB.updateQA(use_qaTC,use_qaCCE)

        # The failed/returned flags
        nB.updateBadness(iControl)

        # And want to make the interactive table here:
        # batch: SN, destination, QA-TC, QA-CCE, comment
        logMAIN.info(nB.short_status_table())
        goodB = query_if_ok(logMAIN)
        if goodB:
            lBuse.append(nB)
        else:
            lBbad.append(nB)
            
    # if have bad-looking info
    if len(lBbad) != 0:
        logMAIN.error("\n Did not agree to the following batch info:")
        for aB in lBbad:
            logMAIN.error("     " + aB.bName())
        logMAIN.error(" will exit without upload!")
        return

    # the time to use with the tests uploads
    myTimeStamp = datetime.now().isoformat()
    # establish a DB client
    c = itkdb.Client() # expires_after=dict(days=1) )

    for aB in lBuse:
        # will want to upload the SN data. This puts the info in the structure as well!
        lMains = aB.lMAINs()
        bName = aB.bName()
        logMAIN.info("\n DB manipulations for batch = " + bName )
        for aS in lMains:
            # this call also rewrites the sensor' "approval" structure
            appJSON = aS.approval_json(myTimeStamp)
            
            # to change for dummy trial!
            succ = upload_testrun(c,appJSON)
            if succ:
                logMAIN.info(" Uploaded approval for Batch = " +
                             bName + ", sensor = " + aS.SN() + ", will exit.")
            else:
                logMAIN.error(" Have a problem uploading the approval test result for Batch = " +
                              bName + ", sensor = " + aS.SN() + ", will exit.")
                return
            
            # presumably the success with the upload => to move to the proper final stage
            finalState = appJSON["FINALSTAGE"]
            logMAIN.info(" will move it to the stage = <" + finalState + ">")
            succ = set_stage(c, aS.code(), finalState)
            if succ:
                logMAIN.info(" Success with the state change.")
            else:
                logMAIN.error(" Error changing the state... Exiting.")
                return

            # this finally changes the counts of the final states and the sensor's state
            # only want to call this after the successful upload above...
            aB.update_counts( aS.SN() )
            
        # Now, change the batch counts
        bID = aB.ID()
        dictBProps = { "N_TOTAL_MAIN"      : aB.nTotal(),
                       "N_READY_MAIN"      : aB.nReady(),
                       "N_UNHAPPY_MAIN"    : aB.nUnhappy(),
                       "N_DAMAGED_MAIN"    : aB.nDamaged(),
                       "N_PHANTOM_MAIN"    : aB.nPhantom(),
                       "N_SPECIAL_USE_MAIN": aB.nSpecial(),
                       "N_RETURNED_MAIN"   : aB.nReturned(),
                       "QA_TC"             : aB.qaTC(),
                       "QA_CCE"            : aB.qaCCE(),
                       "FAILED"            : aB.ifFailed(),
                       "RETURNED"          : aB.ifReturned() }
        for K in dictBProps:
            val = dictBProps[K]
            succ = set_batch_prop( c, bID, K, val, logMAIN )
            msg = " Batch = " + bName + " : " + K + " --> " + str(val)
            if succ:
                logMAIN.info(" Updated " + msg )
            else:
                logMAIN.error(" Failed to update " + msg + " will exit." )
                return

        logMAIN.info(" Done with batch = " + bName + "\n" )
            
        # saving the updated files now
        suffix = "jenelesaispas"
        if aB.isFinal():
            suffix = "fin"
        elif aB.isPartial():
            suffix = "sfn"
        startT = datetime.now()
        dateString = startT.strftime("%Y-%m-%d")
        name_base = ( "summary_" + bName + "_" + 
                      dateString + "_" + aB.testedAtNice() + "_" + suffix )
        name_html = name_base + ".html"
        name_json = name_base + ".json"
        html_string = aB.html_summary()
        with open( name_html, "w" ) as oF:
            oF.write(html_string)
        with open( name_json, "w" ) as jF:
            json.dump( aB.toJD(), jF, indent=2 )

    logMAIN.info("\n Done with all batches this time!")
    return

    # TODO: For the acceptance test: similar, but with the "force" option? or other input option?



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'to summarize the sensor information')
    parser.add_argument('-b', '--batchIDs',    dest = 'iBatches',
                        type = str, default = '',  help = 'input batch IDs')
    parser.add_argument('-l', '--location',    dest = 'iLocation',
                        type = str, default = '.', help = 'directory with batch files')
    parser.add_argument('-c', '--controlFile', dest = 'iControl',
                        type = str, default = 'batchControl.json', help = 'input file with control/corrections')
    parser.add_argument('-t', '--QATC', dest = 'qaTC',
                        type = str, default = '', help = 'QA-TC success flag (yes or no)')
    parser.add_argument('-q', '--QACCE', dest = 'qaCCE',
                        type = str, default = '', help = 'QA-CCE success flag (yes or no)')
    parser.add_argument('-d', '--debug',       dest = 'debug',
                        action = 'store_true', help = 'debugging printout')

    args = parser.parse_args()

    main(args)
