#load json db
#look for any sensors that have "sample" tests
#   -> current stability, full strip
#    = ATLAS18_CURRENT_STABILITY_V1,ATLAS18_FULLSTRIP_STD_V1
# -> label all sensors in that batch with those attributes
#save edited db
import json

sample_tests = ['ATLAS18_CURRENT_STABILITY_V1','ATLAS18_FULLSTRIP_STD_V1']
def main(jsonfile):
    with open(jsonfile,'r') as f:
        data = json.load(f)

    num_failed_in_batch = {}
    for batchnum in data['by_batch']:
        batch_SNs = data['by_batch'][batchnum]
        num_failed_in_batch[batchnum] = {}
        for st in sample_tests: 
            num_failed_in_batch[batchnum][st] = 0

        for SN in batch_SNs:
            tests = data['data_by_SN'][SN]['tests']
            for st in sample_tests:
                isNG = tests[st].get('NG')
                if isNG == True:
                    num_failed_in_batch[batchnum][st] += 1

        for SN in batch_SNs:
            for st in sample_tests:
                if num_failed_in_batch[batchnum][st] >= 4: #~10% of average batch size
                    data['data_by_SN'][SN]['tests'][st]['NG'] = True


    # VF, 2021-04-27: let's indent the file. It's hard to read/compare otherwise
    with open(jsonfile,'w') as f:
        json.dump( data, f, indent=2 )

if __name__ == '__main__':
    print('NOT INTENDED FOR STANDALONE USE. Used as module in create_local_sensorDB.py')
