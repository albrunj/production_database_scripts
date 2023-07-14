#########################################################################
# Andreas Gisen, Simon Huiberts, Giordon Stark UiO,UiB,CERN             #
# andreas.gisen@tu-dortmund.de, shu011@uib.no, GSTARK@CERN.CH           #
# October 2020                                                          #
#########################################################################
# -*- coding: utf-8 -*-
import json
import sys

def coloredFlag(flag):
    if flag:
        return 'Yes, \033[1;32m[PASSED]\x1b[0m'
    else:
        return 'No, \033[1;31m[FAILED]\x1b[0m'


def analyseMETROLOGY(argv, type):
    for data_files in argv:

        with open(data_files, 'r') as data:
            data_file = json.load(data)

        db_sensorID = data_file["component"]
        db_measType = data_file["test"]
        print(db_measType)
        print("Metrology on {}".format(type))


        if db_measType != "Metrology on {}".format(type):
            raise Exception('Not correct data file!')
        db_institute = data_file["institution"]
        db_date = data_file["date"]

        if type == "wafer":
            wafer_bow = data_file["wafer bow"]

            #If wafer bow is 6'' in diameter
            #if wafer_bow > 100:
                #False
            #else:
            #    True

            #if Waferbow is 8'' in diameter
            #if waferbow > 150
              #False
            #else true
            #

        elif type == "sensor":
            sensor_bow =  data_file["sensor bow"]
            sensor_thickness = data_file["sensor thickness"]

            #Ask about this

        else:
            print("Specify wafer or sensor in data file")

        total_flag = True

        if type == "wafer":
            print('{:48} {}'.format('Wafer ID:', db_sensorID))
            print('{:48} {}'.format('Wafer bow:', wafer_bow))
            print('{:48} {}'.format('Does the wafer meet all MS-It criteria?', coloredFlag(total_flag)))

            return db_sensorID, db_institute, db_date, wafer_bow

        if type == "sensor":
            print('{:48} {}'.format('Sensor ID:', db_sensorID))
            print('{:48} {}'.format('Sensor bow:', sensor_bow))
            print('{:48} {}'.format('sensor_thickness:', sensor_thickness))

            print('{:48} {}'.format('Does the sensor meet all MS-It criteria?', coloredFlag(total_flag)))

            return db_sensorID, db_institute, db_date, sensor_bow, sensor_thickness, total_flag

if __name__ == "__main__":
    if len(sys.argv)==1:
        print('Please provide database file(s) as argument(s).')
    else:
        analyseMETROLOGY(sys.argv[1:])
