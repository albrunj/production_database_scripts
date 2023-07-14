#!/usr/bin/env python
import os
import re

#----------------------------------------------------------------
# Original code by Derek Hamersly, summer 2020
# Update 2021-01-31 by VF: added the batch number as an argument
#                          If present, only the SNs for this batch will be printed
# Update 2021-08-11 by VF: fixed "local variable used before assignment", 
#                          more explicit argument I/O, restricted batch name finding
#----------------------------------------------------------------

def main(args):
    inputDir   = args.inputDir
    outputFile = args.outputFile
    batchName  = args.inputBatch
    haveBatch = len(batchName) > 0
    # print( "haveBatch = " + str(haveBatch) )
    print(" Got input: ")
    print("  inputDir   = " + inputDir   )
    print("  outputFile = " + outputFile )
    if haveBatch:
        print("  inputBatch = " + batchName  )

    files = os.listdir(inputDir)
    msg_MAIN = ''
    msg_HM   = ''
    msg_Others = ''
    nSN_MAIN = 0
    nSN_HM   = 0
    nOthers  = 0
    # processing the MAIN sensor IDs
    for fn in files:
        addSN = True # initial goodness

        # select SNs from this batch only
        if haveBatch :
            addSN = False # if questioned, goodness -> sin
            # open the file, loop over lines
            #   then, for the lines containing "Serial", 
            #      check the presence of the batchName
            with open(os.path.join(inputDir,fn), 'r') as file:
                lines = [l.strip() for l in file.readlines()]
                for i, l in enumerate(lines):
                    if re.search( "Serial", l ) :
                        if re.search( batchName, l ) :
                            addSN = True

        if addSN :
            # more sanity checks
            baseName = fn[:-4]
            lSN = len(baseName)
            if ( fn.endswith('txt') and 
                 lSN == 14          and 
                 baseName[:4] == "20US" ) :
                
                # add the SN for the MAIN sensor
                nSN_MAIN += 1
                msg_MAIN += fn[:-4] + '\n'

                # add the SN for Halfmoon
                nSN_HM += 1
                msg_HM += fn[:8] + '9' + fn[9:-4] + '\n'
            else:
                nOthers += 1
                msg_Others += fn + '\n'

# now writing out allSNs
    with open(args.outputFile,'w') as f:
        f.write(msg_MAIN)
        f.write(msg_HM  )

    if nOthers > 0:
        print(" Saw " + str(nOthers) + " weird files:")
        print(msg_Others)

# print what we did
    print(' Found and printed ' + str(nSN_MAIN) + ' MAIN SNs and ' + str(nSN_HM) + ' HM SNs')

    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Script for creating list of SNs from directory of HPK files')
    parser.add_argument('-i', '--inputDir', dest = 'inputDir', type = str,required=True,help = 'directory of HPK files')
    parser.add_argument('-o', '--outputFile', dest = 'outputFile', type = str,required=True,help = 'output file')
# new argument
    parser.add_argument('-b', '--inputBatch', dest = 'inputBatch', type = str,required=False,default='',help = 'HPK Batch Number to matchi in the HPK test file')

    args = parser.parse_args()
    main(args)
