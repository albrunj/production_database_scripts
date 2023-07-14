#!/usr/bin/python
#########################################################################
# Andreas Heggelund, Simon Huiberts, Giordon Stark UiO,UiB,CERN         #
# Andreas.heggelund@fys.uio.no, shu011@uib.no, GSTARK@CERN.CH           #
# October 2020                                                          #
#########################################################################
import json
import sys
import tkinter as tk
from tkinter import Button
from tkinter import filedialog
from tkinter import Label
from tkinter import OptionMenu
from tkinter import StringVar
from tkinter import W

# Insert path to analysis scripts
sys.path.insert(0, '../Analyses/')


# importing Analysis scripts and tool scripts
import analyseIV as IV
import analyseCV as CV
import analyseIT as IT
import analyseMETROLOGY as METROLOGY
import analyseVISUAL as VISUAL
import analyseINTER_CAP as INTER_CAP
import analyseINTER_RES as INTER_RES
import textToJSON as CONVERT
import itkdb

client = itkdb.Client()
client.user.authenticate()

# Dictionary for selecting what kind of test to be performed
list_of_tests = {
                 "IV measurement on sensor": "IV_MEASURE_TILE",
                 "CV measurement on sensor": "CV_MEASURE_TILE",
                 "IT measurement on sensor": "IT_MEASURE_TILE",
                 #"IV measurement on tile": "IV_MEASURE_WAFER",
                 #"CV measurement on wafer": "CV_MEASURE_WAFER",
                 #"CV measurement of test structure": "Entry_for_CV_test_struct",
                 #"IT measurement on Wafer": "IT_MEASURE_WAFER",

                 "Metrology on wafer": "BOW_WAFER",
                 "Metrology on sensor": "BOW_THICK_SENSOR",


                 "Visual inspection on wafer": "VISUAL_WAFER",
                 "Visual inspection on sensor": "VISUAL_SENSOR",
                 #"Inspection of diced edges": "Entry_for_visual_inspect_diced_edge",

                 "Inter-pixel resistance on strip": "INTER-PIXEL_RES",
                 "Inter-pixel capacitance on strip": "INTER-PIXEL_CAP"
                 #"Inter pixel capacitance measurement": "Entry_for_IPC",
}

# This class contains the functions needed to alter the json files that
# are being pushed to the databaseself.

class Settings:
    # __init__ sets up the GUI main loop and creates widgets such as buttons, dropdown lists etc.
    # Data arrays are stored here as well
    def __init__(self):
        # Need to have declared arrays for datafile and input storage
        self.data_files = []
        self.depletion_voltage = []
        self.serial_no = []
        self.institute = []
        self.date = []
        self.flag = []
        self.humidity = []
        self.temperature = []
        self.image = []

        # Declaration of dummy variables to store analysis results to be inserted into json file.
        # These will be updated in the various test upload screens
        self.data_array_time = []
        self.data_array_x = []
        self.data_array_y = []
        self.data_array_yerr = []
        self.data_array_temp = []
        self.data_array_humid = []


        #Data array for extra data for tests
        self.bow = []
        self.dummy_array1 = []
        self.dummy_array2 = []
        self.dummy_array3 = []
        self.dummy_array4 = []

        #Counter for knowing number of uploaded files
        self.counter = 0


        root = tk.Tk()

        self.master = root
        self.master.title("ITk production database - Upload Test results")

        label0 = Label(self.master, text="Choose a test and corresponding data file(s): ")
        label0.grid(row=0,column=0, pady=10, sticky = W, columnspan = 3, padx=20)

        tkvartest = StringVar(root)
        tkvartest.set('Please choose a test')
        dropdown_menu = OptionMenu(self.master, tkvartest, *list_of_tests)
        dropdown_menu.grid(row = 3,column=0, sticky = W, padx = 20)

        label2 = Label(self.master, text="Select datafile: ")
        label2.grid(row=6,column=0, pady=10, sticky = W, columnspan = 3, padx=20)

        browse_test_data = Button(self.master, text="Browse data files", command =  lambda: self.GetDataFiles(self.data_files))
        browse_test_data.grid(row=6,column=0, sticky = W, padx = 20)

        analyse_data = Button(self.master, text="Analyse data files", command= lambda: self.Analyse_test(self.data_files, tkvartest.get()))
        analyse_data.grid(row = 7, column = 0, pady = 20, ipadx = 50, padx = 20, columnspan = 3)

        uploadData = Button(self.master, text="Upload test results", command= lambda: self.UploadtestData(tkvartest.get(), self.data_files))
        uploadData.grid(row=8, column = 0, pady = 20, ipadx = 50, padx = 20, columnspan = 3)

        close_button = Button(self.master, text="Exit", command=self.quit)
        close_button.grid(row=9, column = 0, pady = 20, ipadx = 50, padx = 20, columnspan = 3)

        root.mainloop()


    # Opens a pop-up window when the user presses the "exit"-button
    def quit(self):
        exit_frame = tk.Toplevel()

        question_label = tk.Label(exit_frame, text="Are you sure you want to quit the application?")
        question_label.grid(column=0, row=0, columnspan=2)

        yes_button = tk.Button(exit_frame, text="Yes", command=quit)
        yes_button.grid(column=0, row=2, padx=20)

        no_button = tk.Button(exit_frame, text="No", command=exit_frame.destroy)
        no_button.grid(column=2, row=2, sticky=W)

    #Functions for showing Success message in GUI
    def Successmsg(self, serialNumber):
        Label(self.master, text='Successful test registered!',font="Helvetica 14 bold",fg = "white", bg = "dark green", width=20).grid(row=10, column = 0, pady = 0, ipadx = 50, padx = 20)

        #Functions for clearing Success message in GUI
    def Clearsuccessmsg(self):
        Label(self.master, text='',font="Helvetica 14 bold",fg = "white", width=20, anchor='w').grid(row=10, column = 0, pady = 0, ipadx = 50, padx = 20)

    # Simple function that is bound to the "Browse for data files" button.
    # Lets the user append data files to an array to be batch analysed.
    def GetDataFiles(self, testDataFile):

        self.Clearsuccessmsg()

        testDataFile.append(filedialog.askopenfilename(initialdir = "../data"))

        ##Convert txt.file to JSON format##
        current_file = testDataFile[self.counter].split(".")
        #print(current_file[-1])
        if current_file[-1] == "txt":
            print("Thanks Kenny")
            ####Function that converts txt to JSON file ###
            myDict=CONVERT.Convert(testDataFile[self.counter], debug=False)
            self.jsonPathName = testDataFile[self.counter].replace("txt","json")
            CONVERT.Write(myDict,self.jsonPathName)
            testDataFile[self.counter] = self.jsonPathName

        self.counter += 1

    ####Function that converts txt to JSON file ####
    def Analyse_test(self, data_files, test_type):

        which_test = list_of_tests.get(test_type)

        if which_test == "IV_MEASURE_TILE": # or which_test == "IV_MEASURE_WAFER"
            self.analyseIV(data_files)

        elif which_test == "CV_MEASURE_TILE": #Or which_test == "CV_MEASURE_WAFER" or :
            self.analyseCV(data_files)

        elif which_test == "IT_MEASURE_TILE": #or which_test == "IT_MEASURE_WAFER":
            self.analyseIT(data_files)

        elif which_test == "BOW_WAFER":
            self.analyseMETROLOGY(data_files, type = "wafer")

        elif which_test == "BOW_THICK_SENSOR":
            self.analyseMETROLOGY(data_files, type = "sensor")

        elif which_test == "VISUAL_WAFER":
            self.analyseVISUAL(data_files, type = "wafer")

        elif which_test == "VISUAL_SENSOR":
            self.analyseVISUAL(data_files, type = "sensor")

        elif which_test == "INTER-PIXEL_CAP":
            self.analyseINTER_CAP(data_files)

        elif which_test == "INTER-PIXEL_RES":
            self.analyseINTER_RES(data_files)

        else:
            print("You have chosen a test type that has not been implemented yet.")

    # This function analyses IV data, as many as you specify
    def analyseIV(self, DataFileArray):
        number_of_errors = 0
        for i in range(len(DataFileArray)):

            try:

                db_sensorID, db_institute, db_date, db_humidity, db_temperature, timedata, xdata, ydata, yerr, tempdata, humidata, Vbd, Ilc, plot_path, total_flag = IV.analyseIV([DataFileArray[i]])

                #Parameters arrays
                self.serial_no.append(db_sensorID)
                self.institute.append(db_institute)
                self.date.append(db_date)
                self.flag.append(total_flag)
                self.humidity.append(db_humidity)
                self.temperature.append(db_temperature)
                self.image.append(plot_path)

                # Data Arrays
                self.data_array_time.append(timedata)
                self.data_array_x.append(xdata)
                self.data_array_y.append(ydata)
                self.data_array_yerr.append(yerr)
                self.data_array_temp.append(tempdata)
                self.data_array_humid.append(tempdata)

                #Extra arrays for test
                self.dummy_array1.append(Vbd)
                self.dummy_array2.append(Ilc)

            except IndexError:
                print("\nERROR: Different length of data file and depletion voltage arrays")
                number_of_errors = +1


            finally:
                if number_of_errors > 0:
                    print('\nEncountered %s error(s), the output above may hint at the cause. ')

    # CV analysis function. takes an array of datafiles as input found through the "Browse" button.
    def analyseCV(self, DataArray):

        number_of_errors = 0
        for i in range(len(DataArray)):
            try:
                db_sensorID, db_institute, db_date, db_humidity, db_temperature, timedata, xdata, ydata, yerr, tempdata, humidata, Vdepl, plot_path, total_flag = CV.analyseCV([DataArray[i]])

                #Parameters arrays
                self.serial_no.append(db_sensorID)
                self.institute.append(db_institute)
                self.date.append(db_date)
                self.flag.append(total_flag)
                self.humidity.append(db_humidity)
                self.temperature.append(db_temperature)
                self.image.append(plot_path)

                # Data Arrays
                self.data_array_time.append(timedata)
                self.data_array_x.append(xdata)
                self.data_array_y.append(ydata)
                self.data_array_yerr.append(yerr)
                self.data_array_temp.append(tempdata)
                self.data_array_humid.append(tempdata)

                #Extra arrays for test
                self.dummy_array1.append(Vdepl)

            except IndexError:
                print("Index error, please retry the upload")
                number_of_errors = +1

            finally:
                if number_of_errors > 0:
                    print('\nEncountered %s error(s), the output above may hint at the cause. ')

    # the same goes for IT scan measurements
    def analyseIT(self, DataArray):
        number_of_errors = 0
        for i in range(len(DataArray)):

            try:
                db_sensorID, db_institute, db_date, db_humidity, db_temperature, timedata, voltagedata, ydata, yerr, tempdata, humidata, I_max_variation, plot_path, total_flag = IT.analyseIT([DataArray[i]])

                #Parameters arrays
                self.serial_no.append(db_sensorID)
                self.institute.append(db_institute)
                self.date.append(db_date)
                self.flag.append(total_flag)
                self.humidity.append(db_humidity)
                self.temperature.append(db_temperature)
                self.image.append(plot_path)
                # Data Arrays
                self.data_array_time.append(timedata)
                self.data_array_x.append(voltagedata)
                self.data_array_y.append(ydata)
                self.data_array_yerr.append(yerr)
                self.data_array_temp.append(tempdata)
                self.data_array_humid.append(tempdata)

                #Extra arrays for test
                self.dummy_array1.append(I_max_variation)

            except IndexError:
                print("Index error, please retry the upload")
                number_of_errors = +1

            finally:
                if number_of_errors > 0:
                    print('\nEncountered %s error(s), the output above may hint at the cause. ')

    def analyseMETROLOGY(self, DataArray, type):
        number_of_errors = 0
        for i in range(len(DataArray)):

            if type == "wafer":

                try:
                    db_sensorID, db_institute, db_date, wafer_bow, total_flag = METROLOGY.analyseMETROLOGY([DataArray[i]], type)

                        #Parameters arrays
                    self.serial_no.append(db_sensorID)
                    self.institute.append(db_institute)
                    self.date.append(db_date)
                    self.flag.append(total_flag)

                    #Extra arrays for test
                    self.dummy_array1.append(wafer_bow)

                except IndexError:
                    print("Index error, please retry the upload")
                    number_of_errors = +1

                finally:
                    if number_of_errors > 0:
                        print('\nEncountered %s error(s), the output above may hint at the cause. ')

            if type == "sensor":

                try:

                    db_sensorID, db_institute, db_date, sensor_bow, sensor_thickness, total_flag = METROLOGY.analyseMETROLOGY([DataArray[i]],type)

                    #Parameters arrays
                    self.serial_no.append(db_sensorID)
                    self.institute.append(db_institute)
                    self.date.append(db_date)
                    self.flag.append(total_flag)

                    #Extra arrays for test
                    self.dummy_array1.append(sensor_bow)
                    self.dummy_array2.append(sensor_thickness)

                except IndexError:
                    print("Index error, please retry the upload")
                    number_of_errors = +1

                finally:
                    if number_of_errors > 0:
                        print('\nEncountered %s error(s), the output above may hint at the cause. ')


    def analyseVISUAL(self, DataArray, type):
        number_of_errors = 0
        for i in range(len(DataArray)):

            try:
                db_sensorID, db_institute, db_date, comment, total_flag, image_link, total_flag = VISUAL.analyseVISUAL([DataArray[i]], type)

                #Parameters arrays
                self.serial_no.append(db_sensorID)
                self.institute.append(db_institute)
                self.date.append(db_date)
                self.flag.append(total_flag)

                    #Extra arrays for test
                self.dummy_array1.append(comment)
                self.dummy_array2.append(total_flag)
                self.dummy_array3.append(image_link)

            except IndexError:
                print("Index error, please retry the upload")
                number_of_errors = +1

            finally:
                if number_of_errors > 0:
                    print('\nEncountered %s error(s), the output above may hint at the cause. ')

    def analyseINTER_CAP(self, DataArray):
        number_of_errors = 0
        for i in range(len(DataArray)):

            try:
                db_sensorID, db_institute, db_date, capacitance, total_flag = INTER_CAP.analyseINTER_CAP([DataArray[i]])

                #Parameters arrays
                self.serial_no.append(db_sensorID)
                self.institute.append(db_institute)
                self.date.append(db_date)
                self.flag.append(total_flag)

                    #Extra arrays for test
                self.dummy_array1.append(capacitance)

            except IndexError:
                print("Index error, please retry the upload")
                number_of_errors = +1

            finally:
                if number_of_errors > 0:
                    print('\nEncountered %s error(s), the output above may hint at the cause. ')

    def analyseINTER_RES(self, DataArray):
        number_of_errors = 0
        for i in range(len(DataArray)):

            try:
                db_sensorID, db_institute, db_date, resistance, total_flag = INTER_RES.analyseINTER_RES([DataArray[i]])

                #Parameters arrays
                self.serial_no.append(db_sensorID)
                self.institute.append(db_institute)
                self.date.append(db_date)
                self.flag.append(total_flag)

                    #Extra arrays for test
                self.dummy_array1.append(resistance)

            except IndexError:
                print("Index error, please retry the upload")
                number_of_errors = +1

            finally:
                if number_of_errors > 0:
                    print('\nEncountered %s error(s), the output above may hint at the cause. ')


    # Fetches the choice of test from the dropdown menu and gets a matching test type template from
    # the database. This is then filled with the information from the corresponding analysis. Finally this JSON is
    # posted to the database.
    def UploadtestData(self, testType, data_files):

            testfile = list_of_tests.get(testType)

            for i in range(len(data_files)):
                iterations = i+1

                try:
                    if(testfile == None):
                        print("No test selected. Please choose the test you want to upload")

                    elif testfile[0:2] == "IV":

                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_TILE', 'code': 'IV_MEASURE'})

                        # Fetches information about the component, its ID should be given in the datafile header
                        # then gets the code of that component which is needed as the "childParentRelation"
                        # in the API

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]
                        test_data['properties']['HUM'] = self.humidity[i]
                        test_data['properties']['TEMP'] = self.temperature[i]
                        test_data['results']['IV_IMG'] = []


                        test_data["results"]["IV_ARRAY"] = {
                        "time" : self.data_array_time[i],
                        "voltage": self.data_array_x[i],
                        "current": self.data_array_y[i],
                        "sigma current": self.data_array_yerr[i],
                        "temperature": self.data_array_temp[i],
                        "humidity": self.data_array_humid[i]
                        }

                        ##Additional inputs
                        test_data['results']['BREAKDOWN_VOLTAGE'] =self.dummy_array1[i]
                        test_data['results']['LEAK_CURRENT'] = self.dummy_array2[i]

                        # Debugging JSON data
                        #print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)

                        print(self.image[i])
                        f = open(self.image[i], "rb")

                        client.post('createBinaryTestRunParameter', data=dict(testRun=test['testRun']['id'],parameter="IV_IMG"), files=dict(data=f))

                        number_of_files = len(data_files)

                    elif testfile[0:2] == "CV":

                        test_data =  client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_TILE', 'code': 'CV_MEASURE'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]
                        test_data['properties']['HUM'] = self.humidity[i]
                        test_data['properties']['TEMP'] = self.temperature[i]
                        test_data['results']['CV_IMG'] = []

                        test_data["results"]["CV_ARRAY"] = {
                        "Time" : self.data_array_time[i],
                        "Voltage": self.data_array_x[i],
                        "Capacitance": self.data_array_y[i],
                        "Sigma Capacitance": self.data_array_yerr[i],
                        "Temperature": self.data_array_temp[i],
                        "Humidity": self.data_array_humid[i]
                        }

                        test_data['results']['V_FULLDEPL'] =self.dummy_array1[i]

                        # Debugging JSON data
                        #print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)

                        print(self.image[i])
                        f = open(self.image[i], "rb")

                        client.post('createBinaryTestRunParameter', data=dict(testRun=test['testRun']['id'],parameter="CV_IMG"), files=dict(data=f))

                        number_of_files = len(data_files)


                    elif testfile[0:2] == "IT":
                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_TILE', 'code': 'IT_MEASURE'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]
                        test_data['properties']['HUM'] = self.humidity[i]
                        test_data['properties']['TEMP'] = self.temperature[i]
                        test_data['results']['IT_IMG'] = []

                        test_data["results"]["IT_ARRAY"] = {
                        "Time" : self.data_array_time[i],
                        "Voltage": self.data_array_x[i],
                        "Current": self.data_array_y[i],
                        "Sigma Current": self.data_array_yerr[i],
                        "Temperature": self.data_array_temp[i],
                        "Humidity": self.data_array_humid[i]
                        }

                        test_data['results']['LEAK_48H'] = self.dummy_array1[i]

                        print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)

                        print(self.image[i])
                        f = open(self.image[i], "rb")

                        client.post('createBinaryTestRunParameter', data=dict(testRun=test['testRun']['id'],parameter="IT_IMG"), files=dict(data=f))
                        number_of_files = len(data_files)


                    elif testfile[0:9] == "BOW_WAFER":

                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_WAFER', 'code': 'WAFER_BOW'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]

                        test_data["results"]["BOW_VALUE"] = self.dummy_array1[i]
                        print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)
                        number_of_files = len(data_files)

                    elif testfile[0:9] == "BOW_THICK":

                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_TILE', 'code': 'SENSOR_METROLOGY'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]

                        test_data["results"]["BOW_VALUE"] = self.dummy_array1[i]
                        test_data["results"]["SENSOR_THICK"] = self.dummy_array2[i]

                        print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)
                        number_of_files = len(data_files)



                    elif testfile[0:6] == "VISUAL":

                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_WAFER', 'code': 'VISUAL_INSPECTION'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]

                        test_data["results"]["COMMENT"] = self.dummy_array1[i]
                        test_data["results"]["IMAGE_LINK"] = self.dummy_array3[i]

                        print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)
                        number_of_files = len(data_files)


                    elif testfile[0:15] == "INTER-PIXEL_CAP":

                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_TILE', 'code': 'INTER-PIXEL_CAPACITANCE'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]


                        test_data["results"]["CAPACITANCE"] = self.dummy_array1[i]

                        print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)
                        number_of_files = len(data_files)


                    elif testfile[0:15] == "INTER-PIXEL_RES":

                        test_data = client.get('generateTestTypeDtoSample', json={'project': 'P', 'componentType': 'SENSOR_TILE', 'code': 'INTER-PIXEL_RESISTANCE'})

                        test_data['component'] = self.serial_no[i]
                        test_data['institution'] = self.institute[i]
                        test_data["date"] = self.date[i]
                        test_data["passed"] = self.flag[i]

                        test_data["results"]["RESISTANCE"] = self.dummy_array1[i]

                        print(json.dumps(test_data, indent=4, sort_keys=True))

                        test = client.post('uploadTestRunResults', json=test_data)
                        number_of_files = len(data_files)

                    print(f"Uploading {list_of_tests.get(testType)} test data for {iterations}/{number_of_files} file(s)")
                    successfull_iterations = i+1

                except IndexError:
                    print(f"\n\nWOAH!! Something went wrong!\nUploaded only {successfull_iterations}/{number_of_files} files.\n")
            if iterations == number_of_files:
                print(f"\n\nDone uploading {successfull_iterations}/{number_of_files} data files of {list_of_tests.get(testType)} tests!\n\n")
                self.Successmsg(self.serial_no[i])
            # Reset arrays used for test upload
            self.data_files = []
            self.depletion_voltage = []
            self.serial_no = []
            self.institute = []
            self.date = []
            self.flag = []
            self.humidity = []
            self.temperature = []
            self.image = []
            self.data_array_time = []
            self.data_array_x = []
            self.data_array_y = []
            self.data_array_yerr = []
            self.data_array_temp = []
            self.data_array_humid = []
            self.dummy_array1 = []
            self.dummy_array2 = []
            self.dummy_array3 = []
            self.dummy_array4 = []


settings = Settings()
