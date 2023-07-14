"""
import SENSOR_IV_Analysis

#To get a new single WAFERDICT with analysis variables, run:
NEWWAFERDICT=SENSOR_IV_Analysis.Analyze_IV(WAFERDICT)
"""
import copy
import warnings

import numpy as np
from CommonConfig import ALGORITHM_VERSION
from CommonConfig import AreaFromType
from CommonConfig import CheckHumidity
from CommonConfig import cm
from CommonConfig import GetTempNormalizedI
from CommonConfig import TestType_IV
from CommonConfig import TestType_IV_Hammamatsu
from CommonConfig import TestV


#Parameters
UpperV = 500 # For sensor to pass, I must be < Imax up until this voltage and no breakdown must be detected before then. 
StabilityV = 700 #Voltage with multiple current readings to check stability 
Imax = 100 #value current must not exceed in nA / cm^2 up until UpperV
#TestV, assigned in CommonConfig, current at this reading is printed out and recorded in the WAFERDICT, (e.g. to make histograms with) 
#Max Humidity, assigned in CommonConfig, RH that must not be exceed for whole test. 


def Analyze_IV(WAFERDICT):
    
    print('Starting Analyze_IV for {}-W{}, file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']),str(WAFERDICT['Filename']) ))
          
    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
     
    NEWWAFERDICT['AlgorithmVersion'] = ALGORITHM_VERSION
    NEWWAFERDICT['PassIV'] = None
    NEWWAFERDICT['ExceedImax'] = None #Yes/No
    NEWWAFERDICT['IDataAtTestV']= 999
    NEWWAFERDICT['MicroDischarge']= None #Yes/No
    NEWWAFERDICT['MicroDischargeV']=None
    NEWWAFERDICT['RMS_Stability[nA]'] = -1
    NEWWAFERDICT['Flags'] = []
    NEWWAFERDICT['xdata']=np.array([0])
    NEWWAFERDICT['ydata']=np.array([0])

    #Booleans to keep track of decisions (when failing does not cause a return)
    MeasErr =  False
    FailIV = False
   

    #Check if it is a IV Test
    if WAFERDICT['TestType'] in [TestType_IV,TestType_IV_Hammamatsu]:
        
        #Extract Data
        if WAFERDICT['TABLE_Current[nA]'] is not None:
            I=abs(np.array(WAFERDICT['TABLE_Current[nA]']))
            #Temp Workaround for units issue:
            if WAFERDICT['TestType']==TestType_IV_Hammamatsu:
                I=I/1e-9 #convert from A to nA
        else: 
            print('*** I is Empty, exiting!')
            NEWWAFERDICT['Flags'].append('I is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT  
        
        if WAFERDICT['TABLE_Voltage[V]'] is not None:
            V=abs(np.array(WAFERDICT['TABLE_Voltage[V]']))
        else: 
            print('*** V is Empty, exiting!')
            NEWWAFERDICT['Flags'].append('V is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT      
       
        if WAFERDICT['Temperature[°C]'] is not None:
            Temp=WAFERDICT['Temperature[°C]']
        else: 
            print('*** Temperature is Empty, exiting!')
            NEWWAFERDICT['Flags'].append('Temperature is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT      

        #Check if Data exists
        if I is None or np.shape(I)==() or all(I==0)==True:
            print('*** I is Empty, exiting!')
            NEWWAFERDICT['Flags'].append('I is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT   
        if V is None or np.shape(V)==() or all(V==0)==True:
            print('*** V is Empty, exiting!')
            NEWWAFERDICT['Flags'].append('V is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT       
        
        #Make measurements of 0 equal be None
        I[I==0]=None
    
    else:
        print('*** {} is Not an IV Test!'.format(str(WAFERDICT['Filename'])))
        NEWWAFERDICT['Flags'].append('File Not an IV Test!')
        return NEWWAFERDICT
    
    #Check Humidity is acceptable
    HumidityFlag=CheckHumidity(WAFERDICT)
    if HumidityFlag is not None:
        NEWWAFERDICT['Flags'].append(HumidityFlag)
        MeasErr = True
        
        
    #Define Data for analysis 

    #Get area of the sensor
    AThing=AreaFromType(WAFERDICT['Type'])
    Area=AThing[1]
    if AThing[0] == False:
        MeasErr = True
        NEWWAFERDICT['Flags'].append('Could not find area for type {0}. Using default area: {1} m^2'.format(str(WAFERDICT['Type']),str(Area)))
    Area = Area * (cm)**-2 #Convert to cm^2

    xdata = abs(V) 
    ydata_NotNorm = abs(I) / Area  #Current in nA / cm^2 (not temperature normalized)

    #Remove NaN points 
    idx = np.isfinite(xdata) & np.isfinite(ydata_NotNorm) 
    xdata=xdata[idx]
    ydata_NotNorm=ydata_NotNorm[idx]

    #Ensure data is sorted properly
    order=np.argsort(xdata)
    xdata=xdata[order]
    ydata_NotNorm=ydata_NotNorm[order]

    #Get Temperature Normalized Current
    try:
        ydata = GetTempNormalizedI(ydata_NotNorm, np.full_like(ydata_NotNorm, Temp))
    except: 
        print("Error Normalizing temperature, exiting!") 
        NEWWAFERDICT['Flags'].append("Error Normalizing temperature")
        return NEWWAFERDICT

    #Check max current is not exceeded below UpperV
    IbelowUpperV = ydata[xdata <= UpperV]
    if (IbelowUpperV <= Imax).sum() == IbelowUpperV.size :
        ExceedImax = False 
        NEWWAFERDICT['ExceedImax']='No' #needed?
        print ('Current does not exceed limit of {:.0f} nA/cm^2 below {:.0f} V'.format(Imax, UpperV))
    else: 
        ExceedImax = True 
        NEWWAFERDICT['ExceedImax']='Yes' #needed?
        NEWWAFERDICT['Flags'].append('Current exceeds limit of {:.0f} nA/cm^2 below {:.0f} V!'.format(Imax, UpperV))
        FailIV = True
        print ('Current exceeds limit of {:.0f} nA/cm^2 below {:.0f} V!'.format(Imax, UpperV))
    
    #Check if current is measured up to UpperV
    #TODO: More strict requirement? I.e. specifiy how many measurements? Intervals?
    if UpperV not in xdata and not ExceedImax:
        print ('WARNING: Current was not measured at upper voltage limit ({}V), assigning MeasErr'.format(UpperV))
        NEWWAFERDICT['Flags'].append('Current not measured at ({} V)'.format(UpperV))
        MeasErr = True
    
    #Extract Current at TestV for histogram
    if TestV in xdata:
        jTest = np.where(xdata == TestV)[0][0] #gets index of TestV 
        IDataAtTestV = ydata[jTest]
        NEWWAFERDICT['IDataAtTestV']=IDataAtTestV
        print ('Measured Current at {} V = {:.1f} nA / cm^2'.format(TestV, IDataAtTestV))
    else: 
        print ('Current was not measured at Test Voltage {} V'.format(TestV))
        NEWWAFERDICT['Flags'].append('Current not measured at ({}V)'.format(TestV))
    
    #Write out to NEWWAFERDICT
    NEWWAFERDICT['xdata']=xdata
    NEWWAFERDICT['ydata']=ydata
        
    #Check for micro-discharge in non-normalized current, removing duplicate Voltage entries (e.g. for stability measurements)
    UniqueVs, UniqueIndices = np.unique(xdata, return_index=True)
    MicroDischargeV = LocateMicroDischarge(ydata_NotNorm[UniqueIndices], UniqueVs)
    if MicroDischargeV < np.max(xdata):
        NEWWAFERDICT['MicroDischarge']='Yes'
        print ('Micro-discharge detected starting at {:.0f} V'.format(MicroDischargeV))
        #Determine if micro-discharge occurs before UpperV 
        if MicroDischargeV < UpperV:
            FailIV = True
            NEWWAFERDICT['Flags'].append('micro-discharge occurs before {}V'.format(UpperV))
    else: 
        print ('No micro-discharge detected')
        MicroDischargeV = max(xdata)
    NEWWAFERDICT['MicroDischargeV']=MicroDischargeV
    
    #Check current stability if recorded
    IStability = abs(I[abs(V)==StabilityV])
    if np.size(IStability) > 1: #Maybe make == 4?
        IVariation = abs(np.std(IStability)/np.mean(IStability))
        NEWWAFERDICT['RMS_Stability[nA]'] = IVariation
        print ('RMS_Stability[nA] = {}'.format(NEWWAFERDICT['RMS_Stability[nA]']))
   
    #Assign pass / fail
    if MeasErr or FailIV:
        NEWWAFERDICT['PassIV'] = 'No'
        #MeasErr before Fail
        if MeasErr: 
            NEWWAFERDICT['Decision']='MeasErr'
        else:
            NEWWAFERDICT['Decision']='Fail'
    else: 
        NEWWAFERDICT['PassIV']='Yes'
        NEWWAFERDICT['Decision']='Pass'
    
    print ("Decision = {}".format(NEWWAFERDICT['Decision']))
    
    print ('Finished Analyze_IV for {}-W{}, file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']),str(WAFERDICT['Filename']) ))
    
    return NEWWAFERDICT    


def LocateMicroDischarge(I, V, 
        sm_window=2, 
        bd_limit=5.5,
        allow_running_bd=True,
        use_additional_cond=False,
        tolerence = 0.05,
        voltage_span=4,
        fit_window=5): 
    """
    Function for BDV estimation - if questions please contact Vera Latonova (vera.latonova@cern.ch).
    I,V must have same shape and voltages must be in ascending order,
    same indexes of I&V arrays must correspond each other,
    only invalid data or holdstep should be stripped before 
    but it is not necessary. Measurments U=0&I=0 are removed.
    If there is same or higher amount of same voltages in row than
    sm_window, from this sequence we cannot estimete dI/dV and
    we have to remove this averaged point.

    It is assumed that only parameter use_additional_cond would be 
    changed by caller. Changing of other parameters may affect
    BDV unexpectedly.


    @param[in] I                   - array of currents without any cut
    @param[in] V                   - array of voltages, ascending order, without any cut
    @param[in] sm_window           - size of smoothing window
    @param[in] bd_limit            - BD limit for |U| < 500V
    @param[in] allow_running_bd    - allow increase bd_limit for |U| > 500
    @param[in] use_additional_cond - use additional BD contition
    @param[in] tolerence           - configuration of additional condition
    @param[in] voltage_span        - max width of hump on spectra which may be neglected 
                                     in voltage steps in additional contition
    @param[in] fit_window          - number of points used for linear fit before BD voltage

    @return BD voltage (always positive) or NO_BD_CONST = 9.99e99 if not found.
    """
    NO_BD_CONST = 9.99e99

    # add nan to the end of array 
    V = np.abs( V )
    I = np.abs( I )

    # skip zeros
    ind = np.where(np.logical_or( I!=0, V!=0 ))
    V = V[ind]
    I = I[ind]

    V_ = np.append(V, np.nan*np.ones(sm_window-1))
    I_ = np.append(I, np.nan*np.ones(sm_window-1))

    # make 2D array of I's, V's each row_ind shifted by row_ind index
    # i.e from array [1,3,5] we make (for sm_window=2) 2D array 
    # [  1,3,5,nan]
    # [nan,5,1,3]
    # than get average from each column -> I_avg, V_avg
    r = np.arange( sm_window )

    V2 = np.outer( np.ones( sm_window ), V_)
    row_ind, col_ind = np.ogrid[:V2.shape[0], :V2.shape[1]]
    col_ind = col_ind - r[:, np.newaxis]
    V2 = V2[row_ind, col_ind]
    # strip fields with nans
    V2 = np.transpose(  V2[:,(sm_window-1):-(sm_window-1)] )

    I2 = np.outer( np.ones( sm_window ), I_)
    row_ind, col_ind = np.ogrid[:I2.shape[0], :I2.shape[1]]
    col_ind = col_ind - r[:, np.newaxis]
    I2 = I2[row_ind, col_ind]
    I2 = np.transpose(  I2[:,(sm_window-1):-(sm_window-1)] )

    # get V & I averages
    try:
        V_avg = np.average( V2,axis=1 )
        I_avg = np.average( I2,axis=1 )
    except ZeroDivisionError:
        # not enough data
        return NO_BD_CONST

    # find dI / dV array
    # I'm not able to write this without cycle
    dIdV = np.array([])
    for i in range(V2.shape[0]):
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                dIdV = np.append(dIdV, np.polyfit( V2[i,:], I2[i,:], 1 )[0] )
            except( np.RankWarning, TypeError):
                dIdV = np.append( dIdV, np.nan )

    # stripping U[n] == U[n+1] (i.e. hodlsetp) => fit cannot be sucessful =>
    # dIdV is nan @holdstep
    ind = np.where(np.isfinite(dIdV))
    I_avg = I_avg[ind]
    V_avg = V_avg[ind]
    dIdV  = dIdV [ind]

    #get running BDV limit & compare
    bd_limit_running = bd_limit + np.where( allow_running_bd and V_avg > 500, (V_avg-500.)/100., 0)
    V_avg_BD_ind = dIdV / (I_avg / V_avg ) > bd_limit_running 
    V_avg_BD = V_avg[ V_avg_BD_ind ]

    # Estimate BDV
    BDV = np.array([])
    
    # no break-down 
    if V_avg_BD.shape == (0,):
        return NO_BD_CONST

    # if V_avg_BD_ind[0] == True ... BDV <- V[0]
    # for others V_avg_BD_ind[n] == True BDV <- (V_avg[n] + V_avg[n-1])/2
    if V_avg_BD_ind[0]:
        BDV = np.append(BDV, V[0] )
    V_avg_BD_ind[0] = False

    BDV = np.append( BDV, 
            (V_avg[ np.where(V_avg_BD_ind) ] + 
                V_avg[ np.where(V_avg_BD_ind)[0]-1 ])/2. )

    ###########################################################################
    ## Application of additional condition ####################################
    ###########################################################################
    if not use_additional_cond:
        return BDV[0];

    # get index if V <= BDV
    B = np.where( np.less.outer( BDV, V ))
    col_ind = np.mgrid[:BDV.shape[0],:V.shape[0]][1]
    col_ind[B[0],B[1]] = 0
    V_BDV_ind = np.max(col_ind,axis=1) 

    back_ok_v_ind = 0
    while True:
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                a, b = np.polyfit( V[max(back_ok_v_ind,V_BDV_ind[0]-fit_window):max(back_ok_v_ind,V_BDV_ind[0])], 
                                   I[max(back_ok_v_ind,V_BDV_ind[0]-fit_window):max(back_ok_v_ind,V_BDV_ind[0])],
                                   1) 
            except( np.RankWarning, TypeError):
                return BDV[0]

        ind = np.where(1 - (a*V + b) / I <= tolerence)[0]
        try:
            back_ok_v_ind = np.min(ind[ind > V_BDV_ind[0]+1])
        except ValueError:
            # sensor is not going back 
            return BDV[0]
        # hump is too long -- it cannot be skipped
        if back_ok_v_ind - V_BDV_ind[0] > voltage_span:
            return BDV[0]

        # skip BDVs inside hump
        ind = BDV>=V[back_ok_v_ind]
        BDV = BDV[ind]
        V_BDV_ind = V_BDV_ind[ind]
        if V_avg_BD.shape == (0,):
            return NO_BD_CONST
    return NO_BD_CONST
