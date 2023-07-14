import json

import matplotlib.pyplot as plt
import pandas as pd

CHVDDLR=1
CHCAL=4
CHCUR10V=12
CHCUR1V=13
CHNTCpb=9

def plot_ratio(x,y,xlabel=None,ylabel=None,xlim=None,ylim=None,rlim=None):
    plt.subplots_adjust(hspace=0.,wspace=0.)

    plt.subplot2grid((3,3), (0,0), rowspan=2, colspan=3)
    plt.plot(x,x,'-b',label='Expected')
    plt.plot(x,y,'.k',label='Measured')
    if ylabel: plt.ylabel(ylabel)
    if xlim: plt.xlim(*xlim)
    if ylim: plt.xlim(*ylim)
    plt.xticks([])

    plt.legend(frameon=False)

    plt.subplot2grid((3,3), (2,0), rowspan=1, colspan=3)
    resid=(y-x)/x
    plt.plot(x,resid,'.k')                                     
    plt.plot([0,1],[0,0],'-b')

    if xlim: plt.xlim(*xlim)    
    if rlim: plt.ylim(*rlim)
    plt.ylabel('(Meas-Exp)/Exp')
    if xlabel: plt.xlabel(xlabel)


class Report(object):
    def __init__(self,path):
        #
        # Default values
        self.slope=1.
        self.offset=[0.]*16

        #
        # Load the test results        
        with open(path) as fh:
            data = json.load(fh)

            for test in data['tests']:
                print(test['testType'])

                if test['testType'] in ["BER"]: continue
                df=pd.DataFrame(data=test['results'])
                object.__setattr__(self,test['testType'],df)

                # Extra post-processing based on test
#                if test['name']=='measure_efficiency':
#                    self.measure_efficiency['Iin_offset [A]']=test['Iin_offset']

            #
            # Load the configuration
            self.slope       =data['config']['results']['AMSLOPE']
            self.offset      =data['config']['results']['AMOFFSET']
            self.Cur10Voffset=data['config']['results']['CUR10VOFFSET']
            self.Cur1Voffset =data['config']['results']['CUR1VOFFSET']
            self.NTCpb       =data['config']['results'].get('NTCPB',250.)

            for key,value in data['config']['properties'].items():
                self.__setattr__(key,value)

    def calib(self,channel,counts):
        return self.slope*(counts-self.offset[channel])

class BasicFuncReport(object):
    def __init__(self,path):
        #
        # Load the test results        
        with open(path) as fh:
            data = json.load(fh)
            print('\n' + 'PB ' + str(data['pbNum']))

            for test in data['tests']:
                print(test['testType'])

                if test['testType'] in ["BER"]:
                    df=pd.DataFrame(data={'RELIABILITY':[test['results']['RELIABILITY']]})
                elif test['testType'] in ["PADID"]:
                    df=pd.DataFrame(data={'PADID':[test['results']['PADID']]})
                else:
                    df=pd.DataFrame(data=test['results'])
                object.__setattr__(self,test['testType'],df)
