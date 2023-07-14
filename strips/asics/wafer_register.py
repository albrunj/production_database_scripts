import argparse
import os
import sys
import time

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import itk_pdb.dbAccess as dbAccess

def make_yy_code(die_type):
    if die_type == "ABC":
        yy_code = "AA"
    elif die_type == "AMAC":
        yy_code = "AM"
    elif die_type == "HCC":
        yy_code = "AH"
    else:
        raise RuntimeError("No yy_code for %s" % die_type)

    return yy_code

# 20 USG WA 0 000 095
def make_serial_number(wafer_number, wafer_series, die_index, die_type):
    header = "20USG"

    yy_code = make_yy_code(die_type)

    header += yy_code
    header += "%d" % wafer_series
    header += "%03d" % wafer_number;

    if die_index is None:
        # Make base name for searching
        return header
    else:
        die_number = die_index + 1;

        return header + "%03d" % die_number;

def make_fuse_id(wafer_number, wafer_series, die_index, die_type):

    if die_type != "AMAC" and die_type != "HCC" and die_type != "ABC":
      raise

    die_number = die_index + 1;
    value = (wafer_series << 22) | (wafer_number << 11) | die_number;

    #AMAC always stores die_type
    if die_type == "AMAC":
        value |= 2 << 9
    #HCC only stores die_type for protoype wafer
    elif wafer_series == 0 and die_type == "HCC":
        value |= 1 << 9

    # Store in string as ABC$hex06
    die_string = die_type + "%06x" % value

    # AMAC and HCC store both hex and dec efuse values 
    if die_type == "AMAC" or die_type == "HCC":
        return die_string, value
    else:
        return die_string

def get_inst_short_code(inst_long_code):
    i = dbAccess.doSomething(action="getInstitution", method = "GET",
                         data = {'id': inst_long_code} )

    return i["code"]

def createDieComponent(parent_component, institute_code,
                       component_type_code, component_subtype_code,
                       fuse_value, serial_number):
    die_yy = serial_number[5:7]

    property_code = {
        "AA": "ID",
        "AH": "EFUSE_HEX",
        "AM": "EFUSEID",
    }

    properties = {}

    if die_yy == "AM":
        # The integer version
        properties["AMAC_EFUSE"] = fuse_value[1]
        fuse_value = fuse_value[0]

    if die_yy == "AH":
        # The integer version
        properties["EFUSE"] = fuse_value[1]
        fuse_value = fuse_value[0]

    # Alternative ID has to be unique across project
    properties[property_code[die_yy]] = fuse_value

    createDieDtoIn = {
        "project": parent_component["project"], # "S"
        "subproject": parent_component["subproject"],
        "institution": institute_code,
        "componentType": component_type_code,
        # Sub-type
        "type": component_subtype_code,
        "serialNumber": serial_number,
        "properties": properties,
    }

    print(createDieDtoIn)

    global dry_run
    if dry_run:
        return

    return dbAccess.doSomething(action = "registerComponent", method = "POST",
                                data = createDieDtoIn)

def linkDieComponentToWafer(wafer_component,
                            die_component,
                            slot_id):
    data = {"parent": wafer_component,
            "slot": slot_id,
            "child": die_component}

    print(data)

    global dry_run
    if dry_run:
        return

    dbAccess.doSomething(action = "assembleComponentBySlot", method = "POST",
                         data = data)

def property_value(comp, prop_name):
    props = comp["properties"]
    for p in props:
        if p["code"] == prop_name:
            return p["value"]

    print("Not found " + prop_name)
    print(" in: " + str(comp))
    raise RuntimeError("Failed to look up {}".format(prop_name))

def check_die_list(base_name):
    die_list = dbAccess.doSomething(action = "listComponents", method = "GET",
                                    data = {"filterMap":
                                            {"serialNumber": base_name},
                                            "outputType": "object"})

    die_list = die_list["itemList"]
    return die_list

def create_dice(wafer_component, wafer_number, wafer_series,
                inst_code,
                die_info,
                die_type, die_sn_list, die_code_list):
    global dry_run

    die_subtype = die_info["subtype"]
    length = die_info["count"]

    for d in range(length):
        sn = make_serial_number(wafer_number, wafer_series, d, die_type)

        if sn in die_sn_list:
            print("Component exists for %s" % sn)
            continue

        fuse_id = make_fuse_id(wafer_number, wafer_series, d, die_type)

        print("Create DIE %d component for %s (%s)" % (d, sn, fuse_id))
        die_output = createDieComponent(wafer_component,
                                        inst_code,
                                        die_type,
                                        die_subtype,
                                        fuse_id,
                                        sn)
        if dry_run:
            die_code_list[sn] = "NEW_CODE_%s" % sn
        else:
            new_code = die_output["component"]["code"]
            die_code_list[sn] = new_code

def get_die_wafer_info(wafer_component, wafer_type):
    sub_type = wafer_component["type"]
    print("Extract series from: %s" % sub_type) # ["version"])
    child_types = [c for c in wafer_type["children"][sub_type]]

    die_info = {}
    die_offset = 0

    for c in child_types:
        print(c)
        die_type_code = c["code"]
        die_subtype = c["type"]["code"]

        die_info[die_type_code] = {
            "subtype": die_subtype,
            "offset": die_offset,
            "count": c["quantity"]
        }

        die_offset += c["quantity"]

    for k, v in die_info.items():
        print(k, v)

    return die_info

def link_slots(wafer_component, wafer_number, wafer_series,
               die_info,
               die_type, die_code_list):
    global dry_run

    children = wafer_component["children"]
    count = die_info["count"]
    offset = die_info["offset"]

    for d in range(count):
        child_info = children[d + offset]
        history = None
        if "history" in child_info:
            history = child_info["history"]
        if history != None and len(history) > 1:
            print("Aborting at %d, already have multiple die in slot!" % d)
            sys.exit(1)

        if history != None and len(history) == 1:
            print("Have component in slot %d" % d)
            continue

        # print("Need component in slot %d" % d)

        sn = make_serial_number(wafer_number, wafer_series, d, die_type)

        print("Link %s slot %d serial number %s" % (die_type, d, sn))

        linkDieComponentToWafer(wafer_component["code"],
                                die_code_list[sn],
                                child_info["id"])

def run_wafer(wafer_name):
    start_time = time.time()

    print("Registering die for wafer %s" % wafer_name)

    wafer_component = dbAccess.doSomething(action = "getComponent", method = "GET",
                                           data = {"component": wafer_name,
                                                   "outputType": "object"})

    print("Lookup info for type %s" % wafer_component["componentType"])
    wafer_type = dbAccess.doSomething(action = "getComponentType", method = "GET",
                                      data = {"id": wafer_component["componentType"]})

    # print(json.dumps(wafer_component, indent = True))
    # print(json.dumps(wafer_type, indent = True))

    wafer_style = 1

    print("Wafer type code: %s" % wafer_type["code"])

    if wafer_type["code"] == "MWAFER":
        print("Wafer type code suggests mixed")
        wafer_style = 0

    wafer_number = property_value(wafer_component, [
        "MIXEDWAFERNUMBER", "ABCWAFERNUMBER"][wafer_style])
    print("Using wafer number %d" % wafer_number)

    wafer_series = 1

    # object format doesn't look up short code from long code
    inst_code = get_inst_short_code(wafer_component["institution"])
    print("Create using inst code: %s" % inst_code)

    die_info = get_die_wafer_info(wafer_component, wafer_type)

    for die_type in die_info.keys():
        type_info = die_info[die_type]

        die_base_name = make_serial_number(wafer_number, wafer_series,
                                           None, die_type)
        die_list = check_die_list(die_base_name)

        count = type_info["count"]

        if len(die_list) == count:
            print("All %s die present" % die_type)
        else:
            print("Need to create %s %s dies" % (count-len(die_list), die_type))
        # print(die_sn_list)

        die_sn_list = [d["serialNumber"] for d in die_list]
        die_code_list = dict((d["serialNumber"], d["id"]) for d in die_list)

        type_info["sn_list"] = die_sn_list
        type_info["code_list"] = die_code_list

    for d_type in die_info.keys():
        die_code_list = die_info[d_type]["code_list"]
        die_sn_list = die_info[d_type]["sn_list"]

        create_dice(wafer_component, wafer_number, wafer_series,
                    inst_code,
                    die_info[d_type], d_type, die_sn_list, die_code_list)

    # sys.exit(0)

    # Now look at wafer to see which are attached

    for d_type in die_info.keys():
        die_code_list = die_info[d_type]["code_list"]

        link_slots(wafer_component, wafer_number, wafer_series,
                   die_info[d_type], d_type, die_code_list)

    if dry_run:
        return

    dbAccess.doSomething(action = "setScriptState", method = "POST",
                         data = {"component":
                                 wafer_name,
                                 "type": "registration",
                                 "state": "completed"})

    # print(json.dumps(j))

    end_time = time.time()

    print("Complete in %.1f seconds" % (end_time - start_time))

if os.getenv("ITK_DB_AUTH"):
    dbAccess.token = os.getenv("ITK_DB_AUTH")
else:
    print("No token!")
    sys.exit(1)

dry_run = True

def main():
    global dry_run

    parser = argparse.ArgumentParser(description='Register die in strips wafer.')
    parser.add_argument("wafer", help="Wafer serial number (e.g. 20USGWA1027000).")
    parser.add_argument("--dry-run",
                        action="store_true",
                        help="Don't communicate with DB (except for wafer & type)")
    args = parser.parse_args()

    in_name = args.wafer
    dry_run = args.dry_run

    if in_name[:5] == "20USG":
        if len(in_name) == 11:
            wafer_name = in_name + "000"
        elif len(in_name) == 14:
            wafer_name = in_name
        else:
            print("Bad arg length for 20USG...... %d" % (len(in_name)))
            sys.exit(1)
    else:
        print("Bad arg not 20USG......")
        sys.exit(1)

    run_wafer(wafer_name)

if __name__ == "__main__":
    main()
