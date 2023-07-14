#!/usr/bin/python
import os
from shutil import copy


#________________________________________
# VF, 2021-10-20: to fix the data point
#                 that HPK operators likely miss, of current at Vfd+50V.
#                 (in case of intermediate voltage on the IV grid)
#
#

key50Vpt = "Leakage Current at Vfd + 50V (microA)"
keyVfd   = "Deplation Volts (V)"
keyIV = "#IV"
keyEnd = "700"
delta = 50 # [V] over the Vfd

def find_problem_plus50Vpt(line):
    have_problem = False
    if line.startswith(key50Vpt):
        restL = line[len(key50Vpt):]
        restS = restL.strip()
        if len(restS) == 0:
            have_problem = True
    return have_problem


def find_Vfd(line):
    Vfd = -1.0
    if line.startswith(keyVfd):
        restL = line[len(keyVfd):]
        restS = restL.strip()
        if len(restS) == 0:
            print(" could not get Vfd from line <" + line + ">")
        else:
            try:
                Vfd = float(restS)
            except Exception as e:
                print(" problem converting <" + restS + "> to float!")
                print(e)
    if Vfd < 0:
        print(" find_Vfd: having problems with line <" + line + ">")
    return Vfd


def find_current_val(Vfd, aI, aV):
    # if at the node
    theI = -999.0
    if len(aV) < 2 or len(aV) != len(aI):
        print(" wrong arrays to parse! aI = " + str(aI) + ", aV = " + str(aV))
        return theI
    lArr = len(aV)
    i1 = -1
    for i,V in enumerate(aV):
        if abs(V-Vfd) < 1.0:
            return aI[i]
        # must be in-between
        if i < lArr-1:
            if aV[i] < Vfd and Vfd < aV[i+1]:
                i1 = i
                break
    if i1 == -1:
        print(" didn't find the value of <" + str(Vfd) + "> in aI = " + str(aI) + ", aV = " + str(aV))
        return theI
    # interpolate
    V1 = aV[i1]
    V2 = aV[i1+1]
    I1 = aI[i1]
    I2 = aI[i1+1]
    I = I1 + (I2-I1)/(V2-V1)*(Vfd-V1)
    return I


def fix_plus50Vpt_line(l,curr):
    cleanL = l.strip()
    newL = cleanL + "   " + str(curr)
    return newL


def read_IV(lines):
    read_on = False
    iArr = []
    vArr = []
    for aL in lines:
        cL = aL.strip()
        if cL == keyIV:
            read_on = True
            # will start reading from the next line!
            continue
        if aL.startswith(keyEnd):
            read_on = False
            # will stop from the next line!
        if read_on:
            lLine = aL.split()
            if len(lLine) != 2:
                print(" trouble in the universe: I/V is not 2 numbers! Line = <" + aL + ">")
            # stop reading if the
            if lLine[1] == "O.L." or lLine[1] == "-" :
                break
            aV = float(lLine[0])
            aI = float(lLine[1])

            iArr.append(aI)
            vArr.append(aV)
    return iArr, vArr
            

def main(args):
    inputDir  = args.inputDir
    outputDir = args.outputDir
    print(" Got input: ")  
    print("   inputDir    = " + inputDir  )
    print("   outputDir   = " + outputDir )
      
    files = os.listdir(inputDir)
    # processing the MAIN sensor IDs
    for fn in files:
        inpFile = os.path.join(inputDir,fn)
        outFile = os.path.join(outputDir,fn)
        lines = []
        with open(inpFile, 'r') as iF:
            lines = [l.strip() for l in iF.readlines()]
            
        have_problem = False
        Vfd = -1.0
        for l in lines:
            if l.startswith(key50Vpt):
                have_problem = find_problem_plus50Vpt(l)
            if l.startswith(keyVfd):
                Vfd = find_Vfd(l)
        if have_problem:
            # write the fixed file
            aI, aV = read_IV(lines)
            curr = find_current_val(Vfd+delta, aI, aV)
            # footwork to read the file while preserving the endings and
            #  "to replace 1 string with another"
            newVal = key50Vpt + "\t{:.3e}".format(curr)
            with open(inpFile,'r',newline='') as iF:
                content = iF.read()
            content = content.replace(key50Vpt, newVal)
            with open(outFile, 'w',newline='') as oF:
                oF.write(content)
            print(" fixed file " + fn + " with I(Vfd+50V) = {:.3e}".format(curr) )
        else:
            # copy the file
            copy(inpFile,outFile)
            print("       file " + fn + " is copied without a fix")
    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Script for fixing HPK data files for the magical missing data point')
    parser.add_argument('-i', '--inputDir', dest = 'inputDir', type = str,required=True,help = 'directory of HPK files')
    parser.add_argument('-o', '--outputDir', dest = 'outputDir', type = str,required=True,help = 'output file')

    args = parser.parse_args()
    main(args)
