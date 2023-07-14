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


def analyseINTER_RES(argv):
    for data_files in argv:

        with open(data_files, 'r') as data:
            data_file = json.load(data)

        db_sensorID = data_file["component"]
        db_measType = data_file["test"]
        print(db_measType)
        print("")

        if db_measType != "Inter-pixel resistance":
            raise Exception('Not correct data file!')
        db_institute = data_file["institution"]
        db_date = data_file["date"]

        resistance = data_file["resistance"]

        total_flag = True

        print('{:48} {}'.format('Sensor ID:', db_sensorID))
        print('{:48} {}'.format('Resistance: ', resistance))

        print('{:48} {}'.format('Does the sensor meet all MS-It criteria?', coloredFlag(total_flag)))

        return db_sensorID, db_institute, db_date, resistance, total_flag

if __name__ == "__main__":
    if len(sys.argv)==1:
        print('Please provide database file(s) as argument(s).')
    else:
        analyseINTER_RES(sys.argv[1:])
