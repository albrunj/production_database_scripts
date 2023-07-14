import re
from datetime import datetime


# VF, 2021-08-18: to remove unlikely cases
def check_non_regex_value(k,v,sensor_type,msg):
    valid = False
    if k == "Test Date (DD/MM/YYYY)":
        if bool(re.search(r'^\d{1,2}/\d{1,2}/\d{4}$',v)):
            try:
                Tstart = "12/01/2019"
                Tend   = "01/01/2026"
                start = datetime.strptime(Tstart, "%d/%m/%Y")
                end = datetime.strptime(Tend,"%d/%m/%Y")
                test_date = datetime.strptime(v,"%d/%m/%Y")
                if start <= test_date <= end:
                    valid = True
                else:
                    msg += "Data outside of bounds [" + Tstart + "," + Tend + "]"
            except Exception:
                msg += "Invalid {}: {}\n".format(k,v)
        else:
            msg += "Invalid {}: {}\n".format(k,v)
    if k == "Deplation Volts (V)":
        try:
            voltage = int(v)
            #if 150 <= voltage <= 350:
            if 0 <= voltage <= 350:
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)
    if k.lower().startswith("leakage current"):
        try:
            current = float(v)
            #if 0.05 <= current <= 10:
            if 0.0 <= current <= 10:
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)
    if k == "Substrate R Upper (kOhm.cm)":
        try:
            R = float(v)
            #if 3.5 <= R <= 12:
            if 3.0 <= R :
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)
    if k == "Substrate R Lower (kOhm.cm)":
        try:
            R = float(v)
            #if 3 <= R <= 8:
            if 3.0 <= R :
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)
    # VF, 2021-08-20: let's add this parameter. In principle, it's in Specs
    if k == "Active thickness (nominal value)":
        try:
            R = float(v)
            #if 3 <= R <= 8:
            if R > 270 :
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)
    if k.startswith("Polysilicon Bias Resistance"):
        try:
            R = float(v)
            if 1.0 <= R <= 2.0:
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)
    if k == "Onset voltage of Microdischarge (V)":
        try:
            voltage = float(v)
            if voltage >= 500:
                valid = True
        except Exception:
            # VF, 2021-08-24: a better way, in case they add "V" to it randomly
            #if v == "over 700":
            if v.startswith("over 700") :
                valid = True
            else:
                msg += "Invalid {}: {}\n".format(k,v)

    if k in ["Oxide pinholes","Metal Shorts","Metal Opens","Implant Shorts","Implant Opens","Microdischarge strips","Bias resistor disconnection"]:
        #either 'none', 'n1-m1' or
        # '"n1-m1, n2-m2, ..."'
        
        if sensor_type == 'EC':
            # seems need to increase this for the production data, VF, 2021-08-19
            # minn,maxn = 0,3
            minn,maxn = 0,4
            minm,maxm = 0,1537
        if sensor_type == 'barrel':
            minn,maxn = 1,4
            minm,maxm = 0,1281

        # VF, 2021-08-20: see this too often, remove the warning and 
        #                 move everything else to the "else" clause
        if v == "none" or v == "-": 
            valid = True
        #if v == "none":
        #    valid = True
        #if v == "-":
        #    msg += "Warning: Value for {} is '-'".format(k)
        else:
            if len(v.split('-')) > 2: #multiple n-m pairs
                try:
                    if v[0] == '"': v = v[1:-1]
                    vlist = v.split(',')
                    for nm in vlist[:-1]:
                        n,m = nm.split('-')
                        if not (minn <= int(n) <= maxn and minm <= int(m) <= maxm):
                            msg += "Invalid {}: {}\n".format(k,v)
                    #last element of vlist can be '' so check specifically for that
                    if vlist[-1] != '': #happens when line ends with a comma
                        # VF, 2021-08-20: seems like a subtle bug...
                        #n,m = nm.split('-')
                        n,m = vlist[-1].split('-')
                        if not (minn <= int(n) <= maxn and minm <= int(m) <= maxm):
                            msg += "Invalid {}: {}\n".format(k,v)

                        valid = True
                except Exception:
                    msg += "Invalid {}: {}\n".format(k,v)
            else: #single n-m pair
                try:
                    n,m = v.split('-')
                    if minn <= int(n) <= maxn and minm <= int(m) <= maxm:
                        valid = True
                except Exception:
                    msg += "Invalid {}: {}\n".format(k,v)

    if k == "Percentage of NG strips":
        try:
            if v.endswith('%'):
                percent = float(v[:-1])
            else:
                percent = float(v)
            if 0.0 <= percent <= 1.0:
                valid = True
        except Exception:
            msg += "Invalid {}: {}\n".format(k,v)

    if bool(re.search(r'^\d{2,3}$',k)):
        #is a 2 or 3 digit voltage (for IV sweep)
        kint = int(k)
        # VF, 2021-08-22: let's restrict this to 500 V, as per specs!
        '''
        if kint % 20 == 0 and kint >= 20 and kint <= 700:
            #is multiple of 20 and 20<=k<=700
            try:
                Ileak = float(v)
                if 0 <= Ileak <= 1.0E-5:
                    valid = True
            except Exception:
                if v == 'O.L.':
                    valid = True
                msg += "Invalid {}: {}\n".format(k,v)
        '''
        if kint % 20 == 0 and kint >= 20 :
            if kint <= 500:
            #is multiple of 20 and 20<=k<=500
            # don't want "O.L." or high values
                if v != 'O.L.':
                    try:
                        Ileak = float(v)
                        if 0 <= Ileak <= 1.0E-5:
                            valid = True
                    except Exception:
                        #if v == 'O.L.':
                        #    valid = True
                        msg += "Invalid {}: {}\n".format(k,v)
            else: # more than 500 V : either "O.L." or some numerical value
                if v == 'O.L.':
                    valid = True
                else:
                    try:
                        Ileak = float(v)
                        if 0 <= Ileak <= 1.0E-3:
                            valid = True
                    except Exception:
                        #if v == 'O.L.':
                        #    valid = True
                        msg += "Invalid {}: {}\n".format(k,v)
                
    if bool(re.search(r'^[1-3]0 sec$',k)):
        # VF, 2021-08-22: either "O.L." or some numerical value
        #stability at 700V
        '''
        try:
            Ileak = float(v)
            if 0.0 <= Ileak <= 1.0E-5:
                valid = True
        except Exception:
            if v == 'O.L.':
                valid = True
            msg += "Invalid {}: {}\n".format(k,v)
        '''
        if v == 'O.L.' or v == '-' :
            valid = True
        else:
            try:
                Ileak = float(v)
                if 0 <= Ileak <= 1.0E-3:
                    valid = True
            except Exception:
                #if v == 'O.L.':
                #    valid = True
                msg += "Invalid {}: {}\n".format(k,v)

    
    if valid:
        return v,msg,True
    
    return None,msg,False
