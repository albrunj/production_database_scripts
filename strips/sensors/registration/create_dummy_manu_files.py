#!/usr/bin/env python
import argparse
import os
import sys
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import numpy as np
try:
    import matplotlib.pyplot as plt
    matplotlib_found = True
except ImportError:
    matplotlib_found = False

# Created by Derek Hamersly in summer 2020.
# Updates:
# VF, 2021-08-05: 
#  -- removed comment about needing >= 100 pieces
#  -- moved the ini wafer, ini batch, b/e to the input
#
#####python create_dummy_manu_files.py 500
#####--creates 500 dummy manu files with internally specified ranges/distributions

def random(): 
    return np.random.random()

def random_array(size=1):
    return np.random.random(size)

class GenerateIVdata():
    def __init__(self):
        self.LC_at_vfd_plus50v = None
        self.LC_at_500v = None
        self.vbd = random()*500 + 400
        self.voltages = []
        self.currents = []
        self.points = self.gen_points()
        self.LC_at_700 = self.currents[-1]
        self.stability = self.gen_stability_data()
    def gen_stability_data(self):
        stability = []
        noise = 1e-8
        for i in range(3):
            c = self.LC_at_700
            if c != 'O.L.':
                c += random()*2*noise-noise
            stability.append(c)
        return stability
    def gen_points(self):
        vbd = self.vbd
        voltages = np.arange(20,720,20)
        start_current = 1.0e-7
        
        #curve 1--20 to vbd
        slope1 = random()*1e-10 + 1e-10
        currents = start_current + (voltages-20)*slope1
        noise = random_array(len(currents))*2e-9 - 1e-9
        currents = currents + noise
        if vbd >= 700:
            #get LC_at_500v then return points
            for i in range(len(voltages)):
                v,c = voltages[i],currents[i]
                if v == 500:
                    if c == "O.L.":
                        self.LC_at_500v = c
                    else: #c is float
                        self.LC_at_500v = "{:.4f}".format(c * 1e6)
                    break
            self.voltages = list(voltages)
            self.currents = list(currents)
            return list(zip(voltages,currents))

        #curve 2--vbd to 700
        LC_at_vbd = start_current + (vbd-20)*slope1
        slope2 = 1e-7
        overloads = []
        for i in range(len(voltages)):
            v,c = voltages[i],currents[i]

            if v == 500:
                if c == 'O.L.':
                    self.LC_at_500v = c
                else:
                    self.LC_at_500v = "{:.4f}".format(c * 1e6)
            if v >= vbd:
                currents[i] = LC_at_vbd + slope2*(v-vbd)
                if currents[i] > 1e-5:
                    overloads.append(i)

        self.voltages = list(voltages)
        self.currents = list(currents)
        for overload_ind in overloads:
            print(self.currents[overload_ind],"too high! Corresponding to voltage {}".format(self.voltages[overload_ind]))
            self.currents[overload_ind] = "O.L."

        return list(zip(self.voltages,self.currents))

    def plotIV(self,fileind):
        print("fileind =",fileind)
        currents = list(self.currents)
        for i in range(len(currents)):
            c = currents[i]
            if c == 'O.L.':
                currents[i] = 10
            else:
                currents[i] *= 1e6

        if matplotlib_found:
            plt.plot(self.voltages,currents,'-',label=str(fileind))
    def get_LC_at_vfd_plus_50v(self,deplation_volts):
        for i in range(len(self.voltages)):
            if self.voltages[i] >= deplation_volts + 50:
                c = self.currents[i]
                if c == 'O.L.': 
                    return c
                else: 
                    return "{:.4f}".format(c * 1e6)
        print("ERROR FINDING LC_at_vfd_plus_50v") 

def rand_date(startstr,endstr):
    start_date = datetime.strptime(startstr,"%d/%m/%Y")
    end_date = datetime.strptime(endstr,"%d/%m/%Y")
    days = (end_date - start_date).days
    rand_days = int(random() * days)
    random_date = start_date + timedelta(days=rand_days)
    return datetime.strftime(random_date,"%d/%m/%Y")
    
def rand_nm(type_ind):
    #type_ind=0 -> barrel, 1 -> EC
    value = ""
    if type_ind == 0:
        n = int(round(random()*3+1))
    else:
        n = int(round(random()*3))

    choices = ["none"]*8+["other"]*2
    npairs = 0
    choice = choices[int(random()*len(choices))]
    if choice == "other":
        npairs = int(random()*20+1)
        mstart = int(random()*(1539-npairs))
        if npairs > 1:
            for i in range(npairs-1):
                m = mstart + i
                value += "{}-{}, ".format(n,m)
        #if not none, add final pair w/o trailing comma
        m = mstart + npairs
        value += "{}-{}".format(n,m)
    else:
        value = "none"

    return value,npairs

def random_ingotnum():
    first6str = ""
    for i in range(6):
        first6str += str(int(random()*10))
    second3str = ""
    for i in range(3):
        second3str += str(int(random()*10))
    return first6str + "-" + second3str

def random_ingotnums(n):
    ingotnums = []
    for i in range(n):
        ingotnums.append(random_ingotnum())
    return ingotnums

def write_random_datafiles(nfiles,dirpath,W0, B0, barrel_endcap):
    os.makedirs(dirpath)
    #id_prefixes = ["20USBSX","20USESX"]
    if barrel_endcap == "barrel" :
        id_prefixes = "20USBSX"
        type_ind = 0
    elif barrel_endcap == "endcap" :
        id_prefixes = "20USESX"
        type_ind = 1
    else:
        print(" barrel_endcap choice should be either <barrel> or <endcap> !")
        print(" exiting.")
        return
        
    ingotnums = random_ingotnums(nfiles // 25)
    ingot_ind = 0
    BatchNo = int(B0[3:])
    
    # VF: custom mod for regi
    #    for file_ind in range(100,100+nfiles):
    #for file_ind in range(725,725+nfiles):
    for loop_ind in range(0,nfiles):
        file_ind = W0 + loop_ind
        print("File_ind = ",file_ind)
        ivdata = GenerateIVdata()
        ivdata.plotIV(file_ind)
        msg = "#General information ITEM section\n"
        msg += "%ITEM\n"

        # # VF: custom mod for regi
        # # type_ind = int(round(random())) #0 = barrel, 1 = EC
        # # type_ind = 1 # int(round(random())) #0 = barrel, 1 = EC
        # type_ind = 0 # int(round(random())) #0 = barrel, 1 = EC
        # VF, 2021-08-05: have only one prefix now!
        #idnum = id_prefixes[type_ind] + "%07d"%(file_ind)
        idnum = id_prefixes + "%07d"%(file_ind)
        msg += "Identification Number\t{}\n".format(idnum)
        # VF: custom mod for regi
        #    serialnum = "VPX9000" + str(type_ind+1) + "-W" + str(file_ind)
        #    serialnum = "VPX9002" + str(type_ind+1) + "-W" + str(file_ind)
        #serialnum = "VPX9003" + str(type_ind+1) + "-W" + str(file_ind)

        # VF, 2021-08-05: to increment the batch No. every 50 wafers
        # require 5-digit number
        locBatchNo = BatchNo + int(loop_ind/50)
        strBatchNo = B0[:3] + str(locBatchNo).zfill(5)
        serialnum = strBatchNo + "-W" + str(file_ind)
        msg += "Serial Number\t{}\n".format(serialnum)
        print("Serial Number\t{}\n".format(serialnum))
        #continue
        
        sensor_type = "ATLASDUMMY18"
        msg += "Sensor Type\t{}\n\n".format(sensor_type)
        msg += "#Test information Test section\n"
        msg += "%TEST\n"
        test_date = rand_date("06/01/2020","09/01/2022")
        msg += "Test Date (DD/MM/YYYY)\t{}\n".format(test_date)
        problem = (["NO"]*9+["YES"])[int(random()*10)]
        msg += "PROBLEM\t{}\n".format(problem)
        if problem == "YES": passed = "NO"
        else: passed = "YES"
        msg += "PASSED\t{}\n\n".format(passed)
        
        #DATA####################################
        msg += "#Test data Data section\n"
        msg += "%DATA\n"
        iv_temp = int(round(random()*10) + 20)
        msg += "IV Temperature(C)\t{}\n".format(iv_temp)
        iv_humid = int(round(random()*40) + 20)
        msg += "IV Humidity(%)\t{}\n".format(iv_humid)
        deplation_volts = int(random()*200 + 200)
        msg += "Deplation Volts (V)\t{}\n".format(deplation_volts)
        LC_at_vfd_plus_50v = ivdata.get_LC_at_vfd_plus_50v(deplation_volts)
        msg += "Leakage Current at Vfd + 50V (microA)\t{}\n".format(LC_at_vfd_plus_50v)
        LC_at_500v = ivdata.LC_at_500v
        msg += "Leakage current at 500 V (microA)\t{}\n".format(LC_at_500v) 
        ingotnum = ingotnums[ingot_ind]
        msg += "Substrate Lot No.\t{}\n".format(ingotnum)
        substrate_type = ["FZ1","(FZ1)","FZ-1"][int(random()*3)]
        msg += "Substrate Type\t{}\n".format(substrate_type)
        substrate_orient = "100"
        msg += "Substrate Orient\t{}\n".format(substrate_orient)
        substrate_RUpper = "{:.1f}".format(random()*8.5+3.5)
        msg += "Substrate R Upper (kOhm.cm)\t{}\n".format(substrate_RUpper)
        substrate_RLower = "{:.1f}".format(random()*5 + 3)
        msg += "Substrate R Lower (kOhm.cm)\t{}\n".format(substrate_RLower)
        active_thickness = "290"
        msg += "Active thickness (nominal value)\t{}\n".format(active_thickness)
        polysilicon_bias_upper = "{:.2f}".format(random()+1)
        msg += "Polysilicon Bias Resistance Upper (MOhm)\t{}\n".format(polysilicon_bias_upper)
        polysilicon_bias_lower = "{:.2f}".format(random()+1)
        msg += "Polysilicon Bias Resistance Lower (MOhm)\t{}\n".format(polysilicon_bias_lower)
        onsetV_of_microdischarge = int(round(ivdata.vbd))
        msg += "Onset voltage of Microdischarge (V)\t{}\n\n\n\n\n".format(onsetV_of_microdischarge)

        #DEFECTS##############################
        msg += "#Defects section\n"
        msg += "%DEFECT\n"
        msg += "#DEFECT NAME\n"
        oxide_pinholes,n1 = rand_nm(type_ind)
        msg += "Oxide pinholes\t{}\n".format(oxide_pinholes)
        metal_shorts,n2 = rand_nm(type_ind)
        msg += "Metal Shorts\t{}\n".format(metal_shorts)
        metal_opens,n3 = rand_nm(type_ind)
        msg += "Metal Opens\t{}\n".format(metal_opens)
        implant_shorts,n4 = rand_nm(type_ind)
        msg += "Implant Shorts\t{}\n".format(implant_shorts)
        if type_ind == 1: #EC
            bias_resistor_disconnection,n5 = rand_nm(type_ind)
            msg += "Bias resistor disconnection\t{}\n".format(bias_resistor_disconnection)
            total_defects = n1+n2+n3+n4+n5
            percent_ng_strips = total_defects / (4*1536)
        if type_ind == 0: #barrel
            implant_opens,n5 = rand_nm(type_ind)
            msg += "Implant Opens\t{}\n".format(implant_opens)
            microdischarge_strips,n6 = rand_nm(type_ind)
            if microdischarge_strips == "none":
                microdischarge_strips = "-"
            msg += "Microdischarge strips\t{}\n".format(microdischarge_strips)
            total_defects = n1+n2+n3+n4+n5+n6
            percent_ng_strips = total_defects / (4*1282)
        
        msg += "Percentage of NG strips\t{:.10f}%\n\n".format(percent_ng_strips)

        #RAWDATA########################################
        msg += "#IV raw data Raw data section\n"
        msg += "%RAWDATA\n"
        temp = iv_temp
        msg += "IV Temperature(C)\t{}\n".format(temp)
        humid = iv_humid
        msg += "Humidity (%)\t{}\n".format(humid)
        voltage_step = "20"
        msg += "Voltage step (V)\t{}\n".format(voltage_step)
        delay_time = "1"
        msg += "Delay time (second)\t{}\n".format(delay_time)
        msg += "IV Characteristics (A)\n"
        msg += "#IV\n"
        for v,c in ivdata.points:
            #'20\t1.23E-07\n'
            if c == 'O.L.':
                msg += '{}\t{}\n'.format(v,c)
            else:
                msg += ('{}\t%.2E\n' % Decimal(c)).format(v)
        msg += "\n"

        #stability at 700V####################
        msg += "Id stability test @ 700V\n"
        for i in range(3):
            sec = [10,20,30][i]
            c = ivdata.stability[i]
            if c == 'O.L.':
                msg += '{} sec\t{}\n'.format(sec,c)
            else:
                msg += ('{} sec\t%.2E\n' % Decimal(c)).format(sec)
        msg += "#End of manufacturer data file"
        with open(os.path.join(dirpath,idnum+'.txt'),'w') as f:
            f.write(msg)
        
        #increase ingot ind if written 25 files#####
        if (file_ind+1) % 25 == 0:
            ingot_ind += 1
    
    if matplotlib_found:
        #pre-breakdown plot
        plt.ylim(0,1)
        plt.title("All IV curves (zoomed in)")
        plt.ylabel("Current ($\mu$A)")
        plt.xlabel("Voltage (V)")
        plt.savefig(os.path.join(dirpath,"all_IVs_zoom.png"))

        #post-breakdown plot
        plt.ylim(0,10)
        plt.hlines(10,0,700,linestyle='--')
        plt.title("All IV curves (full scale)")
        plt.ylabel("Current ($\mu$A)")
        plt.xlabel("Voltage (V)")
        plt.savefig(os.path.join(dirpath,"all_IVs_full.png"))


def main(args):
    outputdir = args.outputdir
    nfiles    = args.nfiles
    W0        = args.wafer0
    B0        = args.batch0
    BE        = args.barrel_endcap
    print(" got arguments:")
    print("  outputdir = " + outputdir )
    print("  nfiles    = " + str(nfiles) )
    print("  W0        = " + str(W0    ) )
    print("  B0        = " + B0        )
    print("  BE        = " + BE        )
    if nfiles % 25 != 0: #nfiles < 100 or 
        print("Invalid (-N/-nfiles) argument. Must be a multiple of 25!!")
        sys.exit()
    
    #go thru all non-null keys and assign appropriate random values to them
    #os.system("rm -rf dummyfiles")
    #"Usage: python create_dummy_manu_files.py <nfiles> <outputdir> \n-->Puts nfiles new dummyfiles into outputdir (relative to this script).")
    write_random_datafiles(nfiles,outputdir, W0, B0, BE)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description = 'Create dummy manufacturer test files', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-N', '--nfiles', dest = 'nfiles', type = int, required = True, help = 'Number of files to create. Must be a multiple of 25!!')
    required.add_argument('-b', '--batch0', dest = 'batch0', type = str, required = True, help = '1st batch number, e.g. VPX30409')
    required.add_argument('-w', '--wafer0', dest = 'wafer0', type = int, required = True, help = '1st wafer number, e.g. 700')
    required.add_argument('-c', '--barrel_endcap', dest = 'barrel_endcap', type = str, required = True, help = 'a choice of barrel/endcap')
    required.add_argument('-o', '--outputdir', dest = 'outputdir', type = str, required = True, help = 'Where to put the files')
    args = parser.parse_args()
   
    outputdir = args.outputdir
    main(args)
