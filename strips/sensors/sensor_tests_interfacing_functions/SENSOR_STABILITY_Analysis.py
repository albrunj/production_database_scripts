import copy

import numpy as np
from CommonConfig import ALGORITHM_VERSION
from CommonConfig import GetTempNormalizedI
from CommonConfig import TestType_Stability
from scipy.interpolate import interp1d
#Test Parameters
MaxIVariation = 0.15 #Max fractional variation in current 
TestStartTime = 0 #hrs, Current measurements before this time are not included in Ivariation calculation 
MinTestTime = 24 #hrs, Duration of the test after start time for which Ivariation is calculated
MaxHumidity = 20 # %, for Entire test
NtoRemove = 0 #Number of max and min points to remove in current (e.g. NtoRemove = 2 removes the two largest and two smallest values). This is so random points don't skew the variation measuerment. 



def Analyze_STABILITY(WAFERDICT):
    
    print('Starting Analyze_STABILITY for {}-W{} from file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']), str(WAFERDICT['Filepath']) ))
   
    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
    NEWWAFERDICT['xdata']=np.array([0])
    NEWWAFERDICT['ydata']=np.array([0])
    NEWWAFERDICT['Decision']=None
    NEWWAFERDICT['Flags'] = []
    NEWWAFERDICT['CurrentOrShuntV'] = None
    NEWWAFERDICT['AlgorithmVersion'] = ALGORITHM_VERSION 
    NEWWAFERDICT['AbsILeakAvg[nA]']=None
    NEWWAFERDICT['ILeakVariation']=None
    NEWWAFERDICT['Plot_Current'] = np.array([0])
    NEWWAFERDICT['Plot_NormalisedCurrent'] = np.array([0])
    NEWWAFERDICT['Plot_Time'] = np.array([0])
    NEWWAFERDICT['INTERP_TABLE_Current[nA]']=np.array([0])
    NEWWAFERDICT['INTERP_TABLE_Humidity[%]']=np.array([0])
    NEWWAFERDICT['INTERP_TABLE_Temperature[°C]']=np.array([0])
    NEWWAFERDICT['INTERP_TABLE_COMPCurrent[nA]']=np.array([0])

    #Check if test is STABILITY
    if WAFERDICT['TestType'] in [TestType_Stability]:
        
        #Extract Data
        Time=np.array(WAFERDICT['TABLE_Time[s]'])
        Temp=np.array(WAFERDICT['TABLE_Temperature[°C]'])
        Humidity=np.array(WAFERDICT['TABLE_Humidity[%]'])
        Current = np.array(WAFERDICT['TABLE_Current[nA]'])
        ShuntV = np.array(WAFERDICT['TABLE_Shunt_voltage[mV]'])
    
    else:
        print ('Error File {} not a Stability Test, Aborting Analyze_STABILITY'.format(str(WAFERDICT['Filepath'])))
        return NEWWAFERDICT
        
    #Check if Data exists
    if Time is None or np.shape(Time)==() or all(Time==0)==True:
        print('*** Time is Empty!, Aborting Analyze_STABILITY')
        NEWWAFERDICT['Flags'].append('Time is Empty!')
        return NEWWAFERDICT
    if Temp is None or np.shape(Temp)==() or all(Temp==0)==True:
        print('*** Temp is Empty!, Aborting Analyze_STABILITY')
        NEWWAFERDICT['Flags'].append('Temp is Empty!')
        return NEWWAFERDICT   
    if Humidity is None or np.shape(Humidity)==() or all(Humidity==0)==True:
        print('*** Humidity is Empty!, Aborting Analyze_STABILITY')
        NEWWAFERDICT['Flags'].append('Humidity is Empty!')
        return NEWWAFERDICT
    
    #Check Current or ShuntV are valid (if both, uses Current)
    if Current is None or np.shape(Current)==() or all(Current==0)==True:
        if ShuntV is None or np.shape(ShuntV)==() or all(ShuntV==0)==True:
            print('*** Current & ShuntV are Empty!, Aborting Analyze_STABILITY')
            NEWWAFERDICT['Flags'].append('Current and ShuntV are Empty!')
            return NEWWAFERDICT
        else:
            Current = ShuntV
            NEWWAFERDICT['CurrentOrShuntV'] = 'ShuntV'
    else:
        NEWWAFERDICT['CurrentOrShuntV'] = 'Current'
    

    #Get I normalized to T
    normI = GetTempNormalizedI(Current, Temp)
    

    #Check Test lasts up to MinTestTime (non-zero / None values up until this time)
    if np.max(Time)-TestStartTime*3600 < MinTestTime * 3600:
        NEWWAFERDICT['Decision'] = 'MeasErr'
        NEWWAFERDICT['Flags'].append('Test not carried out for minimum of {} hr(s) (past the first {} hr(s)'.format(MinTestTime, TestStartTime))
    else:
        #Check Current has been recorded at one of previous two readings before TestStartTime + MinTestTime
        TestIdx = np.searchsorted(Time, (TestStartTime+MinTestTime) *3600, side="left")
        LastIs = np.array([normI[TestIdx-1], normI[TestIdx]])
        LastIsIdx = LastIs != np.array(None)
        LastIs = LastIs[LastIsIdx]
        LastIs = LastIs[np.isfinite(LastIs)]
        LastIs = LastIs[np.nonzero(LastIs)]
        if not any(LastIs):
            NEWWAFERDICT['Decision'] = 'MeasErr'
            NEWWAFERDICT['Flags'].append('Current not recorded for {} hrs (past the first {} hr(s))'.format(MinTestTime, TestStartTime))
    
        
    #Check Humidity from TestStartTime does not exceed MaxHumidity for MinTestTime
    Hidx = Humidity != np.array(None)
    TestHumidity = Humidity[Hidx]
    HumidityTime = Time[Hidx]
    TestHumidity = TestHumidity[(TestStartTime*3600 <= HumidityTime) & (HumidityTime <= (TestStartTime+MinTestTime)*3600)]
    if (TestHumidity <= MaxHumidity).sum() != TestHumidity.size:
        NEWWAFERDICT['Decision'] = 'MeasErr'
        NEWWAFERDICT['Flags'].append('Humidity exceeds {}% during first {} hrs'.format(MaxHumidity, MinTestTime))
    
    
    #Check max variation of current is not more than 15% up to MinTestTime
    #TestTime = Time[(TestStartTime*3600 <= Time) & (Time<= (TestStartTime+MinTestTime)*3600)] 
    VarTestI = normI[(TestStartTime*3600 <= Time) & (Time <= (TestStartTime+MinTestTime)*3600)]
    
    Iidx = VarTestI != np.array(None)
    VarTestI = VarTestI[Iidx]
    VarTestI = VarTestI[np.isfinite(VarTestI)]
    VarTestI = VarTestI[np.nonzero(VarTestI)]
    VarTestI = RemoveNMaxAndMin(NtoRemove, VarTestI)

    if VarTestI.size == 0: 
        print('No current readings between {} and {} hrs! Cannot calculate I variation'.format(TestStartTime, TestStartTime +MinTestTime))
        NEWWAFERDICT['Flags'].append('No current readings in Current Variation time range')

    
    #IVariation = abs((np.max(VarTestI) - np.min (VarTestI)) / np.average(VarTestI)) #Range / average, = 0 for no variation
    #IVariation = abs(np.sqrt(np.mean(VarTestI**2)) / np.mean(VarTestI)) # RMS/mean, = 1 for no variation
    IVariation = abs(np.std(VarTestI)/np.mean(VarTestI)) #Standard deviation over mean, = 0 for no variation
    AbsILeakAv = abs(np.mean(VarTestI))
    print ("AbsILeakAv = {0:.1f} nA".format(AbsILeakAv))

    if IVariation is not None and not np.isnan(IVariation):
        print('Current Variation = {:.1f}%'.format(IVariation*100))
    else:
        print('Error Calculating Current Variation')
        NEWWAFERDICT['Flags'].append('Error Calculating Current Variation')
    
    if IVariation > MaxIVariation:
        NEWWAFERDICT['Decision'] = 'Fail'
        NEWWAFERDICT['Flags'].append('Leakage Current varies by more than {}%'.format(MaxIVariation*100))
     
        
    #Get x and y data for current
    xdata, ydata = PrepareForPlotting(Time, abs(normI))
    Plot_current = abs(PrepareForPlotting(Time, Current)[1])

    #Write out to NEWWAFERDICT
    NEWWAFERDICT['xdata'] = xdata
    NEWWAFERDICT['ydata'] = ydata
    NEWWAFERDICT['Plot_Current'] = Plot_current
    NEWWAFERDICT['Plot_NormalisedCurrent'] = ydata
    NEWWAFERDICT['Plot_Time'] = xdata

    #Select data for correlation plots
    CorrTime = xdata[-1] #Only plot up until current readings stop
    
    #Write out interpolated
    NEWWAFERDICT['INTERP_TABLE_Current[nA]']=abs(Interpolate(Time[Time <= CorrTime], Current[Time <= CorrTime]))
    NEWWAFERDICT['INTERP_TABLE_Humidity[%]']=Interpolate(Time[Time <= CorrTime],Humidity[Time <= CorrTime])
    NEWWAFERDICT['INTERP_TABLE_Temperature[°C]']=Interpolate(Time[Time <= CorrTime],Temp[Time <= CorrTime])
    NEWWAFERDICT['INTERP_TABLE_COMPCurrent[nA]']= abs(Interpolate(Time[Time <= CorrTime],normI[Time <= CorrTime]))
    
    NEWWAFERDICT['AbsILeakAvg[nA]'] = AbsILeakAv
    NEWWAFERDICT['ILeakVariation'] = IVariation
    
    if NEWWAFERDICT['Decision']==None:
        NEWWAFERDICT['Decision']='Pass'
        print('Sensor Passed Stability')
    else:
        print ('Sensor Failed Stability')
        print ('Flags:')
        for entry in NEWWAFERDICT['Flags']:
            print (entry)
        del entry 

    print('Finished Analyze_STABILITY for {}-W{} from file {}\n'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']), str(WAFERDICT['Filepath']) ))
        
    
    return NEWWAFERDICT
        

def RemoveNMaxAndMin(N, Iarray):
    """ Removes N max and N min values of Iarray"""
    i = 0
    while i < N: 
        Mask = np.logical_and(Iarray != max(Iarray), Iarray != min(Iarray))
        Iarray = Iarray[Mask]
        i += 1
    return Iarray
    
    
def PrepareForPlotting(xdata, ydata):
    """Remove entries None, NaN and 0"""
    #Remove None
    idx = ydata != np.array(None)
    xdata = np.array(xdata[idx], dtype = float)
    ydata = np.array(ydata[idx], dtype = float)
    #Remove NaN points
    idx = np.isfinite(xdata) & np.isfinite(ydata)
    xdata = xdata[idx]
    ydata = ydata[idx]
    #Remove entries where current is zero
    idx = np.nonzero(ydata)
    xdata = xdata[idx]
    ydata = ydata[idx]

    return xdata, ydata

   
def Interpolate(time, thing):
    thing=thing.copy()
    if thing[0]==None:
        thing[0]=thing[thing!=None][0]
    func= interp1d(time[thing!=None], thing[thing!=None], kind='cubic', fill_value="extrapolate")
    interpthing=func(time)
    return interpthing
