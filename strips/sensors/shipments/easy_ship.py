#!/usr/bin/python
import json
from pathlib import Path

import itkdb
from __path__ import updatePath
updatePath()

from strips.sensors.SensorSNUtils import checkSN_basic
from strips.sensors.SensorSNUtils import get_codes_bulk



# VF, 2021-06-22: to make a shipment with minimal footwork
#     There are two types of inputs:
#       - either from a Control File, where keywords are separated by semicolon from the values
#       - or, if the file argument is not present, interactively
#
# ISSUE: apparently, "status" key is not supported for "creatShipment", contrary to the online documentation
#
# VF, 2021-08-11: to add option of only creating the shipment, without sending it off
#
#

def get_shipment_params_file(ControlFile):

    # initialize
    shName     = ""
    shSender   = ""
    shRecip    = ""
    shTrack    = ""
    shService  = ""
    shType     = ""
    #shStatus   = "" # let's not do this stuff, should always get into "inTransit"
    iSNs       = ""
    iFile      = ""
    shComment  = ""

    # find my file and read it
    fAbsPath = Path(ControlFile)
    myLines = []
    if fAbsPath.is_file():
        with open(ControlFile,'r') as iFile:
            myLines = iFile.readlines()
    else:
        print(" Funny file, cannot process ")
        return shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment

    for aLine in myLines:
        # want to have commented out lines
        if aLine.startswith("#") : 
            continue
        # remove the comments, which start with "#" symbol
        listWords = aLine.split("#") # presume it could be a comma-separated list
        myRealData = listWords[0]
        # presume the keyword and the value are separated by ":"
        listKeyValue = myRealData.split(":")
        if len(listKeyValue) != 2:
            print("wrong Control File Syntax: expect only 1 Key and 1 Value in a line. Exiting...")
            print("got:")
            print(listKeyValue)
            return shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment
        # assign the key and its value
        rawKey = listKeyValue[0]
        rawVal = listKeyValue[1]
        # remove spaces
        aKey = rawKey.strip()
        aVal = rawVal.strip()
        # clean them
        aKey.strip()
        aVal.strip()
        # find the key
        if   aKey == "Name"            : 
            shName    = aVal
        elif aKey == "Sender"          : 
            shSender  = aVal
        elif aKey == "Recipient"       : 
            shRecip   = aVal
        elif aKey == "TrackingNumber"  : 
            shTrack   = aVal
        elif aKey == "ShipmentService" : 
            shService = aVal
        elif aKey == "ShipmentType"    : 
            shType    = aVal
        elif aKey == "SerialNumbers"   : 
            iSNs      = aVal
        elif aKey == "SNFile"          : 
            iFile     = aVal
        elif aKey == "Comment"         : 
            shComment = aVal
        else:
            print("wront Control File Syntax: found an unexpected line:")
            print(" Key   = " + aKey )
            print(" Value = " + aVal )
            print(" ...exiting.")
            return shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment

    return shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment


def get_shipment_params_interactive():

    while True:

        # get them
        print("")
        shName    = input("Name            : " )
        shSender  = input("Sender          : " )
        shRecip   = input("Recipient       : " )
        shTrack   = input("TrackingNumber  : " )
        shService = input("ShipmentService : " )
        shType    = input("ShipmentType    : " )
        iSNs      = input("SerialNumbers   : " )
        iFile     = input("SNFile          : " )
        shComment = input("Comment         : " )

        # print them
        print("\n Got: \n")
        print("Name            : " + shName    )
        print("Sender          : " + shSender  )
        print("Recipient       : " + shRecip   )
        print("TrackingNumber  : " + shTrack   )
        print("ShipmentService : " + shService )
        print("ShipmentType    : " + shType    )
        print("SerialNumbers   : " + iSNs      )
        print("SNFile          : " + iFile     )
        print("Comment         : " + shComment )
        print("")

        # confirm with the user
        shHappy   = input("Happy (yes/no)? : " )
        if shHappy == "yes": # *anything* else is basically "no"
            break

    print(" Thank you! ")

    return shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment



def make_shipment(c,shName, shSender, shRecip, shTrack, shService, shType, listSN, shComment):

    #    c.post("createShipment", json = {'name':'Powerboards', 'sender':'LBL', 'recipient':args.recipient, 'type':args.globe, 'status':'inTransit','shipmentItems':component_codes})
    # const createShipmentDtoInSchema = {
    #     name: "...", // shipment name
    #     sender: "...", // code of the Institution
    #     recipient: "...", // code of the Institution
    #     trackingNumber: "...", // tracking number
    #     shippingService: "...", // shipping service
    #     type: "...", 
    #                   // shipment type (domestic / intraContinental / continental)
    #     status: "...", // current status of the shipment
    #     shipmentItems: ["..."], // array of component codes
    #     comments: ["...", "..."] // array of comments
    # };

    # testing:
    print("Name            : " + shName    )
    print("Sender          : " + shSender  )
    print("Recipient       : " + shRecip   )
    print("TrackingNumber  : " + shTrack   )
    print("ShipmentService : " + shService )
    print("ShipmentType    : " + shType    )
    print("shipmentItems   : ", end='' )
    print(listSN)
    print("Comment         : " + shComment )
    # return (True,"haha")

    listComments = [shComment]

    # Find the codes first
    err,listCodes = get_codes_bulk(c,listSN, True)
    if err:
        return err,listCodes
    print(listCodes)

    error = False
    Resp = {}
    try:
        Resp = c.post( 'createShipment',
                       json = { 'name'           : shName,
                                'sender'         : shSender,
                                'recipient'      : shRecip,
                                'trackingNumber' : shTrack,
                                'shippingService': shService,
                                'type'           : shType,
                                'shipmentItems'  : listCodes,
                                'comments'       : listComments } )
        #                       'status'         : "inTransit",
    except Exception as e:
        error = True
        print("Error: shipment not made ")
        print(e)
        if e.__class__.__name__ == 'Forbidden' :
            print("Error: got bad connection in <get_response>")
            #bad_connection = True

    return error, Resp


# 2021-07-01 It seems the sender info is not necessary, contrary to the documentation.
#            Getting warnings in the real shipments
#def send_off_shipment(c, aResp,shSender,shRecip,shType):
def send_off_shipment(c, aResp,shRecip,shType):

    error = False
    cResp = {}
    try:
        cResp = c.post( 'updateShipment',
                        json = { 'shipment'       : aResp['id'],
                                 'recipient'      : shRecip,
                                 'type'           : shType,
                                 'status'         : "inTransit" })
        #                        'sender'         : shSender,
    except Exception as e:
        error = True
        print("Error: shipment change to <inTransit> status was not completed ")
        print(e)
        if e.__class__.__name__ == 'Forbidden' :
            print("Error: got bad connection in <get_response>")

    return error,cResp


def main(args,aTemplate):
    ControlFile   = args.ControlFile
    printTemplate = args.printTemplate
    onlyCreate    = args.onlyCreate
    print(" Got input: ")
    print("   ControlFile   = " + ControlFile )
    print("   printTemplate = " + str(printTemplate) )
    if onlyCreate:
        print("   onlyCreate   = " + str(onlyCreate) )

    if printTemplate:
        oFile = "ControlFile_example.txt"
        print("\nWill write the Control File template to file <" + oFile + "> and exit.\n")
        with open(oFile,'w') as oF:
            oF.write(aTemplate)
        return
        

    # Check if have the inputs to start with
    shName     = ""
    shSender   = ""
    shRecip    = ""
    shTrack    = ""
    shService  = ""
    shType     = ""
    #shStatus   = "" # let's not do this stuff, should always get into "inTransit"
    iSNs       = ""
    iFile      = ""
    shComment  = ""
    if len(ControlFile) > 0 :
        print("got the Control File name, will process it")
        shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment = get_shipment_params_file(ControlFile)
    else:
        print("no Control File name => will get the parameters interactively")
        shName, shSender, shRecip, shTrack, shService, shType, iSNs, iFile, shComment = get_shipment_params_interactive()

    # check the values received
    listShTypes = ["domestic", "intraContinental", "continental"]
    if len(shSender) == 0 :
        print(" bad Sender info, exiting.")
        return
    if len(shRecip ) == 0 :
        print(" bad Recipient info, exiting.")
        return
    if shType not in listShTypes :
        print(" bad shipment type, exiting.")
        return
    if len(iSNs) == 0 and len(iFile) == 0 :
        print(" don't have the necessary SNs to form a shipment, exiting...")
        return
        
    # To form the list of SNs
    listSN = []
    if len(iSNs) > 0 :
        listSN1 = iSNs.split(",") # presume it could be a comma-separated list
        for anSN in listSN1:
            cleanSN = anSN.strip()
            listSN.append(cleanSN)

    if len(iFile) > 0 :
        lAbsPath = Path(iFile)
        if lAbsPath.is_file():
            with open(iFile,'r') as iF:
                lines = iF.readlines()
        else:
            print(" Funny file name: <" + iFile + ">" )
            print(" .... cannot process. Exiting. ")
            return

        for aLine in lines:
            # want to have commented out lines
            if aLine.startswith("#") : 
                continue

            # let's strip the SN from the trailing stuff
            cleanSN = aLine.strip()

            # check the input SN formatting
            if not checkSN_basic(cleanSN) :
                print("Error: SN = <" + cleanSN + "> is illegal!")
            else:
                listSN.append(cleanSN)

    if len(listSN) == 0:
        print("could not form a valid SN list, exiting")
        return


    # in case the DB interaction goes south
    output_err_file = "Error_DB_response.json"

    # a log file for reporting
    oFile = ControlFile + ".log"
    oLog = open( oFile, 'w' )

    # Should have enough information to send off
    c = itkdb.Client()  # expires_after=dict(days=1) )

    # Step 1 of 2: to prepare the shipment
    (err, prepResp) = make_shipment(c,shName, shSender, shRecip, shTrack, shService, shType, listSN, shComment)
    if err:
        aMsg =   " Got error in step 1 of 2: Shipment preparation \n"
        aMsg +=  "  ---> No shipment was made! \n"
        print     (aMsg)
        oLog.write(aMsg+"\n")
        with open(output_err_file,'w') as oF:
            json.dump( prepResp, oF, indent=2 )
        aMsg = "  The DB response was writting to file <" + output_err_file + ">\n"
        aMsg += "  ...Exiting."
        print     (aMsg)
        oLog.write(aMsg+"\n")
        oLog.close()
        return

    aMsg = " Completed step 1 of 2: Shipment preparation "
    oLog.write(aMsg+"\n")

    # Step 2 of 2: to send it off
    # (err,transResp) = send_off_shipment(c,prepResp,shSender,shRecip,shType)
    if not onlyCreate:
        (err,transResp) = send_off_shipment(c,prepResp,shRecip,shType)
        if err:
            aMsg = " Got error in step 2 of 2: sending the shipment off (change to <inTransit>) "
            aMsg += "  ---> No shipment was made! "
            print     (aMsg)
            oLog.write(aMsg+"\n")
            with open(output_err_file,'w') as oF:
                json.dump( transResp, oF, indent=2 )
            aMsg = "  The DB response was writting to file <" + output_err_file + ">"
            aMsg += "  ...Exiting."
            print     (aMsg)
            oLog.write(aMsg+"\n")
            oLog.close()
            return

    # print( json.dumps(transResp,indent=2) )

    ID   = "<did not get the value>"
    try:
        if onlyCreate:
            ID = prepResp ['id']
        else:
            ID = transResp['id']
    except:
        aMsg = " Could not get ID"
        print     (aMsg)
        oLog.write(aMsg+"\n")

    Status  = "<did not get the value>"
    try:
        if onlyCreate:
            Status = prepResp ['status']
        else:
            Status = transResp['status']
    except:
        aMsg = " Could not get Status"
        print     (aMsg)
        oLog.write(aMsg+"\n")


    aMsg = " Completed step 2 of 2: Shipment preparation \n"
    aMsg += " The shipment status is <" + Status + ">\n"
    aMsg += "\n"
    aMsg += " The URL is likely this: https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/dcb3f6d1f130482581ba1e7bbe34413c/shipping/shipmentDetail?shipment=" + ID + "\n"
    aMsg += "\n"
    aMsg += "Wrote the log file <" + oFile + ">\n"
    aMsg += " Done!\n"

    print     (aMsg)
    oLog.write(aMsg+"\n")
    oLog.close()

    # print(json.dumps(cResp,indent=2))
    # print(aResp)


if __name__ == '__main__':
    import argparse
    aTemplate  = " Name            : <Shipment name>                 # (arbitrary) \n"
    aTemplate += " Sender          : <Sending institutes's handle in DB>\n"
    aTemplate += " Recipient       : <Receiving institute's handle in DB>\n"
    aTemplate += " TrackingNumber  : <Shipment tracking number>      # (optional)  \n"
    aTemplate += " ShipmentService : <E.g. FedEx / UPS / DHL / ...>  # (optional)  \n"
    aTemplate += " ShipmentType    : <Either of \"domestic\"/\"intraContinental\"/\"continental\">\n"
    aTemplate += " SerialNumbers   : <SN1,SN2,SN3,...>               # (optional [1])\n"
    aTemplate += " SNFile          : <File name with a SN per line>  # (optional [1])\n"
    aTemplate += " Comment         : <A comment to include>          # (optional)\n"

    strDescription = "simple shipment script with either a Control File or interactive option\n\n"
    strDescription += " A Control File content example (between \"-------\" lines):\n\n"
    strDescription += " ----------------------------------------\n"
    strDescription += aTemplate
    # strDescription += " Name            : <Shipment name>                 # (arbitrary)\n"
    # strDescription += " Sender          : <Sending institutes's handle in DB>\n"
    # strDescription += " Recipient       : <Receiving institute's handle in DB>\n"
    # strDescription += " TrackingNumber  : <Shipment tracking number (optional)>\n"
    # strDescription += " ShipmentService : <E.g. FedEx / UPS / DHL / ...>  # (optional)  \n"
    # strDescription += " ShipmentType    : <Either of \"domestic\"/\"intraContinental\"/\"continental\">\n"
    # strDescription += " SerialNumbers   : <SN1,SN2,SN3,...>               # (optional [1])\n"
    # strDescription += " SNFile          : <File name with a SN per line>  # (optional [1])\n"
    # strDescription += " Comment         : <A comment to include>          # (optional)\n"
    strDescription += " ----------------------------------------\n"
    strDescription += " [1] either SerialNumbers or SNFile (or both) must have data to use\n"

    parser = argparse.ArgumentParser(
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = strDescription )
    parser.add_argument('-c', '--ControlFile', dest = 'ControlFile', type = str, default = '', help = 'Control File name/path')
    parser.add_argument('-p', '--printTemplate',dest = 'printTemplate',action="store_true", help = 'To print Control File template and exit')
    parser.add_argument('-o', '--onlyCreate',  dest = 'onlyCreate',action="store_true", help = 'only create the shipment, without sending it off')

    args = parser.parse_args()

    main(args,aTemplate)
