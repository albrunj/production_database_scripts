#!/usr/bin/python
#########################################################################
# Andreas Heggelund, Simon Huiberts, Giordon Stark UiO,UiB,CERN         #
# Andreas.heggelund@fys.uio.no, shu011@uib.no, GSTARK@CERN.CH           #
# October 2020                                                          #
#########################################################################
import json
import tkinter as tk # for Python 3 version
from tkinter import Button
from tkinter import E
from tkinter import END
from tkinter import filedialog
from tkinter import Frame
from tkinter import Label
from tkinter import Menu
from tkinter import N
from tkinter import OptionMenu
from tkinter import S
from tkinter import Scrollbar
from tkinter import StringVar
from tkinter import Text
from tkinter import W

import itkdb

try:
    input = raw_input
except NameError:
    pass

#setting up authentication for the itkdb
#Be sure to have set up the environment variables ITKDB_ACCESS_CODE's
client = itkdb.Client()
client.user.authenticate()


path = ""
attachment = 0
user_choices = {
                "dd_project": "",
                "dd_subProject": "",
                "dd_institution": "",
                "dd_component": "",
                "dd_version": "",
                "dd_vendor":"",
                "dd_sensorType":""
}


# These functions sets the dropdown menus option in the file
def dd_project(*args):
    selected = tkvarP.get().rsplit(':')[0]
    user_choices['dd_project'] = selected

def dd_subProject(*args):
    selected = tkvarSP.get().rsplit(':')[0]
    user_choices['dd_subProject'] = selected

def dd_institution(*args):
    selected = tkvarINST.get().rsplit(':')[0]
    selected = choices_institution.get(selected)
    user_choices['dd_institution'] = selected

def dd_component(*args):
    selected = tkvarCOMP.get().rsplit(':')[0]
    selected = choices_component.get(selected)
    user_choices['dd_component'] = selected

def dd_version(*args):
    selected = tkvarVERS.get().rsplit(':')[0]
    selected = choices_version.get(selected)
    user_choices['dd_version'] = selected

def dd_componentType(*args, tkvarCOMP=None):
    selected = tkvarCOMP.get().rsplit(':')[0]
    option_choice = choices_component.get(selected)
    selected = tkvarT.get().rsplit(':')[0]

#Set the drop down menu for wafer or tile based on user selection
    if option_choice == "SENSOR_WAFER":
        selected = choices_type_wafer.get(selected)

    else:
        selected = choices_type_sensor.get(selected)

    user_choices['dd_componentType'] = selected

def dd_vendor(*args):
    selected = tkvarVEND.get().rsplit(':')[0]
    selected = choices_vendor.get(selected)
    user_choices['dd_vendor'] = selected

def dd_sensorType(*args):
    selected = tkvarSENST.get().rsplit(':')[0]
    selected = choices_senstype.get(selected)
    user_choices['dd_sensorType'] = selected

#Callback function of button
def buttonCallback():
    global path
    global post_file
    switch = user_choices.get("dd_component")
    global attachment
    Clearsuccessmsg()

    #Generates the correct templates for filling the entries: Wafer or tile
    if switch == "SENSOR_TILE":
        if textAttachment.get('1.0', END) == "\n":
            data_dict = client.get('generateComponentTypeDtoSample', json={'project': 'P', 'code': 'SENSOR_TILE'})
            data_dict['properties']['SENSOR_TYPE_OR_TEST_STRUCTURE'] = user_choices.get("dd_sensorType")
        else:
            print('No attachment yet for Tiles')
            attachment = 1

    if switch == "SENSOR_WAFER":
        if textAttachment.get('1.0', END) == "\n":
            data_dict = client.get('generateComponentTypeDtoSample', json={'project': 'P', 'code': 'SENSOR_WAFER'})
            data_dict['properties']['DICING'] = dicing_vendor.get('1.0', END).rstrip('\n')
            data_dict['properties']['UBM'] = UBM_vendor.get('1.0', END).rstrip('\n')
        else:
           print('No attachment yet for Wafers')
    elif switch == "":
        print("No component type selected. Please choose what to register.")
        return

    #Debugging print
    #temp_display_file = tempfile.TemporaryFile()

    #Adding the entries into the template
    data_dict['project'] = user_choices.get("dd_project")
    data_dict['subproject'] = user_choices.get("dd_subProject")
    data_dict['institution'] = user_choices.get("dd_institution")
    data_dict['componentType'] = user_choices.get("dd_component")
    data_dict['type'] = user_choices.get("dd_componentType")
    data_dict['properties']['VERSION'] = user_choices.get("dd_version")
    data_dict['properties']['MAIN_VENDOR'] = user_choices.get("dd_vendor")
    data_dict['properties']['MAN_SNO'] = manufacturer_SNO.get('1.0', END).rstrip('\n')

    if attachment == 1:
        attachment_list = data_dict["attachments"][0]
        attachment_list["filename"] = textAttachment.get('1.0', END).rstrip('\n')

    #print json data to check correctness:
    #print(json.dumps(data_dict, indent=4, sort_keys=True))

    temp_display_dict=json.dumps(data_dict)
    post_file = data_dict

    textJson.delete('1.0', END)
    textJson.insert(END,temp_display_dict)

#Function to change window size
def Resize():
    buttonContainer.grid(row = 8, column = 10, sticky=(N,W,E,S), padx = 20, pady = 0)
    dropdownContainer.grid(row = 2, column = 2, sticky=(N,W,E,S), padx = 20, pady = 20)
    displayContainer.grid(row = 2, column = 10, sticky=(N,W,E,S), padx = 20, pady = 20)

#Function for opening and adding attachments to uploadTestRunResults
def AddAttachment():
    filename = filedialog.askopenfilename()
    textAttachment.delete('1.0', END)
    textAttachment.insert(END,filename)

#Functions for removing Success message in GUI
def infomsg(message):
    Label(dropdownContainer, text=message,font="Helvetica 14 bold", width=15).grid(row=20, column = 1)


def Clearsuccessmsg():
    Label(dropdownContainer, text='',font="Helvetica 14 bold",fg = "white", width=20, anchor='w').grid(row=32, column = 0)
    Label(dropdownContainer, text='',font="Helvetica 14 bold",fg = "white", width=20, anchor='w').grid(row=34, column = 0)

#Functions for showing Success message in GUI
def Successmsg(serialNumber):
    Label(dropdownContainer, text='Successfully registered!',font="Helvetica 14 bold",fg = "white", bg = "dark green", width=20, anchor='w').grid(row=32, column = 0)
    Label(dropdownContainer, text='SN: {}'.format(serialNumber),font="Helvetica 14 bold",fg = "white", bg = "dark green", width=20, anchor='w').grid(row=34, column = 0)

#Reads in wafer map into a matrix
def ReadMap(vendor):
    #Get the json wafer map by look at the vendor selection
    global Wafer_matrix
    global Wafer_children
    count = 0
    vendor_name = "Vendor{}".format(vendor+1)
    with open('../WaferMap/{}.json'.format(vendor_name), 'r') as f:
        Wafer_json = json.load(f)
        Wafer_vendor = Wafer_json["Vendor"]
        Wafer_matrix = Wafer_json["Map"]
        Wafer_children = Wafer_json["children"]
        print("Wafer matrix for Vendor: {} selected".format(Wafer_vendor))
        print("Loaded wafer matrix map:")
        for row in Wafer_matrix:
            count += len(row)
            print(row)

        print("{} sensor tiles found on this wafer map".format(count))
        print("\n")
        #Sanity check on that vendor selection is the same in vendor in json file
        #if list(vendor_table.keys())[vendor] == vendor_name and vendor_table[vendor_name] == Wafer_vendor:
        print("Is {}: {} and above wafer matrix correct?".format(vendor_name,Wafer_vendor))
        answer = None
        while answer not in ("y", "n"):answer = input("Enter y or n: " ) # nosec
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print("Please enter 'y' or n''")
        #else:
            #print("Table list is {} != {} or Table vendor {} != {}. Please check your vendor and wafer map".format(list(vendor_table.keys())[vendor],vendor_name,vendor_table[vendor_name],Wafer_vendor))
            #return False

#Checks the Manufacuter serial number for Wafer and return False if its incorrect
def Check_Wafer_MANSNO(Wafer_template):

    #Check that the Manufacuter number has 7 digits
    if len(Wafer_template['properties']['MAN_SNO']) != 11:
        print("\nPlease type in correct format of local manufacturer serial number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number")
        return False

    #Find the Manufacturer SN and Wafer number
    try:
        Vendor_number = Wafer_template['properties']['MAN_SNO'].rsplit("-")[0]
        Wafer_Number = Wafer_template['properties']['MAN_SNO'].rsplit("-")[2]

    except:
        print("\nPlease type in correct format of local manufacturer serial number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number")
        return False


    ##Check if the correct vendor is typed in
    selected_vendor = tkvarVEND.get().rsplit(':')[0]

    if Vendor_number != selected_vendor:
        print("Vendor_number: {} is not equal to selected_vendor {}. Please re-check your vendor selection".format(Vendor_number, selected_vendor))
        return False

    ##Check if the Wafer numbers are actually numbers
    if Wafer_Number.isdigit() == True and len(Wafer_Number) == 6 and Wafer_Number != '000000':
        print("Wafer number is = {}. Continuing...".format(str(int(Wafer_Number))))
    else:
        print("\nPlease type in correct format of the Wafer number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number (1)")
        return False

#Checks the Manufacuter serial number for Tiles and return False if its incorrect
def Check_Tile_MANSNO(Sensor_template):

    #Check that the Manufacuter number has 10 digits
    if len(Sensor_template['properties']['MAN_SNO']) != 14:
        print("\nPlease type in correct format of local manufacturer serial number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number and NN is the sensor number (2)")
        return False

    #Find the Manufacturer SN and Wafer number
    try:
        Vendor_number = Sensor_template['properties']['MAN_SNO'].rsplit("-")[0]
        Wafer_Number = Sensor_template['properties']['MAN_SNO'].rsplit("-")[2]
        Sensor_number = Sensor_template['properties']['MAN_SNO'].rsplit("-")[3]

    except:
        print("\nPlease type in correct format of local manufacturer serial number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number and NN is the sensor number (3)")
        return False


    #Check if the correct vendor is typed in
    selected_vendor = tkvarVEND.get().rsplit(':')[0]

    if Vendor_number != selected_vendor:

        print("Vendor_number: {} is not equal to selected_vendor {}. Please re-check your vendor selection".format(Vendor_number, selected_vendor))
        return False

    #Check if the Wafer numbers are actually numbers and none equal to zero
    if Wafer_Number.isdigit() == True and len(Wafer_Number) == 6 and Wafer_Number != '000000':
        print("Wafer number is = {}. Continuing...".format(str(int(Wafer_Number))))
    else:
        print("\nPlease type in correct format of the Wafer number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number and NN is the sensor number (4)")
        return False

    if Sensor_number.isdigit() == True and len(Sensor_number) == 2 and Sensor_number != '00':
        print("Sensor number is = {}. Continuing...".format(str(int(Sensor_number))))
    else:
        print("\nPlease type in correct format of the Wafer number\n")
        print("The correct format is: VX-Y-WWWWWW-NN where X is the vendor number, Y is prototype, pre- or production number, WWWWWW is the Wafer number and NN is the sensor number (5)")
        return False

#Decides if the user will register a wafer or a single sensor tile
def UploadToDatabase(dictionary_template):
    print("\nUploading to ITk Production database...\n")

    if dictionary_template['componentType'] ==  "SENSOR_WAFER":
        if Check_Wafer_MANSNO(dictionary_template) == False:
            return
        print("\nUploading Sensor Wafer to ITk Production database...\n")
        RegisterWafer(dictionary_template)

    elif dictionary_template['componentType'] ==  "SENSOR_TILE":
        if Check_Tile_MANSNO(dictionary_template) == False:
            return
        print("\nUploading Single Sensor Tile to ITk Production database...\n")
        RegisterSingleChild(dictionary_template)

    else:
        print("\n##Please select component to register!\n")

#Function for Single registration of wafer
def RegisterWafer(Wafer_template):

    #Register Wafer
    new_Wafer = client.post('registerComponent', json=Wafer_template)
    Successmsg(new_Wafer['component']['serialNumber'])

    #Ask for automatic children registration
    print("Do you want to automatically register sensor tiles with Wafer Map?")
    infomsg("See terminal")

    #User can choose "y" or "n" to register children automatically
    answer = None
    while answer not in ("y", "n"):answer = input("Enter y or n: " ) # nosec
    if answer == "y":
        AutomaticRegisterChildren(new_Wafer['component']['code'],Wafer_template)
    elif answer == "n":
        return
    else:
        print("Please enter 'y' or n''")

#Automatic registration of several children tiles
def AutomaticRegisterChildren(wafer_code,Wafer_template):

    print("\nUploading children tile to ITk Production database from Wafer Map...\n")

    #Generate new Sensor tile templates and changes entry based on Wafer entries
    child_template = client.get('generateComponentTypeDtoSample', json={'project': 'P', 'code': 'SENSOR_TILE'})
    child_template['institution'] = Wafer_template['institution']
    child_template['subproject'] = Wafer_template['subproject']
    child_template["properties"]['MAIN_VENDOR'] = Wafer_template["properties"]['MAIN_VENDOR']
    child_template["properties"]['VERSION'] = Wafer_template["properties"]['VERSION']

    #Fill in new properties for the tiles
    wafer_object = client.get('getComponent',json = {"project": "P", "component":wafer_code})

    #Read map corresponding to vendor selected
    if ReadMap(Wafer_template["properties"]['MAIN_VENDOR']) == False:
        return

    #child_template['type'] = wafer_object["children"][0]["type"]["code"]
    child_template['type'] = Wafer_children

    #Print all children slots and stores them
    nchildren = 0
    childslot = []

    for child in wafer_object["children"]:
        child_component_code = child["id"]
        print(child['type']['name'])
        print(Wafer_children)
        if child['type']['code'] == Wafer_children:
            childslot.append(child_component_code)
            nchildren+=1
    print("Found {} available children slots for this Wafer!\n".format(nchildren))

    #Register all sensor tiles
    slotnumber = 0
    for row in range(len(Wafer_matrix)):
        for col in range(len(Wafer_matrix[row])):

        #Chages the Sensor_Type according to wafer map
            child_template["properties"]['SENSOR_TYPE_OR_TEST_STRUCTURE'] = Wafer_matrix[row][col]

        #Chages Manufacuter number according to Wafer map
            if slotnumber <= 8:
                Manufacturer_string = Wafer_template["properties"]['MAN_SNO'] + "-0" + str(slotnumber+1)
                print(Manufacturer_string)
            else:
                Manufacturer_string = Wafer_template["properties"]['MAN_SNO'] + "-" + str(slotnumber+1)
                print(Manufacturer_string)

            #Filling in the manufacturer number and registering the child component
            child_template["properties"]['MAN_SNO'] = Manufacturer_string
            print("Registering child: ")
            print(child_template)
            newChildComponent = client.post('registerComponent', json=child_template)
            child_SN = newChildComponent['component']['serialNumber']
            print("Child with SN: {} successfully registed!\n".format(child_SN))

            #Tries to attach the children tile to the parent wafer. If it fails, it gets deleted
            try:
                client.post('assembleComponentBySlot', json = {"parent": wafer_code, "slot": childslot[slotnumber], "child": child_SN, "properties":{"MAPPING_NUMBER":(slotnumber+1)}})
                slotnumber+=1

            except Exception as e:
                print(e)
                print("########  PLEASE SEE ERROR ABOVE ##############")
                client.post('deleteComponent', json={'component': child_SN})
                print("Could not attach child to parent wafer. Deleting children component")
                return


#Single registration of child
def RegisterSingleChild(Sensor_template):

    #Get the vendor number and Wafer number
    Wafer_MAN_SNO = Sensor_template['properties']['MAN_SNO'].rsplit("-",1)[0]
    Sensor_number = Sensor_template['properties']['MAN_SNO'].rsplit("-",1)[1]

    #Get the component with this Number
    print("Searching for Wafer with number: {}".format(Wafer_MAN_SNO))
    MAN_SNO_list = client.get('listComponentsByProperty', json = {"filterMap":{"project": 'P', "subproject": Sensor_template['subproject'],
    "componentType":"SENSOR_WAFER","propertyFilter": [{"code":"MAN_SNO","operator": "=","value":Wafer_MAN_SNO}]}})

    #Prints out the component list for debugging
    #print(MAN_SNO_list.total)

    if MAN_SNO_list.total == 0:
        print("Can't find any matching Wafer with the given local manufacturer SN.")
        print("Please register the wafer or type in correct local manufacturer SN")
        return

    #Finds the wafer object in the list
    for i, comp in enumerate(MAN_SNO_list):
        print("Found Parent Wafer with SN: {}".format(comp['serialNumber']))
        wafer_object = client.get('getComponent',json = {"project": "P", "component":comp['code']})
        if wafer_object['state'] == 'deleted':
            print("Found one deleted component, searcing for next..")
            wafer_code = comp['code']
            continue
        #Printing for debugging
        #print(comp['state'])
        #print(wafer_object['state'])
        wafer_code = comp['code']
        break

    #Registration of children tiles
    newChildComponent = client.post('registerComponent', json=Sensor_template)
    child_SN = newChildComponent['component']['serialNumber']

    #Getting the children slot corresponding with sensor number and attaching it to parent wafer
    #If it fails to attach it, it will delete the children tile

    #V3-0123-76

    for child in wafer_object["children"]:
        if child['type']['code'] == Sensor_template["type"]:
            if child['component'] == None:
                child_component_code = child['id']
                print(child)
                break
    try:
        print("Attaching child to parent wafer in slot number: {}".format(int(Sensor_number)-1))
        client.post('assembleComponentBySlot', json = {"parent": wafer_code, "slot": child_component_code, "child": child_SN,"properties":{"MAPPING_NUMBER":int(Sensor_number)}})
        Successmsg(newChildComponent['component']['serialNumber'])
    except Exception as e:
        print(e)
        print("########  PLEASE SEE ERROR ABOVE ##############")
        client.post('deleteComponent', json={'component': child_SN})
        print("Could not attach child to parent wafer. Deleting children component")
        return


#Start of main loop - called root
root = tk.Tk()
root.title("ITk production database - Register component")

#Setting up menu bar in root window
menubar = Menu(root)
root.config(menu=menubar)

filemenu = Menu(menubar, tearoff=0)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

viewmenu = Menu(menubar, tearoff = 0)
viewmenu.add_separator()
viewmenu.add_command(label="Resize", command=Resize)
menubar.add_cascade(label="View", menu=viewmenu)



# Declaring widgets position and spacing in the GUI frame
buttonContainer = Frame(root)
buttonContainer.grid(row = 8, column = 10, sticky=(N,W,E,S), padx = 100, pady = 100)

dropdownContainer = Frame(root)
dropdownContainer.grid(row = 2, column = 2, sticky=(N,W,E,S), padx = 50, pady = 100)

displayContainer = Frame(root)
displayContainer.grid(row = 2, column = 10, sticky=(N,W,E,S), padx = 50, pady = 100)

# Declaring variables to be traced
tkvarP = StringVar(root)
tkvarSP = StringVar(root)
tkvarINST = StringVar(root)
tkvarCT = StringVar(root)
tkvarT = StringVar(root)
tkvarVERS = StringVar(root)
tkvarVEND = StringVar(root)
tkvarID = StringVar(root)
tkvarCMNT = StringVar (root)
tkvarCOMP = StringVar(root)
tkvarSENST = StringVar(root)


# Dictionaries for dropdown options and module uploads
# Institutions, and type of sensor/wafer is taken from DB via. client.get() method

choices_project = { 'P: Pixels' }

choices_subProject = { 'PG: Pixel General',
                       'PI: Inner Pixels'
}

choices_institution = {inst['name']: inst['code'] for inst in client.get('listInstitutes') for il in inst.get('componentType', []) for comp in il.get('itemList', []) if comp['code'].startswith('SENSOR_')
}

choices_component = { "Sensor Wafer": "SENSOR_WAFER",
                      "Sensor Tile": "SENSOR_TILE",
}

choices_type_wafer = {type['name']: type['code'] for comptype in client.get('listComponentTypes', json={'project': 'P'}) if comptype['code'] == 'SENSOR_WAFER' for type in comptype.get('types', []) if type['existing'] == True
}

choices_type_sensor = {type['name']: type['code'] for comptype in client.get('listComponentTypes', json={'project': 'P'}) if comptype['code'] == 'SENSOR_TILE' for type in comptype.get('types', []) if type['existing'] == True
}

choices_vendor = {"V1":0,
                  "V2":1,
                  "V3":2,
                  "V4":3,
                  "V5":4,
                  "V6":5,
                  "V7":6,
                  "V8":7
                 }

choices_version = {}

choices_senstype = {"RD53A test structure":0,
                    "Single":1,
                    "Double":2,
                    "Quad":3,
                    "Planar diode test structure":4,
                    "Strip test structure":5,
                    "Mini-sensor test structure":6,
                    "Inter pixel capacitance test structure":7,
                    "Biasing test structure (poli-Si resistivity or punch through)":8,
                    "3D diode test structure":9
                    }

# Setting default options of dropdowns and widgets with options
tkvarP.set('                   -                   ')
tkvarSP.set('                   -                   ')
tkvarINST.set('                   -                   ')
tkvarCOMP.set('                   -                   ')
tkvarT.set('                   -                   ')
tkvarVERS.set('                   -                   ')
tkvarVEND.set('                   -                   ')
tkvarSENST.set('                   -                   ')

# Global variables for componentType tracing
option_wafer = False
option_sensor = False
menu_exist = False

# Creating widgets ##############################################################
Label(dropdownContainer, text="Please choose the settings for your registration:", font="Helvetica 18 bold", width = 45, anchor = 'e').grid(row=0, column=0, pady = 25)

popupMenu = OptionMenu(dropdownContainer, tkvarP, *choices_project)
Label(dropdownContainer, text="Project:", width=30, anchor='w').grid(row = 2, column = 0)
popupMenu.grid(row = 3, column =0)

popupMenu2 = OptionMenu(dropdownContainer, tkvarSP, *choices_subProject)
Label(dropdownContainer, text="Subproject:", width=30, anchor='w').grid(row = 4, column = 0)
popupMenu2.grid(row = 5, column = 0 )

popupMenu3 = OptionMenu(dropdownContainer, tkvarINST, *choices_institution)
Label(dropdownContainer, text="Institution:", width=30, anchor='w').grid(row = 6, column = 0)
popupMenu3.grid(row = 7, column = 0 )

popupMenu4 = OptionMenu(dropdownContainer, tkvarCOMP, *choices_component)
Label(dropdownContainer, text="Component type:", width=30, anchor='w').grid(row = 8, column = 0)
popupMenu4.grid(row = 9, column = 0 )

popupMenu6 = OptionMenu(dropdownContainer, tkvarVEND, *choices_vendor)
Label(dropdownContainer, text="Vendor:", width=30, anchor='w').grid(row = 12, column = 0)
popupMenu6.grid(row = 13, column = 0 )

# Based on the user selection, tries to destory old contains and create new ones
def update_types(*args):
    tkvarT.set('                   -                   ')

    # Define gloal parameters to be traced
    global popupMenu5
    global dicing_vendor
    global UBM_vendor
    global popupMenu7
    global option_wafer
    global option_sensor
    #global parent_wafer

    selected = tkvarCOMP.get().rsplit(':')[0]
    option_choice = choices_component.get(selected)

    # Tries to destroy old selected boxes and set string container to empty
    if option_wafer == True:
        popupMenu5.destroy()
        dicing_vendor.destroy()
        UBM_vendor.destroy()
        option_wafer = False

    if option_sensor == True:
        popupMenu7.destroy()
        popupMenu5.destroy()
        option_sensor = False


    Label(dropdownContainer, text='', width=30, anchor='w').grid(row=14, column = 0)
    Label(dropdownContainer, text='', width=30, anchor='w').grid(row=16, column = 0)

    # Creates the new dropdowncintains depending on wafer or sensor user selection
    if option_choice == "SENSOR_WAFER":

        popupMenu5 = OptionMenu(dropdownContainer, tkvarT, *choices_type_wafer)
        Label(dropdownContainer, text="Type:", width=30, anchor='w').grid(row = 10, column = 0)
        popupMenu5.grid(row = 11, column = 0 )

        Label(dropdownContainer, text='Dicing Vendor (optional)', width=30, anchor='w').grid(row=14, column = 0)
        dicing_vendor = Text(dropdownContainer, height = 1, width = 30)
        dicing_vendor.grid(row = 15, column = 0)

        Label(dropdownContainer, text='UBM Vendor (optional)', width=30, anchor='w').grid(row=16, column = 0)
        UBM_vendor = Text(dropdownContainer, height = 1, width = 30)
        UBM_vendor.grid(row = 17, column = 0)

        Label(dropdownContainer, text='Local Manufacturer SN (VX-Y-WWWWW):', width=40, anchor='w').grid(row=21, column = 0)

        option_wafer = True

    if option_choice == "SENSOR_TILE":

        popupMenu5 = OptionMenu(dropdownContainer, tkvarT, *choices_type_sensor)
        Label(dropdownContainer, text="Type:", width=30, anchor='w').grid(row = 10, column = 0)
        popupMenu5.grid(row = 11, column = 0 )

        popupMenu7 = OptionMenu(dropdownContainer, tkvarSENST, *choices_senstype)
        Label(dropdownContainer, text="Sensor type or test structure:", width=30, anchor='w').grid(row = 14, column = 0)
        popupMenu7.grid(row = 15, column = 0 )

        Label(dropdownContainer, text='Local Manufacturer SN (VX-Y-WWWWWW-NN):', width=40, anchor='w').grid(row=21, column = 0)

        option_sensor = True

#Creates Version pop menu based on user selection on type
def update_version(*args):

    tkvarVERS.set('                          -                       ')

    global menu_exist
    global popMenuVen
    got_choices = False

    #Reads in type
    selected = tkvarT.get().rsplit(':')[0]
    option_type = choices_type_sensor.get(selected)

    #Destroys old version type to refresh it
    if menu_exist == True:
        popMenuVen.destroy()
        choices_version.clear()
        menu_exist == False

    #If type is not selected for sensor, try wafer selection
    if option_type == None:
        option_type = choices_type_wafer.get(selected)

    #Fetches the avaible versions on selected component from Database and store it in array
    if option_type != None:
        for comptype in client.get('listComponentTypes',json={'project': 'P'}):
             if comptype['code'] == "SENSOR_TILE" or comptype['code'] == "SENSOR_WAFER":
                  for type in comptype.get('types', []):
                      if type['code'] == option_type:
                          for version in type["version"]:
                              if type["version"][version] == True:
                                  choices_version[version] = version
                                  got_choices = True

    #Crate vendor choices conatiner
    if got_choices == True:
        popMenuVen = OptionMenu(dropdownContainer, tkvarVERS, *choices_version)
        Label(dropdownContainer, text="Version:", width=30, anchor='w').grid(row = 18, column = 0)
        popMenuVen.grid(row = 19, column = 0 )
        menu_exist = True

    #choices_versions = {type['version'][0] for comptype in client.get('listComponentTypes',json={'project': 'P'}) if comptype['code'] == "SENSOR_TILE" for type in comptype.get('types', []) if type['code'] == option_type}

#Create label
textJson = Text(displayContainer, height = 25, width = 45)
textJson.grid(row = 5, column = 0)

Label(dropdownContainer, text='Local Manufacturer SN:', width=30, anchor='w').grid(row=21, column = 0)
manufacturer_SNO = Text(dropdownContainer, height = 1, width = 30)
manufacturer_SNO.grid(row = 22, column = 0)

browsebutton = Button(dropdownContainer, text="Browse", command=AddAttachment, width = 8, anchor='w')

textAttachment = Text(dropdownContainer, height = 1, width = 30)
textAttachment.grid(row=24, column=0)

Label(dropdownContainer, text="      Attachments: ", font="Helvetica 14 bold", width=30, anchor ='w').grid(row = 23, column = 0)
browsebutton.grid(row = 24, column = 1)

# Adding scroll functionality to text field
scroll = Scrollbar(displayContainer)
scroll.config(command=textJson.yview)
textJson.config(yscrollcommand=scroll.set)

button = Button(buttonContainer, text = "Set parameters of component", command = buttonCallback)
button.grid(row = 1, column = 1 )

uploadButton = Button(buttonContainer, text = "Register component", command = lambda: UploadToDatabase(post_file))
uploadButton.grid(row = 1, column = 2)

# Link functions to widget interactions
tkvarP.trace('w', dd_project)
tkvarSP.trace('w', dd_subProject)
tkvarINST.trace('w', dd_institution)
tkvarCOMP.trace('w', dd_component)
tkvarCOMP.trace('w', update_types)
tkvarT.trace('w', lambda *args: dd_componentType(*args, tkvarCOMP=tkvarCOMP))
tkvarT.trace('w', update_version)
tkvarVERS.trace('w', dd_version)
tkvarVEND.trace('w', dd_vendor)
tkvarSENST.trace('w', dd_sensorType)

root.mainloop()
