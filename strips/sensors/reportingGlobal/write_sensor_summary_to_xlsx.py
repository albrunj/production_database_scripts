#!/usr/bin/python
import json
import sys
from datetime import datetime

import json_to_xlsx
from __path__ import updatePath
#from pprint import PrettyPrinter

updatePath()

values_json,formatting_json = "tmpvalues.json","tmpformatting.json"

testrun_codes = ['MANUFACTURING18','ATLAS18_VIS_INSPECTION_V1','ATLAS18_IV_TEST_V1','ATLAS18_CV_TEST_V1','ATLAS18_SHAPE_METROLOGY_V1','ATLAS18_CURRENT_STABILITY_V1','ATLAS18_FULLSTRIP_STD_V1','ATLAS18_MAIN_THICKNESS_V1','ATLAS18_HM_THICKNESS_V1']

testrun_attrs = {'ATLAS18_HM_THICKNESS_V1':['AvThickness'],'ATLAS18_CURRENT_STABILITY_V1':['Abs_I_leak_av','I_leak_variation'],'ATLAS18_CV_TEST_V1':['vfd','Neff'],'ATLAS18_MAIN_THICKNESS_V1':['AvThickness'],'ATLAS18_FULLSTRIP_STD_V1':['N_badcluster_max','bad_strip_fraction'],'ATLAS18_VIS_INSPECTION_V1':[],'ATLAS18_IV_TEST_V1':['I_500V','VBD','RMS_stability'],'ATLAS18_SHAPE_METROLOGY_V1':['bowing'],'MANUFACTURING18':['percentNGstrips','microdischarge','Ileak@500V','vfd']}
fields = ['serialNumber','componentType','type','currentStage','origLocation','currentLocation','assembled','DATE_RECEIVED','ID']
sensor_type_abbrevs = ['SS','LS','R0','R1','R2','R3','R4','R5','DUMMY']

header_row = 7
row,col = header_row+1,0
MAXROWS = 30000
MAXCOLS = 200
class Buffersheet():
    def __init__(self):
        self.values = []
        self.formattings = []
        self.init()
    def init(self):
        for r in range(MAXROWS):
            self.values.append([])
            self.formattings.append([])
            for c in range(MAXCOLS):
                self.values[r].append('')
                self.formattings[r].append({})

    def write(self,row,col,value,formatting={}):
        try:
            self.values[row][col] = value
            #formatting['shrink'] = True #always shrink to fit
            formatting['border'] = 1
            #formatting['border_color'] = '#000000'
            self.formattings[row][col] = formatting
        except IndexError:
            print("Write error: Row ({}) or col ({}) greater than MAXROWS ({}) or MAXCOLS ({})".format(row,col,MAXROWS,MAXCOLS)) 
    def truncate_row(self,row,endcol):
        self.values[row] = self.values[row][:endcol]
        self.formattings[row] = self.formattings[row][:endcol]
    def trim_extra_rows(self):
        for r in range(len(self.values)-1,-1,-1):
            null_row = True
            for elem in self.values[r]:
                if elem != '':
                    null_row = False
            if not null_row:
                break

        self.values = self.values[:r+1]
        self.formattings = self.formattings[:r+1]

    def getvalue(self,row,col):
        try:
            return self.values[row][col]
        except Exception:
            return None
    def getrow(self,row):
        return self.values[row]
    


def load_components(bufferfile):
    try:
        with open(bufferfile,'r') as f:
            return json.load(f)
    except Exception:
        print("Problem loading buffer file",bufferfile)
        sys.exit()

def get_wafer_numbers(components,intersection):
    wafernums = []
    for SN in intersection:
        wafernums.append((components['data_by_SN'][SN]['waferNumber'],components['data_by_SN'][SN]['code']))
    sorted_wafernums = sorted(wafernums,key=lambda x:int(x[0]))
    return sorted_wafernums

def get_sensor_type_counts(sensor_type_abbrev,count):
    sensor_type_abbrev_vals = []
    for abbrev in sensor_type_abbrevs:
        if sensor_type_abbrev == abbrev:
            sensor_type_abbrev_vals.append(count)
        else:
            sensor_type_abbrev_vals.append(0)
    return sensor_type_abbrev_vals

def get_status_color(status):
    if status == 'prepared':
        status_color = '#FFFF99'
    elif status == 'inTransit':
        status_color = '#FFBB30'
    elif status == 'delivered':
        status_color = '#88FF88'
    elif status == 'deliveredWithDamage':
        status_color = '#FF8888'
    else:
        status_color = '#FFFFFF'
    return status_color

def iterate_filters(client,components,filters,filter_keys=[],filter_components=[],depth=0):
    global row,col,buffersheet
    #filter_keys=values of all filters in a line (when depth=len(filters))
    #filter_key = a value of a filter
    #filter = like "batch" or "ingot"
    current_filter = filters[depth]
    for filter_key in components['by_'+current_filter]:
        #update filter_keys, truncate or append
        if len(filter_keys) <= depth:
            filter_keys.append(filter_key)
        else:
            filter_keys[depth] = filter_key
        
        filter_keys = list(filter_keys[:depth+1])

        current_filter_components = components['by_'+current_filter][filter_key]

        if len(filter_components) == 0:
            intersection = list(current_filter_components)
        else:
            intersection = list(set(filter_components).intersection(current_filter_components))
        count = len(intersection)
        if count == 0: 
            continue

        if depth < len(filters)-1:
            iterate_filters(client,components,filters,
                    filter_components=intersection,
                    filter_keys=filter_keys,
                    depth=depth+1)

        else: #iterator reached final filter, so write new line
            qaminis,qachips = 0,0
            bad_data_counts = {}
            num_tested = {}
            for testrun_code in testrun_codes:
                bad_data_counts[testrun_code] = {}
                bad_data_counts[testrun_code]['numNGsensors'] = 0
                num_tested[testrun_code] = 0

            bolds = [] #bold wafernums of NG sensors
            for SN in intersection:
                bold = False
                component = components['data_by_SN'][SN]
                qaminis += component['QAminiCount']
                qachips += component['QAchipCount'] 
                
                #update bad_data_counts for all tests and their values
                if filters[0] == 'sensor':
                    test_data_values = {}
                for testrun_code in testrun_codes:
                    if filters[0] == 'sensor':
                        test_data_values[testrun_code] = {} #for sensor summaries
                    found_bad_data = False
                    if component['tests'].get(testrun_code) != None:
                        if component['tests'][testrun_code]['tested']:
                            num_tested[testrun_code] += 1

                        #review which specific parameters in tests are NG
                        for k in component['tests'][testrun_code]:
                            if type(component['tests'][testrun_code][k]) == dict:
                                valdict = component['tests'][testrun_code][k]
                                value,isNG = valdict['value'],valdict['NG']
                                if filters[0] == 'sensor':
                                    test_data_values[testrun_code][k] = value

                                isNG = component['tests'][testrun_code][k]['NG']

                                if isNG:
                                    try:
                                        bad_data_counts[testrun_code][k] += 1
                                    except KeyError:
                                        bad_data_counts[testrun_code][k] = 1

                                    found_bad_data = True

                    if found_bad_data:
                        bad_data_counts[testrun_code]['numNGsensors'] += 1
                        bold = True
                
                #keep track of bold wafer numbers (bold when NG for any test)
                bolds.append(bold)

            #get shipment data
            bg_color = '#FFFFFF' #white: default background color
            if 'shipment' in filters:
                shipment_id = filter_keys[filters.index('shipment')]
                resp = client.get('getShipment',data={'shipment':shipment_id})
                if resp != None:
                    shipment = (resp['name'],resp['history'][-1]['dateTime'],resp['status'],shipment_id,resp['sender']['code'],resp['recipient']['code'])
                else:
                    shipment = ('No shipment','N/A','N/A','N/A','N/A','N/A')

                status = shipment[2]
                status_color = get_status_color(status)

            #write formatted data (all filters below) to buffer
            for f in range(len(filters)):
                print("FILTER:",filters[f])
                if filters[f] in ['arrivalDate','origLocation','currentLocation','batch','ingot']:
                    val = component.get(filters[f],'Not found')
                    writecell(row,col,val)
                    col += 1
                elif filters[f] == 'sensor':
                    #intersection should just be length 1
                    writecell(row,col,intersection[0])
                    col += 1
                elif filters[f] == 'shipment':
                    name,date,status,shipment_id,from_code,to_code = shipment
                    writecell(row,col,name)
                    writecell(row,col+1,date)
                    writecell(row,col+2,status,{'bg_color':status_color})
                    writecell(row,col+3,shipment_id)
                    writecell(row,col+4,from_code)
                    writecell(row,col+5,to_code)
                    col += 6
                elif filters[f] == 'sensorType':
                    print("filter_keys= ",filter_keys)
                    print("filter_keys[f]= ",filter_keys[f])

                    sensor_type_abbrev = (filter_keys[f][-2:] if filter_keys[f].startswith("ATLAS18") else "DUMMY")
                    sensor_type_abbrev_vals = get_sensor_type_counts(sensor_type_abbrev,count)
                    for c in range(9):
                        writecell(row,col,sensor_type_abbrev_vals[c])
                        col += 1
                else:
                    pass

            #write remaining columns
            writecell(row,col,qaminis)
            writecell(row,col+1,qachips)
            col += 2

            #write NG columns
            for testrun_code in testrun_codes:
                numNG = bad_data_counts[testrun_code]['numNGsensors']
                ntested = num_tested[testrun_code]
                NGformat = {}
                if numNG > 0:
                    NGformat = {'bg_color':'#FF0000'}
                writecell(row,col,'{}/{}/{}'.format(ntested,numNG,count),NGformat)
                col += 1
                if filters[0] != 'shipment':
                    for k in testrun_attrs[testrun_code]:
                        NGformat = {}
                        try: 
                            badcount = bad_data_counts[testrun_code][k]
                            NGformat = {'bg_color':'#FF0000'}
                        except KeyError:
                            badcount = 0

                        #if sensor summary, write values. Else, write number of sensors with NG values
                        if filters[0] == 'sensor':
                            value = test_data_values[testrun_code].get(k,'Not found')
                            writecell(row,col,'{}'.format(value),NGformat)
                        else:
                            writecell(row,col,'{}'.format(badcount),NGformat)
                        col += 1
                
            #write wafer number columns
            wafer_numbers = get_wafer_numbers(components,intersection)
            for w in range(len(wafer_numbers)):
                wnum,compcode = wafer_numbers[w]
                bg_color = json_to_xlsx.lightercolor('#BBBBFF')
                formatting = {'bg_color':bg_color,'font_color':'#0000FF'}
                
                formatting['link'] = 'https://itkpd-test.unicorncollege.cz/componentView?code={}'.format(compcode)
                if bolds[w]: 
                    formatting['bold'] = True
                    formatting['font_name'] = 'Courier'
                    formatting['font_color'] = '#FF0000'
                writecell(row,col,wnum,formatting)
                col += 1


            print("Wrote line!",row) 
            buffersheet.truncate_row(row,col)
            #increment row, reset col to start of line
            row,col = row + 1,0

def writecell(row,col,value,formatting={}):
    global buffersheet
    buffersheet.write(row,col,value,formatting)
    
def getcell(row,col):
    global buffersheet
    return buffersheet.getvalue(row,col)

def write_summary(client,components,groupBy,sortBy,filters):
    global buffersheet,outfilepath,row
    print("Writing summary...")
    buffersheet = Buffersheet()
    if groupBy == 'default': 
        groupBy = 'shipment'
    filters.insert(0,groupBy)

    title = "SENSOR (and SENSOR_S_TEST) inventory summary: "
    title += 'Grouped by {}'.format(groupBy)
    title += ', Sorted by {}'.format(sortBy)
    title += ', Updated {}'.format(datetime.now().strftime('%Y-%m-%d'))

    writecell(0,5,title,{'font_name':'calibri','font_size':20,'bold':True})

    #if 'shipment' in filters:
    #    writecell(3,12,"KEY:",{'bold':True})
    #    writecell(3,13,'DELIVERED',{'bold':True,'bg_color':'#88FF88'})
    #    writecell(3,14,'PREPARED',{'bold':True,'bg_color':'#FFFF99'})
    #    writecell(3,15,'DAMAGED',{'bold':True,'bg_color':'#FF8888'})
    #    writecell(3,16,'IN TRANSIT',{'bold':True,'bg_color':'#FFBB30'})

    writecell(3,20,'NG sensor (bold blue font)',{'bold':True,'font_color':'#0000FF','font_size':18})
    writecell(4,20,'NG data format: NUM_TESTED/NUM_NG/total',{'bold':True,'font_color':'#FF0000','font_size':18})


    colnum = 0
    for header in filters: 
        bg_color = '#BBBBBB'
        if header == "sensorType":
            for c in range(9):
                bg_color = bg_color[0] + str(c) + bg_color[2:]
                writecell(header_row,colnum,sensor_type_abbrevs[c],{'bg_color':bg_color})
                colnum += 1
        elif header == "shipment":
            bg_color = '#BBBB00'
            writecell(header_row,colnum,"ShipmentName",{'bg_color':bg_color})
            writecell(header_row,colnum+1,"ShipmentDate",{'bg_color':bg_color})
            writecell(header_row,colnum+2,"ShipmentStatus",{'bg_color':bg_color})
            writecell(header_row,colnum+3,"ShipmentID",{'bg_color':bg_color})
            writecell(header_row,colnum+4,"From",{'bg_color':bg_color})
            writecell(header_row,colnum+5,"To",{'bg_color':bg_color})
            colnum = colnum + 6
        else:
            if header == "arrivalDate":
                bg_color = '#55BB55'
            elif header == "ingot":
                bg_color = '#BBBB55'
            elif header == "batch":
                bg_color = '#BB2233'
            elif header == "sensor":
                bg_color = '#44AAFF'
            elif header.endswith('Location'):
                bg_color = '#BBFF99'
            else:
                bg_color = '#BBBBBB'
            writecell(header_row,colnum,"{}".format(header),{'bg_color':bg_color})
            colnum = colnum + 1

    more_headers = [("Total QA minis",{'bg_color':'#CCCCCC'}),("Total QA chips",{'bg_color':'#CCCCCC'})]
    for testrun_code in testrun_codes:
        fmt = {'bg_color':'#DD6666'}
        if testrun_code == 'MANUFACTURING18':
            #make hpk test different color
            fmt['bg_color'] = '#22FF22'
        more_headers.append(("NG-"+testrun_code,fmt))
        if filters[0] != 'shipment':
            for k in testrun_attrs[testrun_code]:
                more_headers.append(("NG-"+k,fmt))
    
    fmt = {'bg_color':'#BBBBFF'} #blue
    more_headers.append(("Wafer Numbers",fmt))
    
    for header,fmt in more_headers:
        writecell(header_row,colnum,header,fmt)
        colnum += 1

    #ex. filter = "shipment", filter_key = "3ff33193848fds390", filter_components = [...SNlist...]
    iterate_filters(client,components,filters)

    buffersheet.trim_extra_rows()
    with open(values_json,'w') as jsonfile:
        json.dump(buffersheet.values,jsonfile)
    with open(formatting_json,'w') as jsonfile:
        json.dump(buffersheet.formattings,jsonfile)

    json_to_xlsx.write_summary_to_xlsx(outfilepath,values_json,formatting_json,summary_type=groupBy,sortBy=sortBy)
    print("wrote summary to {}".format(outfilepath))

def main(client,args):
    global outfilepath
    sortBy = args.sortBy
    groupBy = args.groupBy
    filters = args.filters
    timestamp = datetime.now().strftime('%Y-%m-%d')
    if args.outfile == None:
        outfilepath = "{}_summary_sortedBy_{}_{}.xlsx".format(groupBy,sortBy,timestamp)
    else:
        outfilepath = args.outfile
    
    localDBname = args.localDBname

    #get all components w component data from inputfile
    components = load_components(localDBname)

    write_summary(client,components,groupBy,sortBy,filters)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Specialized inventory summary to local XLSX')
    parser.add_argument('-g', '--groupBy', dest = 'groupBy', type = str,required=True, choices = ['sensor','shipment','batch'],default='shipment', help = 'how to group each line in outfile')
    parser.add_argument('-f','--filters',dest='filters',nargs='*',default='default',type=str,help='Space-separated list of filters to specify what must be constant on each line in outfile (groupBy filter already applied). Choose any of "shipment","sensorType","currentLocation","origLocation","batch",and "ingot".')
    parser.add_argument('-o', '--outfile', dest = 'outfile', type = str, default=None, help = 'outfile name (default is <groupBy>_summary_<timestamp>.xlsx)')
    parser.add_argument('-d','--localDBname',dest='localDBname',type=str,default='localDB.json',help = 'local sensor database filename')
    parser.add_argument('-s','--sortBy',dest = 'sortBy',choices=['ingot','ShipmentDate','arrivalDate','batch','currentLocation','origLocation'],type=str,default = 'default',help = 'which column to sort rows by (pick any column header)')
    args = parser.parse_args()
    
    defaults = {'filters': 
            {'shipment':['sensorType','origLocation','currentLocation','batch','ingot'],
             'batch':['arrivalDate','sensorType','ingot','origLocation','currentLocation'],
             'sensor':['arrivalDate','sensorType','batch','ingot','origLocation','currentLocation']
             },

                'sortBy':
            {'shipment':'ShipmentDate',
             'batch':'arrivalDate',
             'sensor':'arrivalDate'
             }
    }

    if args.filters == 'default':
        args.filters = defaults['filters'][args.groupBy]
    if args.sortBy == 'default':
        args.sortBy = defaults['sortBy'][args.groupBy]

    import itkdb
    client = itkdb.Client(expires_after=dict(days=1))
    main(client,args)
