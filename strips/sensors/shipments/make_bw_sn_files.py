#!/usr/bin/env python
import os
import re

#----------------------------------------------------------------
# A code to create the SN/Batch/WaferNo lists for a set of HPK data files
# V1, 2021-09-29, VF
#----------------------------------------------------------------

def main(args):
    inputDir       = args.inputDir
    outputBasename = args.outputBasename
    print(" Got input: ")
    print("  inputDir   = " + inputDir   )
    print("  outputBasename = " + outputBasename )

    files = os.listdir(inputDir)

    # arrays to store, then process
    dictSBW = {}

    # processing the MAIN sensor IDs
    for fn in files:
        # more sanity checks
        baseName = fn[:-4]
        lenSN = len(baseName)
        if ( fn.endswith('txt') and 
             lenSN == 14        and 
             baseName[:4] == "20US" ) :
            with open(os.path.join(inputDir,fn), 'r') as file:
                lines = [l.strip() for l in file.readlines()]
        else:
            print(" weird file: <" + fn + ">, skipping! ")
            continue
 

        batch = "N/A"
        wafer = "N/A"
        for L in lines:
            if L.startswith("Serial Number"):

                items = re.split(' |\t',L) #L.split(" ")
                #print(str(items))
                bwno = items[2]
                items = bwno.split("-")
                if len(items) != 2:
                    print(" bad, bad, bad: don't see the batch-wafer numbers: " + str(items))
                    return
                batch = items[0].strip()
                wafer = items[1].strip()

        dictSBW[baseName] = {}
        dictSBW[baseName]["batch"] = batch
        dictSBW[baseName]["wafer"] = wafer

    # Now, process and find the batch list
    lB = []
    lSN = []
    for sn in dictSBW:
        lSN.append(sn)
        batch = dictSBW[sn]["batch"]
        if not batch in lB:
            lB.append(batch)
    print(" seeing batches: " + str(lB))

    # there shall be order!
    ordSN = sorted(lSN)

    # write files
    for aB in lB:
        print(" processing batch aB:")
        fname = outputBasename + "_" + aB + ".csv"
        oF = open( fname, "w")

        nS = 0
        #for sn in dictSBW:
        for sn in ordSN:
            batch = dictSBW[sn]["batch"]
            wafer = dictSBW[sn]["wafer"]
            if batch == aB:
                nS += 1
                oF.write(sn + "," + batch + "," + wafer + '\n')
        oF.close()
        print(" wrote " + str(nS) + " lines/sensors from batch " + aB)

    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Script for creating list of SNs from directory of HPK files')
    parser.add_argument('-i', '--inputDir', dest = 'inputDir', type = str,required=True,help = 'directory of HPK files')
    parser.add_argument('-o', '--outputBasename', dest = 'outputBasename', type = str,required=True,help = 'output file basename')

    args = parser.parse_args()
    main(args)
