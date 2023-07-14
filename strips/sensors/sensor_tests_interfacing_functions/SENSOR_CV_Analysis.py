"""
import SENSOR_CV_Analysis

#To get a new single WAFERDICT with analysis stuff filled in like fit, Vdep, decision, etc., run:
NEWWAFERDICT=SENSOR_CV_Analysis.Analyze_CV(WAFERDICT)

#

"""
#The Tech Specs has the following criteria:
#1) Active Thickness > 270 um [pg 16]
#2) Initial Depl Voltage V_fd < 350 V [pg 18]
#Futhermore, if the fit doesn't work and the humidity is off this will be noted
import copy

import numpy as np
from CommonConfig import ALGORITHM_VERSION
from CommonConfig import AreaFromType
from CommonConfig import CheckHumidity
from CommonConfig import cm
from CommonConfig import colorlistonoff
from CommonConfig import colorlistonoffuseful
from CommonConfig import e
from CommonConfig import eps0
from CommonConfig import epsr
from CommonConfig import errprint
from CommonConfig import fitnpoints
from CommonConfig import GoodChars
from CommonConfig import norprint
from CommonConfig import pF
from CommonConfig import TestType_CV
from CommonConfig import um
from scipy.optimize import curve_fit

alternateCVnames=[TestType_CV]

#Define fitting function
heav=lambda x,f: (x>=f)
iheav=lambda x,f: (x<f)
CURVE = lambda x,a,f,d,w,b: -np.sqrt(abs(w**2+(x-f)**2*(a**2*iheav(x,f)-heav(x,f)*b**2)))+d+w
#CURVE = lambda x,a,f,d,w,b: (x-f)*(a*iheav(x,f)+heav(x,f)*b)+d
#[1,1000,5,1000,1e-4]
ub_f=1000 #upper bound for f
ub_d=5 #upper bound for d (normalized by mean!)
ub_a=1 #upper bound for a
ub_w=1000 #upper bound for w
ub_b=5e-3 #upper bound for b 1e-2?
#the point of inflection is at (x,y)=(f,d)
#b is the slope of the flat line
#a is the slope of the initial slope
#w is a parameter for how smooth the transition is
#Note that the functions are normalized before fitting to ensure more consistent fitting

#More stable fitting function
L=lambda x,a,f,d: a*x+d-a*f  
R=lambda x,b,f,d: b*x+d-b*f  
M=lambda x,A,B,C: A*x*x+B*x+C 
heav=lambda x,x0: 1*(x>=x0)
def CURVE(x,a,f,d,w,b):
    A=(b-a)/(4*w)
    B=(a+b-4*A*f)/2
    C=a*(f-w)+d-a*f-A*(f-w)*(f-w)-B*(f-w)
    return (1-heav(x,f-w))*L(x,a,f,d)+(heav(x,f-w)-heav(x,f+w))*M(x,A,B,C)+(heav(x,f+w)-0)*R(x,b,f,d)
ub_w=100



#Other Parameters
lowerboundV=50 #Ignore fitting any V under this
Rgoodfit=1e-3 #Threshold of R in a normalized curve for a good fit
Cbad=1e6 #Any C above this is an obvious bad measurement


def CompareBatchesCV(NEWLISTTESTDICTLIST,OLDLISTTESTDICTLIST,TITLESLIST):


    counter=1
    colorkeylist=list(colorlistonoff.keys())
    filenamehtmllist=[]


    ANALYZEDNEWLISTTESTDICTLIST=[]
    ANALYZEDOLDLISTTESTDICTLIST=[]

    for compareind in range(0,len(TITLESLIST)):
        """
        #For Plotting:
        plt.figure()
        """

        NEWCOMPTESTDICTLIST=NEWLISTTESTDICTLIST[compareind]
        OLDCOMPTESTDICTLIST=OLDLISTTESTDICTLIST[compareind]
        title=TITLESLIST[compareind]

        ANALYZEDNEWCOMPTESTDICTLIST=[]
        ANALYZEDOLDCOMPTESTDICTLIST=[]

        xdatalist=[]
        ydatalist=[]
        xfitlist=[]
        yfitlist=[]
        nameslist=[]
        colorofflist=[]
        coloronlist=[]


        for WAFERDICT in NEWCOMPTESTDICTLIST:
            ANALYZEDWAFERDICT=Analyze_CV(WAFERDICT)
            ANALYZEDNEWCOMPTESTDICTLIST.append(ANALYZEDWAFERDICT)

            xdatalist.append(ANALYZEDWAFERDICT['xdata'])
            ydatalist.append(ANALYZEDWAFERDICT['ydata'])
            xfitlist.append(ANALYZEDWAFERDICT['xfit'])
            yfitlist.append(ANALYZEDWAFERDICT['yfit'])

            
            name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16]+' ['+str(counter)+']')
            modifiednameslist=[i.split('(')[0] for i in nameslist]
            if name in modifiednameslist:
                nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
            else:
                nameslist.append(name)
            counter+=1

            colorkey='Current'+str(ANALYZEDWAFERDICT['Decision'])

            if colorkey in colorkeylist:
                coloronlist.append(colorlistonoffuseful[colorkey][0])
                colorofflist.append(colorlistonoffuseful[colorkey][1])
            else:
                coloronlist.append(colorlistonoffuseful['CurrentUnknown'][0])
                colorofflist.append(colorlistonoffuseful['CurrentUnknown'][1])

            """
            #Plotting:    
            xdata=ANALYZEDWAFERDICT['xdata']
            ydata=ANALYZEDWAFERDICT['ydata']
            norm=ANALYZEDWAFERDICT['norm']
            popt=ANALYZEDWAFERDICT['popt']
            plt.plot(xdata,ydata/norm,'x',label=str(WAFERDICT['Wafer']), markeredgewidth=linewidth)
            plt.plot(popt[1]*np.array([1,1]),np.array([0,1.1*max(ydata)/norm]), linewidth=linewidth)
            plt.plot(xdata,CURVE(xdata,*popt),'-', linewidth=linewidth) 
            """

        for WAFERDICT in OLDCOMPTESTDICTLIST:
            ANALYZEDWAFERDICT=Analyze_CV(WAFERDICT)
            ANALYZEDOLDCOMPTESTDICTLIST.append(ANALYZEDWAFERDICT)

            xdatalist.append(ANALYZEDWAFERDICT['xdata'])
            ydatalist.append(ANALYZEDWAFERDICT['ydata'])
            xfitlist.append(ANALYZEDWAFERDICT['xfit'])
            yfitlist.append(ANALYZEDWAFERDICT['yfit'])

            name='W'+str(ANALYZEDWAFERDICT['Wafer'])+' '+str(ANALYZEDWAFERDICT['Timestamp'][0:16])
            modifiednameslist=[i.split('(')[0] for i in nameslist]
            if name in modifiednameslist:
                nameslist.append(name+'('+str(modifiednameslist.count(name)+1)+')')
            else:
                nameslist.append(name)

            colorkey='Past'+str(ANALYZEDWAFERDICT['Decision'])

            if colorkey in colorkeylist:
                coloronlist.append(colorlistonoffuseful[colorkey][0])
                colorofflist.append(colorlistonoffuseful[colorkey][1])
            else:
                coloronlist.append(colorlistonoffuseful['PastUnknown'][0])
                colorofflist.append(colorlistonoffuseful['PastUnknown'][1])

            """
            #Plotting:    
            xdata=ANALYZEDWAFERDICT['xdata']
            ydata=ANALYZEDWAFERDICT['ydata']
            norm=ANALYZEDWAFERDICT['norm']
            popt=ANALYZEDWAFERDICT['popt']
            plt.plot(xdata,ydata/norm,'x',label=str(WAFERDICT['Wafer']), markeredgewidth=linewidth)
            plt.plot(popt[1]*np.array([1,1]),np.array([0,1.1*max(ydata)/norm]), linewidth=linewidth)
            plt.plot(xdata,CURVE(xdata,*popt),'-', linewidth=linewidth) 
            """

        filenamehtml=''
        identifier=''
        for i in title:
            if i in GoodChars:
                filenamehtml+=i
            if i in GoodChars[:-1]:
                identifier+=i
                


        
        #Sort lists by names
        if len(nameslist)>1:
            nameslist,xdatalist,ydatalist,xfitlist,yfitlist,colorofflist,coloronlist= [list(i) for i in zip(*sorted(zip(nameslist,xdatalist,ydatalist,xfitlist,yfitlist,colorofflist,coloronlist)))]

        #DataToPlotly.DataToPlotly(tmpplotsfolder,filenamehtml,xdatalist,ydatalist,xfitlist,yfitlist,nameslist,colorofflist,coloronlist,title,'Voltage [V]','Capacitance [Normalized by Curve Area]',identifier)
        #filenamehtmllist.append(filenamehtml+'.html')

        """
        #Plotting
        plt.title(title)
        plt.legend(loc='upper center',bbox_to_anchor=(1, 1))
        #plt.tight_layout(pad=7)
        plt.show()
        """

        ANALYZEDNEWLISTTESTDICTLIST.append(ANALYZEDNEWCOMPTESTDICTLIST)
        ANALYZEDOLDLISTTESTDICTLIST.append(ANALYZEDOLDCOMPTESTDICTLIST)

    return ANALYZEDNEWLISTTESTDICTLIST,ANALYZEDOLDLISTTESTDICTLIST, filenamehtmllist


def Analyze_CV(WAFERDICT):
    
    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
    
    NEWWAFERDICT['popt']=None
    NEWWAFERDICT['R']=None
    NEWWAFERDICT['Flags']=[]
    NEWWAFERDICT['Vdep[V]']=None
    NEWWAFERDICT['Neff[1e12/cm^3]']=None
    NEWWAFERDICT['Dfull[um]']=None
    NEWWAFERDICT['xdata']=np.array([0])
    NEWWAFERDICT['ydata']=np.array([0])
    NEWWAFERDICT['norm']=1
    NEWWAFERDICT['xfit']=np.array([0])
    NEWWAFERDICT['yfit']=np.array([0])
    NEWWAFERDICT['AlgorithmVersion']=ALGORITHM_VERSION
    NEWWAFERDICT['Decision']=None
    
    #Check if it is a CV Test
    if WAFERDICT['TestType'] in alternateCVnames:
        
        #Extract Data
        V=np.array(WAFERDICT['TABLE_Voltage[V]'])
        C=np.array(WAFERDICT['TABLE_Capacitance[pF]'])
        
        #Check if Data exists
        if np.shape(C)==() or all(C==0)==True:
            errprint('C is Empty!',WAFERDICT['Filename'])
            NEWWAFERDICT['Flags'].append('C is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT   
        if np.shape(V)==() or all(V==0)==True:
            errprint('V is Empty!',WAFERDICT['Filename'])
            NEWWAFERDICT['Flags'].append('V is Empty!')
            NEWWAFERDICT['Decision']='MeasErr'
            return NEWWAFERDICT       
        #Remove bad measurements
        C[C>Cbad]=None 
        C[C==0]=None
    else:
        errprint('Not a CV Test!',WAFERDICT['Filename'])
        NEWWAFERDICT['Flags'].append('Not a CV Test!')
        return NEWWAFERDICT
        
    print('')
    print('')
    norprint('Analyzing: '+str(WAFERDICT['Filename'])+': '+str(WAFERDICT['Batch'])+': '+str(WAFERDICT['Wafer']))
    
    #Define data for fit 
    xdata=abs(V)
    ydata=1/C**2
    
    #Remove NaN points
    idx = np.isfinite(xdata) & np.isfinite(ydata) 
    xdata=xdata[idx]
    ydata=ydata[idx]
    
    #Ensure data is sorted properly
    order=np.argsort(xdata)
    xdata=xdata[order]
    ydata=ydata[order]
    
    #Normalize data for better fitting
    norm=np.mean(ydata)
    
    #Cut out low noisy V
    firstgoodV=np.argmax(xdata>=lowerboundV)
    
    if firstgoodV==0 and xdata[0]<lowerboundV:
        errprint('There is no data above lowerboundV. Trying to fit with all data. Max V in data is ',str(max(xdata)))
        NEWWAFERDICT['Flags'].append('No Data Above LowerBoundV')
        NEWWAFERDICT['Decision']='MeasErr'

    NEWWAFERDICT['xdata']=xdata
    NEWWAFERDICT['ydata']=ydata
    NEWWAFERDICT['norm']=norm
    
    #Try fit:
    try:
        #Fit
        popt,pcov = curve_fit(CURVE,xdata[firstgoodV:],ydata[firstgoodV:]/norm, bounds=([0,0,0,0,0],[ub_a, ub_f, ub_d, ub_w, ub_b]))
        R=sum((CURVE(xdata,*popt)-ydata/norm)**2/len(xdata[firstgoodV:]))
    except:
        # Fit failed
        errprint('WARNING: FIT FAILED!','')
        NEWWAFERDICT['Flags'].append('FIT FAILED!')
        NEWWAFERDICT['Decision']='Fail'
        return NEWWAFERDICT
        
        
    #Get parameters ready for Neff and Dfull extraction
    AThing=AreaFromType(WAFERDICT['Type'])
    A=AThing[1]
    if AThing[0] == False:
        NEWWAFERDICT['Decision']='MeasErr'
        NEWWAFERDICT['Flags'].append('Could not find area for type {0}. Using default area: {1} m^2'.format(str(WAFERDICT['Type']),str(A)))
    Vdep=popt[1]
        
    #Via Plateau: (Optional with above)
    plateau=popt[2]*norm
    plateau=plateau/pF/pF
    (Neff,Dfull)=extractNeffDfullPlateau(A,Vdep,plateau)
    print('plateau Neff,Dfull=',Neff,Dfull)
    
    #Via Slope: (Optional with below)
    slope=popt[0]*norm
    slope=slope/pF/pF
    (Neff,Dfull)=extractNeffDfullSlope(A,Vdep,slope)
    print('slope Neff,Dfull=',Neff,Dfull)
        
    
    #Create fitxdata and fitydata for plotting
    xfit=np.linspace(xdata[0],xdata[-1],fitnpoints)
    yfit=CURVE(xfit,*popt)*norm
    

    #Write out to NEWWAFERDICT
    NEWWAFERDICT['popt']=popt
    NEWWAFERDICT['R']=R
    NEWWAFERDICT['Vdep[V]']=Vdep   
    NEWWAFERDICT['Neff[1e12/cm^3]']=Neff/1e12*cm**3
    NEWWAFERDICT['Dfull[um]']=Dfull/um
    NEWWAFERDICT['xfit']=xfit
    NEWWAFERDICT['yfit']=yfit
        
        
    ##Detect Errors and Flag them!
        
    #If goodness of fit is very off:
    if R>Rgoodfit:
        errprint('WARNING: BAD FIT! R is',str(R))
        NEWWAFERDICT['Flags'].append('BAD FIT!')
        NEWWAFERDICT['Decision']='Fail'
              
    #If Vdep is greater than the data:
    if popt[1]>=xdata[-1]:
        errprint('WARNING: Fitted Vdep is greater than the data range! Max V in Data is',str(xdata[-1]))
        NEWWAFERDICT['Flags'].append('Fitted Vdep is greater than the data range!')
        NEWWAFERDICT['Decision']='MeasErr'
        
        
    ###Start Tech Spec Checks
    
    #Active Thickness must > 270 um [pg 16]
    if Dfull<=270e-6:
        errprint('WARNING: Active Thickness must > 270 um [pg 16]. Current Active Thickness is',str(Dfull))
        NEWWAFERDICT['Flags'].append('Active Thickness is below 270 um')
        NEWWAFERDICT['Decision']='Fail'
        
    #Initial Depl Voltage V_fd < 350 V [pg 18]
    if popt[1]>=350:
        errprint('WARNING: Initial Depl Voltage Vdep must < 350 V [pg 18]. Current Depl Voltage is',str(popt[1]))
        NEWWAFERDICT['Flags'].append('Initial Depl Voltage Vdep is above 350 V')
        NEWWAFERDICT['Decision']='Fail'
        

    ####Humidity Check:
    HumidityFlag=CheckHumidity(WAFERDICT)
    if HumidityFlag is not None:
        NEWWAFERDICT['Flags'].append(HumidityFlag)
        NEWWAFERDICT['Decision']='MeasErr'
        
        
    #Enter additional checks for decision here!
        
    ##Print Stuff
    norprint('popt='+str([ '%.3E' % elem for elem in popt ]))
    norprint('Vdep='+str(popt[1])+'V')
    norprint('R='+str('%.4E' % R))
    norprint('Neff='+str('%.3E' % Neff)+' m^3')
    norprint('Dfull='+str(int (Dfull*1e6))+' um')
    
    
    
    
    if NEWWAFERDICT['Decision']==None and len(NEWWAFERDICT['Flags'])==0:
        NEWWAFERDICT['Decision']='Pass'
    norprint(str(NEWWAFERDICT['Decision']))
    norprint(str(NEWWAFERDICT['Flags']))
    
    return NEWWAFERDICT    
        
    
    
####Function to extract Neff and tfull
def extractNeffDfullSlope(A,Vdep,slope):
    Neff=2/slope/e/eps0/epsr/A/A
    Dfull=np.sqrt(2*epsr*eps0*Vdep/e/Neff)
    return(Neff,Dfull)

def extractNeffDfullPlateau(A,Vdep,plateau):
    Dfull=epsr*eps0*A*np.sqrt(plateau)
    Neff=2*epsr*eps0*Vdep/e/Dfull/Dfull
    return(Neff,Dfull)
