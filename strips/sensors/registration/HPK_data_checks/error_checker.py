#How to use:
#    1) "dirpaths" variable should have paths to directories with exclusively wafer txt files
#    2) change variable names of wafer databases to "D<keyword>"--this will propagate into directory and file names for saving plots
#    3) run with "python3 error_checker.py"
#    4) output will be a "errors" folder in same directory as this script
import codecs
import logging
import os
import re
from datetime import datetime

from strips.sensors.registration.HPK_data_checks.check import check_key
from strips.sensors.registration.HPK_data_checks.check import check_value
from strips.sensors.registration.HPK_data_checks.check import expected_keys_reduced_barrel
from strips.sensors.registration.HPK_data_checks.check import expected_keys_reduced_EC
from strips.sensors.registration.HPK_data_checks.strict_check import expected_keys_barrel
from strips.sensors.registration.HPK_data_checks.strict_check import expected_keys_EC
from strips.sensors.registration.HPK_data_checks.strict_check import strict_check_key
from strips.sensors.registration.HPK_data_checks.strict_check import strict_check_value
#"check" checks for shifts and doesn't care if keys/values are on wrong line
#"check valid" is more strict about whether keys/values are on correct line, so
# this finds when files have repeats (too many lines)

######################
#dirpaths = []
#dirpaths.append("_All_HPK-prepro-data")

# VF, 2021-08-13: to add the checking algorithm version, and rename the dir structure
checkerVersion = "1.0"
#registration_outputdir = "RegistrationOutput"
registration_outputdir = "HPK_Data_Issues"
#errors_dirpath = "{}/errors_ATLAS_{}".format(registration_outputdir,datetime.now().strftime('%Y-%m-%d_T_%Hh%Mm%Ss'))
errors_dirpath = "{}/errors_{}".format(registration_outputdir,datetime.now().strftime('%Y-%m-%d_T_%Hh%Mm%Ss'))
error_files_path = '{}/error_files'.format(errors_dirpath)
corrected_files_path = '{}/corrected_files'.format(errors_dirpath)
#######################

class Wafer():
    def __init__(self,keys,values):
        #values[dirpath_ind][file_ind][line_ind] = "value"
        #keys[dirpath_ind][file_ind][line_ind] = "key"
        self.filename = None #set later
        self.values = values
        self.keys = keys
        self.corrupted = False
        self.valuesdict = {}
        self.init()
    def init(self):
        for i in range(len(self.keys)):
            self.valuesdict[self.keys[i]] = self.values[i]

    def set_filename(self,filename):
        self.filename = filename
    def set_corrupted(self,corrupted):
        self.corrupted = corrupted

class Data():
    def __init__(self,dirpaths):
        self.dirpaths = dirpaths
        self.fpaths = []
        #self.fpaths[dirpath_ind][file_ind] = fpath
        self.filenames = [] #list of filenames in arbitrary order
        self.Ncorrupted_files = 0
        self.sensor_types = {}
        self.file_corrupted = {} #bool
        #self.file_corrupted[filename] = bool
        self.flags = {}
        self.error_msgs = {}#shifts,data errors
        self.valid_error_msgs = {}#more strict,gets repeats,checks alignment of keys to line numbers
        self.summary_msgs = {} #brief summary of all files in all dirpaths
        
        self.keys = {} #
        self.values = {} #strings
        #self.keys[fn][key_ind] = key, self.values[fn][value_ind] = value
        
        self.wafers = [] #Wafer objects
        #self.wafers[i] = Wafer(...)

        self.defined_err_dir = False
        self.defined_corr_dir = False

        self.to_log = logging.getLogger().hasHandlers()
        
        self.declare()
        self.strict_scan_wafers()
        self.scan_wafers() #less strict, checks for shifts and data errors
        self.init_wafers()
        self.write_corrected_files()
        self.write_summary()


    #def setflag(self,fn,new_flag):
    #    sn = fn[:-4]
    def setflag(self,SN,new_flag):
        #only add flag to wafers without flags
        try:
            self.flags[SN]
        except KeyError:
            self.flags[SN] = new_flag

        old_flag = self.flags[SN]
        #flag already exists, so upgrade or do nothing
        if new_flag == 'WARNING' and old_flag == 'OK':
            self.flags[SN] = 'WARNING'
        elif new_flag == 'ERROR' and old_flag in ['OK','WARNING']:
            self.flags[SN] = 'ERROR'
        else:
            pass #don't assign to new flag if not worse than old flag


    def make_err_dir(self):
        logMED = logging.getLogger('LOG-MED')
        # if neither path existed => will declare the creation
        if not (self.defined_err_dir or self.defined_corr_dir) :
            logMED.info(" Will log the issues with data in this dir:")
            logMED.info("<" + errors_dirpath + ">")

        if not self.defined_err_dir :
            if not os.path.exists(error_files_path):
                os.makedirs(error_files_path)
            self.defined_err_dir = True


    def make_corr_dir(self):
        logMCD = logging.getLogger('LOG-MCD')
        # if neither path existed => will declare the creation
        if not (self.defined_err_dir or self.defined_corr_dir) :
            logMCD.info(" Will log the issues with data in this dir:")
            logMCD.info("<" + errors_dirpath + ">")

        if not self.defined_corr_dir :
            if not os.path.exists(corrected_files_path):
                os.makedirs(corrected_files_path)
            self.defined_corr_dir = True


    # VF, 2021-08-14: let's do an early declaration
    def declare(self):
        logECD = logging.getLogger('LOG-ECD')
        logECD.info(" >> Will check the data integrity with checker Version " + checkerVersion)
        logECD.info("")


    def strict_scan_wafers(self): #checks if all lines are as desired
        # VF, 2021-08-13: switch from printing to logging
        logSSW = logging.getLogger('LOG-SSW')
        #loc_msg = "\n################################\n"
        loc_msg = " >> Scanning for expected keys/values at specific lines"
        #loc_msg += "\n################################\n"
        self.report(logSSW,loc_msg)

        for i in range(len(self.dirpaths)):
            dirpath = self.dirpaths[i]
            self.fpaths.append([])
            files = list(filter(lambda s: s.endswith('.txt'),os.listdir(dirpath)))
            self.filenames.extend(files)
            for j in range(len(files)):
                fn = files[j]
                SN = fn[:-4]
                # VF, 2021-08-13: add original goodness, just to have it always defined
                self.setflag(SN,"OK")

                fpath = os.path.join(dirpath,fn)
                self.fpaths[-1].append(fpath)
                self.summary_msgs[SN] = ":" #for this file
                self.valid_error_msgs[SN] = ""
                
                msg = 'Strict errors first:\n'
                with codecs.open(fpath,'r',encoding='ISO-8859-1') as f:
                    rawlines = f.readlines()
                # 2021-08-23, VF: not sure why the codec was needed, but
                #             the windows EOL is messing up the parsing occasionally
                lines = []
                for rawline in rawlines:
                    newline = rawline.replace('\r','')
                    lines.append(newline)
                #first get sensor type because 
                #they determine number of lines
                sensor_type = "EC"
                #get sensor type
                for line in lines:
                    if line.startswith("Microdischarge"):
                        sensor_type = "barrel"

                self.sensor_types[SN] = sensor_type
                #collect all keys and values
                line_ind = 0
                extralines = 0
                while line_ind < len(lines):
                    line = lines[line_ind]
                    splitline = line.split('\t')
                    try: skey = splitline[0].strip()
                    except Exception: skey = ""
                    
                    if skey.startswith("#End of manufacturer data file"):
                        break

                    # VF, 2021-08-18: this is a strict line-by-line check of the keys + values
                    key,line_ind,msg = strict_check_key(sensor_type,line_ind-extralines,skey,msg)
                    
                    try: val = splitline[1].strip().strip('\n')
                    except Exception: val = ""

                    
                    #edge case, special keys can have multi-line values
                    if key in ["Oxide pinholes","Metal Shorts","Metal Opens","Implant Shorts","Implant Opens","Microdischarge strips","Bias resistor disconnection"]:
                        #check if overflow onto next line
                        while bool(re.search(r'\d{1}-\d{1,}',lines[line_ind+extralines+1].split('\t')[0])):
                            val += lines[line_ind+extralines+1].split('\t')[0].strip('\n')
                            extralines += 1

                    
                    if key != None:

                        rv = strict_check_value(sensor_type,line_ind,key,val,msg)
                        
                        value,msg = rv
                        if value == None:
                            msg += "Error getting valid value for key '{}'. (value was '{}')\n".format(key,val)
                            #print("line: '{}'".format(line))
                            
                    else:
                        a_msg = "For SN = {}, splitline = '{}'".format(SN,splitline)
                        self.report(logSSW,a_msg,"debug")

                        # VF, 2021-08-22: This was causing problems
                        #msg += "Invalid key '{}' with orig key,value: {},{}\n".format(key,splitline[0].strip(),splitline[1].strip())
                        msg += "Invalid key '{}' with orig key,value: {},{}\n".format(key,skey, val)

                    #print("####END of file######\n\n\n\n\n")
                    line_ind += 1
                    
                    if extralines > 0:
                        #means there was an extra line
                        line_ind += extralines

                
                self.valid_error_msgs[SN] = msg
                if "Too many lines" in msg:
                    self.summary_msgs[SN] += "\tExtra lines or Repeats!"
                    self.setflag(SN,"WARNING")

                # VF, 2021-08-13: only write the files if there is a reason.
                # Otherwise it will be too confusing for the user
                if self.flags[SN] != "OK" :
                    if self.to_log:
                        logSSW.error("\n SN = " + SN + ", error = " + self.valid_error_msgs[SN])
                    else:
                        self.make_err_dir()
                        #savepath = os.path.join("{}/error_files".format(errors_dirpath),fn[:-4]+"_errors.txt")
                        #savepath = os.path.join( error_files_path, fn[:-4]+"_errors.txt" )
                        savepath = os.path.join( error_files_path, SN+"_errors.txt" )
                        with open(savepath,'a+') as writefile:
                            writefile.write(datetime.now().strftime("%c")+"\n\n")
                            writefile.write(self.valid_error_msgs[SN]+"\n\n\n")




    def scan_wafers(self):
        # VF, 2021-08-13: switch from printing to logging
        logCSW = logging.getLogger('LOG-CSW')
        #loc_msg = "\n################################\n"
        loc_msg = " >> Scanning for shifts and invalid non-null values"
        #loc_msg += "\n################################\n"
        self.report(logCSW,loc_msg)

        #looks for errors and gets values
        for i in range(len(self.dirpaths)):
            dirpath = self.dirpaths[i]


            files = list(filter(lambda s: s.endswith('.txt'),os.listdir(dirpath)))
            
            for j in range(len(files)):
                #print("########### i,j = {},{} ######".format(i,j))
                fn = files[j]
                SN = fn[:-4]
                fpath = os.path.join(dirpath,fn)
                self.error_msgs[SN] = ""
                self.file_corrupted[SN] = False
                self.keys[SN] = []
                self.values[SN] = []

                shift = 0
                #print("len(self.values[{}]) = {}".format(i,len(self.values[i]))) 
                #weird encoding needed to deal with special symbols like angstrom
                with codecs.open(fpath,'r',encoding='ISO-8859-1') as f:
                    #print("---Filepath {}-----".format(fpath))
                    rawlines = f.readlines()
                # 2021-08-23, VF: not sure why the codec was needed, but
                #             the windows EOL is messing up the parsing occasionally
                lines = []
                for rawline in rawlines:
                    newline = rawline.replace('\r','')
                    lines.append(newline)

                msg = "" #error message for this file (shifts and data errors)

                #first get sensor type because 
                #they determine number of lines
                sensor_type = "EC"
                #get sensor type
                for line in lines:
                    if line.startswith("Microdischarge"):
                        sensor_type = "barrel"
                
                #filter out all value-less lines
                expected_keys_reduced = {}
                if sensor_type == 'barrel':
                    expected_keys_reduced = expected_keys_reduced_barrel
                elif sensor_type == 'EC':
                    expected_keys_reduced = expected_keys_reduced_EC
                else:
                    raise RuntimeError('Unknown sensor type: \'%s\'' % sensor_type)

                # VF, 2021-08-22 Let's remove duplicates just in case
                lines_clean = []
                for line in lines:
                    clean = line.strip()
                    if ( len(clean) > 0 and
                         not clean.startswith("IV Temperature(C)") and
                         not clean.startswith("Humidity") ):
                        if clean in lines_clean:
                            lines.remove(line)
                            self.report(logCSW," removing duplicate line <" + clean + ">")
                            continue
                        else:
                            lines_clean.append(clean)

                lines_copy = list(lines)
                orig_index = {}
                for line_ind in range(len(lines_copy)):
                    line = lines_copy[line_ind]
                    try:
                        key = line.split('\t')[0].strip().strip('\n')
                        if key not in expected_keys_reduced:
                            lines.remove(line)
                        else:
                            orig_index[line] = line_ind
                    except Exception:
                        lines.remove(line)
                
                # VF, 2021-08-22: Now, let's check that all the expected keys are in
                # Otherwise there seems to be the case of infinite recursion
                to_proceed = True
                for K in expected_keys_reduced:
                    kFound = False
                    for L in lines:
                        if K in L:
                            kFound = True
                    if not kFound:
                        to_proceed = False
                        self.report(logCSW," key <{}> not found in file <{}>".format(K,fn))
                if not to_proceed:
                    self.file_corrupted[SN] = True
                    self.Ncorrupted_files += 1
                    self.summary_msgs[SN] += "\tContains data errors"
                    self.setflag(SN,"ERROR")
                    continue

                keys,values = [],[]
                #collect all keys and values
                for line_ind in range(len(lines)):
                    # case of duplicates
                    if line_ind == len(lines): break
                    line = lines[line_ind]
                    splitline = line.split('\t')
                    try: key = splitline[0].strip()
                    except Exception: key = ""
                    
                    if check_key(sensor_type,line_ind,key,msg)[0] == None:
                        continue #skip line because doesn't have a value anyway

                    try: val = splitline[1].strip().strip('\n')
                    except Exception: val = ""

                    #edge case, special keys can have 2-line values :( (assume no more than 2 lines)
                    if key in ["Oxide pinholes","Metal Shorts","Metal Opens","Implant Shorts","Implant Opens","Microdischarge strips","Bias resistor disconnection"]:
                        #check for overflow onto next line
                        extralines = 1
                        while bool(re.search(r'\d{1}-\d{1,}',lines_copy[int(orig_index[line])+extralines].split('\t')[0])):
                            # VF: want to add the space to match Matt's readout
                            add = lines_copy[int(orig_index[line])+extralines].split('\t')[0].strip('\n')
                            if not (val.endswith(" ") or add.startswith(" ") ):
                                val += " "
                            val += add
                            extralines += 1

                    keys.append(key)
                    values.append(val)
                
                #now check keys and values with known strings
                for line_ind in range(len(lines)):
                    if (keys[line_ind].startswith("Microdischarge") or keys[line_ind].startswith("Bias resistor disconnection")) and shift != 0:
                        #this is prescribed--usually end of shifted section
                        shift = 0
                        msg += "Shift ends at {}\n".format(keys[line_ind])
                    key,line_ind,msg = check_key(sensor_type,line_ind,keys[line_ind],msg)
                    rv = check_value(sensor_type,line_ind,key,values,msg,shift=shift)
                    if len(rv) == 3:
                        #this means it found a shift
                        value,shift,msg = rv
                    else:
                        value,msg = rv
                    
                    if value == None:
                        #this means it is a bad value. let its value now be what it was in the file
                        value = values[line_ind+shift]
                        #only give a warning if there is a Ingot problem
                        if "Ingot" in msg and "Ingot" not in self.summary_msgs[SN]:
                            ingot_ind = msg.index("Ingot")
                            ingot_msg = msg[ingot_ind:msg[ingot_ind:].index('\n')]
                            self.summary_msgs[SN] += '\t'+ingot_msg
                            self.setflag(SN,"WARNING")
                        else:
                            self.file_corrupted[SN] = True
                        msg += "Error getting value for key '{}'. Value was '{}'\n".format(keys[line_ind],values[line_ind+shift])
                            
                    if key not in self.keys[SN]: #if haven't already added key...
                        self.keys[SN].append(key)
                        self.values[SN].append(value) #could be None

                    #print("####END of file######\n\n\n\n\n")
                
                if self.file_corrupted[SN]: 
                    self.Ncorrupted_files += 1
                    self.summary_msgs[SN] += "\tContains data errors"
                    self.setflag(SN,"ERROR")
                if "Shift" in msg: 
                    self.summary_msgs[SN] += "\tContains shift"
                    self.setflag(SN,"ERROR")

                if self.summary_msgs[SN] == ":":
                    self.summary_msgs[SN] += "\tOK"
                    self.setflag(SN,"OK")

                #check if can safely delete file-specific error file
                if not (self.summary_msgs[SN] in [':',':\tOK'] or self.summary_msgs[SN].endswith("'")):        
                    self.error_msgs[SN] = msg

                # VF, 2021-08-13: only write the files if there is a reason.
                # Otherwise it will be too confusing for the user
                if self.flags[SN] != "OK" :
                    if self.to_log:
                        logCSW.error("\n SN = " + SN + ", Errors (bad errors, after parsing shift): ")
                        logCSW.error(self.error_msgs[SN])
                    else:
                        self.make_err_dir()
                        #savepath = os.path.join("{}/error_files".format(errors_dirpath),fn[:-4]+"_errors.txt")
                        savepath = os.path.join( error_files_path, SN+"_errors.txt" )
                        with open(savepath,'a+') as writefile:
                            writefile.write(datetime.now().strftime("%c")+"\n\n")
                            #already wrote strict errors in previous method, so now append (a+) bad errors
                            writefile.write("Errors (bad errors, after parsing shift):\n") 
                            writefile.write(self.error_msgs[SN]+"\n\n\n")


    def write_summary(self):
        # logger area for this function
        logCWS = logging.getLogger('LOG-CWS')

        # VF, 2021-08-13: only write summary if there is any error
        OK = True
        for aKey in self.flags :
            if self.flags[aKey] != "OK":
                OK = False
                break
        #save error summary file

        logCWS.info(" >> Finished checking the data integrity.\n")
        if OK:
            logCWS.info(" Found no issues.")
            logCWS.info("")
        else:
            logCWS.info(" Found issues.")
            logCWS.info("")
            if self.to_log:
                logCWS.info("Total files with errors : {}/{}\n".format(self.Ncorrupted_files,len(self.filenames)) )
                for fn in sorted(self.summary_msgs.keys()):
                    each_msg = fn + self.summary_msgs[fn] # + '\n'
                    logCWS.info( each_msg )
            else:
                with open("{}/error_summary.txt".format(errors_dirpath),"a+") as sumfile:
                    sumfile.write("Total files with errors : {}/{}\n".format(self.Ncorrupted_files,len(self.filenames)))
                    for fn in sorted(self.summary_msgs.keys()):
                        each_msg = fn + self.summary_msgs[fn] # + '\n'
                        sumfile.write( each_msg + '\n')
        # end of check for presence of issues


            
    def init_wafers(self):
        # VF, 2021-08-13: will remove this for now - might be confusing for a casual reader
        #logCIW = logging.getLogger('LOG-CIW')
        #loc_msg = "Initializing wafers"
        # report(logCIW, loc_msg)

        #print("Total corrupted files = {}/{}".format(self.Ncorrupted_files,len(self.filenames)))
        for fn in self.filenames:
            SN = fn[:-4]
            new_wafer = Wafer(self.keys[SN],self.values[SN])
            new_wafer.set_filename(fn)
            new_wafer.set_corrupted(self.file_corrupted[SN])
            self.wafers.append(new_wafer)


    def write_corrected_files(self):
        logWCF = logging.getLogger('LOG-WCF')
        for wafer in self.wafers:
            fn = wafer.filename
            SN = fn[:-4]
            if "shift" in self.summary_msgs[SN] or "Extra lines" in self.summary_msgs[SN]:
                self.make_corr_dir()
                fpath = "{}/{}_corrected.txt".format(corrected_files_path,SN)
                self.write_file(wafer,fpath)
                MSG = "Wrote corrected file = " + fpath
                self.report(logWCF,MSG)


    def write_file(self,wafer,fpath):
        with open(fpath,'a+') as f:
            expected_keys_all = {}
            fn = wafer.filename
            SN = fn[:-4]
            sensor_type = self.sensor_types[SN]
            if sensor_type == 'barrel':
                expected_keys_all = expected_keys_barrel
            elif sensor_type == 'EC':
                expected_keys_all = expected_keys_EC
            else:
                raise RuntimeError('Unknown sensor type: \'%s\'' % sensor_type)
            for i in range(len(expected_keys_all)):
                k = expected_keys_all[i]
                f.write(k+"\t")
                try:
                    f.write(wafer.valuesdict[k]+"\n")
                except Exception:
                    f.write("\n")

    def report(self,LOG,MSG,option="info"):
        if self.to_log:
            if   option == "info":
                LOG.info( MSG )
            elif option == "debug":
                LOG.debug( MSG )
            elif option == "error":
                LOG.error( MSG )
        else:
            print( MSG )


#############################
#create a few wafer databases
#(D means database)

#Dglobal = Data(dirpaths)
#Datlas12 = Data([dirpaths[0]] + [dirpaths[1]])
#Datlas17 = Data([dirpaths[2]])
#Datlas12EC = Data([dirpaths[3]])
#if __name__ == "__main__":
#    Datlas18 = Data(dirpaths)
#all error checking happens within constructor (__init__)
