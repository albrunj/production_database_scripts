#for now the Average Thickness test works ONLY for Main and Dummy sensors and data format which is specify in DataFormats folder as STANDARD_2021_04_THICKNESS.txt
import copy

from CommonConfig import TestType_Thickness

#Parameters
Th_max=335
Th_min=305

def Analyze_THICKNESS(WAFERDICT):

    print('Starting Analyze_THICKNESS for {}-W{}, file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']),str(WAFERDICT['Filename']) ))
          
    #initialize new wafer dict
    NEWWAFERDICT=copy.deepcopy(WAFERDICT)
    NEWWAFERDICT['Decision']=None
    NEWWAFERDICT['Flags']=[]
     #NEWWAFERDICT['AvThickness']=None
    #MeasErr =  False
     #Check if it is a Thickness Test
    if WAFERDICT['TestType'] in [TestType_Thickness]:

         #Extract Data
        Thickness=WAFERDICT['AvThickness']
    else:
        print('*** {} is Not a Thickness Test!'.format(str(WAFERDICT['Filename'])))
        NEWWAFERDICT['Flags'].append('File Not a Thickness Test!')
        return NEWWAFERDICT

    #Check if Data exists
    if Thickness is None:
        print('*** Thickness is Empty, exiting!')
        NEWWAFERDICT['Flags'].append('Thickness is Empty!')
        NEWWAFERDICT['Decision']='MeasErr'
        return NEWWAFERDICT 


    #Check if thickness does not exceed limits
    Thickness=float(Thickness)
    if (Th_min<Thickness<Th_max):
        NEWWAFERDICT['Flags'].append('Thickness does not exceed limit: min {:.0f} um, max {:.0f} um'.format(Th_min, Th_max))
        NEWWAFERDICT['Flags'].append('The average thickness value is {:.0f} um.'.format(Thickness))
        NEWWAFERDICT['Decision']='Pass'
        print ('Thickness does not exceed limit: min{:.0f} um, max {:.0f} um'.format(Th_min, Th_max))
        print ('The average thickness value is {:.0f} um.'.format(Thickness))
    else:
        NEWWAFERDICT['Flags'].append('Thickness exceeds limit: min {:.0f} um, max {:.0f} um'.format(Th_min, Th_max))
        NEWWAFERDICT['Flags'].append('The average thickness value is {:.0f} um.'.format(Thickness))
        NEWWAFERDICT['Decision']='Fail'
        print ('Thickness exceeds limit: min{:.0f} um, max {:.0f} um'.format(Th_min, Th_max))
        print ('The average thickness value is {:.0f} um.'.format(Thickness))

    print ("Decision = {}".format(NEWWAFERDICT['Decision']))
    print ('Finished Analyze_THICKNESS for {}-W{}, file {}'.format(str(WAFERDICT['Batch']), str(WAFERDICT['Wafer']),str(WAFERDICT['Filename']) ))

    return NEWWAFERDICT
