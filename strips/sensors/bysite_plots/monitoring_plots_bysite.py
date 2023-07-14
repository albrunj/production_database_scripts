#for each cluster and sensortype, plot 3 cumulative curves
#1) # sensors of each type received (from anywhere)
#2) # sensors of each type fully tested and passed (based on all tests)
#3) # sensors of each type sent out to module sites (?)
import datetime
import json
import os

import matplotlib.pyplot as plt
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

###globals ###############
sensor_types = ['ATLAS18SS','ATLAS18LS',
                        'ATLAS18R0','ATLAS18R1',
                        'ATLAS18R2','ATLAS18R3',
                        'ATLAS18R4','ATLAS18R5',
                        'ATLASDUMMY18']

colors = ['blue','green',
                'red','black',
                'brown','orange',
                'purple','pink',
                'lightblue'] #one for each sensor type

sensType_color = {}
for i in range(len(sensor_types)):
    sensType_color[sensor_types[i]] = colors[i]


################
def load_local_db(jsonfile):
    try:
        with open(jsonfile,'r') as f:
            local_db = json.load(f)
    except IOError as e:
        raise(e)
    return local_db

def get_fully_tested_and_passed(local_db,SN):
    component = local_db['data_by_SN'][SN]
    for testrun_code in component['tests']:
        testdata = component['tests'][testrun_code]
        if not testdata['passed'] and testdata['required']:
            return False
    return True

def get_fully_tested_and_passed_sensors(local_db,sensor_data):
    ftp_sensors = {}
    #get num sensors of each type fully tested and passed
    for sensType in sensor_data:
        ftp_sensors[sensType] = {}
        #first look at sensors received
        for dateobj in sensor_data[sensType]['received']:
            ftp_sensors[sensType][dateobj] = {}
            for SN in sensor_data[sensType]['received'][dateobj]:
                ftp = get_fully_tested_and_passed(local_db,SN)
                ftp_sensors[sensType][dateobj][SN] = ftp
        #look at sensors sent out (might be some overlap)
        for dateobj in sensor_data[sensType]['sent out']:
            if ftp_sensors[sensType].get(dateobj) == None:
                ftp_sensors[sensType][dateobj] = {}
            for SN in sensor_data[sensType]['sent out'][dateobj]:
                ftp = get_fully_tested_and_passed(local_db,SN)
                ftp_sensors[sensType][dateobj][SN] = ftp
    return ftp_sensors
            
def get_sensors_from_all_shipments(client,local_db,cluster,mindate,maxdate):
    inst_codes = cluster.strip('-')
    sensor_data = {}
    for sensType in sensor_types:
        sensor_data[sensType] = {}
        sensor_data[sensType]['received'] = {}
        sensor_data[sensType]['sent out'] = {}

    """
    OLD version: doesn't look at shipments, just looks at where sensors
    currently are...I don't think this is useful

    #get sensors received from anywhere (by type)
    for inst_code in inst_codes:
        SNs_received_at_institute = local_db['by_currentLocation'][inst_code]
        for SN in SNs_received_at_institute:
            sensorType = local_db['data_by_SN'][SN]['type']
            try:
                sensors_received[sensorType].append(local_db['data_by_SN'][SN])
            except KeyError as e:
                raise(e)

    return sensors_received
    """
    for SN in local_db['by_sensor']:

        sensorType = local_db['data_by_SN'][SN]['type']
        shipment_ids = local_db['data_by_SN'][SN]['shipments']
        if len(shipment_ids) == 0:
            continue

        for sid in shipment_ids:
            shipment = client.get('getShipment',data={'shipment':sid})
            status = shipment['status']
            dateobj = parse(shipment['history'][-1]['dateTime']).date()
            if dateobj < mindate or dateobj > maxdate:
                continue
            
            #round date to beginning of month (for binning)
            dateobj = datetime.date(dateobj.year,dateobj.month,1)

            if status == 'delivered':
                if shipment['sender']['code'] in inst_codes and \
                        shipment['recipient']['code'] not in inst_codes:
                    #left this cluster
                    print('{} sent out shipment: {}'.format(cluster,shipment['name']))
                    try:
                        sensor_data[sensorType]['sent out'][dateobj].append(SN)
                    except KeyError:
                        sensor_data[sensorType]['sent out'][dateobj] = [SN]

                if shipment['recipient']['code'] in inst_codes and \
                        shipment['sender']['code'] not in inst_codes:
                    #received by this cluster
                    print('{} received shipment: {}'.format(cluster,shipment['name']))
                    try:
                        sensor_data[sensorType]['received'][dateobj].append(SN)
                    except KeyError:
                        sensor_data[sensorType]['received'][dateobj] = [SN]

    return sensor_data

def plot_common(dates,counts,sensorType,series_label='Series 1',color='k'):
    if not any(counts):
        #if all zeros, don't plot any data
        return False

    plt.plot_date(dates,counts,'-',marker='.',label=series_label,color=color)
    return True


def plot_received(cluster,sensorType,dates,counts):
    color = 'g'
    return plot_common(dates,counts,sensorType,
                series_label='{} sensors received'.format(sensorType),
                color = color
    )

def plot_ftp_received(cluster,sensorType,dates,counts):
    color = 'darkgreen'
    return plot_common(dates,counts,sensorType,
                series_label='FT&P {} sensors received'.format(sensorType),
                color = color
    )

def plot_sent_out(cluster,sensorType,dates,counts):
    color = 'r'
    return plot_common(dates,counts,sensorType,
                series_label='{} sensors sent out'.format(sensorType),
                color = color
    )
def plot_ftp_sent_out(cluster,sensorType,dates,counts):
    color = 'darkred'
    return plot_common(dates,counts,sensorType,
                series_label='FT&P {} sensors sent out'.format(sensorType),
                color = color
    )

def get_month_range(start,end):
    start = datetime.date(start.year,start.month,1)
    mrange = [start]
    tmp = start
    while tmp < end:
        tmp = tmp + relativedelta(months=+1)
        if tmp > end:
            tmp = end
        mrange.append(tmp)
    return mrange


def plot_sensors(timestamp,cluster,sensor_data,fully_tested_and_passed_sensors,mindate,maxdate):
    dates = get_month_range(mindate,maxdate) 
    for sensType in sensor_types:
        #print(sensType)
        num_received,received = 0,[]
        num_sent_out,sent_out = 0,[]
        num_ftp_received,ftp_received = 0,[]
        num_ftp_sent_out,ftp_sent_out = 0,[]
        
        for monthdate in dates:
            #sensors received
            sensors_received = sensor_data[sensType]['received'].get(monthdate,[])
            num_received += len(sensors_received)
            received.append(num_received)
            
            #sensors sent out from cluster
            sensors_sent_out = sensor_data[sensType]['sent out'].get(monthdate,[])
            num_sent_out += len(sensors_sent_out)
            sent_out.append(num_sent_out)
            
            
            #sensors received that are fully tested and passed
            ftp_sensors_received = list(filter(lambda SN: fully_tested_and_passed_sensors[sensType].get(monthdate,{}).get(SN)==True,sensors_received))
            num_ftp_received += len(ftp_sensors_received)
            ftp_received.append(num_ftp_received)

            #sensors sent out that are fully tested and passed
            ftp_sensors_sent_out = list(filter(lambda SN: fully_tested_and_passed_sensors[sensType].get(monthdate,{}).get(SN)==True,sensors_sent_out))
            num_ftp_sent_out += len(ftp_sensors_sent_out)
            ftp_sent_out.append(num_ftp_sent_out)

        #print("dates:",dates)
        rv1 = plot_received(cluster,sensType,dates,received)
        rv2 = plot_ftp_received(cluster,sensType,dates,ftp_received)
        rv3 = plot_sent_out(cluster,sensType,dates,sent_out)
        rv4 = plot_ftp_sent_out(cluster,sensType,dates,ftp_sent_out)

        if any([rv1,rv2,rv3,rv4]):
            #format figure
            plt.xlabel("Date")
            plt.ylabel("Number of sensors")
            plt.title("{} : {} Production History".format(cluster,sensType))
            plt.gcf().autofmt_xdate()
            plt.legend()
            savedir = os.path.join(timestamp,cluster)
            try:
                #create cluster dir if doesn't exist
                os.makedirs(savedir)
            except OSError:
                pass
            pdf_path = os.path.join(savedir,sensType+'.pdf')
            plt.savefig(pdf_path)
            plt.clf()

    
#def cleanup(cluster):
#    dirlist = os.listdir(cluster)
#    if len(dirlist) == 0:
#        os.system('rm -r {}'.format(cluster))


def main(client):
    now = datetime.datetime.now()
    now_epoch = now.strftime('%s')

    QC_clusters = ['CAM','QMUL','FZU','SFU-TRIUMF','CU','KEK-UCSC_STRIP_SENSORS']
    jsonfile = '/home/vf/ITkSS_reporting/localDB_2021-09-29.json'
    mindate,maxdate = datetime.date(2020,1,1),datetime.date(2022,1,1)
    local_db = load_local_db(jsonfile)
    for clusterString in QC_clusters:
        sensor_data = get_sensors_from_all_shipments(client,local_db,clusterString,mindate,maxdate)
        fully_tested_and_passed_sensors = get_fully_tested_and_passed_sensors(local_db,sensor_data)
        plot_sensors(now_epoch,clusterString,sensor_data,fully_tested_and_passed_sensors,mindate,maxdate)
        #cleanup(clusterString)


if __name__ == '__main__':
    import itkdb
    client = itkdb.Client(expires_after=dict(days=1))
    main(client)
