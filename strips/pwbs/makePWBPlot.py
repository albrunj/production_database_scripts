#!/usr/bin/env python
import argparse

import matplotlib.pyplot as plt
import pbreport
from matplotlib.backends.backend_pdf import PdfPages
# matplotlib.rcParams['font.size'] = 15
# matplotlib.rcParams['figure.figsize']=(12,8)
# matplotlib.rcParams['legend.fontsize']=20


#
# Arguments
parser = argparse.ArgumentParser()

parser.add_argument("testresults", help="path to test output file")

args=parser.parse_args()

#
# Load the data
r=pbreport.Report(args.testresults)

pdf=PdfPages('report.pdf')

#
# Enable table
LVVon =r.LV_ENABLE[r.LV_ENABLE.LVENABLE==True ].iloc[0]['VOUT']
LVVoff=r.LV_ENABLE[r.LV_ENABLE.LVENABLE==False].iloc[0]['VOUT']

if hasattr(r, 'HV_ENABLE'):
	HVVon =r.HV_ENABLE[r.HV_ENABLE.HVENABLE==True ].iloc[0]['HVVIN']
	HVIon =r.HV_ENABLE[r.HV_ENABLE.HVENABLE==True ].iloc[0]['HVIIN']

	HVVoff=r.HV_ENABLE[r.HV_ENABLE.HVENABLE==False].iloc[0]['HVVIN']
	HVIoff=r.HV_ENABLE[r.HV_ENABLE.HVENABLE==False].iloc[0]['HVIIN']

	cellText=[['LV','{}V'.format(LVVoff),'{}V'.format(LVVon)],['HV','{}V ({:0.1f}mA)'.format(HVVoff,HVIoff*1e3),'{}V ({:0.1f}mA)'.format(HVVon,HVIon*1e3)]]
	cellColours=[['w','r' if LVVoff>0.1 else 'w','r' if abs(LVVon-1.5)>0.1 else 'w'],['w','r' if HVVoff>350.0 and HVIoff < 2e-6 else 'w', 'r' if HVVon>250.0 and HVIon > 0.4e-3 else 'w']]

else:
	cellText=[['LV','{}V'.format(LVVoff),'{}V'.format(LVVon)]]
	cellColours=[['w','r' if LVVoff>0.1 else 'w','r' if abs(LVVon-1.5)>0.1 else 'w']]

t=plt.table(cellText=cellText, colLabels=['','Off','On'], cellColours=cellColours,loc='center')
t.scale(1,4)

pdf.savefig()
plt.close()


#
# Efficiency plot
r.DCDCEFFICIENCY['myeff']=(1.5*r.DCDCEFFICIENCY['IOUT'])/(11*(r.DCDCEFFICIENCY['IIN']-r.DCDCEFFICIENCY['IINOFFSET']))
plt.plot(r.DCDCEFFICIENCY['IOUT'],r.DCDCEFFICIENCY['myeff'])
plt.xlabel('Output Current [A]')
plt.ylabel('DC/DC Efficiency')
pdf.savefig()
plt.close()

#
# Calibration curve
r.AMSLOPE['CAL']=r.calib(pbreport.CHCAL,r.AMSLOPE['AMACCAL'])

pbreport.plot_ratio(r.AMSLOPE['CALIN'],r.AMSLOPE['CAL']/1e3,
                    xlabel='Input Voltage [V]',ylabel='AMAC Reading [V]',
                    xlim=(0,1),ylim=(0,1),rlim=(-0.1,0.1))
pdf.savefig()
plt.close()

#
# Input current
plt.plot(r.DCDCEFFICIENCY['IIN'],r.DCDCEFFICIENCY['AMACCUR10V'],'.k')

plt.xlabel('Input Current [A]')
plt.ylabel('AMAC Input Current [counts]')

plt.xlim(0,1)
plt.ylim(0,1024)

pdf.savefig()
plt.close()
    

#
# Output current
plt.plot(r.DCDCEFFICIENCY['IOUT'],r.DCDCEFFICIENCY['AMACCUR1V'],'.k')

plt.xlabel('Output Current [A]')
plt.ylabel('AMAC Output Current [counts]')

plt.xlim(0,3)
plt.ylim(0,1024)

pdf.savefig()
plt.close()    

#
# HV Sense curve
if hasattr(r, 'HV_ENABLE'):
	plt.semilogx(r.HVSENSE['HVI'],r.HVSENSE['AMACGAIN0'],'.',label='Gain 0')
	plt.semilogx(r.HVSENSE['HVI'],r.HVSENSE['AMACGAIN1'],'.',label='Gain 1')
	plt.semilogx(r.HVSENSE['HVI'],r.HVSENSE['AMACGAIN2'],'.',label='Gain 2')
	plt.semilogx(r.HVSENSE['HVI'],r.HVSENSE['AMACGAIN4'],'.',label='Gain 4')
	plt.semilogx(r.HVSENSE['HVI'],r.HVSENSE['AMACGAIN8'],'.',label='Gain 8')

	plt.xlabel('HV Current [A]')
	plt.ylabel('AMAC Reading [counts]')

	pdf.savefig()
	plt.close()    

#
# Cleanup
pdf.close()
