import os

def main(args):
    files = os.listdir(args.inputDir)
    msg = ''
    for fn in files:
        if fn.endswith('txt'):
            msg += fn[:-4] + '\n'

    for fn in files:
        if fn.endswith('txt'):
            #halfmoon = 20UXXYYA900000
            msg += fn[:8] + '9' + fn[9:-4] + '\n'
    
    with open(args.outputFile,'w') as f:
        f.write(msg)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Script for creating list of SNs from directory of HPK files')
    parser.add_argument('-i', '--inputDir', dest = 'inputDir', type = str,required=True,help = 'directory of HPK files')
    parser.add_argument('-o', '--outputFile', dest = 'outputFile', type = str, required=True,help = 'output file')
    args = parser.parse_args()

    main(args)
