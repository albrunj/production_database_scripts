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

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


def coloredFlag(flag):
    if flag:
        return 'Yes, \033[1;32m[PASSED]\x1b[0m'
    else:
        return 'No, \033[1;31m[FAILED]\x1b[0m'

# Function: slope: 2a, intercept: -a*x0+b, const: a*x0+b
def fit_func(x, x0, a, b):
    return -a*np.abs(x-x0) + a*x + b

def analyseCV(argv):
    for data_files in argv:
        fig, ax = plt.subplots(1, figsize=(7.2,4.0))
        ax1 = ax.twinx()
        ax2 = ax.twinx()


        with open(data_files, 'r') as data:
            data_file = json.load(data)
            print(data_file)
            db_sensorID = data_file["component"]
            db_measType = data_file["test"]
            if db_measType != 'CV':
                raise Exception('Not an CV file!')
            db_institute = data_file["institution"]
            db_date = data_file["date"]
            db_prefix = data_file["prefix"]
            #If temp/hum properties missing, calculate from average
            try:
                db_temperature = data_file["properties"]["TEMP"]
                db_humidity = data_file["properties"]["HUM"]
            except:
                num_temp = np.array(data_file["CV_ARRAY"]["temperature"])
                num_hum= np.array(data_file["CV_ARRAY"]["humidity"])
                db_temperature = np.average(num_temp)
                db_humidity = np.average(num_hum)

            cv_data = {"t":[],
                       "U":[],
                       "Iavg":[],
                       "Istd":[],
                       "T":[],
                       "RH":[]
                       }


            cv_data['U'] = data_file["CV_ARRAY"]["voltage"]
            cv_data['Cavg'] = data_file["CV_ARRAY"]["capacitance"]
            try:
                timedata = cv_data["t"] = data_file["CV_ARRAY"]["time"]
                cv_data['Cstd'] = data_file["CV_ARRAY"]["sigma capacitance"]
                tempdata = cv_data['T'] = data_file["CV_ARRAY"]["temperature"]
                humidata = cv_data['RH'] = data_file["CV_ARRAY"]["humidity"]
            except:
                    timedata = cv_data["t"]
                    tempdata = cv_data['T']
                    humidata = cv_data['RH']

            xdata = [abs(x) for x in cv_data['U']]


        if db_prefix == "F":
            cv_data['Cavg'] = [x*1e+12 for x in cv_data['Cavg']]
            cv_data['Cstd'] = [x*1e+12 for x in cv_data['Cstd']]


        #Creating the 1/C**2 voltage Curve
        ydata = [1/x**2*1e6 for x in cv_data['Cavg']]
        yerr = [-2/x**3*y*1e6 for x,y in zip(cv_data['Cavg'], cv_data['Cstd'])]

        #Fitting the curves
        popt, pcov = curve_fit(fit_func, xdata, ydata, [20,0.1,10])
        Vdepl = popt[0]
        Vdepl_err = np.sqrt(pcov[0][0])

        if any(db_sensorID[6] == x for x in ["G","H","I","J","V","W"]):
            print("Setting Criterias for 3D sensor\n")
            is3D = True

        else:
            print("Setting Criterias for planar sensor\n")
            is3D = False


        #Capacitance planar lower 100fF
        #Good if full-depletion Voltage < 60V for 100um
        #Good if full-depletion Voltage < 100V for 150 um

        if is3D:
            if 0 < Vdepl < 10:
                Vdepl_flag = True
            else:
                Vdepl_flag = False

        else:
                #Depletion voltage criteria for 100um thick sensors
            if (0 < Vdepl < 60) and any(db_sensorID[6] == x for x in ["6","8","2","T"]):
                Vdepl_flag = True
                #Depletion voltage criteria for 150um thick sensors
            elif (0 < Vdepl < 100) and any(db_sensorID[6] == x for x in ["7","9","3","U"]):
                Vdepl_flag = True
            else:
                Vdepl_flag = False

        for idx,V in enumerate(xdata):
            if V<Vdepl:
                continue
            else:
                print("Extracting capacitance value for Voltage = {} V".format(V))
                CapVdep = cv_data['Cavg'][idx]
                break

        #Check if the sensor is half or full size
        if any(db_sensorID[6] == x for x in ["6","7","G","H"]):
            sensor_size = "Half"

        elif any(db_sensorID[6] == x for x in ["8","9","I","J"]):
            sensor_size = "Full"

        #The L0 inner pixel 3D sensor tiles are also full size in pre- and production
        elif any(db_sensorID[6] == x for x in ["0","1"]):
            sensor_size = "Full"

        #Test structure
        elif any(db_sensorID[6] == x for x in ["T","U", "V","W"]):
            sensor_size = "Test"

        else:
            print("Could not find size of sensor. Check SN")
            return


        #Finding the number of sensor pixels
        if sensor_size == "Half" and db_sensorID[8] == "1":
            pixels = 76800 #Number of pixels for half-size single

        elif sensor_size == "Full" and db_sensorID[8] == "1":
            pixels = 153600 #Number of pixels for full-size single

        elif sensor_size == "Half" and db_sensorID[8] == "2":
            pixels = 153600 #Number of pixels for half-size double

        elif sensor_size == "Full" and db_sensorID[8] == "2":
            pixels = 307200 #Number of pixels for full-size double

        elif db_sensorID[8] == "3":
            pixels = 614400 #pixels for Quad (No half size)

        #3D diodes vendor 3  and SINTEF: 0.04 cm2 with 1600 pixels
        elif db_sensorID[8] == "9" and (db_sensorID[7] == "2" or db_sensorID[7] == "7"):
            pixels = 1600 #pixels
        #3D diodes vendor for CNM
        elif db_sensorID[8] == "9" and db_sensorID[6] == "2":
            pixels = 2500 #pixels for 3D diodes

        elif db_sensorID[8] == "4":
            pixels = 1 #pixels for planar diodes

        else:
            print("No pixels found on your pixel sensor")
            pixels = int(input("Enter sensor pixels to continue: "))

        Capperpix = CapVdep/pixels

        if Capperpix < 0.1:
            Capaci_flag = True
        else:
            Capaci_flag = False

        total_flag = Vdepl_flag and Capaci_flag

        print('{:48} {}'.format('Sensor ID:', db_sensorID))
        print('{:48} {:.1f} +- {:.1f} V'.format('Depletion voltage:', Vdepl, Vdepl_err))
        print('{:48} {}'.format('Less than criteria V?', coloredFlag(Vdepl_flag)))

        print('{:48} {}'.format('Pixel below 0.1pF (={}pF)?'.format(Capperpix), coloredFlag(Capaci_flag)))

        print('{:48} {}'.format('Does the sensor meet all MS-CV criteria?', coloredFlag(total_flag)))

        if len(yerr) == 0:

            p1 = ax.plot(xdata[1:], ydata[1:], label='cv data')
            first_legend = plt.legend(handles = p1, loc="lower center", bbox_to_anchor=(0.15, -0.33))
            plt.gca().add_artist(first_legend)

        else:
            p1 = ax.errorbar(xdata, ydata, yerr=yerr, fmt='ko', label='cv data')
            first_legend = plt.legend(handles = [p1], loc="lower center", bbox_to_anchor=(0.15, -0.33))
            plt.gca().add_artist(first_legend)
        x_plot = np.linspace(min(xdata), max(xdata), len(xdata)*10)
        p4, = ax.plot(x_plot, fit_func(x_plot, *popt), 'r', label='fit')


        if len(tempdata) == 0:
            print("No temperature array given")
        else:
            p2, = ax1.plot(xdata, cv_data['T'], color='C1', label='temperature')
            ax1.set_ylabel('T [°C]', color='C1', fontsize='large')
            second_legend = plt.legend(handles = [p2], loc="lower center", bbox_to_anchor=(0.5, -0.33))
            plt.gca().add_artist(second_legend)

        if len(humidata) == 0:
            print("No humidity array given")
        else:
            p3, = ax2.plot(xdata, cv_data['RH'], color='C2', label='humidity')
            ax2.set_ylabel('RH [%]', color='C2', fontsize='large')
            ax2.spines['right'].set_position(('outward', 60))
            third_legend = plt.legend(handles = [p3], loc="lower center", bbox_to_anchor=(0.85, -0.33))
            plt.gca().add_artist(third_legend)


        ax.set_title('CV for sensor "{}", {}'.format(db_sensorID, '[PASSED]' if Vdepl_flag else '[FAILED]'), fontsize='large')
        ax.set_xlabel('U [V]', ha='right', va='top', x=1.0, fontsize='large')
        ax.set_ylabel(r'$1/C_{avg}^2$ [$\mathrm{1/nF}^2$]', ha='right', va='bottom', y=1.0, fontsize='large')
        fig.subplots_adjust(bottom=0.25)
        fig.subplots_adjust(right=0.75)


        ax.grid()

        pathname = dirname(os.getcwd()) + "/plots/"
        namefile = basename(data_files)
        savename = os.path.join(pathname,os.path.splitext(namefile)[0])

        fig.savefig(savename+'.pdf'.format(), dpi=300)
        fig.savefig(savename+'.png'.format(), dpi=300)

        plot_path = savename+'.png'

        return db_sensorID, db_institute, db_date,db_humidity, db_temperature, timedata, xdata, ydata, yerr, tempdata, humidata, Vdepl, plot_path, total_flag
if __name__ == "__main__":
    if len(sys.argv)==1:
        print('Please provide database file(s) as argument(s).')
    else:
        analyseCV(sys.argv[1:])
