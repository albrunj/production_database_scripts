#!/usr/bin/env python
#GetFamilyTree.py
        ##           -- Draw Family Tree of a component
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#created 06/06/2019
#last update 06/13/2019

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import argparse
import numpy as np
from itk_pdb.databaseUtilities import ERROR, INFO
from itk_pdb.dbAccess import ITkPDSession
from graphviz import Digraph

class plotFamilyTree(object):

#init: children_recursive; component_id; type; g = Digraph('G', filename='hello.gv')
    def __init__(self,project = "S", component_code = "STAVE",save_filename = "FamilyTree", component_name=None, type_code = "SS-A", recursive=1, includeAllType = False,ITkPDSession=None):
        self.project=project
        self.filename=save_filename
        self.comp_code = component_code
        self.name = component_name
        self.type = type_code
        self.r=recursive
        self.includeAllType = includeAllType
        self.ITkPDSession = ITkPDSession

        #self.children_nodes = []

        #initiate Digraph
        self.g=Digraph('G',filename=self.filename,node_attr={'shape': 'record', 'height': '.1'})
        self.g.attr(size='8.5,11')
        #self.g.attr(rankdir='LR')

        self.createFamilyTree()

#Functions

    def getComponentType(self,code):
        #Stave ID: 5ad8850c09d7a800067a4f60
        component=self.ITkPDSession.doSomething(action='getComponentTypeByCode',method='GET',
                                            data={'project':self.project,'code': code})
        return component

    #plot parent as well
    #def getParent(self):

    #read Component dict
    def createFamilyTree(self):
        component=self.getComponentType(self.comp_code)

        for type in component["types"]:
            if type["code"] == self.type:
                self.type_name = type["name"]

        #Head node
        self.head='H'
        self.g.node('H', self.name + ' (' + self.type_name + ')',color="red")

        self.generation = 0
        try:
            self.getChildren(component["children"], self.type, self.head)
        except TypeError:
            ERROR("component has no children... exiting program")
            exit()

            #for parent in new_parent_info:
            #    parent_code = parent["code"]
            #    component = getComponentType(parent_code)

        self.g.view()

    #children value from getComponentType; parent type code to find the corresponding children type
    #parent node to connect children node with parent node
    def getChildren(self, children_dict, parent_type, parent_node):

        #this_generation = []

        #if ask to include All Type
        if self.includeAllType:
            try:
                #append all-type's children
                children_list = np.concatenate((children_dict[parent_type], children_dict["*"]), axis=0)
            #no all-type
            except KeyError:
                children_list = children_dict[parent_type]

        #exclude All Type
        else:
            children_list = children_dict[parent_type]

        #start the first generation of children
        self.generation+=1 # self.generation<=self.r here

        #enumerate all children
        for ind,children in enumerate(children_list):

            children_name=children["name"]
            children_code = children["code"]
            try:
                children_type=children["type"]["name"]
                children_typeCode = children["type"]["code"]

            except TypeError:
                children_type = "NoType"
                children_typeCode= "NoType"

            #check children in the right generation
            print(self.generation)
            print(children_name)
            print(children_type)

            #save nodes names
            children_node = "G"+str(self.generation)+children_name+children_typeCode.strip()+str(ind)

            print(children_node)

            #create node and connect with parent
            self.g.node(children_node,children_name+'\n ('+children_type+')')
            self.g.edge(parent_node,children_node)

            #if generation hasn't reached user's input resursive
            if self.generation < self.r and children_type != "NoType":

                #find component type in database
                this_child = self.getComponentType(children_code)

                #if children has children, recursively run getChildren till the recursive level user asked for
                if "children" in this_child.keys() and this_child["children"] != None:

                    #children become the parent
                    self.getChildren(this_child["children"],children_typeCode,children_node)

                    #finished finding the children's children, go back up a generation
                    self.generation-=1

                #if this children has no children, move on to the next children
                else:
                    continue

                #if is the last children
                #if children == children_list[-1]:
                    #self.generation -= 1

            #if children type is None, move on to the next children
            elif children_type == " ":
                continue

            #exceeded the user input recursive
            #else:
                #self.generation -= 1
                #return None


if __name__ =='__main__':

    parser=argparse.ArgumentParser(description='Change parameter in input .dat files of VBFNLO')
    #parser.add_argument('command',type=str,choices=['initiate','update'],help='initiate: register new STAVE and assemble modules; update: find STAVE and assemble more modules')
    parser.add_argument('--project', type=str, default='S', choices=['S','P'], help='project code, S-strip (default: S)')
    parser.add_argument('--component-code', type=str, help='ex. STAVE, MODULE, SENSOR')
    parser.add_argument('--save-filename', type=str, default='FamilyTree', help='name of the output pdf (default: FamilyTree.pdf)')
    parser.add_argument('--component-name',type=str, default='',help='local identifier, ex. stave8, Hyb007 (default: same as component-code)')
    parser.add_argument('--type-code',type=str, help='code of the type of this component, ex. for module, SLIM')
    parser.add_argument('-r','--recursive',type=int, choices=[1,2,3,4], default=1, help='number of generations to see, ex. r=1 for children and grandchildren (default: 1)')
    parser.add_argument('--alltype-children',type=bool,default=True, help='include children of all types of parent (default: True)')

    args=parser.parse_args()

    try:
        session = ITkPDSession()
        session.authenticate()
        component_name=args.component_name
        if component_name == '':
            component_name = args.component_code

        plotFamilyTree(project = args.project, component_code = args.component_code,save_filename = args.save_filename,
                    component_name=component_name, type_code = args.type_code, recursive=args.recursive, includeAllType = args.alltype_children,
                    ITkPDSession=session)

    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        INFO('Finished with error.')
        exit()


    #plotFamilyTree(project = "S", component_code = "SENSOR",save_filename = "SENSORFamilyTree", component_name="Stave", type_code = "ATLAS17LS", recursive=1, includeAllType = True,ITkPDSession=session)

    ####stave examples####
    #plotFamilyTree(project = "S", component_code = "STAVE",save_filename = "FamilyTree", component_name="Stave", type_code = "SS-A", recursive=2, includeAllType = True,ITkPDSession=session)
    #plotFamilyTree(component_name="Stave",save_filename ="withAllType", recursive=1, includeAllType = True, ITkPDSession=session)
    #plotFamilyTree(component_name="Stave",save_filename ="withAllType", recursive=1, includeAllType = True, ITkPDSession=session)

    ####a module example
    #plotFamilyTree(component_code = "MODULE", component_name="Module", type_code = "SLIM",recursive=2, ITkPDSession=session)
