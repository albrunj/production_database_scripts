"""
To use:
import SENSOR_BOW_Analysis

Add more here

"""
import copy

import numpy as np
from CommonConfig import ALGORITHM_VERSION
from CommonConfig import mm
from CommonConfig import TestType_Metrology
from CommonConfig import um
from scipy.optimize import curve_fit

"""
Info
Analysis function for SENSOR_BOW test.

First we fit and subtract a plane and set the centre point to be z=0 to create new points.

From this, Maximum bow (and flag), avg bow, std bow, 

"""

def CURVE(XY,A,B,C): 
    X,Y=XY
    return A*X+B*Y+C

MaxAllowedBow_um=200

#Flatness: The sensors shall be flat (when unstressed) to within 200 μm                
#Function to analyze a metrology test file 
def Analyze_BOW(WAFERDICT):
    print('Starting Analyze_BOW for {}-W{} Seg {} file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']), str(WAFERDICT['Segment']), str(WAFERDICT['Filepath']) ))
   
    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
    NEWWAFERDICT['AlgorithmVersion'] = ALGORITHM_VERSION
    NEWWAFERDICT['popt'] = None
    NEWWAFERDICT['TABLE_Z_bow[mm]'] = []
    NEWWAFERDICT['MaxBow[um]'] = None
    NEWWAFERDICT['AvgBow[um]'] = None
    NEWWAFERDICT['StdBow[um]'] = None 
    NEWWAFERDICT['Flags'] = []
    NEWWAFERDICT['Decision']=None
    NEWWAFERDICT['norm']=None
    
    

    if WAFERDICT['TestType'] in [TestType_Metrology]:
        #Extract Data
        X=np.array(WAFERDICT['TABLE_X[mm]'])
        Y=np.array(WAFERDICT['TABLE_Y[mm]'])
        Z=np.array(WAFERDICT['TABLE_Z[mm]'])            
    else:
        print('*** {} is Not an Metrology Test!'.format(str(WAFERDICT['Filename'])))
        NEWWAFERDICT['Flags'].append('File Not an Metrology Test!')
        return NEWWAFERDICT
        
    #Check if Data exists
    if X is None or np.shape(X)==() or (X==0).all()==True:
        print('*** X[mm] is Empty!, Aborting Analyze_BOW')
        NEWWAFERDICT['Flags'].append('X[mm] is Empty!')
        return NEWWAFERDICT
    if Y is None or np.shape(Y)==() or (Y==0).all()==True:
        print('*** Y[mm] is Empty!, Aborting Analyze_BOW')
        NEWWAFERDICT['Flags'].append('Y[mm] is Empty!')
        return NEWWAFERDICT
    if Z is None or np.shape(Z)==() or (Z==0).all()==True:
        print('*** Z[mm] is Empty!, Aborting Analyze_BOW')
        NEWWAFERDICT['Flags'].append('Z[mm] is Empty!')
        return NEWWAFERDICT

    
    #Fit 2D Plane:
    try:
        popt,pcov = curve_fit(CURVE,(X,Y),Z)
    except:
        print('*** Fit Failed!, Aborting Analyze_BOW')
        NEWWAFERDICT['Flags'].append('2D Plane Fit Failed!')
        NEWWAFERDICT['Decision']='MeasErr'
        return NEWWAFERDICT
    
    NEWWAFERDICT['popt']=popt
    Plane=CURVE((X,Y),*popt)
    Z_BaselineSubtract=Z-Plane
    
    
    #Find wafer mid-point (or point closest to midpoint)
    midX=np.mean(X)
    midY=np.mean(Y)
    
    Z_BaselineSubtract=Z_BaselineSubtract-Z_BaselineSubtract[((X-midX)**2+(Y-midY)**2).argmin()]
    
    NEWWAFERDICT['TABLE_Z_bow[mm]']=[float(i) for i in Z_BaselineSubtract]
    NEWWAFERDICT['MaxBow[um]'] = mm/um*(max(Z_BaselineSubtract) -min(Z_BaselineSubtract) )
    NEWWAFERDICT['AvgBow[um]'] = mm/um*np.mean(Z_BaselineSubtract)
    NEWWAFERDICT['StdBow[um]'] = mm/um*np.std(Z_BaselineSubtract)
    
    if NEWWAFERDICT['MaxBow[um]']>MaxAllowedBow_um:
        NEWWAFERDICT['Flags'].append('MaxBow Exceeds Compliance!!')
        NEWWAFERDICT['Decision']='Fail'
        
    if NEWWAFERDICT['Decision']==None:
        NEWWAFERDICT['Decision']='Pass'
    
    print('Finished Analyze_BOW for {}-W{} Seg {} file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']), str(WAFERDICT['Segment']), str(WAFERDICT['Filepath']) ))

    return NEWWAFERDICT
