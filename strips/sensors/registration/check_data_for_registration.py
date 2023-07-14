#!/usr/bin/env python
#import datetime
import argparse
import logging
import os
import sys

from __path__ import updatePath
updatePath()


from strips.sensors.registration.registerSensors__ATLAS18 import process_files_in_folder
from strips.sensors.registration.registerSensors__ATLAS18 import reverify_data
from strips.sensors.SensorSNUtils import setup_logging


#------------------------------------------------------------
# VF, 2021-08-15: Created as a subset of registerSesnors_ATLAS18.py
#                 The basic idea is only to verify the input data, with 
#                 All the read-in functionality from Matt B. and Derek H.
#
#------------------------------------------------------------



# VF, 2021-08-12: let's make a graceful exit
def the_end(logFile):
    logging.shutdown()

    return


def main(args):

    # process the input parameters
    input_dir     = args.input_dir
    force_upload  = args.force_upload

    # VF, 2021-08-09 : add logging
    log_base_file = "DBregiLOG_checkData_"
    logFile = setup_logging(log_base_file)

    '''
    startT = datetime.datetime.now()
    startS = startT.strftime("%Y-%m-%d_%Hh-%Mm-%Ss")
    logFile = "DBregiLOG_checkData_" + startS + ".txt"

    # set up logging to file; will print the log origin ("name")
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)-8s: %(message)s',
                        filename=logFile,
                        filemode='w')
    # define a Handler which writes DEBUG messages or higher
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('  %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    '''

    logMAIN = logging.getLogger('LOG-MAIN')
    logMAIN.info(" starting the log file for DB : " + logFile )
    logMAIN.info('\n *** check_data_for_registration.py ***\n')

    logMAIN.info(" ------------------------------------- ")
    logMAIN.info(" Got input: "                           )
    logMAIN.info("   input_dir     = " + input_dir        )
    logMAIN.info("   force_upload  = " + str(force_upload))
    logMAIN.info(" ------------------------------------ " )


    # VF, 2021-08-14: add the check on the directory existence
    if not os.path.isdir(input_dir):
        logMAIN.error(" The input directory is invalid. Will exit.")
        logMAIN.error(" Verification FAILED.")
        return

    # Main information processing
    try:

        files_ok, inputData, flags = process_files_in_folder(input_dir, force_upload)

        if files_ok:
            logMAIN.info(" Processed " + str(len(inputData)) + " files")
            logMAIN.info("")
        else:
            logMAIN.error("")
            logMAIN.error(" See problems with input data.")
            logMAIN.error(" Verification FAILED. Please see the log file for details.")
            the_end(logFile)
            return

         # Final verification
        logMAIN.info(" Will verify the data again.")
        data_pass = reverify_data(force_upload,inputData)
        if data_pass:
            logMAIN.info(" Verification passed. ")
            logMAIN.info("")
        else:
            logMAIN.error("")
            logMAIN.error(" Verification FAILED. Please see the log file for details.")

    except Exception as e:
        logMAIN.error("")
        logMAIN.error(" Received exception during execution:")
        logMAIN.error(e)
        logMAIN.error(" Verification FAILED. Please see the log file for details.")

    the_end(logFile)
    return
           

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Batch verification of input data (ATLAS18 datasheets)', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-d', '--inputDir', dest = 'input_dir', type = str, required = True, help = 'Location of manufacturer test results files (directory)')
    required.add_argument('-f', '--forceUpload', dest = 'force_upload', action = 'store_true', help = 'force upload data not passing HPK datafile consistency checks')

    args = parser.parse_args()
    sys.exit(main(args))
