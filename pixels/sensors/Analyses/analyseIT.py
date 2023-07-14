#########################################################################
# Andreas Gisen, Simon Huiberts, Giordon Stark UiO,UiB,CERN             #
# andreas.gisen@tu-dortmund.de, shu011@uib.no, GSTARK@CERN.CH           #
# October 2020                                                          #
#########################################################################
# -*- coding: utf-8 -*-
import datetime as dt
import json
import os
import sys
from os.path import basename
from os.path import dirname

import matplotlib.pyplot as plt
import numpy as np
#from scipy.optimize import curve_fit


def coloredFlag(flag):
    if flag:
        return 'Yes, \033[1;32m[PASSED]\x1b[0m'
    else:
        return 'No, \033[1;31m[FAILED]\x1b[0m'


def analyseIT(argv):
    for data_files in argv:
        fig, ax = plt.subplots(1, figsize=(7.2,4.0))
        ax1 = ax.twinx()
        ax2 = ax.twinx()

        with open(data_files, 'r') as data:
            data_file = json.load(data)

        db_sensorID = data_file["component"]
        db_measType = data_file["test"]
        if db_measType != 'IT':
            raise Exception('Not an IT file!')
        db_institute = data_file["institution"]
        db_date = data_file["date"]
        db_prefix = data_file["prefix"]
        #If temp/hum properties missing, calculate from average
        try:
            db_temperature = data_file["properties"]["TEMP"]
            db_humidity = data_file["properties"]["HUM"]
        except:
            num_temp = np.array(data_file["IT_ARRAY"]["temperature"])
            num_hum= np.array(data_file["IT_ARRAY"]["humidity"])
            db_temperature = np.average(num_temp)
            db_humidity = np.average(num_hum)


        it_data = {"t":[],
                   "U":[],
                   "Iavg":[],
                   "Istd":[],
                   "T":[],
                   "RH":[]
                   }


        timedata = xdata = it_data["t"] = data_file["IT_ARRAY"]["time"]
        it_data['U'] = data_file["IT_ARRAY"]["voltage"]
        it_data['Iavg'] = data_file["IT_ARRAY"]["current"]
        try:
            it_data['Istd'] = data_file["IT_ARRAY"]["sigma current"]
            tempdata = it_data['T'] = data_file["IT_ARRAY"]["temperature"]
            humidata = it_data['RH'] = data_file["IT_ARRAY"]["humidity"]
        except:
            tempdata = it_data['T']
            humidata = it_data['RH']

        #Converting to absolute values
        voltagedata = [abs(x) for x in it_data['U']]
        ydata = [abs(x) for x in it_data['Iavg']]
        yerr  = [abs(x) for x in it_data['Istd']]

        #Convert to "uA" if data is in A
        if db_prefix == "A":
            ydata = [x*1e+6 for x in ydata]
            yerr = [x*1e+6 for x in yerr]

        #Should record for 48H
        if timedata[-1] <= 172800:
            time_flag = False
        else:
            time_flag = True

        #Removing the first 10 min
        ydataintime = np.array(ydata[1:])

        #Criteria for stabile current and time when it was max/min
        I_avg = np.average(ydataintime)
        I_max_variation = 1-min(ydataintime)/max(ydataintime)
        timemax = np.argmax(ydataintime)
        timemin = np.argmin(ydataintime)

        if I_max_variation > 0.25:
            Ivar_flag = False
        else:
            Ivar_flag = True

        total_flag = time_flag and Ivar_flag


        print('{:48} {}'.format('Sensor ID:', db_sensorID))
        print('{:48} {:3.0f} V'.format('Bias voltage:', np.mean(it_data['U'])))
        print('{:48} {}'.format('Total duration:', str(dt.timedelta(seconds=it_data['t'][-1]))))
        print('{:48} {}'.format('Total duration longer or equal 48H?:', coloredFlag(time_flag)))
        print('{:48} {:.3} uA'.format('Average leakage current, excl. t=0:', I_avg))
        print('{:48} {:.3} uA at time {}'.format('Maximum leakage current, excl. t=0', max(ydataintime),str(dt.timedelta(seconds=xdata[timemax]))))
        print('{:48} {:.3} uA at time {}'.format('Minimum leakage current, excl. t=0:',min(ydataintime),str(dt.timedelta(seconds=xdata[timemin]))))
        print('{:48} {:2.1f} %'.format('Maximum variation, excl. t=0:', I_max_variation*100))
        print('{:48} {}'.format('Variation less than 25%?', coloredFlag(Ivar_flag)))

        print('{:48} {}'.format('Does the sensor meet all MS-It criteria?', coloredFlag(total_flag)))

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
            p2, = ax1.plot(xdata[1:], it_data['T'][1:], color='C1', label='temperature')
            ax1.set_ylabel('T [°C]', color='C1', fontsize='large')
            second_legend = plt.legend(handles = [p2], loc="lower center", bbox_to_anchor=(0.5, -0.33))
            plt.gca().add_artist(second_legend)

        if len(humidata) == 0:
                print("No humidity array given")

        else:
            p3, = ax2.plot(xdata[1:], it_data['RH'][1:], color='C2', label='humidity')
            ax2.set_ylabel('RH [%]', color='C2', fontsize='large')
            ax2.spines['right'].set_position(('outward', 60))
            third_legend = plt.legend(handles = [p3], loc="lower center", bbox_to_anchor=(0.85, -0.33))
            plt.gca().add_artist(third_legend)

        ax.set_title('IT for sensor "{}", {}'.format(db_sensorID, '[PASSED]' if Ivar_flag else '[FAILED]'), fontsize='large')
        ax.set_xlabel('t [s]', ha='right', va='top', x=1.0, fontsize='large')
        ax.set_ylabel('I [uA]', ha='right', va='bottom', y=1.0, fontsize='large')

        ax1.set_ylabel('T [°C]', color='C1', fontsize='large')
        ax2.set_ylabel('RH [%]', color='C2', fontsize='large')
        ax2.spines['right'].set_position(('outward', 60))
        fig.subplots_adjust(bottom=0.25)
        fig.subplots_adjust(right=0.75)


        ax.grid()

        pathname = dirname(os.getcwd()) + "/plots/"
        namefile = basename(data_files)
        savename = os.path.join(pathname,os.path.splitext(namefile)[0])

        fig.savefig(savename+'.pdf'.format(), dpi=300)
        fig.savefig(savename+'.png'.format(), dpi=300)

        plot_path = savename+'.png'

        return db_sensorID, db_institute, db_date, db_humidity, db_temperature, timedata, voltagedata, ydata, yerr, tempdata, humidata, I_max_variation, plot_path, total_flag

if __name__ == "__main__":
    if len(sys.argv)==1:
        print('Please provide database file(s) as argument(s).')
    else:
        analyseIT(sys.argv[1:])
