#########################################################################
# Andreas Gisen, Simon Huiberts, Giordon Stark UiO,UiB,CERN             #
# andreas.gisen@tu-dortmund.de, shu011@uib.no, GSTARK@CERN.CH           #
# October 2020                                                          #
#########################################################################
# -*- coding: utf-8 -*-
import json
import os
import sys
from os.path import basename
from os.path import dirname

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np

try:
    input = raw_input
except NameError:
    pass

def coloredFlag(flag):
    if flag:
        return 'Yes, \033[1;32m[PASSED]\x1b[0m'
    else:
        return 'No, \033[1;31m[FAILED]\x1b[0m'


def analyseIV(argv):

    for data_files in argv:
        fig, ax = plt.subplots(1, figsize=(7.2,4.0))
        ax1 = ax.twinx()
        ax2 = ax.twinx()

        #Open json file and read in the data
        with open(data_files, 'r') as data:
            data_file = json.load(data)
            db_sensorID = data_file["component"]
            db_measType = data_file["test"]
            if db_measType != 'IV':
                raise Exception('Not an IV file!')
            db_institute = data_file["institution"]
            db_date = data_file["date"]
            db_prefix = data_file["prefix"]
            Vdepl = data_file["depletion_voltage"]
            #If temp/hum properties missing, calculate from average
            try:
                db_temperature = data_file["properties"]["TEMP"]
                db_humidity = data_file["properties"]["HUM"]
            except:
                num_temp = np.array(data_file["IV_ARRAY"]["temperature"])
                num_hum= np.array(data_file["IV_ARRAY"]["humidity"])
                db_temperature = np.average(num_temp)
                db_humidity = np.average(num_hum)

            iv_data = {"t":[],
                       "U":[],
                       "Iavg":[],
                       "Istd":[],
                       "T":[],
                       "RH":[]
                       }

            iv_data['U'] = data_file["IV_ARRAY"]["voltage"]
            iv_data['Iavg'] = data_file["IV_ARRAY"]["current"]
            try:
                timedata = iv_data["t"] = data_file["IV_ARRAY"]["time"]
                iv_data['Istd'] = data_file["IV_ARRAY"]["sigma current"]
                tempdata = iv_data['T'] = data_file["IV_ARRAY"]["temperature"]
                humidata = iv_data['RH'] = data_file["IV_ARRAY"]["humidity"]
            except:
                timedata = iv_data["t"]
                iv_data['Istd']
                tempdata = iv_data['T']
                humidata = iv_data['RH']

            #Converting to absolute values
            xdata = [abs(x) for x in iv_data['U']]
            ydata = [abs(x) for x in iv_data['Iavg']]
            yerr  = [abs(x) for x in iv_data['Istd']]

            #Convert to "uA" if data is in A
            if db_prefix == "A":
                ydata = [x*1e+6 for x in ydata]
                yerr = [x*1e+6 for x in yerr]

        #Finding Leakage current and breakdown voltage
        if Vdepl == None:
            Vdepl = float(input('Please enter the depletion voltage (in V) for sensor "{}":\n'.format(db_sensorID)))

        Vbd = 0
        Ilc = 0

        #Checking if the component is 3D by using YY-identifiers
        if any(db_sensorID[6] == x for x in ["G","H","I","J","V","W"]):
            print("Setting Criterias for 3D sensor\n")
            is3D = True

        else:
            print("Setting Criterias for planar sensor\n")
            is3D = False

        #3D sensor criterias
        if is3D:
            if 0 < Vdepl < 10:
                Vdepl_flag = True
            else:
                Vdepl_flag = False
            I_voltage_point = Vdepl + 20
            break_threshold = Vdepl + 20
            I_treshold = 2.5 #current in uA

        #Planar sensor criterias
        else:
            #Depletion voltage criteria for 100um thick sensors
            if (0 < Vdepl < 60) and any(db_sensorID[6] == x for x in ["6","8","2","T"]):
                Vdepl_flag = True

            #Depletion voltage criteria for 150um thick sensors
            elif (0 < Vdepl < 100) and any(db_sensorID[6] == x for x in ["7","9","3","U"]):
                Vdepl_flag = True
            else:
                Vdepl_flag = False

            I_voltage_point = Vdepl + 50
            break_threshold = Vdepl + 70
            I_treshold = 0.75 #current in uA

        #Finding leakage current at threshold voltage
        for idx,V in enumerate(xdata):
            if V<Vdepl:
                continue
            elif V<=I_voltage_point:
               Vlc = V
               Ilc = ydata[idx]

            #Finding breakdown voltage for 3D
            if is3D:
                if ydata[idx] > ydata[idx-5]*2 and xdata[idx-5] > Vdepl:
                    Vbd = xdata[idx-5]
                    print('Breakdown at {:.1f} V for 3D sensor'.format(Vbd))
                    ax.axvline(Vbd, linewidth=4, color='r', label='Bd @ {:.0f}V'.format(Vbd))
                    break

            #Finding breakdown voltage for Planar
            else:
                if ydata[idx]>ydata[idx-1]*1.2 and xdata[idx-1] != 0:
                    Vbd = V
                    print('Breakdown at {:.1f} V for planar sensor'.format(Vbd))
                    ax.axvline(Vbd, linewidth=4, color='r', label='Bd @ {:.0f}V'.format(Vbd))
                    break

        #Check if the sensor is half or full size
        if any(db_sensorID[6] == x for x in ["6","7","G","H"]):
            sensor_size = "Half"

        if any(db_sensorID[6] == x for x in ["8","9","I","J"]):
            sensor_size = "Full"

        #The L0 inner pixel 3D sensor tiles are also full size in pre- and production
        if any(db_sensorID[6] == x for x in ["0","1"]):
            sensor_size = "Full"

        #Test structure
        if any(db_sensorID[6] == x for x in ["T","U", "V","W"]):
            sensor_size = "Test"

        #Finding the Sensor Area
        if sensor_size == "Half" and db_sensorID[8] == "1":
            area = 1.92 #cm^2 for half-size-singel

        elif sensor_size == "Full" and db_sensorID[8] == "1":
            area = 3.84 #cm^2 for singel ITkpix_V1

        elif sensor_size == "Half" and db_sensorID[8] == "2":
            area = 3.86 #cm^2 for half-double sensors

        elif sensor_size == "Full" and db_sensorID[8] == "2":
            area = 7.73 #cm^2 for Full-double sensors

        elif db_sensorID[8] == "3":
            area = 15.52 #cm^2 for Quad (No half size)

        #3D diodes vendor 3  and SINTEF: 0.04 cm2 with 1600 pixels
        elif db_sensorID[8] == "9" and (db_sensorID[7] == "2" or db_sensorID[7] == "7"):
            area = 0.04 #cm^2 for 3D diodes
        #3D diodes vendor for CNM
        elif db_sensorID[8] == "9" and db_sensorID[6] == "2":
            area = 0.0625 #cm^2 for 3D diodes

        elif db_sensorID[8] == "4":
            area = 0.25 #cm^2 for planar diodes

        else:
            print("No area found on your pixel sensor")
            area = float(input("Enter sensor area to continue: ")) # nosec

        Ilc_uA_cm = (Ilc)/area
        Ilc_uA_cm = round(Ilc_uA_cm, 4)

        #Pass or fail on leakaged current
        if Ilc_uA_cm > I_treshold:
            Ilc_flag = False
        else:
            Ilc_flag = True

        #Pass or fail on breakdown voltage
        if 0 < Vbd < break_threshold:
            Vbd_flag = False
        else:
            Vbd_flag = True

        total_flag = Vbd_flag and Ilc_flag and Vdepl_flag

        #Printing and plotting
        print('{:48} {}'.format('Sensor ID:', db_sensorID))
        print('{:48} {} V'.format('Breakdown voltage:', Vbd))
        print('{:48} {}'.format('In excess of {} (={:.0f}V)?'.format(break_threshold,  Vbd), coloredFlag(Vbd_flag)))

        print('{:48} {} uA'.format('Leakage current at {} (={:.0f}V):'.format(I_voltage_point, Vlc), Ilc) )
        print('{:48} {}'.format('Leakage current {} uA/cm2 pass?'.format(Ilc_uA_cm), coloredFlag(Ilc_flag)))

        print('{:48} {}'.format('Does the sensor meet all MS-IV criteria?', coloredFlag(total_flag)))


        #Plotting options
        if len(yerr) == 0:
            p1 = ax.plot(xdata[1:], ydata[1:], label='current')
            first_legend = plt.legend(handles = p1, loc="lower center", bbox_to_anchor=(0.15, -0.33))
            plt.gca().add_artist(first_legend)
        else:
            p1 = ax.errorbar(xdata[1:], ydata[1:], yerr=yerr[1:], fmt='ko', label='current')
            first_legend = plt.legend(handles = [p1], loc="lower center", bbox_to_anchor=(0.15, -0.33))
            plt.gca().add_artist(first_legend)

        if len(tempdata) == 0:
            print("No temperature array given")
        else:
            p2, = ax1.plot(xdata[1:], iv_data['T'][1:], color='C1', label='temperature')
            ax1.set_ylabel('T [°C]', color='C1', fontsize='large')
            second_legend = plt.legend(handles = [p2], loc="lower center", bbox_to_anchor=(0.5, -0.33))
            plt.gca().add_artist(second_legend)

        if len(humidata) == 0:
            print("No humidity array given")
        else:
            p3, = ax2.plot(xdata[1:], iv_data['RH'][1:], color='C2', label='humidity')
            ax2.set_ylabel('RH [%]', color='C2', fontsize='large')
            ax2.spines['right'].set_position(('outward', 60))
            third_legend = plt.legend(handles = [p3], loc="lower center", bbox_to_anchor=(0.85, -0.33))
            plt.gca().add_artist(third_legend)

        ax.set_title('IV for sensor "{}", {}'.format(db_sensorID, '[PASSED]' if total_flag else '[FAILED]'), fontsize='large')
        ax.set_xlabel('U [V]', ha='right', va='top', x=1.0, fontsize='large')
        ax.set_ylabel('I [uA]', ha='right', va='bottom', y=1.0, fontsize='large')
        fig.subplots_adjust(bottom=0.25)
        fig.subplots_adjust(right=0.75)

        ax.grid()

        pathname = dirname(os.getcwd()) + "/plots/"
        namefile = basename(data_files)
        savename = os.path.join(pathname,os.path.splitext(namefile)[0])

        fig.savefig(savename+'.pdf'.format(), dpi=300)
        fig.savefig(savename+'.png'.format(), dpi=300)

        ax.set_yscale('log')

        fig.savefig(savename+'_log.pdf'.format(), dpi=300)
        fig.savefig(savename+'_log.png'.format(), dpi=300)

        plot_path = savename+'.png'

        return db_sensorID, db_institute, db_date,db_humidity, db_temperature, timedata, xdata, ydata, yerr, tempdata, humidata, Vbd, Ilc, plot_path, total_flag

if __name__ == "__main__":
    if len(sys.argv)==1:
        print('Please provide database file(s) as argument(s).')
    else:
        analyseIV(sys.argv[1:])
