#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import os
import argparse
import itk_pdb.dbAccess as dbAccess


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Determines the number of components without a parent, i.e. not attached to a powerboard.")

    parser.add_argument("component", help="Code of component.")
    parser.add_argument("type", help="Code for component subtype.")

    args = parser.parse_args()

    if os.getenv("ITK_DB_AUTH"):
            dbAccess.token = os.getenv("ITK_DB_AUTH")

    i = 0
    comp_list = dbAccess.doSomething("listComponents", {'project':'S', 'componentType':args.component, 'type':args.type, 'institution':'LBL'}, method='GET')
    get_comp_list = dbAccess.doSomething("getComponentBulk", {'component':[component['code'] for component in comp_list['pageItemList']]}, method='GET')
    for component in get_comp_list['itemList']:
        if len(component['parents'])==0 and component['trashed']==False:
          i = i + 1

    print(i)
