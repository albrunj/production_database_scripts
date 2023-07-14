import os
import sys
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import matplotlib.pyplot as plt
import numpy as np

#python create_fake_data.py 500
#--creates 500 fake data files with internally specified ranges/distributions

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
                        self.LC_at_500v = "{:.4f}".format(c*1e6)
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
                value += f"{n}-{m}, "
        #if not none, add final pair w/o trailing comma
        m = mstart + npairs
        value += f"{n}-{m}"
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

def write_random_datafiles(nfiles,dirpath):
    os.makedirs(dirpath,exist_ok=True)
    id_prefixes = ["20USBSX","20USESX"]
    ingotnums = random_ingotnums(nfiles // 25)
    ingot_ind = 0
    for file_ind in range(100,100+nfiles):
        print("File_ind = ",file_ind)
        ivdata = GenerateIVdata()
        ivdata.plotIV(file_ind)
        msg = "#General information ITEM section\n"
        msg += "%ITEM\n"

        type_ind = int(round(random())) #0 = barrel, 1 = EC
        idnum = id_prefixes[type_ind] + "%07d"%(file_ind)
        msg += f"Identification Number\t{idnum}\n"
        serialnum = "VPX9000" + str(type_ind+1) + "-" + str(file_ind)
        msg += f"Serial Number\t{serialnum}\n"
        
        sensor_type = "ATLASDUMMY18"
        msg += f"Sensor Type\t{sensor_type}\n\n"
        msg += "#Test information Test section\n"
        msg += "%TEST\n"
        test_date = rand_date("06/01/2020","09/01/2020")
        msg += f"Test Date (DD/MM/YYYY)\t{test_date}\n"
        problem = (["NO"]*9+["YES"])[int(random()*10)]
        msg += f"PROBLEM\t{problem}\n"
        if problem == "YES": passed = "NO"
        else: passed = "YES"
        msg += f"PASSED\t{passed}\n\n"
        
        #DATA####################################
        msg += "#Test data Data section\n"
        msg += "%DATA\n"
        iv_temp = int(round(random()*10) + 20)
        msg += f"IV Temperature(C)\t{iv_temp}\n"
        iv_humid = int(round(random()*40) + 20)
        msg += f"IV Humidity(%)\t{iv_humid}\n"
        deplation_volts = int(round(random()*400 + 100))
        msg += f"Deplation Volts (V)\t{deplation_volts}\n"
        LC_at_vfd_plus_50v = ivdata.get_LC_at_vfd_plus_50v(deplation_volts)
        msg += "Leakage Current at Vfd + 50V (microA)\t{}\n".format(LC_at_vfd_plus_50v)
        LC_at_500v = ivdata.LC_at_500v
        msg += "Leakage current at 500 V (microA)\t{}\n".format(LC_at_500v) 
        ingotnum = ingotnums[ingot_ind]
        msg += f"Substrate Lot No.\t{ingotnum}\n"
        substrate_type = ["FZ1","(FZ1)","FZ-1"][int(random()*3)]
        msg += f"Substrate Type\t{substrate_type}\n"
        substrate_orient = "100"
        msg += f"Substrate Orient\t{substrate_orient}\n"
        substrate_RUpper = "{:.1f}".format(random()*8.5+3.5)
        msg += f"Substrate R Upper (kOhm.cm)\t{substrate_RUpper}\n"
        substrate_RLower = "{:.1f}".format(random()*5 + 3)
        msg += f"Substrate R Lower (kOhm.cm)\t{substrate_RLower}\n"
        active_thickness = "290"
        msg += f"Active thickness (nominal value)\t{active_thickness}\n"
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
        msg += f"Oxide pinholes\t{oxide_pinholes}\n"
        metal_shorts,n2 = rand_nm(type_ind)
        msg += f"Metal Shorts\t{metal_shorts}\n"
        metal_opens,n3 = rand_nm(type_ind)
        msg += f"Metal Opens\t{metal_opens}\n"
        implant_shorts,n4 = rand_nm(type_ind)
        msg += f"Implant Shorts\t{implant_shorts}\n"
        if type_ind == 1: #EC
            bias_resistor_disconnection,n5 = rand_nm(type_ind)
            msg += "Bias resistor disconnection\t{}\n".format(bias_resistor_disconnection)
            total_defects = n1+n2+n3+n4+n5
            percent_ng_strips = total_defects / (4*1536)
        if type_ind == 0: #barrel
            implant_opens,n5 = rand_nm(type_ind)
            msg += f"Implant Opens\t{implant_opens}\n"
            microdischarge_strips,n6 = rand_nm(type_ind)
            if microdischarge_strips == "none":
                microdischarge_strips = "-"
            msg += "Microdischarge strips\t{}\n".format(microdischarge_strips)
            total_defects = n1+n2+n3+n4+n5+n6
            percent_ng_strips = total_defects / (4*1282)
        
        # VF, 2021-08-14: this is actually a fraction, not percentage -> will remove the "%" sign
        #msg += "Percentage of NG strips\t{:.10f}%\n\n".format(percent_ng_strips)
        msg += "Percentage of NG strips\t{:.10f}\n\n".format(percent_ng_strips)

        #RAWDATA########################################
        msg += "#IV raw data Raw data section\n"
        msg += "%RAWDATA\n"
        temp = iv_temp
        msg += f"IV Temperature(C)\t{temp}\n"
        humid = iv_humid
        msg += f"Humidity (%)\t{humid}\n"
        voltage_step = "20"
        msg += f"Voltage step (V)\t{voltage_step}\n"
        delay_time = "1"
        msg += f"Delay time (second)\t{delay_time}\n"
        msg += "IV Characteristics (A)\n"
        msg += "#IV\n"
        for v,c in ivdata.points:
            #'20\t1.23E-07\n'
            if c == 'O.L.':
                msg += f'{v}\t{c}\n'
            else:
                msg += f'{v}\t%.2E\n' % Decimal(c)
        msg += "\n"

        #stability at 700V####################
        msg += "Id stability test @ 700V\n"
        for i in range(3):
            sec = [10,20,30][i]
            c = ivdata.stability[i]
            if c == 'O.L.':
                msg += f'{sec} sec\t{c}\n'
            else:
                msg += f'{sec} sec\t%.2E\n' % Decimal(c)
        msg += "#End of manufacturer data file"
        with open(os.path.join(dirpath,idnum+'.txt'),'w') as f:
            f.write(msg)
        
        #increase ingot ind if written 25 files#####
        if (file_ind+1) % 25 == 0:
            ingot_ind += 1
    #pre-breakdown plot
    plt.ylim(0,1)
    plt.title("All IV curves (zoomed in)")
    plt.ylabel("Current ($\mu$A)")
    plt.xlabel("Voltage (V)")
    plt.savefig("dummyfiles/all_IVs_zoom.png")
    #post-breakdown plot
    plt.ylim(0,10)
    plt.hlines(10,0,700,linestyle='--')
    plt.title("All IV curves (full scale)")
    plt.ylabel("Current ($\mu$A)")
    plt.xlabel("Voltage (V)")
    plt.savefig("dummyfiles/all_IVs_full.png")

def main():
    #go thru all non-null keys and assign appropriate random values to them
    try:
        nfiles = int(sys.argv[1])
        write_random_datafiles(nfiles,"dummyfiles/")
    except Exception as e:
        raise(e)
        print("Usage: python create_fake_data.py <nfiles>")
        sys.exit()

if __name__ == "__main__": 
    main()
