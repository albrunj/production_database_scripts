#!/usr/bin/env python
import os
import re

#----------------------------------------------------------------
# Copied from "makeSNLists" and changed over the info for the QA pieces
# 2021-10-03, VF, V1
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
    QAminis = []
    QAchips = []
    Others  = []
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
                
                # add the SN for the "Mini & MD8" piece
                SN_QAmini = fn[:8] + '1' + fn[9:-4]
                QAminis.append( SN_QAmini )

                # add the SN for the "Test Chip & MD8" piece
                SN_QAchip = fn[:8] + '7' + fn[9:-4]
                QAchips.append( SN_QAchip )
            else:
                Others.append( fn )

    # now writing out allSNs
    minis = sorted(QAminis)
    chips = sorted(QAchips)
    with open(args.outputFile,'w') as f:
        for obj in minis:
            f.write( obj+'\n')
        for obj in chips:
            f.write( obj+'\n')

    if len(Others) > 0:
        print(" Saw " + str(len(Others)) + " weird files:")
        for item in Others:
            print( item )

# print what we did
    print(' Found and printed ' + str(len(QAminis)) + ' QAminis and ' + str(len(QAchips)) + ' QAchips')

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
