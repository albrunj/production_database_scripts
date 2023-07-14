#!/usr/bin/env python3
import argparse
import glob
import json
import os

import matplotlib.pyplot as plt
import pbreport
from matplotlib.backends.backend_pdf import PdfPages

#
# Arguments
parser = argparse.ArgumentParser()

parser.add_argument("paneldate", help="path to date directory via panel directory")

args=parser.parse_args()

pdf=PdfPages('report.pdf')

pbs = ['pb0', 'pb1', 'pb2', 'pb3', 'pb4', 'pb5', 'pb6', 'pb7', 'pb8', 'pb9']

pbFolder = glob.glob(args.paneldate + "/pb*")

#
# Load the data
r = [[]]*10
for i in range (0, len(pbFolder)):
    pbBFPath = glob.glob(pbFolder[i] + "/*_pbv3-diagnostic.json")
    if(len(pbBFPath)==1):
        with open(pbBFPath[0]) as f:
            data = json.load(f)
            pbNum = data["pbNum"]
            
        if(os.stat(pbBFPath[0]).st_size > 0):
            r[pbNum] = pbreport.BasicFuncReport(pbBFPath[0])

cellText = [None]*10
cellColours = [None]*10



#################################
######## LV Enable Table ########
#################################

LVVon = [None]*10
LVVoff = [None]*10
for i in range(0,10):
    if hasattr(r[i], 'LV_ENABLE'):
        LVVon[i] = r[i].LV_ENABLE[r[i].LV_ENABLE.LVENABLE==True ].iloc[0]['VOUT']
        LVVoff[i] = r[i].LV_ENABLE[r[i].LV_ENABLE.LVENABLE==False].iloc[0]['VOUT']
        cellText[i] = ['{}V'.format(LVVoff[i]),'{}V'.format(LVVon[i])]
        cellColours[i] = ['r' if LVVoff[i]>0.1 else 'w','r' if abs(LVVon[i]-1.5)>0.1 else 'w']
    else:
        LVVon[i] = ''
        LVVoff[i] = ''
        cellText[i] = ['','']
        cellColours[i] = ['w', 'w']

fig, axs = plt.subplots(1,1)
axs.axis('tight')
axs.axis('off')
axs.set_title('LV Enable')
t=axs.table(cellText=cellText, colLabels=['Off', 'On'], rowLabels=pbs, cellColours=cellColours,loc='center')
pdf.savefig()
plt.close()



#################################
######## HV Enable Table ########
#################################

HVVon = [None]*10
HVIon = [None]*10
HVVoff = [None]*10
HVIoff = [None]*10
for i in range(0,10):
    if hasattr(r[i], 'HV_ENABLE'):
        HVVon[i] =r[i].HV_ENABLE[r[i].HV_ENABLE.CntSetHV0en==True ].iloc[0]['HVVIN']
        HVIon[i] =r[i].HV_ENABLE[r[i].HV_ENABLE.CntSetHV0en==True ].iloc[0]['HVIIN']

        HVVoff[i]=r[i].HV_ENABLE[r[i].HV_ENABLE.CntSetHV0en==False].iloc[0]['HVVIN']
        HVIoff[i]=r[i].HV_ENABLE[r[i].HV_ENABLE.CntSetHV0en==False].iloc[0]['HVIIN']

        cellText[i] = ['{}V ({:0.1f}mA)'.format(HVVoff[i], HVIoff[i]*1e3),'{}V ({:0.1f}mA)'.format(HVVon[i], HVIon[i]*1e3)]
        cellColours[i] = ['r' if ((HVVoff[i]>501.0 and HVIoff[i] < 2e-6) or HVIon[i]-HVIoff[i]<0.4e-3) else 'w','r' if ((HVVon[i] > 490.0 and HVIon[i] > 0.001) or HVIon[i]-HVIoff[i]<0.4e-3) else 'w']

    else:
        HVVon[i] = ''
        HVIon[i] = ''
        HVVoff[i] = ''
        HVIoff[i] = ''
        cellText[i] = ['','']
        cellColours[i] = ['w', 'w']

fig, axs = plt.subplots(1,1)
axs.axis('tight')
axs.axis('off')
axs.set_title('HV Enable')
t=axs.table(cellText=cellText, colLabels=['Off', 'On'], rowLabels=pbs, cellColours=cellColours,loc='center')
pdf.savefig()
plt.close()



#################################
######### Test OF Table #########
#################################

OFon = [None]*10
OFoff = [None]*10
for i in range(0,10):
    if hasattr(r[i], 'OF'):
        OFon[i] = r[i].OF[r[i].OF.OF==1].iloc[0]['linPOLV']
        OFoff[i] = r[i].OF[r[i].OF.OF==0].iloc[0]['linPOLV']
        cellText[i] = ['{}V'.format(OFoff[i]),'{}V'.format(OFon[i])]
        cellColours[i] = ['r' if OFoff[i]<1.3 else 'w','r' if OFon[i]>0.2 else 'w']
    else:
        OFon[i] = ''
        OFoff[i] = ''
        cellText[i] = ['','']
        cellColours[i] = ['w', 'w']

fig, axs = plt.subplots(1,1)
axs.axis('tight')
axs.axis('off')
axs.set_title('LinPOL Output Voltage')
t=axs.table(cellText=cellText, colLabels=['Off', 'On'], rowLabels=pbs, cellColours=cellColours,loc='center')
pdf.savefig()
plt.close()



#################################
##### Bit Error Rate Table ######
#################################

Reliability = [None]*10
for i in range(0,10):
    #
    # testOF table
    if hasattr(r[i], 'BER'):
        Reliability[i] = r[i].BER.RELIABILITY[0]
        cellText[i] = ['{}'.format(Reliability[i])]
        cellColours[i] = ['r' if Reliability[i]<1 else 'w']
    else:
        Reliability[i] = ''
        cellText[i] = ['']
        cellColours[i] = ['w']

fig, axs = plt.subplots(1,1)
axs.axis('tight')
axs.axis('off')
axs.set_title('Bit Error Rate Test')
t=axs.table(cellText=cellText, colLabels=['Reliability'], rowLabels=pbs, cellColours=cellColours,loc='center')
pdf.savefig()
plt.close()



#################################
########## PADID Table ##########
#################################

padid = [None]*10
for i in range(0,10):
    #
    # testOF table
    if hasattr(r[i], 'PADID'):
        padid[i] = r[i].PADID.PADID[0]
        cellText[i] = ['{}'.format(padid[i])]
        cellColours[i] = ['r' if padid[i]!=0 else 'w']
    else:
        padid[i] = ''
        cellText[i] = ['']
        cellColours[i] = ['w']

fig, axs = plt.subplots(1,1)
axs.axis('tight')
axs.axis('off')
axs.set_title('Scan PADID')
t=axs.table(cellText=cellText, colLabels=['PADID'], rowLabels=pbs, cellColours=cellColours,loc='center')
pdf.savefig()
plt.close()



#################################
###### Toggle Output Table ######
#################################

cellTextOn = [None]*10
cellColoursOn = [None]*10

cellTextOff = [None]*10
cellColoursOff = [None]*10

Calxon = [None]*10
Calyon = [None]*10
LDx0Enon = [None]*10
LDx1Enon = [None]*10
LDx2Enon = [None]*10
LDy0Enon = [None]*10
LDy1Enon = [None]*10
LDy2Enon = [None]*10
OFouton = [None]*10
Shuntxon = [None]*10
Shuntyon = [None]*10
Vouton = [None]*10

Calxoff = [None]*10
Calyoff = [None]*10
LDx0Enoff = [None]*10
LDx1Enoff = [None]*10
LDx2Enoff = [None]*10
LDy0Enoff = [None]*10
LDy1Enoff = [None]*10
LDy2Enoff = [None]*10
OFoutoff = [None]*10
Shuntxoff = [None]*10
Shuntyoff = [None]*10
Voutoff = [None]*10

colLabelsOff=['VoutOff', 'OFOff', 'CalxOff', 'CalyOff', 'LDx0EnOff', 'LDx1EnOff', 'LDx2EnOff', 'LDy0EnOff', 'LDy1EnOff', 'LDy2EnOff', 'ShuntxOff', 'ShuntyOff']
colLabelsOn=['VoutOn', 'OFOn', 'CalxOn', 'CalyOn', 'LDx0EnOn', 'LDx1EnOn', 'LDx2EnOn', 'LDy0EnOn', 'LDy1EnOn', 'LDy2EnOn', 'ShuntxOn', 'ShuntyOn']

for i in range(0,10):
    if hasattr(r[i], 'TOGGLEOUTPUT'):
        Calxon[i] = r[i].TOGGLEOUTPUT.CALx_value[1]
        Calxoff[i] = r[i].TOGGLEOUTPUT.CALx_value[0]
        Calyon[i] = r[i].TOGGLEOUTPUT.CALy_value[1]
        Calyoff[i] = r[i].TOGGLEOUTPUT.CALy_value[0]
        LDx0Enon[i] = r[i].TOGGLEOUTPUT.LDx0EN_value[1]
        LDx0Enoff[i] = r[i].TOGGLEOUTPUT.LDx0EN_value[0]
        LDx1Enon[i] = r[i].TOGGLEOUTPUT.LDx1EN_value[1]
        LDx1Enoff[i] = r[i].TOGGLEOUTPUT.LDx1EN_value[0]
        LDx2Enon[i] = r[i].TOGGLEOUTPUT.LDx2EN_value[1]
        LDx2Enoff[i] = r[i].TOGGLEOUTPUT.LDx2EN_value[0]
        LDy0Enon[i] = r[i].TOGGLEOUTPUT.LDy0EN_value[1]
        LDy0Enoff[i] = r[i].TOGGLEOUTPUT.LDy0EN_value[0]
        LDy1Enon[i] = r[i].TOGGLEOUTPUT.LDy1EN_value[1]
        LDy1Enoff[i] = r[i].TOGGLEOUTPUT.LDy1EN_value[0]
        LDy2Enon[i] = r[i].TOGGLEOUTPUT.LDy2EN_value[1]
        LDy2Enoff[i] = r[i].TOGGLEOUTPUT.LDy2EN_value[0]
        OFouton[i] = r[i].TOGGLEOUTPUT.OFout_value[1]
        OFoutoff[i] = r[i].TOGGLEOUTPUT.OFout_value[0]
        Shuntxon[i] = r[i].TOGGLEOUTPUT.Shuntx_value[1]
        Shuntxoff[i] = r[i].TOGGLEOUTPUT.Shuntx_value[0]
        Shuntyon[i] = r[i].TOGGLEOUTPUT.Shunty_value[1]
        Shuntyoff[i] = r[i].TOGGLEOUTPUT.Shunty_value[0]
        Vouton[i] = r[i].TOGGLEOUTPUT.Vout_value[1]
        Voutoff[i] = r[i].TOGGLEOUTPUT.Vout_value[0]

        cellTextOff[i] = ['{}'.format(round(Voutoff[i],5)), '{}'.format(round(OFoff[i], 5)), '{}'.format(round(Calxoff[i],5)), '{}'.format(round(Calyoff[i],5)), '{}'.format(round(LDx0Enoff[i],5)), '{}'.format(round(LDx1Enoff[i],5)), '{}'.format(round(LDx2Enoff[i],5)), '{}'.format(round(LDy0Enoff[i],5)), '{}'.format(round(LDy1Enoff[i],5)), '{}'.format(round(LDy2Enoff[i],5)), '{}'.format(round(Shuntxoff[i],5)), '{}'.format(round(Shuntyoff[i],5))]

        cellColoursOff[i] = ['w' if -0.1 < Voutoff[i] < 0.1 else 'r', 'w' if 1.0 < OFoff[i] < 1.5 else 'r', 'w' if -0.1 < Calxoff[i] < 0.1 else 'r', 'w' if -0.1 < Calyoff[i] < 0.1 else 'r', 'w' if -0.1 < LDx0Enoff[i] < 0.1 else 'r', 'w' if -0.1 < LDx1Enoff[i] < 0.1 else 'r', 'w' if -0.1 < LDx2Enoff[i] < 0.1 else 'r', 'w' if -0.1 < LDy0Enoff[i] < 0.1 else 'r', 'w' if -0.1 < LDy1Enoff[i] < 0.1 else 'r', 'w' if -0.1 < LDy2Enoff[i] < 0.1 else 'r', 'w' if -0.1 < Shuntxoff[i] < 0.3 else 'r', 'w' if -0.1 < Shuntyoff[i] < 0.3 else 'r']

        cellTextOn[i] = ['{}'.format(round(Vouton[i],5)), '{}'.format(round(OFon[i], 5)), '{}'.format(round(Calxon[i],5)), '{}'.format(round(Calyon[i],5)), '{}'.format(round(LDx0Enon[i],5)), '{}'.format(round(LDx1Enon[i],5)), '{}'.format(round(LDx2Enon[i],5)), '{}'.format(round(LDy0Enon[i],5)), '{}'.format(round(LDy1Enon[i],5)), '{}'.format(round(LDy2Enon[i],5)), '{}'.format(round(Shuntxon[i],5)), '{}'.format(round(Shuntyon[i],5))]

        cellColoursOn[i] = ['w' if 1.4 < Vouton[i] < 1.6 else 'r', 'w' if -0.1 < OFon[i] < .2 else 'r', 'w' if 0.9 < Calxon[i] < 1.3 else 'r', 'w' if 0.9 < Calyon[i] < 1.3 else 'r', 'w' if -1.0 < LDx0Enon[i] < 1.5 else 'r', 'w' if 1.0 < LDx1Enon[i] < 1.5 else 'r', 'w' if 1.0 < LDx2Enon[i] < 1.5 else 'r', 'w' if 1.0 < LDy0Enon[i] < 1.5 else 'r', 'w' if 1.0 < LDy1Enon[i] < 1.5 else 'r', 'w' if 1.0 < LDy2Enon[i] < 1.5 else 'r', 'w' if 0.9 < Shuntxon[i] < 1.3 else 'r', 'w' if 0.9 < Shuntyon[i] < 1.3 else 'r']

    else:
        Calxon[i] = ''
        Calxoff[i] = ''
        Calyon[i] = ''
        Calyoff[i] = ''
        LDx0Enon[i] = ''
        LDx0Enoff[i] = ''
        LDx1Enon[i] = ''
        LDx1Enoff[i] = ''
        LDx2Enon[i] = ''
        LDx2Enoff[i] = ''
        LDy0Enon[i] = ''
        LDy0Enoff[i] = ''
        LDy1Enon[i] = ''
        LDy1Enoff[i] = ''
        LDy2Enon[i] = ''
        LDy2Enoff[i] = ''
        OFouton[i] = ''
        OFoutoff[i] = ''
        Shuntxon[i] = ''
        Shuntxoff[i] = ''
        Shuntyon[i] = ''
        Shuntyoff[i] = ''
        Vouton[i] = ''
        Voutoff[i] = ''
        cellTextOff[i] = ['']*len(colLabelsOff)
        cellColoursOff[i] = ['w']*len(colLabelsOff)
        cellTextOn[i] = ['']*len(colLabelsOn)
        cellColoursOn[i] = ['w']*len(colLabelsOn)


fig, axs = plt.subplots(2,1)
axs[0].axis('tight')
axs[0].axis('off')
axs[1].axis('tight')
axs[1].axis('off')
axs[0].set_title('ToggleOutput Off State')
axs[1].set_title('ToggleOutput On State')
tOff=axs[0].table(cellText=cellTextOff, colLabels=colLabelsOff, rowLabels=pbs, cellColours=cellColoursOff,loc='center')
tOff.auto_set_font_size(False)
tOff.set_fontsize(4)
tOn=axs[1].table(cellText=cellTextOn, colLabels=colLabelsOn, rowLabels=pbs, cellColours=cellColoursOn,loc='center')
tOn.auto_set_font_size(False)
tOn.set_fontsize(4)
pdf.savefig()
plt.close()

#
# Cleanup
pdf.close()
