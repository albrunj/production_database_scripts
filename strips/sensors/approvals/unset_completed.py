#!/usr/bin/python
import logging
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import setup_logging
from strips.sensors.SensorSNUtils import checkSN_basic


#-----------------------------------------------------
# V1 by VF, 2021-08-24: created
#     The script will loop over the items and unset "Completed" flag from the objects
#
#



# 2021-08-24 Put this here (instead of SensorSNUtils), since expect only a rare use
def unset_completed(c, listSN):

    error = False
    cResp = {}
    try:
        cResp = c.post( 'setComponentCompletedBulk',
                        json = { 'components'  : listSN,
                                 'completed'    : False} )
    except Exception as e:
        error = True
        print("Error: un-set \"Completed\" failed ")
        print(e)

    return error,cResp


def main(args):
    base_log_name = "DB-log-UnsetCompleted_"
    setup_logging(base_log_name)
    logM = logging.getLogger('LOG-MAIN')

    FileListSN   = args.FileListSN
    logM.info(" Got input: ")
    logM.info("   FileListSN   = " + FileListSN )


    if len(FileListSN) > 0 :
        logM.info("got the Control File name, will process it")
    else:
        logM.error("no Control File name => will exit")
        return

    listSN = []
    if len(FileListSN) > 0 :
        lAbsPath = Path(FileListSN)
        if lAbsPath.is_file():
            with open(FileListSN,'r') as iF:
                lines = iF.readlines()
        else:
            logM.error(" Funny file name: <" + FileListSN + ">" )
            logM.error(" .... cannot process. Exiting. ")
            return

        for aLine in lines:
            # let's strip the SN from the trailing stuff
            cleanSN = aLine.strip()

            # want to have commented out lines
            if len(cleanSN) == 0 or cleanSN.startswith("#") : 
                continue

            # check the input SN formatting
            if not checkSN_basic(cleanSN) :
                logM.error("Error: SN = <" + cleanSN + "> is illegal!")
            else:
                listSN.append(cleanSN)

    if len(listSN) == 0:
        logM.error("could not form a valid SN list, exiting")
        return

    # check if the list is too long. The DB call cannot accept more than 1000 items...
    logM.info(" Have a list of <" + str(len(listSN)) + "> SNs")
    SuperList = []
    currentList = []
    for i,SN in enumerate(listSN):
        # keep adding if the size is small
        if len(currentList) == 900:
            # add to the list of lists and reset
            SuperList.append(currentList)
            currentList = []
        # rolling addition
        currentList.append(SN)
        # let's not forget the last one
        if i == len(listSN)-1:
            SuperList.append(currentList)
    logM.info(" made <" + str(len(SuperList)) + "> lists of SN lists:")
    for i,aL in enumerate(SuperList):
        logM.info(" list number " + str(i) + ", it has " + str(len(aL)) + " SNs")


    # Should have enough information to send off
    c = itkdb.Client()  # expires_after=dict(days=1) )

    # loop over the items
    for i,aL in enumerate(SuperList):
        logM.info(" going after list number " + str(i) )
        (err, aResp) = unset_completed(c,aL)
        if err:
            logM.error(" Got error unsetting the \"completed\" flag for listSN = " + str(aL) + "\n")
            return
        else:
            logM.info(" Success unsetting the \"completed\" flag for listSN = " + str(aL) + "\n")

    return


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--FileListSN', dest = 'FileListSN', type = str, default = '', help = 'Input File name/path for SN list')

    args = parser.parse_args()

    main(args)
