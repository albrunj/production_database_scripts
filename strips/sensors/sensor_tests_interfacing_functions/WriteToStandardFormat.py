"""
#To use:

import WriteToStandardFormat
WriteToStandardFormat.WriteToStandardFormat(WAFERDICTLIST,MirrorDirectoryMap=None)

#where WAFERDICTLIST is obtained elsewhere, probably via ImportData
"""
"""###Author: David Rousso"""
import os

from CommonConfig import ColumnsDict
from CommonConfig import dataformatpath
from CommonConfig import errprint
from CommonConfig import floatformat
from CommonConfig import FormatFilesDict
from CommonConfig import intformat
from CommonConfig import NoneInTable
from CommonConfig import norprint
from CommonConfig import standarddelimiter
from CommonConfig import standardfilenameprefix
from CommonConfig import Timestamp2DateTime
#If CreateMirrorDirectory==None, then it will add the standard file in the same directory as the old file
#If CreateMirrorDirectory==(OriginalDirectory,MappedDirectory), then all standard files will be added to mapped directory in the same file substructure as the original directory

def WriteToStandardFormat(WAFERDICTLIST,MirrorDirectoryMap=None):
    print('')
    print('')
    print('')
    print('')
    print('')
    print("Running WriteToStandardFormat.py: Writing a TESTDICTLIST object to standard test formats locally.:")
    print('')
    keylistlist={}
    formatlistlist={}

    for TestType in FormatFilesDict.keys():
        with open(dataformatpath+FormatFilesDict[TestType]) as f:
            RAWDATAFORMAT=f.read()
        norprint(FormatFilesDict[TestType])
        #Generate Key List:
        keylist=[i.split('&&&')[0] for i in RAWDATAFORMAT.split('$$$') if i]
        keylist=[i for i in keylist if i!='TABLE']
        keylist=[i for i in keylist if i!='IGNORE']
        formatlist=[i.split('&&&')[1] for i in RAWDATAFORMAT.split('$$$') if i]

        formatlistlist[TestType]=formatlist
        keylistlist[TestType]=keylist


    
    UsedFilepaths=[]

    for WAFERDICT in WAFERDICTLIST:

        print('')
        print('')
        print('')
        norprint('Current file is: ' +WAFERDICT['Filepath'])

        #Determine Test Type
        TestType=WAFERDICT['TestType']
        try:
            keylist=keylistlist[TestType]
            formatlist=formatlistlist[TestType]
            columns=ColumnsDict[TestType]
        except:
            errprint('TestType not found' ,str(TestType))
            continue

        #Check if already in standard format
        if WAFERDICT['DataFormat']==FormatFilesDict[TestType]:
            norprint('The original file is already in a standard format (DataFormat is equal to the standard)')
            continue
        if WAFERDICT['Filename'][0:4]==standardfilenameprefix:
            norprint('Already in standard format (filename prefix is already that of a standard file)')
            continue
        if WAFERDICT['Filepath'].split('/')[-1][0:4]==standardfilenameprefix:
            norprint('Already in standard format (filename prefix in filepath is already that of a standard file):')
            continue

        #Create Header
        outputstr=''
        (Date,Time)=Timestamp2DateTime(WAFERDICT['Timestamp'])
        for i in range(0,len(keylist)):
            if keylist[i]=='Date':
                outputstr+=str(Date)
            elif keylist[i]=='Time':
                outputstr+=str(Time)
            elif keylist[i]=='Filename':
                outputstr+=standardfilenameprefix+WAFERDICT['Filename']
            else:
                value=WAFERDICT[keylist[i]]
                if value!=None:
                    outputstr+=str(WAFERDICT[keylist[i]])
                else:
                    outputstr+=''

            outputstr+=formatlist[i]

        #Create Table
        TABLEINV=[]
        lengthlist=[]
        for columnname in columns:
            column=WAFERDICT[columnname]
            if column!=None:
                lengthlist.append(len(column))
                TABLEINV.append(column)
            else:
                errprint('Warning! The Column for does not appear in the file',columnname )
                lengthlist.append(0)
                TABLEINV.append([])

        #make all columns the same length
        numrows=max(lengthlist)
        for columnind in range(0,len(columns)):
            columnlength=len(TABLEINV[columnind])
            if columnlength!=numrows:
                for i in range(columnlength,numrows):
                    TABLEINV[columnind].append(0)

        ##Invert the table
        TABLEROWS=[]
        #Add table headers while removing the TABLE_ prefix
        TABLEROWS.append([i[6:] for i in columns])
        #Add table rows while inverting
        for rowind in range(0,numrows):
                TABLEROWS.append([i[rowind] for i in TABLEINV])

        #print out table
        for row in TABLEROWS:
            tempstr=""
            firstitem=True
            for item in row:
                if firstitem:
                    delim=""
                    firstitem=False
                else:
                    delim=standarddelimiter
                    
                itemtoadd=item
                if item is None:
                    item=NoneInTable  
                if type(item)==int:
                    itemtoadd=intformat.format(item)
                if type(item)==float:
                    itemtoadd=floatformat.format(item)

                tempstr+=delim+itemtoadd

            outputstr+=tempstr+'\n'


        for i in range(len(keylist),len(formatlist)):
            outputstr+=formatlist[i]

        #print(outputstr)

        #print out table to file
        if WAFERDICT['Filepath']!=None and WAFERDICT['Filename']!=None:
            filepath=WAFERDICT['Filepath']
            filename=WAFERDICT['Filename']
            
            if MirrorDirectoryMap is None:
                newfilepath=os.path.join(os.path.dirname(filepath),standardfilenameprefix+filename)
            elif type(MirrorDirectoryMap) is tuple and len(MirrorDirectoryMap)==2 and type(MirrorDirectoryMap[0]) is str and type(MirrorDirectoryMap[1]) is str:
                try:
                    newfolder=os.path.abspath(os.path.dirname(filepath)).replace(
                        os.path.abspath(MirrorDirectoryMap[0]),
                        os.path.abspath(MirrorDirectoryMap[1])
                    )
                except:
                    errprint('Not valid directory map. Error.',MirrorDirectoryMap)
                    newfolder=MirrorDirectoryMap[1]
                if not os.path.isdir(newfolder):
                    os.makedirs(newfolder)
                newfilepath=os.path.join(newfolder,standardfilenameprefix+filename)
            else: 
                errprint('Not valid directory map',MirrorDirectoryMap)
                newfilepath=os.path.join(os.path.dirname(filepath),standardfilenameprefix+filename)
            
            #For tests that share filenames, add a counter to the end
            if newfilepath in UsedFilepaths:
                filepathiscopy=True
                counter=1
                while filepathiscopy:
                    tempnewfilepath=newfilepath+'_'+str(counter)
                    if tempnewfilepath in UsedFilepaths:
                        counter+=1
                    else:
                        filepathiscopy=False
                        newfilepath=tempnewfilepath
            
            with open(newfilepath,"w+") as f:
                f.write(outputstr)
            UsedFilepaths.append(newfilepath)
            norprint('Written to: '+newfilepath)
        else:
            errprint('No filepath or filename found','')

    print('WriteToStandardFormat.py Complete!')
    return None
