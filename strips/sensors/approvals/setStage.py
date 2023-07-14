#!/usr/bin/env python
import argparse

from __path__ import updatePath

updatePath()

import itkdb	
from pprint import PrettyPrinter
# import itk_pdb.dbAccess as dbAccess
# from itk_pdb.dbAccess import ITkPDSession


pp = PrettyPrinter(indent = 1,width=200)

def main(client,args):
    SNs = args.serialNumbers
    newStage = args.newStage
    for SN in SNs:
        resp = client.get('getComponent',data = {'component':SN})
        pp.pprint(resp)
        if resp == None:
            print("Component with SN {} doesn't exist".format(SN))
            continue

        dto = {'component':resp['code'],
                'stage': newStage,
                
                'comment': "setting to new stage"}

        resp2 = client.post('setComponentStage', data = dto)
        if resp2 != None:
            print("Set stage for component {}".format(SN))
        else:
            print("Error setting stage for component {}".format(SN))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Set/change stage for existing sensors')
    required = parser.add_argument_group('required arguments')
    required.add_argument('-s', '--serialNumbers', nargs='*', dest = 'serialNumbers', type = str, required = True, help = 'Space-separated serial numbers (e.g. 20UXXYYAB00000)')
    required.add_argument('-S', '--stage', dest = 'newStage', type = str, required = True, help = 'Stage code (e.g. QC_Tests)')
    args = parser.parse_args()

#    import itkdb
#    import redis
#    from cachecontrol.caches.redis_cache import RedisCache
#
#    cache = RedisCache(redis.Redis(connection_pool=redis.ConnectionPool(host='itkstrips.ucsc.edu', port=6379, db=0)))
    client = itkdb.Client() #cache=cache, expires_after={'days': 1})
    main(client,args)
