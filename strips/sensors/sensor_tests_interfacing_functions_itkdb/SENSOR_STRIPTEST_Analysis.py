"""
To use do:
import SENSOR_STRIPTEST_Analysis
NEWWAFERDICT = SENSOR_STRIPTEST_Analysis.Analyze_STRIPTEST_SEG(WAFERDICT)
This gives a new wafer dictionary containing the derived parameters
"""
import copy 
from itertools import groupby
from operator import itemgetter

import numpy as np
from CommonConfig import ALGORITHM_VERSION
from CommonConfig import cm
from CommonConfig import StripLengthFromType
from CommonConfig import TestType_Manufacturing
from CommonConfig import TestType_Strip
#import math

"""
Info
Analysis function for the Strip Test. Note the Analyze_STRIPTEST_SEG function gives a Pass/Fail for a single segment, not a wafer. 
Current implementation is that a segment fails if any of the following coniditons are met:
- More than 1% of the total channels are bad
- There are more than 8 bad channels in a row

In addition, a Measurement error is given if there are more than 2 Bad Channels which are separated by a multiple of the number of channels scanned by the probe card at a time. 

If no frequency is recorded, or the frequency is not 1 kHz, currently this is only added to the WAFERDICT flags but the segment is still analyzed for a Pass/Fail.

There are flags for the Channels that fail the specification. Each flag is defined by a range for I, C and R. There are currently four groups of flags, each group has a dictionary. The groups are:
SimpleFlags - e.g. 'R Low'
UsefulFlags - e.g. 'Pinhole'
MeasErrFlasgs - should also be included in UsefulFlags, separate dictionary to provide print / plotting options. Currently only contains 'Likely Bad Contact'
SoSoFlags - don't fail spec but values differ significantly from expected / average. Currently only contains R above/below average. 
Currently SimpleFlags and UsefulFlags are printed out, e.g ['I high', 'Pinhole']
"""
    
#Set Limits 
MaxPercentBadChannels = 1 
MaxConsecBadChannels = 8 #fails if greater than this
ProbeCardN = 32 #Number of channels the probe card scans at a time
MaxNumberCoincidences = 2 #Maximum number of times bad channels can be separated by a multiple of ProbeCardN before being flagged.
TestFrequency = 1 #kHz
MaxBadChannelsToPrint = 20 #only print this many entries in the bad channels dictionary if there are more than this number of bad channels

#Used in Flag Definitions:
#Note Cmin and Cmax are definied in Analyze_STRIPTEST_SEG as they depend on the strip length
MinCperLength = 20 #pF/cm, from Spec
MaxCperLength = 30 #pF/cm
Rmin = 1 #Mohm
Rmax = 2 #Mohm
Rtypical = 1.4 #Mohm
Ishort = 500 #nA
#ShortThreshold = 5000 #nA

#SoSoFlags Parameters
RSoSoTol = 0.1 #Mohm above / below R average resulting in a SoSo Flag for R


#Function to analyze a strip test file (i.e. per segment)
def Analyze_STRIPTEST_SEG(WAFERDICT):
    print('Starting Analyze_STRIPTEST_SEG for {}-W{} Seg {} file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']), str(WAFERDICT['Segment']), str(WAFERDICT['Filepath']) ))
   
    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
    NEWWAFERDICT['AlgorithmVersion']=ALGORITHM_VERSION
    NEWWAFERDICT['N_badcluster_max'] = 0
    NEWWAFERDICT['Bad_strip_fraction[%]'] = None
    NEWWAFERDICT['Flags'] = []
    NEWWAFERDICT['Decision']=None
    NEWWAFERDICT['ChannelRange']=None
    NEWWAFERDICT['NumBadChannels'] = None #All bad channels, including those flagged as a measurement error 
    NEWWAFERDICT['BadChannelsList'] = []
    NEWWAFERDICT['BadChannelsDict'] = {} #Dictionary for bad channels in format Channel : Flaglist
    NEWWAFERDICT['NumSoSoChannels'] = None
    NEWWAFERDICT['SoSoChannelsList'] = []
    NEWWAFERDICT['SoSoChannelsDict'] = {} 
    NEWWAFERDICT['NumMeasErrChannels'] = None
    NEWWAFERDICT['MeasErrChannelsList'] = []
    NEWWAFERDICT['MeasErrChannelsDict'] = {}
    NEWWAFERDICT['NumBadChannelsNoMeasErr'] = None #Bad Channels excluding those flagged as a measurement error 
    NEWWAFERDICT['BadChannelsNoMeasErrList'] = []
    NEWWAFERDICT['BadChannelsNoMeasErrDict'] = {}
    NEWWAFERDICT['BadChannelsDictConcise']={}
    NEWWAFERDICT['List_shorts'] = []
    NEWWAFERDICT['List_pinholes'] = []
    NEWWAFERDICT['List_implant_break'] = [] 
    NEWWAFERDICT['List_metal_short'] = [] 
    NEWWAFERDICT['List_open_resistor'] = [] 
    NEWWAFERDICT['List_rbias_defect'] = [] 
    NEWWAFERDICT['List_bad_contact'] = [] 
    

    #Check if a Strip Test
    if WAFERDICT['TestType'] in [TestType_Strip]:
        #Extract Data
        Channel=np.array(WAFERDICT['TABLE_ProbeplanIndex'])
        I=np.array(WAFERDICT['TABLE_Current[nA]'])
        C=np.array(WAFERDICT['TABLE_Capacitance[pF]'])
        R=np.array(WAFERDICT['TABLE_Resistance[MOhm]'])
        Frequency = WAFERDICT['Frequency[kHz]']
    else:
        print ('Error: {} is not a Strip Test, aborting Analyze_STRIPTEST_SEG'.format(str(WAFERDICT['Filepath'])))
        return NEWWAFERDICT
        
    #Check if Data exists
    if Channel is None or np.shape(Channel)==() or all(Channel==0)==True:
        print('*** ProbeplanIndex is Empty!, Aborting Analyze_STRIPTEST_SEG')
        NEWWAFERDICT['Flags'].append('ProbeplanIndex is Empty!')
        return NEWWAFERDICT
    if I is None or np.shape(I)==() or all(I==0)==True:
        print('*** I is Empty!, Aborting Analyze_STRIPTEST_SEG')
        NEWWAFERDICT['Flags'].append('I is Empty!')
        return NEWWAFERDICT   
    if C is None or np.shape(C)==() or all(C==0)==True:
        print('*** C is Empty!, Aborting Analyze_STRIPTEST_SEG')
        NEWWAFERDICT['Flags'].append('C is Empty!')
        return NEWWAFERDICT
    if R is None or np.shape(R)==() or all(R==0)==True:
        print('*** R is Empty!, Aborting Analyze_STRIPTEST_SEG')
        NEWWAFERDICT['Flags'].append('R is Empty!')
        return NEWWAFERDICT
    
    I=I[Channel!=0]
    C=C[Channel!=0]
    R=R[Channel!=0]
    Channel=Channel[Channel!=0]
    
    #Channel Range
    #print(TempChannel)
    if len(sorted(set(Channel)))==max(Channel)-min(Channel)+1:
        NEWWAFERDICT['ChannelRange']=(int(min(Channel)),int(max(Channel)))
    else:
        print('Probed channels are not consecutive')
    
    #Check Frequency is 1000 Hz (not in all files?)
    if Frequency is not None or Frequency != "":
        try: 
            Frequency = float(Frequency.split('kHz')[0])
            print ('Frequency = {} kHz'.format(Frequency))
            if not Frequency == TestFrequency:
                print ('Warning: Frequency not equal to Test Frequency! ({} kHz)'.format(TestFrequency))
                NEWWAFERDICT['Flags'].append('Frequency not equal to Test Frequency')
        except:
            print ('Warning: Frequency in file could not be interpreted (as a float)')
            NEWWAFERDICT['Flags'].append('No Frequency recorded')
    else:
        print ('Warning: no Frequency recorded!')
        NEWWAFERDICT['Flags'].append('No Frequency recorded')
         
    #Calculate Pinhole threshold
    Rseries_test = WAFERDICT['Rseries_Test[MOhm]']
    try:
        Rseries_test=float(Rseries_test.split('MOhm')[0])
        print("Rseries_test={0} MOhm".format(Rseries_test))
    except:
        Rseries_test = 2.2
        print("Warning: Cannot find Rseries_test in file, using 2.2 MOhm for calculation of Ipinhole")
    Ipinhole = (10/(Rmin + Rseries_test)) *1000
    
    #Print Number of Channels Tested
    NChannels = Channel.size 
    print ('#Channels tested: {}'.format(NChannels))
    NEWWAFERDICT['N_strips']=NChannels

    #Get Strip length dependent limits
    print('Wafer Type: '+str(WAFERDICT['Type']))
    print('Wafer Segment: '+str(WAFERDICT['Segment']))
    StripLengthThing = StripLengthFromType(WAFERDICT['Type'], WAFERDICT['Segment'])
    StripLength=StripLengthThing[1]
    print('Using Strip Length: '+str(StripLength))
    if StripLengthThing[0]==False:
        NEWWAFERDICT['Decision'] = 'MeasErr'
        NEWWAFERDICT['Flags'].append('Cannot find strip length for '+str((WAFERDICT['Type'], WAFERDICT['Segment']))+', using default striplength: '+str(StripLength)+' m')
    Cmin = MinCperLength * StripLength / cm
    Cmax = MaxCperLength * StripLength / cm
    
    
    #Flag Definitions
    #All SimpleFlags defined in dictionary,  SimpleFlagsDict, except for R bias Outlier.    
    #All useful Flags listed in UsefulFlagList, defined in loop over channels
    
    #SimpleFlags                    
    SimpleFlagsDict = {}
    #SimpleFlagsDict['Flag name'] = ['Imin for flag', 'Imax for flag', 'Cmin for flag', 'Cmax for flag', 'Rmin for flag', 'Rmax for flag']
    SimpleFlagsDict['C high'] = [0, float('inf'), Cmax, float('inf'), -float('inf'), float ('inf') ]
    SimpleFlagsDict['C low'] = [0, float('inf'), 0, Cmin, -float('inf'), float('inf')]
    SimpleFlagsDict['R high'] = [ 0, float('inf'),0, float('inf'), Rmax, float('inf')]
    SimpleFlagsDict['R low'] = [ 0, float('inf'),0, float('inf'), 0, Rmin]
    SimpleFlagsDict['I high'] = [Ishort, float('inf'), -float('inf'), float('inf'), -float('inf'), float('inf')]

    #UsefulFlags
    UsefulFlagsList = ['shorts', 'pinholes', 'bad_contact','metal_short', 'implant_break', 'rbias_defect', 'open_resistor'] #Flags to be written out as flag_list
    
    #MeasErr Flags (should also be in Useful Flags)
    MeasErrFlagsDict = {}
    MeasErrFlagsDict['Likely Bad Contact'] = [0, float('inf'), 0, Cmin, Rmax, float('inf')]
    
    #'So-so' Flags
    #Depend on averages
    RsToAverage = R[ (R > Rmin) & (R < Rmax) ]
    Raverage = np.average(RsToAverage) 
    Rsigma = np.std(RsToAverage)
    
    SoSoFlagsDict = {}
    SoSoFlagsDict['R more than {} MOhm below average'.format(RSoSoTol)] = [ 0, float('inf'),0, float('inf'), Rmin, Raverage - RSoSoTol] 
    SoSoFlagsDict['R more than {} MOhm above average'.format(RSoSoTol)] = [ 0, float('inf'),0, float('inf'), Raverage + RSoSoTol, Rmax]
    
    #Loop over all Channels 
    it = np.nditer(Channel, flags=['f_index'])
    while not it.finished:
        
        TempSimpleFlagList = []
        TempUsefulFlagList = []
        TempSoSoFlagList = []
        TempMeasErrFlagList = []
        
        #Simple flags
        for Flag, FlagValues in SimpleFlagsDict.items():
            if (FlagValues[0] <= I[it.index] < FlagValues[1] and
                FlagValues[2] <= C[it.index] < FlagValues[3] and
                FlagValues[4] <= R[it.index] < FlagValues[5]):
                TempSimpleFlagList.append(Flag) #Comment this out if don't want SimpleFlags to be added. 
        del Flag, FlagValues
        
        #Check if Rbias outlier 
        RbiasOutlier = False
        if R[it.index] > Raverage + 2*Rsigma or R[it.index] < Raverage -2*Rsigma:
            RbiasOutlier = True 
        
        #Useful Flags
        if Ishort < I[it.index] <= Ipinhole:
            TempUsefulFlagList = ['shorts']
            
        elif I[it.index] > Ipinhole:
            TempUsefulFlagList = ['pinholes']
            
        elif C[it.index] < Cmin and R[it.index] > Rmax:
            TempUsefulFlagList = ['bad_contact']
            
        elif C[it.index] < Cmin and RbiasOutlier:
            TempUsefulFlagList = ['implant_break']
            TempSimpleFlagList.append("Rbias outlier") #This is here as it is not a failure criterion on it's own
            
        elif C[it.index] > Cmax*2 and R[it.index] < Rmin*0.5:
            TempUsefulFlagList = ['metal_short']
            
        elif C[it.index] < Cmin: #Will never be flagged due to implant_break flag
            TempUsefulFlagList = ['open_resistor']
        
        elif R[it.index] < Rmin or R[it.index] > Rmax:
            TempUsefulFlagList = ['rbias_defect']
            
        #SoSo Flags
        for Flag, FlagValues in SoSoFlagsDict.items():
            if (FlagValues[0] <= I[it.index] < FlagValues[1] and
                FlagValues[2] <= C[it.index] < FlagValues[3] and
                FlagValues[4] <= R[it.index] < FlagValues[5]):
                TempSoSoFlagList.append(Flag)
        del Flag, FlagValues
        
        #MeasErr Flags
        for Flag, FlagValues in MeasErrFlagsDict.items():
            if (FlagValues[0] <= I[it.index] < FlagValues[1] and
                FlagValues[2] <= C[it.index] < FlagValues[3] and
                FlagValues[4] <= R[it.index] < FlagValues[5]):
                TempMeasErrFlagList.append(Flag)
        del Flag, FlagValues
        
        
        #Add to Bad Channels Dictionaries
        if TempSimpleFlagList:
            if not TempUsefulFlagList:
                TempUsefulFlagList = ['Unknown Fault']
            NEWWAFERDICT['BadChannelsDict'][int(it[0])] = TempSimpleFlagList + TempUsefulFlagList
            NEWWAFERDICT['BadChannelsList'].append(int(it[0]))
       
        if TempMeasErrFlagList:
            NEWWAFERDICT['MeasErrChannelsDict'][int(it[0])] = TempSimpleFlagList + TempMeasErrFlagList
            NEWWAFERDICT['MeasErrChannelsList'].append(int(it[0]))
            it.iternext()
        
        elif TempSimpleFlagList: 
            if not TempUsefulFlagList:
                TempUsefulFlagList.append('Unknown Fault')
            NEWWAFERDICT['BadChannelsNoMeasErrDict'][int(it[0])] = TempSimpleFlagList + TempUsefulFlagList
            NEWWAFERDICT['BadChannelsNoMeasErrList'].append(int(it[0]))
            it.iternext()
            
        elif TempSoSoFlagList:
            NEWWAFERDICT['SoSoChannelsDict'][int(it[0])] = TempSoSoFlagList
            NEWWAFERDICT['SoSoChannelsList'].append(int(it[0]))
            it.iternext()

        else:
            it.iternext()

    del TempSimpleFlagList
    del TempUsefulFlagList
    del TempSoSoFlagList
    del TempMeasErrFlagList
    
    #Make Concise BadChannelsDict for Report
    NEWWAFERDICT['BadChannelsDictConcise']=ConciseBadChannelsDict(NEWWAFERDICT['BadChannelsDict'])
    
    
    #Get Number of Bad Channels                                                
    NEWWAFERDICT['NumBadChannels'] = len(NEWWAFERDICT['BadChannelsDict'])
    NEWWAFERDICT['NumBadChannelsNoMeasErr'] = len(NEWWAFERDICT['BadChannelsNoMeasErrDict'])
    NEWWAFERDICT['NumSoSoChannels'] = len(NEWWAFERDICT['SoSoChannelsDict'])
    NEWWAFERDICT['NumMeasErrChannels'] = len(NEWWAFERDICT['MeasErrChannelsDict'])
    print ('#Bad Channels (including Meas Err Flags): {}'.format(NEWWAFERDICT['NumBadChannels']))
    #print ('#Bad Channels (excluding Meas Err Flags): {}'.format(NEWWAFERDICT['NumBadChannelsNoMeasErr']))
    #print ('#MeasErr Channels: {}'.format(NEWWAFERDICT['NumMeasErrChannels']))
    print ('#So-So Channels: {}'.format(NEWWAFERDICT['NumSoSoChannels']))
    
    
    #Check Bad Channels don't differ by multiples of the Probe Card
    ProbeCardMultipleChannels = CheckMultipleOfProbeCard(NEWWAFERDICT['BadChannelsList'])
    if ProbeCardMultipleChannels:
        ProbeCardMultipleChannelsConcise=MakeProbeCardMultipleChannelsConcise(ProbeCardMultipleChannels)
        NEWWAFERDICT['Decision'] = 'MeasErr'
        NEWWAFERDICT['Flags'].append('Warning: Bad Channels separated by a multiple of the probe card ({}) on more than {} occassions. See Channels ({})'.format(ProbeCardN, MaxNumberCoincidences, '\n'.join([str(i) for i in ProbeCardMultipleChannelsConcise]) )) 
    
    
    #Check max number of bad channels not excceded
    Bad_strip_fraction = (NEWWAFERDICT['NumBadChannels'] / NChannels) *100
    if Bad_strip_fraction > MaxPercentBadChannels:
        print('#Bad Channel fraction (including Meas Errs) = {}%, exceeds {}%. Segment fails Strip test!'.format(Bad_strip_fraction, MaxPercentBadChannels))
        NEWWAFERDICT['Flags'].append('Max percent of Bad Channels exceeded')
        NEWWAFERDICT['Decision']='Fail'
    NEWWAFERDICT['Bad_strip_fraction[%]'] = Bad_strip_fraction 
        
        
    #Check not more than MaxConsecBadChannels bad Channels in a row
    NbadClusterMax = GetNbadClusterMax(NEWWAFERDICT['BadChannelsList'])
    if NbadClusterMax > MaxConsecBadChannels:
        ConsecsMorethanMax = GetConsecBadChannels(NEWWAFERDICT['BadChannelsList'])
        NEWWAFERDICT['Decision'] = 'Fail'
        NEWWAFERDICT['Flags'].append('More than {} Consecutive Bad Channels'.format(MaxConsecBadChannels))
        print ('More than {} bad channels in a row, N_bad_cluster_max = {}. Segment fails Strip test. See Channels {}'.format(MaxConsecBadChannels, NbadClusterMax, ConsecsMorethanMax))
    NEWWAFERDICT['N_badcluster_max'] = NbadClusterMax
        
        
    #Print Bad Channels
    if NEWWAFERDICT['BadChannelsDict']:
        if len(NEWWAFERDICT['BadChannelsDict']) > MaxBadChannelsToPrint:
            BCD=NEWWAFERDICT['BadChannelsDict']
            ChannelsToPrint = {k:BCD[k] for k in BCD.keys() if k<MaxBadChannelsToPrint}
            print ('More than {0} Bad Channels, only printing first {0} entries in Bad Channels Dictionary (including Measurement Error Flags):'.format(MaxBadChannelsToPrint))
        else:
            ChannelsToPrint = NEWWAFERDICT['BadChannelsDict']
            print ('Printing all entries in Bad Channels Dictionary (including Measurement Error Flags):')
        print ('Channel \t Flags')   
        for BadChannel, ChannelFlags  in ChannelsToPrint.items():
            print ('{} \t {}'.format(BadChannel, ChannelFlags))
            
    """
    #Print Bad Channels excluding Meas Errs        
    if NEWWAFERDICT['BadChannelsNoMeasErrDict']:
        print ('Printing Bad Channels Dictionary (excluding Meas Err Flags):')
        print ('Channel \t Flags')   
        for BadChannel, ChannelFlags  in NEWWAFERDICT['BadChannelsNoMeasErrDict'].items():
            print ('{} \t {}'.format(BadChannel, ChannelFlags))
                
    #Print MeasErr Channels
    if NEWWAFERDICT['MeasErrChannelsDict']:
        print ('Printing Measurement Error Channels Dictionary:')
        print ('Channel \t Flags')   
        for BadChannel, ChannelFlags  in NEWWAFERDICT['MeasErrChannelsDict'].items():
            print ('{} \t {}'.format(BadChannel, ChannelFlags))
    """
    
    #Print SoSo Channels
    if NEWWAFERDICT['SoSoChannelsDict']:
        print ('Printing SoSo Channels Dictionary:')
        print ('Channel \t Flags')   
        for BadChannel, ChannelFlags  in NEWWAFERDICT['SoSoChannelsDict'].items():
            print ('{} \t {}'.format(BadChannel, ChannelFlags))
               
                
    #Pass if hasn't failed
    if NEWWAFERDICT['Decision'] == None:
        NEWWAFERDICT['Decision'] = 'Pass'
        print ('Segment passed Strip test')
        
            
    #Write out each useful flag to arrays
    if NEWWAFERDICT['BadChannelsDict']:
        for BadChannel, ChannelFlags  in NEWWAFERDICT['BadChannelsDict'].items():
            for flag in UsefulFlagsList:
                if flag in ChannelFlags:
                    NEWWAFERDICT['List_{}'.format(flag)].append('{}-{}'.format(str(WAFERDICT['Segment']), BadChannel)) 
                
    
    print('Finished Analyze_STRIPTEST_SEG for {}-W{} Seg {} file {}\n'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']), str(WAFERDICT['Segment']), str(WAFERDICT['Filepath']) ))
               
    return NEWWAFERDICT
    
    
def GetConsecBadChannels (BadChannelList):
    """Returns a list of lists of consecutive bad channels e.g. [ [1,2,3,4], [11,12,13,14]"""
    ConsecBadChannels = []
    for k, g in groupby(enumerate(BadChannelList), lambda ix: (ix[0] - ix[1])):
        #print (list(map(itemgetter(1), g)))
        ConsecBadChannels.append(list(map(itemgetter(1), g)))
    AtLeast2 = [entry for entry in ConsecBadChannels if len(entry) > 1]
    return AtLeast2


def GetNbadClusterMax (BadChannelList):
    ConsecBadChannels = GetConsecBadChannels(BadChannelList)
    if ConsecBadChannels:
        lenghts = [len(i) for i in ConsecBadChannels]
        return (max(lenghts))
    else:
        return 0


def CheckMultipleOfProbeCard (BadChannelList):
    """ Returns a list of bad channels multiples if More than MaxNumberCoincidences, e.g [[1, 33, 65], [2, 34, 66], [3, 35, 67]]"""
    ProbeCardDiffChannels = []
    for BadChannel in BadChannelList:
        #Check not already in list
        if not any(BadChannel in MultipleList for MultipleList in ProbeCardDiffChannels):
            MultiplesForChannel = [BadChannel]
            RestofList = BadChannelList[BadChannelList.index(BadChannel)+1:]
            for OtherChannel in RestofList:
                Difference = (OtherChannel - BadChannel) / ProbeCardN
                if (Difference).is_integer():
                    MultiplesForChannel.append(OtherChannel)
            if len(MultiplesForChannel) > MaxNumberCoincidences:
                ProbeCardDiffChannels.append(MultiplesForChannel)

    return ProbeCardDiffChannels

def MakeProbeCardMultipleChannelsConcise(ProbeCardDiffChannels):
    ProbeCardDiffChannelsConcise=[]
    for ProbeChannelList in ProbeCardDiffChannels:
        ProbeChannelListConcise=[]
        ind_i=0
        range_i=ProbeChannelList[ind_i]
        ind_f=0
        range_f=ProbeChannelList[ind_f]

        for ind in range(1,len(ProbeChannelList)):
            currentstrip=ProbeChannelList[ind]
            #If the current strip is N consecutive to previous add to a range
            if currentstrip==range_f+ProbeCardN:
                ind_f=ind
                range_f=ProbeChannelList[ind_f]
            #else, write out the last strip and make current strip new
            else:
                #Write out single strip if single
                if ind_f==ind_i:
                    ProbeChannelListConcise.append(range_i)
                #Write out range of strips if range
                else:
                    ProbeChannelListConcise.append(str(range_i)+'-(+'+str(ProbeCardN)+'*n)-'+str(range_f))
                #make current strip new starting point
                ind_i=ind
                range_i=ProbeChannelList[ind_i]
                ind_f=ind
                range_f=ProbeChannelList[ind_f]
        #Write out last strip
        if ind_f==ind_i:
            ProbeChannelListConcise.append(range_i)
        #Write out range of strips if range
        else:
            ProbeChannelListConcise.append(str(range_i)+'-(+'+str(ProbeCardN)+'*n)-'+str(range_f))

        ProbeCardDiffChannelsConcise.append(ProbeChannelListConcise)
        
    return ProbeCardDiffChannelsConcise

#Strips Summarizer
def STRIPS_SUMMARY(TESTCOMPARISONDATA,BatchInd,Wafer):
    STRIPSDICTLIST=[]
    STRIPSDICTLIST+=[i for i in TESTCOMPARISONDATA[TestType_Strip]['HistoricalTests'][BatchInd] if i['Wafer']==Wafer]
    STRIPSDICTLIST+=[i for i in TESTCOMPARISONDATA[TestType_Strip]['CurrentTests'][BatchInd] if i['Wafer']==Wafer]
    
    if len(STRIPSDICTLIST)==0:
        return None,None,None
    #sort by timestamp
    STRIPSDICTLIST=list(list(zip(*sorted([(STRIPSDICTLIST[i]['Timestamp'],i,STRIPSDICTLIST[i]) for i in range(0,len(STRIPSDICTLIST))])))[2])
    
    WaferStripsMatrix={}
    for TEST in STRIPSDICTLIST:
        TempStripsDict={}
        if TEST['ChannelRange'] is not None:
            StripInds=range(TEST['ChannelRange'][0],TEST['ChannelRange'][1]+1)
            for strip in StripInds:
                TempStripsDict[strip]=None
            for strip in TEST['BadChannelsDict'].keys():
                TempStripsDict[strip]=TEST['BadChannelsDict'][strip]
            
            #If segment hasn't been done before, just add everything
            if TEST['Segment'] not in WaferStripsMatrix.keys():
                WaferStripsMatrix[TEST['Segment']]=TempStripsDict
            #If segment is there before and is well defined, update entire section
            elif TEST['Segment'] is not None:
                for strip in TempStripsDict.keys():
                    WaferStripsMatrix[TEST['Segment']][strip]=TempStripsDict[strip]
            #If segment is there before and is None, update only bad strips
            else:
                for strip in TempStripsDict.keys():
                    if strip not in WaferStripsMatrix[TEST['Segment']].keys() or TempStripsDict[strip] is not None:
                        WaferStripsMatrix[TEST['Segment']][strip]=TempStripsDict[strip]
        elif len([i for i in TEST['TABLE_ProbeplanIndex'] if i!=0])==0:
            continue
        else:
            print('There is an error in summarizing the strips results. The probing range is not consecutive')
            return None,None,None
        
    #SUMMARIZE
    RegionsProbed={Seg:(int(min(WaferStripsMatrix[Seg].keys())),int(max(WaferStripsMatrix[Seg].keys()))) for Seg in sorted(WaferStripsMatrix.keys()) if len(sorted(set(WaferStripsMatrix[Seg].keys())))==max(WaferStripsMatrix[Seg].keys())-min(WaferStripsMatrix[Seg].keys())+1}
    Summary={Seg:{Strip:WaferStripsMatrix[Seg][Strip] for Strip in sorted(WaferStripsMatrix[Seg].keys()) if WaferStripsMatrix[Seg][Strip] is not None} for Seg in sorted(WaferStripsMatrix.keys())}
    
    
    #Summarize the summary so we don't overwhelm the report if there are too many bad strips:
    ConciseSummary={}
    for Seg in sorted(Summary.keys()):
        ConciseSummary[Seg]=ConciseBadChannelsDict(Summary[Seg])
    
    return RegionsProbed,Summary, ConciseSummary


#Strips Summarizer
def STRIPS_SUMMARY_HPK(TESTCOMPARISONDATA,BatchInd,Wafer):
    STRIPSDICTLIST=[]
    STRIPSDICTLIST+=[i for i in TESTCOMPARISONDATA[TestType_Manufacturing]['HistoricalTests'][BatchInd] if i['Wafer']==Wafer]
    STRIPSDICTLIST+=[i for i in TESTCOMPARISONDATA[TestType_Manufacturing]['CurrentTests'][BatchInd] if i['Wafer']==Wafer]
    
    if len(STRIPSDICTLIST)==0:
        return None
    
    STRIPSDICTLIST=list(list(zip(*sorted([(STRIPSDICTLIST[i]['Timestamp'],i,STRIPSDICTLIST[i]) for i in range(0,len(STRIPSDICTLIST))])))[2])
    Test=STRIPSDICTLIST[-1]
    
    if Test['Defects'] is None:
        return None
    ListofStrings=[j[0] for j in Test['Defects'].values() if j[0]!='none' and j[0]!='-' and j[0]!='9-9999' and '%' not in j[0]]
    if len(ListofStrings)<1:
        return None
    
    Summary={}
    for stripsstring in ListofStrings:
        for segstrip in stripsstring.split(','):
            if segstrip=='':
                continue
            
            segstrip=segstrip.strip('"').strip(' ')
            
            seg_strip=segstrip.split('-')
            if len(seg_strip)==2:
                seg=int(seg_strip[0])
                strip=int(seg_strip[1])
                
                if seg in Summary.keys():
                    Summary[seg][strip]=[]
                else:
                    Summary[seg]={strip:[]}                

    return Summary



def ConciseBadChannelsDict(BadChannelsDict):
    NewSegDict={}
    OriginalBadStripsList=sorted(BadChannelsDict.keys())

    if len(OriginalBadStripsList)>=1:
        ind_i=0
        range_i=OriginalBadStripsList[ind_i]
        ind_f=0
        range_f=OriginalBadStripsList[ind_f]

        for ind in range(1,len(OriginalBadStripsList)):
            currentstrip=OriginalBadStripsList[ind]
            #If the current strip is consecutive to previous and has same flag, add to a range
            if currentstrip==range_f+1 and str(sorted(BadChannelsDict[currentstrip]))==str(sorted(BadChannelsDict[range_f])):
                ind_f=ind
                range_f=OriginalBadStripsList[ind_f]
            #else, write out the last strip and make current strip new
            else:
                #Write out single strip if single
                if ind_f==ind_i:
                    NewSegDict[range_i]=BadChannelsDict[range_i]
                #Write out range of strips if range
                else:
                    NewSegDict[str(range_i)+'-'+str(range_f)]=BadChannelsDict[range_i]
                #make current strip new starting point
                ind_i=ind
                range_i=OriginalBadStripsList[ind_i]
                ind_f=ind
                range_f=OriginalBadStripsList[ind_f]
       #Write out last strip
        if ind_f==ind_i:
            NewSegDict[range_i]=BadChannelsDict[range_i]
        #Write out range of strips if range
        else:
            NewSegDict[str(range_i)+'-'+str(range_f)]=BadChannelsDict[range_i]

    return NewSegDict
