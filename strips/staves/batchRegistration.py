#!/usr/bin/env python
#LoadedStave_class.py
        ##           -- class of STAVE, and all of its children comp: MODULEs, CORE, EOS
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#last update 6/12/2019
from __future__ import print_function #import python3 printer if python2 is used

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

# sys.path.append('../')
import argparse
import numpy as np
from itk_pdb.databaseUtilities import ERROR, INFO
from itk_pdb.dbAccess import ITkPDSession

def main(args):

    JSON={} #initiate DTOin for STAVE registration
    #fill in JSON
    JSON['institution']=args.institute
    JSON['componentType']=args.component_type
    JSON['project']='S' #strip
    JSON['subproject']='SB' #strip barrel
    JSON['type']=args.type
    Properties={}
    #staveProperties['SIDE']=self.type

    csv = np.genfromtxt(args.component_list,delimiter=",",dtype=str)

    #initiate a ITkPD session
    session = ITkPDSession()
    session.authenticate()

    try:
        property_code = csv[0,:]
        for i,ID in enumerate(csv[1:,0]): #first column is the IDs

            for j,property in enumerate(property_code):
                Properties[property]=csv[i,j]

            JSON['properties']=Properties
            session.doSomething(action='registerComponent',method='POST',data=JSON)
            INFO("registered " +args.component_type +" with ID: "+ID)

    except IndexError:
        property = csv[0]
        for i,ID in enumerate(csv[1:]): #first column is the IDs
            Properties[property]=ID
            JSON['properties']=Properties
            session.doSomething(action='registerComponent',method='POST',data=JSON)
            INFO("registered " +args.component_type +" with ID: "+ID)


if __name__ =='__main__':
    parser=argparse.ArgumentParser(description='Batch registration of the same type of component in the database')
    parser.add_argument('--institute',type=str, choices=['BU','BNL'],help='Brandeis/BNL')
    parser.add_argument('--component-list',type=str, help='path to the csv with all component properties')
    parser.add_argument('--component-type',type=str, choices=['HYBRID','MODULE','STAVE'],help='core type long/short strip')
    parser.add_argument('--type',type=str ,help='ex. Module, choose from [LONG, SS, R0...]')


    #parser.add_argument('--positions',type=str,help='enter module positions (ex. 2,3,4 or 2-4); enter \'all\' for all module 1-14')
    args=parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        INFO('Finished with error.')
        exit()
