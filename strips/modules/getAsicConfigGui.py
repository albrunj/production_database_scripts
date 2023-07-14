#!/usr/bin/env python3
### Author: Albrun Johnson
### partially adapted from getAsicConfig.py by Ian Dyckes
### for pulling ABC configuration during probe testing from DB and writing ITSDAQ config
### run code and then input serial number for desired modules to get corresponding st_system_config.dat and/or individual config.dat file
### if only individual files are created, they will be named 'SN'+self.sernum+'.det'
### if system config is created, individual files will be named 'star_stave_pos'+j+'.det' where j is 0-27 (long)/0-55
### can be run with --verbose and/or --outDir arguments but not necessary
### --verbose: Increase verbosity of DB interactions.
### --outDir: Output directory for configs
### IP address and port number defined in __init__

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import argparse
import os
import pathlib
import sys
import re

if __name__ == '__main__':
            from __path__ import updatePath
            updatePath()

#arguments
parser = argparse.ArgumentParser(description='For pulling ABC configuration during probe testing from DB and writing itsdaq config.')
parser.add_argument('--verbose', default=False, action='store_true', help='Increase verbosity of DB interactions.')
parser.add_argument('--outDir', default='./hybrid_configs/', help='Output directory for configs.')
args = parser.parse_args()

#DB verbosity.
if args.verbose:
    dbAccess.verbose = True

#Get DB token
if os.getenv("ITK_DB_AUTH"):
    dbAccess.token = os.getenv("ITK_DB_AUTH")


import itk_pdb.dbAccess as dbAccess

####################################################
####################################################
####################################################

class AsicGui:
    
    def __init__(self):
        
        #IP address and port number
        self.ip = "192.168.222.16"
        self.port = "60001"

        #gui creation and basic design
        self.root = Tk()
        self.root.title("ASIC Config Files")
        self.root.geometry("220x200")

        #gui content
        self.text1 = Label(self.root,text="Do you want config files for",font=('Times',14))
        self.text1.grid(row=0,column=0,columnspan=4,sticky=EW)
        self.short = Button(self.root,text="SHORT",font=('Times',14),command=self.shortGui)
        self.short.grid(row=1,column=0)
        self.text2 = Label(self.root,text="or",font=('Times',14))
        self.text2.grid(row=1,column=1)
        self.long = Button(self.root,text="LONG",font=('Times',14),command=self.longGui)
        self.long.grid(row=1,column=2)
        self.text3 = Label(self.root,text="strips?",font=('Times',14))
        self.text3.grid(row=2,column=1)

        #call gui
        self.root.mainloop()

#######################################################################
#######################################################################
#######################################################################

    #gui for short strips
    def shortGui(self):
         
        #gui creation and basic design
        self.win = Tk()
        self.win.title("ASIC Config Files -- Short Strips")
        self.win.geometry("700x500")

        #create framework
        self.main = Frame(self.win)
        self.main.pack(fill=BOTH,expand=1)
        self.canvas = Canvas(self.main)
        self.canvas.pack(side=LEFT,fill=BOTH,expand=1)
        self.scrolly = ttk.Scrollbar(self.main,orient=VERTICAL,command=self.canvas.yview)
        self.scrolly.pack(side=RIGHT,fill=Y)
        self.canvas.configure(yscrollcommand=self.scrolly)
        self.canvas.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window=self.frame,anchor="nw")

        #Gui Content
        self.title = Label(self.frame,text="Create and Save Module Config Files",font=('Times',18))
        self.title.grid(row=0,columnspan=7)

##################################################

        #J side modules 1-14
        self.modlab1 = Label(self.frame,text="Module J Side",font=('Times',12))
        self.modlab1.grid(row=1,column=0,sticky=W)
        self.serlab1 = Label(self.frame,text="Serial Number",font=('Times',12))
        self.serlab1.grid(row=1,column=1,sticky=W)

        self.moduleJ1 = Label(self.frame,text="Module 1:",font=('Times',10))
        self.moduleJ1.grid(column=0,row=2,sticky=W)
        self.serialJ1 = Entry(self.frame, font=('Times',10))
        self.serialJ1.grid(column=1,row=2,sticky=W)
        self.buttonJ1 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ1.grid(column=2,row=2,sticky=W)

        self.moduleJ2 = Label(self.frame,text="Module 2:",font=('Times',10))
        self.moduleJ2.grid(column=0,row=3,sticky=W)
        self.serialJ2 = Entry(self.frame, font=('Times',10))
        self.serialJ2.grid(column=1,row=3,sticky=W)
        self.buttonJ2 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ2.grid(column=2,row=3,sticky=W)

        self.moduleJ3 = Label(self.frame,text="Module 3:",font=('Times',10))
        self.moduleJ3.grid(column=0,row=4,sticky=W)
        self.serialJ3 = Entry(self.frame, font=('Times',10))
        self.serialJ3.grid(column=1,row=4,sticky=W)
        self.buttonJ3 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ3.grid(column=2,row=4,sticky=W)

        self.moduleJ4 = Label(self.frame,text="Module 4:",font=('Times',10))
        self.moduleJ4.grid(column=0,row=5,sticky=W)
        self.serialJ4 = Entry(self.frame, font=('Times',10))
        self.serialJ4.grid(column=1,row=5,sticky=W)
        self.buttonJ4 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ4.grid(column=2,row=5,sticky=W)

        self.moduleJ5 = Label(self.frame,text="Module 5:",font=('Times',10))
        self.moduleJ5.grid(column=0,row=6,sticky=W)
        self.serialJ5 = Entry(self.frame, font=('Times',10))
        self.serialJ5.grid(column=1,row=6,sticky=W)
        self.buttonJ5 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ5.grid(column=2,row=6,sticky=W)

        self.moduleJ6 = Label(self.frame,text="Module 6:",font=('Times',10))
        self.moduleJ6.grid(column=0,row=7,sticky=W)
        self.serialJ6 = Entry(self.frame, font=('Times',10))
        self.serialJ6.grid(column=1,row=7,sticky=W)
        self.buttonJ6 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ6.grid(column=2,row=7,sticky=W)

        self.moduleJ7 = Label(self.frame,text="Module 7:",font=('Times',10))
        self.moduleJ7.grid(column=0,row=8,sticky=W)
        self.serialJ7 = Entry(self.frame, font=('Times',10))
        self.serialJ7.grid(column=1,row=8,sticky=W)
        self.buttonJ7 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ7.grid(column=2,row=8,sticky=W)

        self.moduleJ8 = Label(self.frame,text="Module 8:",font=('Times',10))
        self.moduleJ8.grid(column=0,row=9,sticky=W)
        self.serialJ8 = Entry(self.frame, font=('Times',10))
        self.serialJ8.grid(column=1,row=9,sticky=W)
        self.buttonJ8 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ8.grid(column=2,row=9,sticky=W)

        self.moduleJ9 = Label(self.frame,text="Module 9:",font=('Times',10))
        self.moduleJ9.grid(column=0,row=10,sticky=W)
        self.serialJ9 = Entry(self.frame, font=('Times',10))
        self.serialJ9.grid(column=1,row=10,sticky=W)
        self.buttonJ9 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ9.grid(column=2,row=10,sticky=W)

        self.moduleJ10 = Label(self.frame,text="Module 10:",font=('Times',10))
        self.moduleJ10.grid(column=0,row=11,sticky=W)
        self.serialJ10 = Entry(self.frame, font=('Times',10))
        self.serialJ10.grid(column=1,row=11,sticky=W)
        self.buttonJ10 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ10.grid(column=2,row=11,sticky=W)

        self.moduleJ11 = Label(self.frame,text="Module 11:",font=('Times',10))
        self.moduleJ11.grid(column=0,row=12,sticky=W)
        self.serialJ11 = Entry(self.frame, font=('Times',10))
        self.serialJ11.grid(column=1,row=12,sticky=W)
        self.buttonJ11 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ11.grid(column=2,row=12,sticky=W)

        self.moduleJ12 = Label(self.frame,text="Module 12:",font=('Times',10))
        self.moduleJ12.grid(column=0,row=13,sticky=W)
        self.serialJ12 = Entry(self.frame, font=('Times',10))
        self.serialJ12.grid(column=1,row=13,sticky=W)
        self.buttonJ12 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ12.grid(column=2,row=13,sticky=W)

        self.moduleJ13 = Label(self.frame,text="Module 13:",font=('Times',10))
        self.moduleJ13.grid(column=0,row=14,sticky=W)
        self.serialJ13 = Entry(self.frame, font=('Times',10))
        self.serialJ13.grid(column=1,row=14,sticky=W)
        self.buttonJ13 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ13.grid(column=2,row=14,sticky=W)

        self.moduleJ14 = Label(self.frame,text="Module 14:",font=('Times',10))
        self.moduleJ14.grid(column=0,row=15,sticky=W)
        self.serialJ14 = Entry(self.frame, font=('Times',10))
        self.serialJ14.grid(column=1,row=15,sticky=W)
        self.buttonJ14 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ14.grid(column=2,row=15,sticky=W)

#####################################################

        #J side modules 15-28
        self.modlab2 = Label(self.frame,text="Module J Side",font=('Times',12))
        self.modlab2.grid(row=1,column=3,sticky=W)
        self.serlab2 = Label(self.frame,text="Serial Number",font=('Times',12))
        self.serlab2.grid(row=1,column=4,sticky=W)

        self.moduleJ15 = Label(self.frame,text="Module 15:",font=('Times',10))
        self.moduleJ15.grid(column=3,row=2,sticky=W)
        self.serialJ15 = Entry(self.frame, font=('Times',10))
        self.serialJ15.grid(column=4,row=2,sticky=W)
        self.buttonJ15 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ15.grid(column=5,row=2,sticky=W)

        self.moduleJ16 = Label(self.frame,text="Module 16:",font=('Times',10))
        self.moduleJ16.grid(column=3,row=3,sticky=W)
        self.serialJ16 = Entry(self.frame, font=('Times',10))
        self.serialJ16.grid(column=4,row=3,sticky=W)
        self.buttonJ16 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ16.grid(column=5,row=3,sticky=W)

        self.moduleJ17 = Label(self.frame,text="Module 17:",font=('Times',10))
        self.moduleJ17.grid(column=3,row=4,sticky=W)
        self.serialJ17 = Entry(self.frame, font=('Times',10))
        self.serialJ17.grid(column=4,row=4,sticky=W)
        self.buttonJ17 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ17.grid(column=5,row=4,sticky=W)

        self.moduleJ18 = Label(self.frame,text="Module 18:",font=('Times',10))
        self.moduleJ18.grid(column=3,row=5,sticky=W)
        self.serialJ18 = Entry(self.frame, font=('Times',10))
        self.serialJ18.grid(column=4,row=5,sticky=W)
        self.buttonJ18 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ18.grid(column=5,row=5,sticky=W)

        self.moduleJ19 = Label(self.frame,text="Module 19:",font=('Times',10))
        self.moduleJ19.grid(column=3,row=6,sticky=W)
        self.serialJ19 = Entry(self.frame, font=('Times',10))
        self.serialJ19.grid(column=4,row=6,sticky=W)
        self.buttonJ19 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ19.grid(column=5,row=6,sticky=W)

        self.moduleJ20 = Label(self.frame,text="Module 20:",font=('Times',10))
        self.moduleJ20.grid(column=3,row=7,sticky=W)
        self.serialJ20 = Entry(self.frame, font=('Times',10))
        self.serialJ20.grid(column=4,row=7,sticky=W)
        self.buttonJ20 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ20.grid(column=5,row=7,sticky=W)

        self.moduleJ21 = Label(self.frame,text="Module 21:",font=('Times',10))
        self.moduleJ21.grid(column=3,row=8,sticky=W)
        self.serialJ21 = Entry(self.frame, font=('Times',10))
        self.serialJ21.grid(column=4,row=8,sticky=W)
        self.buttonJ21 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ21.grid(column=5,row=8,sticky=W)

        self.moduleJ22 = Label(self.frame,text="Module 22:",font=('Times',10))
        self.moduleJ22.grid(column=3,row=9,sticky=W)
        self.serialJ22 = Entry(self.frame, font=('Times',10))
        self.serialJ22.grid(column=4,row=9,sticky=W)
        self.buttonJ22 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ22.grid(column=5,row=9,sticky=W)

        self.moduleJ23 = Label(self.frame,text="Module 23:",font=('Times',10))
        self.moduleJ23.grid(column=3,row=10,sticky=W)
        self.serialJ23 = Entry(self.frame, font=('Times',10))
        self.serialJ23.grid(column=4,row=10,sticky=W)
        self.buttonJ23 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ23.grid(column=5,row=10,sticky=W)

        self.moduleJ24 = Label(self.frame,text="Module 24:",font=('Times',10))
        self.moduleJ24.grid(column=3,row=11,sticky=W)
        self.serialJ24 = Entry(self.frame, font=('Times',10))
        self.serialJ24.grid(column=4,row=11,sticky=W)
        self.buttonJ24 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ24.grid(column=5,row=11,sticky=W)

        self.moduleJ25 = Label(self.frame,text="Module 25:",font=('Times',10))
        self.moduleJ25.grid(column=3,row=12,sticky=W)
        self.serialJ25 = Entry(self.frame, font=('Times',10))
        self.serialJ25.grid(column=4,row=12,sticky=W)
        self.buttonJ25 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ25.grid(column=5,row=12,sticky=W)

        self.moduleJ26 = Label(self.frame,text="Module 26:",font=('Times',10))
        self.moduleJ26.grid(column=3,row=13,sticky=W)
        self.serialJ26 = Entry(self.frame, font=('Times',10))
        self.serialJ26.grid(column=4,row=13,sticky=W)
        self.buttonJ26 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ26.grid(column=5,row=13,sticky=W)

        self.moduleJ27 = Label(self.frame,text="Module 27:",font=('Times',10))
        self.moduleJ27.grid(column=3,row=14,sticky=W)
        self.serialJ27 = Entry(self.frame, font=('Times',10))
        self.serialJ27.grid(column=4,row=14,sticky=W)
        self.buttonJ27 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ27.grid(column=5,row=14,sticky=W)

        self.moduleJ28 = Label(self.frame,text="Module 28:",font=('Times',10))
        self.moduleJ28.grid(column=3,row=15,sticky=W)
        self.serialJ28 = Entry(self.frame, font=('Times',10))
        self.serialJ28.grid(column=4,row=15,sticky=W)
        self.buttonJ28 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonJ28.grid(column=5,row=15,sticky=W)

###################################################

        #L side modules 1-14
        self.modlab3 = Label(self.frame,text="Module J Side",font=('Times',12))
        self.modlab3.grid(row=16,column=0,sticky=W)
        self.serlab3 = Label(self.frame,text="Serial Number",font=('Times',12))
        self.serlab3.grid(row=16,column=1,sticky=W)

        self.moduleL1 = Label(self.frame,text="Module 1:",font=('Times',10))
        self.moduleL1.grid(column=0,row=17,sticky=W)
        self.serialL1 = Entry(self.frame, font=('Times',10))
        self.serialL1.grid(column=1,row=17,sticky=W)
        self.buttonL1 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL1.grid(column=2,row=17,sticky=W)

        self.moduleL2 = Label(self.frame,text="Module 2:",font=('Times',10))
        self.moduleL2.grid(column=0,row=18,sticky=W)
        self.serialL2 = Entry(self.frame, font=('Times',10))
        self.serialL2.grid(column=1,row=18,sticky=W)
        self.buttonL2 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL2.grid(column=2,row=18,sticky=W)

        self.moduleL3 = Label(self.frame,text="Module 3:",font=('Times',10))
        self.moduleL3.grid(column=0,row=19,sticky=W)
        self.serialL3 = Entry(self.frame, font=('Times',10))
        self.serialL3.grid(column=1,row=19,sticky=W)
        self.buttonL3 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL3.grid(column=2,row=19,sticky=W)

        self.moduleL4 = Label(self.frame,text="Module 4:",font=('Times',10))
        self.moduleL4.grid(column=0,row=20,sticky=W)
        self.serialL4 = Entry(self.frame, font=('Times',10))
        self.serialL4.grid(column=1,row=20,sticky=W)
        self.buttonL4 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL4.grid(column=2,row=20,sticky=W)

        self.moduleL5 = Label(self.frame,text="Module 5:",font=('Times',10))
        self.moduleL5.grid(column=0,row=21,sticky=W)
        self.serialL5 = Entry(self.frame, font=('Times',10))
        self.serialL5.grid(column=1,row=21,sticky=W)
        self.buttonL5 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL5.grid(column=2,row=21,sticky=W)

        self.moduleL6 = Label(self.frame,text="Module 6:",font=('Times',10))
        self.moduleL6.grid(column=0,row=22,sticky=W)
        self.serialL6 = Entry(self.frame, font=('Times',10))
        self.serialL6.grid(column=1,row=22,sticky=W)
        self.buttonL6 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL6.grid(column=2,row=22,sticky=W)

        self.moduleL7 = Label(self.frame,text="Module 7:",font=('Times',10))
        self.moduleL7.grid(column=0,row=23,sticky=W)
        self.serialL7 = Entry(self.frame, font=('Times',10))
        self.serialL7.grid(column=1,row=23,sticky=W)
        self.buttonL7 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL7.grid(column=2,row=23,sticky=W)

        self.moduleL8 = Label(self.frame,text="Module 8:",font=('Times',10))
        self.moduleL8.grid(column=0,row=24,sticky=W)
        self.serialL8 = Entry(self.frame, font=('Times',10))
        self.serialL8.grid(column=1,row=24,sticky=W)
        self.buttonL8 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL8.grid(column=2,row=24,sticky=W)

        self.moduleL9 = Label(self.frame,text="Module 9:",font=('Times',10))
        self.moduleL9.grid(column=0,row=25,sticky=W)
        self.serialL9 = Entry(self.frame, font=('Times',10))
        self.serialL9.grid(column=1,row=25,sticky=W)
        self.buttonL9 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL9.grid(column=2,row=25,sticky=W)

        self.moduleL10 = Label(self.frame,text="Module 10:",font=('Times',10))
        self.moduleL10.grid(column=0,row=26,sticky=W)
        self.serialL10 = Entry(self.frame, font=('Times',10))
        self.serialL10.grid(column=1,row=26,sticky=W)
        self.buttonL10 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL10.grid(column=2,row=26,sticky=W)

        self.moduleL11 = Label(self.frame,text="Module 11:",font=('Times',10))
        self.moduleL11.grid(column=0,row=27,sticky=W)
        self.serialL11 = Entry(self.frame, font=('Times',10))
        self.serialL11.grid(column=1,row=27,sticky=W)
        self.buttonL11 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL11.grid(column=2,row=27,sticky=W)

        self.moduleL12 = Label(self.frame,text="Module 12:",font=('Times',10))
        self.moduleL12.grid(column=0,row=28,sticky=W)
        self.serialL12 = Entry(self.frame, font=('Times',10))
        self.serialL12.grid(column=1,row=28,sticky=W)
        self.buttonL12 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL12.grid(column=2,row=28,sticky=W)

        self.moduleL13 = Label(self.frame,text="Module 13:",font=('Times',10))
        self.moduleL13.grid(column=0,row=29,sticky=W)
        self.serialL13 = Entry(self.frame, font=('Times',10))
        self.serialL13.grid(column=1,row=29,sticky=W)
        self.buttonL13 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL13.grid(column=2,row=29,sticky=W)

        self.moduleL14 = Label(self.frame,text="Module 14:",font=('Times',10))
        self.moduleL14.grid(column=0,row=30,sticky=W)
        self.serialL14 = Entry(self.frame, font=('Times',10))
        self.serialL14.grid(column=1,row=30,sticky=W)
        self.buttonL14 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL14.grid(column=2,row=30,sticky=W)

#####################################################

        #L side modules 15-28
        self.modlab4 = Label(self.frame,text="Module J Side",font=('Times',12))
        self.modlab4.grid(row=16,column=3,sticky=W)
        self.serlab4 = Label(self.frame,text="Serial Number",font=('Times',12))
        self.serlab4.grid(row=16,column=4,sticky=W)

        self.moduleL15 = Label(self.frame,text="Module 15:",font=('Times',10))
        self.moduleL15.grid(column=3,row=17,sticky=W)
        self.serialL15 = Entry(self.frame, font=('Times',10))
        self.serialL15.grid(column=4,row=17,sticky=W)
        self.buttonL15 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL15.grid(column=5,row=17,sticky=W)

        self.moduleL16 = Label(self.frame,text="Module 16:",font=('Times',10))
        self.moduleL16.grid(column=3,row=18,sticky=W)
        self.serialL16 = Entry(self.frame, font=('Times',10))
        self.serialL16.grid(column=4,row=18,sticky=W)
        self.buttonL16 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL16.grid(column=5,row=18,sticky=W)

        self.moduleL17 = Label(self.frame,text="Module 17:",font=('Times',10))
        self.moduleL17.grid(column=3,row=19,sticky=W)
        self.serialL17 = Entry(self.frame, font=('Times',10))
        self.serialL17.grid(column=4,row=19,sticky=W)
        self.buttonL17 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL17.grid(column=5,row=19,sticky=W)

        self.moduleL18 = Label(self.frame,text="Module 18:",font=('Times',10))
        self.moduleL18.grid(column=3,row=20,sticky=W)
        self.serialL18 = Entry(self.frame, font=('Times',10))
        self.serialL18.grid(column=4,row=20,sticky=W)
        self.buttonL18 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL18.grid(column=5,row=20,sticky=W)

        self.moduleL19 = Label(self.frame,text="Module 19:",font=('Times',10))
        self.moduleL19.grid(column=3,row=21,sticky=W)
        self.serialL19 = Entry(self.frame, font=('Times',10))
        self.serialL19.grid(column=4,row=21,sticky=W)
        self.buttonL19 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL19.grid(column=5,row=21,sticky=W)

        self.moduleL20 = Label(self.frame,text="Module 20:",font=('Times',10))
        self.moduleL20.grid(column=3,row=22,sticky=W)
        self.serialL20 = Entry(self.frame, font=('Times',10))
        self.serialL20.grid(column=4,row=22,sticky=W)
        self.buttonL20 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL20.grid(column=5,row=22,sticky=W)

        self.moduleL21 = Label(self.frame,text="Module 21:",font=('Times',10))
        self.moduleL21.grid(column=3,row=23,sticky=W)
        self.serialL21 = Entry(self.frame, font=('Times',10))
        self.serialL21.grid(column=4,row=23,sticky=W)
        self.buttonL21 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL21.grid(column=5,row=23,sticky=W)

        self.moduleL22 = Label(self.frame,text="Module 22:",font=('Times',10))
        self.moduleL22.grid(column=3,row=24,sticky=W)
        self.serialL22 = Entry(self.frame, font=('Times',10))
        self.serialL22.grid(column=4,row=24,sticky=W)
        self.buttonL22 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL22.grid(column=5,row=24,sticky=W)

        self.moduleL23 = Label(self.frame,text="Module 23:",font=('Times',10))
        self.moduleL23.grid(column=3,row=25,sticky=W)
        self.serialL23 = Entry(self.frame, font=('Times',10))
        self.serialL23.grid(column=4,row=25,sticky=W)
        self.buttonL23 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL23.grid(column=5,row=25,sticky=W)

        self.moduleL24 = Label(self.frame,text="Module 24:",font=('Times',10))
        self.moduleL24.grid(column=3,row=26,sticky=W)
        self.serialL24 = Entry(self.frame, font=('Times',10))
        self.serialL24.grid(column=4,row=26,sticky=W)
        self.buttonL24 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL24.grid(column=5,row=26,sticky=W)

        self.moduleL25 = Label(self.frame,text="Module 25:",font=('Times',10))
        self.moduleL25.grid(column=3,row=27,sticky=W)
        self.serialL25 = Entry(self.frame, font=('Times',10))
        self.serialL25.grid(column=4,row=27,sticky=W)
        self.buttonL25 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL25.grid(column=5,row=27,sticky=W)

        self.moduleL26 = Label(self.frame,text="Module 26:",font=('Times',10))
        self.moduleL26.grid(column=3,row=28,sticky=W)
        self.serialL26 = Entry(self.frame, font=('Times',10))
        self.serialL26.grid(column=4,row=28,sticky=W)
        self.buttonL26 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL26.grid(column=5,row=28,sticky=W)

        self.moduleL27 = Label(self.frame,text="Module 27:",font=('Times',10))
        self.moduleL27.grid(column=3,row=29,sticky=W)
        self.serialL27 = Entry(self.frame, font=('Times',10))
        self.serialL27.grid(column=4,row=29,sticky=W)
        self.buttonL27 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL27.grid(column=5,row=29,sticky=W)

        self.moduleL28 = Label(self.frame,text="Module 28:",font=('Times',10))
        self.moduleL28.grid(column=3,row=30,sticky=W)
        self.serialL28 = Entry(self.frame, font=('Times',10))
        self.serialL28.grid(column=4,row=30,sticky=W)
        self.buttonL28 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigShort)
        self.buttonL28.grid(column=5,row=30,sticky=W)

###################################################

        #Complete System Config File
        self.systemConfig = Label(self.frame,text="System Config:",font=('Times',10))
        self.systemConfig.grid(column=0,row=31,sticky=W)
        self.buttonSys = Button(self.frame,text="Create Files",font=('Times',10),command=self.getSysConfigShort)
        self.buttonSys.grid(column=1,row=31,sticky=W)
        self.info = Label(self.frame,text="Input all desired serial numbers first.",font=('Times',10))
        self.info.grid(column=2,row=31,sticky=W, columnspan=2)

        #file input
        self.text = Label(self.frame,text="OR select given txt file with serial numbers here:", font=('Times',10))
        self.text.grid(column=0,row=32,columnspan=6,sticky=W)
        self.txt = Button(self.frame,text="Select",font=('Times',10),command=self.selectFile)
        self.txt.grid(column=0,row=33,sticky=W)
        self.select = Button(self.frame,text="Create Files",font=('Times',10),command=self.createConfigShort)
        self.select.grid(column=1,row=33,sticky=W)

        #call gui
        self.win.mainloop()
    
########################################################################
########################################################################
########################################################################

    #gui for long strips
    def longGui (self):

        #gui creation and basic design
        self.win = Tk()
        self.win.title("ASIC Config Files -- Long Strips")
        self.win.geometry("700x500")

        #create framework
        self.main = Frame(self.win)
        self.main.pack(fill=BOTH,expand=1)
        self.canvas = Canvas(self.main)
        self.canvas.pack(side=LEFT,fill=BOTH,expand=1)
        self.scrolly = ttk.Scrollbar(self.main,orient=VERTICAL,command=self.canvas.yview)
        self.scrolly.pack(side=RIGHT,fill=Y)
        self.canvas.configure(yscrollcommand=self.scrolly)
        self.canvas.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.frame = Frame(self.canvas)
        self.canvas.create_window((0,0),window=self.frame,anchor="nw")

        #Gui Content
        self.title = Label(self.frame,text="Create and Save Module Config Files",font=('Times',18))
        self.title.grid(row=0,columnspan=7)

##################################################

        #J side modules 1-14
        self.modlab1 = Label(self.frame,text="Module J Side",font=('Times',12))
        self.modlab1.grid(row=1,column=0,sticky=W)
        self.serlab1 = Label(self.frame,text="Serial Number",font=('Times',12))
        self.serlab1.grid(row=1,column=1,sticky=W)

        self.moduleJ1 = Label(self.frame,text="Module 1:",font=('Times',10))
        self.moduleJ1.grid(column=0,row=2,sticky=W)
        self.serialJ1 = Entry(self.frame, font=('Times',10))
        self.serialJ1.grid(column=1,row=2,sticky=W)
        self.buttonJ1 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ1.grid(column=2,row=2,sticky=W)

        self.moduleJ2 = Label(self.frame,text="Module 2:",font=('Times',10))
        self.moduleJ2.grid(column=0,row=3,sticky=W)
        self.serialJ2 = Entry(self.frame, font=('Times',10))
        self.serialJ2.grid(column=1,row=3,sticky=W)
        self.buttonJ2 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ2.grid(column=2,row=3,sticky=W)

        self.moduleJ3 = Label(self.frame,text="Module 3:",font=('Times',10))
        self.moduleJ3.grid(column=0,row=4,sticky=W)
        self.serialJ3 = Entry(self.frame, font=('Times',10))
        self.serialJ3.grid(column=1,row=4,sticky=W)
        self.buttonJ3 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ3.grid(column=2,row=4,sticky=W)

        self.moduleJ4 = Label(self.frame,text="Module 4:",font=('Times',10))
        self.moduleJ4.grid(column=0,row=5,sticky=W)
        self.serialJ4 = Entry(self.frame, font=('Times',10))
        self.serialJ4.grid(column=1,row=5,sticky=W)
        self.buttonJ4 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ4.grid(column=2,row=5,sticky=W)

        self.moduleJ5 = Label(self.frame,text="Module 5:",font=('Times',10))
        self.moduleJ5.grid(column=0,row=6,sticky=W)
        self.serialJ5 = Entry(self.frame, font=('Times',10))
        self.serialJ5.grid(column=1,row=6,sticky=W)
        self.buttonJ5 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ5.grid(column=2,row=6,sticky=W)

        self.moduleJ6 = Label(self.frame,text="Module 6:",font=('Times',10))
        self.moduleJ6.grid(column=0,row=7,sticky=W)
        self.serialJ6 = Entry(self.frame, font=('Times',10))
        self.serialJ6.grid(column=1,row=7,sticky=W)
        self.buttonJ6 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ6.grid(column=2,row=7,sticky=W)

        self.moduleJ7 = Label(self.frame,text="Module 7:",font=('Times',10))
        self.moduleJ7.grid(column=0,row=8,sticky=W)
        self.serialJ7 = Entry(self.frame, font=('Times',10))
        self.serialJ7.grid(column=1,row=8,sticky=W)
        self.buttonJ7 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ7.grid(column=2,row=8,sticky=W)

        self.moduleJ8 = Label(self.frame,text="Module 8:",font=('Times',10))
        self.moduleJ8.grid(column=0,row=9,sticky=W)
        self.serialJ8 = Entry(self.frame, font=('Times',10))
        self.serialJ8.grid(column=1,row=9,sticky=W)
        self.buttonJ8 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ8.grid(column=2,row=9,sticky=W)

        self.moduleJ9 = Label(self.frame,text="Module 9:",font=('Times',10))
        self.moduleJ9.grid(column=0,row=10,sticky=W)
        self.serialJ9 = Entry(self.frame, font=('Times',10))
        self.serialJ9.grid(column=1,row=10,sticky=W)
        self.buttonJ9 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ9.grid(column=2,row=10,sticky=W)

        self.moduleJ10 = Label(self.frame,text="Module 10:",font=('Times',10))
        self.moduleJ10.grid(column=0,row=11,sticky=W)
        self.serialJ10 = Entry(self.frame, font=('Times',10))
        self.serialJ10.grid(column=1,row=11,sticky=W)
        self.buttonJ10 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ10.grid(column=2,row=11,sticky=W)

        self.moduleJ11 = Label(self.frame,text="Module 11:",font=('Times',10))
        self.moduleJ11.grid(column=0,row=12,sticky=W)
        self.serialJ11 = Entry(self.frame, font=('Times',10))
        self.serialJ11.grid(column=1,row=12,sticky=W)
        self.buttonJ11 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ11.grid(column=2,row=12,sticky=W)

        self.moduleJ12 = Label(self.frame,text="Module 12:",font=('Times',10))
        self.moduleJ12.grid(column=0,row=13,sticky=W)
        self.serialJ12 = Entry(self.frame, font=('Times',10))
        self.serialJ12.grid(column=1,row=13,sticky=W)
        self.buttonJ12 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ12.grid(column=2,row=13,sticky=W)

        self.moduleJ13 = Label(self.frame,text="Module 13:",font=('Times',10))
        self.moduleJ13.grid(column=0,row=14,sticky=W)
        self.serialJ13 = Entry(self.frame, font=('Times',10))
        self.serialJ13.grid(column=1,row=14,sticky=W)
        self.buttonJ13 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ13.grid(column=2,row=14,sticky=W)

        self.moduleJ14 = Label(self.frame,text="Module 14:",font=('Times',10))
        self.moduleJ14.grid(column=0,row=15,sticky=W)
        self.serialJ14 = Entry(self.frame, font=('Times',10))
        self.serialJ14.grid(column=1,row=15,sticky=W)
        self.buttonJ14 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonJ14.grid(column=2,row=15,sticky=W)

#####################################################

        #L side modules 1-14
        self.modlab2 = Label(self.frame,text="Module L Side",font=('Times',12))
        self.modlab2.grid(row=1,column=3,sticky=W)
        self.serlab2 = Label(self.frame,text="Serial Number",font=('Times',12))
        self.serlab2.grid(row=1,column=4,sticky=W)

        self.moduleL1 = Label(self.frame,text="Module 1:",font=('Times',10))
        self.moduleL1.grid(column=3,row=2,sticky=W)
        self.serialL1 = Entry(self.frame, font=('Times',10))
        self.serialL1.grid(column=4,row=2,sticky=W)
        self.buttonL1 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL1.grid(column=5,row=2,sticky=W)

        self.moduleL2 = Label(self.frame,text="Module 2:",font=('Times',10))
        self.moduleL2.grid(column=3,row=3,sticky=W)
        self.serialL2 = Entry(self.frame, font=('Times',10))
        self.serialL2.grid(column=4,row=3,sticky=W)
        self.buttonL2 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL2.grid(column=5,row=3,sticky=W)

        self.moduleL3 = Label(self.frame,text="Module 3:",font=('Times',10))
        self.moduleL3.grid(column=3,row=4,sticky=W)
        self.serialL3 = Entry(self.frame, font=('Times',10))
        self.serialL3.grid(column=4,row=4,sticky=W)
        self.buttonL3 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL3.grid(column=5,row=4,sticky=W)

        self.moduleL4 = Label(self.frame,text="Module 4:",font=('Times',10))
        self.moduleL4.grid(column=3,row=5,sticky=W)
        self.serialL4 = Entry(self.frame, font=('Times',10))
        self.serialL4.grid(column=4,row=5,sticky=W)
        self.buttonL4 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL4.grid(column=5,row=5,sticky=W)

        self.moduleL5 = Label(self.frame,text="Module 5:",font=('Times',10))
        self.moduleL5.grid(column=3,row=6,sticky=W)
        self.serialL5 = Entry(self.frame, font=('Times',10))
        self.serialL5.grid(column=4,row=6,sticky=W)
        self.buttonL5 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL5.grid(column=5,row=6,sticky=W)

        self.moduleL6 = Label(self.frame,text="Module 6:",font=('Times',10))
        self.moduleL6.grid(column=3,row=7,sticky=W)
        self.serialL6 = Entry(self.frame, font=('Times',10))
        self.serialL6.grid(column=4,row=7,sticky=W)
        self.buttonL6 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL6.grid(column=5,row=7,sticky=W)

        self.moduleL7 = Label(self.frame,text="Module 7:",font=('Times',10))
        self.moduleL7.grid(column=3,row=8,sticky=W)
        self.serialL7 = Entry(self.frame, font=('Times',10))
        self.serialL7.grid(column=4,row=8,sticky=W)
        self.buttonL7 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL7.grid(column=5,row=8,sticky=W)

        self.moduleL8 = Label(self.frame,text="Module 8:",font=('Times',10))
        self.moduleL8.grid(column=3,row=9,sticky=W)
        self.serialL8 = Entry(self.frame, font=('Times',10))
        self.serialL8.grid(column=4,row=9,sticky=W)
        self.buttonL8 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL8.grid(column=5,row=9,sticky=W)

        self.moduleL9 = Label(self.frame,text="Module 9:",font=('Times',10))
        self.moduleL9.grid(column=3,row=10,sticky=W)
        self.serialL9 = Entry(self.frame, font=('Times',10))
        self.serialL9.grid(column=4,row=10,sticky=W)
        self.buttonL9 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL9.grid(column=5,row=10,sticky=W)

        self.moduleL10 = Label(self.frame,text="Module 10:",font=('Times',10))
        self.moduleL10.grid(column=3,row=11,sticky=W)
        self.serialL10 = Entry(self.frame, font=('Times',10))
        self.serialL10.grid(column=4,row=11,sticky=W)
        self.buttonL10 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL10.grid(column=5,row=11,sticky=W)

        self.moduleL11 = Label(self.frame,text="Module 11:",font=('Times',10))
        self.moduleL11.grid(column=3,row=12,sticky=W)
        self.serialL11 = Entry(self.frame, font=('Times',10))
        self.serialL11.grid(column=4,row=12,sticky=W)
        self.buttonL11 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL11.grid(column=5,row=12,sticky=W)

        self.moduleL12 = Label(self.frame,text="Module 12:",font=('Times',10))
        self.moduleL12.grid(column=3,row=13,sticky=W)
        self.serialL12 = Entry(self.frame, font=('Times',10))
        self.serialL12.grid(column=4,row=13,sticky=W)
        self.buttonL12 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL12.grid(column=5,row=13,sticky=W)

        self.moduleL13 = Label(self.frame,text="Module 13:",font=('Times',10))
        self.moduleL13.grid(column=3,row=14,sticky=W)
        self.serialL13 = Entry(self.frame, font=('Times',10))
        self.serialL13.grid(column=4,row=14,sticky=W)
        self.buttonL13 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL13.grid(column=5,row=14,sticky=W)

        self.moduleL14 = Label(self.frame,text="Module 14:",font=('Times',10))
        self.moduleL14.grid(column=3,row=15,sticky=W)
        self.serialL14 = Entry(self.frame, font=('Times',10))
        self.serialL14.grid(column=4,row=15,sticky=W)
        self.buttonL14 = Button(self.frame,text="Create File",font=('Times',10),command=self.getConfigLong)
        self.buttonL14.grid(column=5,row=15,sticky=W)

###################################################

        #Complete System Config File
        self.systemConfig = Label(self.frame,text="System Config:",font=('Times',10))
        self.systemConfig.grid(column=0,row=16,sticky=W)
        self.buttonSys = Button(self.frame,text="Create Files",font=('Times',10),command=self.getSysConfigLong)
        self.buttonSys.grid(column=1,row=16,sticky=W)
        self.info = Label(self.frame,text="Input all desired serial numbers first.",font=('Times',10))
        self.info.grid(column=2,row=16,sticky=W, columnspan=6)

        #file input
        self.text = Label(self.frame,text="OR select given txt file with serial numbers here:", font=('Times',10))
        self.text.grid(column=0,row=17,columnspan=6,sticky=W)
        self.txt = Button(self.frame,text="Select",font=('Times',10),command=self.selectFile)
        self.txt.grid(column=0,row=18,sticky=W)
        self.select = Button(self.frame,text="Create Files",font=('Times',10),command=self.createConfigLong)
        self.select.grid(column=1,row=18,sticky=W)

        #call gui
        self.win.mainloop()

#########################################################################
#########################################################################
#########################################################################

    #select serial number file
    def selectFile(self):
         #directory that houses serial number txt
         self.directory = "./serial_numbers"
         self.filename = filedialog.askopenfilename(initialdir=self.directory,title="Select file",filetypes=(("text files","*.txt"),))
         return self.filename

    #use 'type' instead of component type to differentiate ASIC versions
    def allChildrenAssembled(self, hybridJSON, childType):
         
         #first get the number of slots for this child type
         self.nChildSlots = len([child['type']['code'] for child in hybridJSON['children'] if child['type']['code']==childType])
         print("Number of ",childType, ", child slots: ", self.nChildSlots)
         if self.nChildSlots==0:
              messagebox.showerror(title="Child Error",message=f"No child slots of type: {childType}. Exiting.")
              sys.exit()
              

         self.nAssembled = 0
         for child in hybridJSON['children']:
              #skip any child that doesn't match desired child type
              if not child['type']['code']==childType:
                   continue
              #none if nothing assembled in this slot
              if child['component']:
                   #somehow someone assembled a chip without a serial
                   if not child['component']['serialNumber']:
                        continue
                   #then position of chip matters
                   if childType=="ABCSTARV1":
                        self.position = [prop['value'] for prop in child['properties'] if prop['code']=='ABC_POSITION'][0]
                        print(f"Already an ABCSTARV1 assembled to position {self.position}")
                   self.nAssembled += 1

         if childType=="ABCSTARV1":
              if not self.nAssembled==self.nChildSlots:
                   messagebox.showerror(title="Assemble Error",message=f"Only found {self.nAssembled} {childType} already assembled. Expect {self.nChildSlots}. Please assemble more first.")
                   return False
              else:
                   print("Found", self.nAssembled, childType, "already assembled.")
                   return True
         #only expect 1 of these
         else:
              if self.nAssembled==0:
                   messagebox.showerror(type="Assemble Error",message=f"Did not find any {childType} already assembled. Please assemble more first.")
                   return False
              else:
                   print("Found ", self.nAssembled, childType, "already assembled.")
                   return True
              
######################################################
######################################################
######################################################

    #file header
    def hybrid_header(self,nABCs, positions):

        self.chipMask = 0
        for p in positions:
            self.chipMask |= 1 << p

        self.header  = "Module : Chipset \n"
        self.header +="           9 \n \n"

        self.header += "# Speed of readout from HCC \n"
        self.header += "Speed 320 \n \n"

        self.header += "HCC 15 auto \n \n"

        self.header += "#   R32        R33        R34        R35 \n"
        self.header += "    0x02400000 0x44444444 0x00000444 0x00ff3b05 \n"
        self.header += "#   R36        R37        R38        R39 \n"
        self.header += "    0x00000000 0x00000004 0x0fffffff 0x00000014 \n"
        self.header += "#   R40        R41        R42        R43 \n"
        self.header += "    0x%08x 0x00010001 0x00010001 0x00000000 \n" % self.chipMask
        self.header += "#   R44        R45        R46        R47 \n"
        self.header += "    0x0000018e 0x00710003 0x00710003 0x00000000 \n"
        self.header += "#   R48 \n"
        self.header += "    0x00406600 \n \n"

        self.header += "Order " + ' '.join([str(i) for i in reversed(range(nABCs))]) + " \n \n"
  
        return self.header
    
######################################################
######################################################
######################################################

    #get results for <testType> test for all ASICs on hybrid with serial <hybridSerial>.
    #returns a list of dictionaries.
    # Each element is of the form {'serial':<ABC serial>,'position':<ABC position>,'testType':<testType>,"testJSON":<full test JSON>}
    def getAsicTestResults(self,hybridSerial,testType):
         
        #get complete info on this STAR Hybrid Assembly
        try:
            self.hybridJSON = dbAccess.doSomething(action='getComponent',method='GET',data={"component":hybridSerial})
        except:
            messagebox.showerror(title="Serial Error",message="Failed when trying to get STAR Hybrid Assembly info from the DB. Check Serial Number. Exiting.")
            sys.exit()
           
        #check if all ABCSTARV1 are assembled to the hybrid
        if not self.allChildrenAssembled(self.hybridJSON,'ABCSTARV1'):
             messagebox.showerror(title="Assemble Error",message="Not all ABCSTARV1 chips were assembled in the database. Exiting.")
             sys.exit()
             
        #declare output list (use list instead of dict b/c order matters.) 
        self.abcConfigList = []

        #go through ABCSTARV1 children and get info on each
        for child in self.hybridJSON['children']:
            self.thisType = child['type']['code']
            if not self.thisType=="ABCSTARV1":
                continue

            #already assembled a chip here, else it's null. Should be true due to check earlier 
            if child['component']:
                 self.existingChipSerial = child['component']['serialNumber']
                 self.existingChipPosition = [prop["value"] for prop in child['properties'] if prop['code']=="ABC_POSITION"][0]
                 self.existingChipWafer = [prop["value"] for prop in child['properties'] if prop['code']=="WAFER_NUMBER"][0]
                 print(f"Found ABCStarV1: {self.existingChipSerial}, position: {self.existingChipPosition}, wafer: {self.existingChipWafer}")
                 
                 #get all runs matching testType
                 try:
                      self.testRuns = dbAccess.doSomething(action="listTestRunsByComponent",method='GET',data={"filterMap": {"serialNumber": self.existingChipSerial, "state":["ready","requestedToDelete"], "testType":testType}})
                 except:
                      messagebox.showerror(title="Accessing Error",message=f"Failed when trying to get test info from the DB for ABCSTARV1 with serial: {self.existingChipSerial} and test type: {testType}. Exiting")
                      sys.exit()
                      
                 #now get all the info from a particular run
                 #get latest run if multiple
                 self.run = self.testRuns['itemList'][-1]
                 self.runNumber, self.runID = self.run["runNumber"], self.run['id']
                 try:
                      self.runInfo = dbAccess.doSomething(action="getTestRun",method='GET',data={'testRun':self.runID})
                 except:
                      messagebox.showerror(title="Test Error",message=f"Failed to get results for following test: Test code/type: {testType}, Run: {self.runNumber}, ID: {self.runID}. Exiting.")
                      sys.exit()

                 
                 #convert existingChipPosition to an integer if necessary
                 #Some may use this format: ABC_<hybrid_type>_<chip_number>
                 try:
                      self.existingChipPosition = int(self.existingChipPosition)
                 except:
                      try:
                        self.existingChipPosition = int(self.existingChipPosition.split('_')[-1])
                      except:
                           messagebox.showerror(title="Chip Error",message=f"Cannot parse this chip's position property: {self.existingChipPosition}. Not an integer or in the ABC_<hybrid_type>_<chip_number> format. Exiting.")
                           sys.exit()
                 #return everything
                 self.resultsDict = {'serial':self.existingChipSerial, 'position': self.existingChipPosition,'testType':testType, "testJSON": self.runInfo}
                 self.abcConfigList.append(self.resultsDict)
        return self.abcConfigList

####################################################
####################################################
####################################################

#function to create and save config file for short strips
    def getConfigShort(self):

        #Serial of hybrid
        self.serial =[
             self.serialJ1.get(),self.serialJ2.get(),self.serialJ3.get(),self.serialJ4.get(),self.serialJ5.get(),self.serialJ6.get(),
             self.serialJ7.get(),self.serialJ8.get(),self.serialJ9.get(),self.serialJ10.get(),self.serialJ11.get(),self.serialJ12.get(),
             self.serialJ13.get(),self.serialJ14.get(),self.serialJ15.get(),self.serialJ16.get(),self.serialJ17.get(),self.serialJ18.get(),
             self.serialJ19.get(),self.serialJ20.get(),self.serialJ21.get(),self.serialJ22.get(),self.serialJ23.get(),self.serialJ24.get(),
             self.serialJ25.get(),self.serialJ26.get(),self.serialJ27.get(),self.serialJ28.get(),self.serialL1.get(),self.serialL2.get(),
             self.serialL3.get(),self.serialL4.get(),self.serialL5.get(),self.serialL6.get(),self.serialL7.get(),self.serialL8.get(),
             self.serialL9.get(),self.serialL10.get(),self.serialL11.get(),self.serialL12.get(),self.serialL13.get(),self.serialL14.get(),
             self.serialL15.get(),self.serialL16.get(),self.serialL17.get(),self.serialL18.get(),self.serialL19.get(),self.serialL20.get(),
             self.serialL21.get(),self.serialL22.get(),self.serialL23.get(),self.serialL24.get(),self.serialL25.get(),self.serialL26.get(),
             self.serialL27.get(),self.serialL28.get()
             ]
        self.sernum = 0
        for i in range(len(self.serial)):
            if len(self.serial[i])==14:
                  self.sernum = self.serial[i]
        #error if no serial number or wrong format
        if self.sernum==0:
            messagebox.showerror(title="Serial Error",message="No valid Serial Number. Please check Serial Number.")
            return
        else:

          #get test results for all ABCs on the hybrid  
          self.testType = "DAC_TEST"
          self.testResults = self.getAsicTestResults(self.sernum,self.testType)

          self.testType = "IMUX_TEST"
          self.imuxResults = self.getAsicTestResults(self.sernum,self.testType)

          #maintain order should be 9 to 0
          self.testResults = sorted(self.testResults,key=lambda d: d['position'],reverse=True)

          self.positions = [d['position'] for d in self.testResults]

          #get number of ABCs for this hybrid type
          self.nABCs = len(self.testResults)

          #write itsdaq config
          self.hybridConfig = self.hybrid_header(self.nABCs,self.positions)
          for abc in self.testResults: #abc is a dictionary
               self.location = abc['position']
               #get just the vital info
               self.results = {result["code"]:result["value"] for result in abc['testJSON']['results']}

               self.imuxChipResult = {res["code"]:res["value"] for iabc in self.imuxResults for res in iabc['testJSON']['results'] if iabc['position']==self.location}

               self.chip = "###### \n"
               self.chip =  f"Chip {self.location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
               self.chip += "            1    0     0       0      4     1  1  134\n"
               self.chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
               self.chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
               self.chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

               self.dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
               self.dacs = [int(self.results[d_n]) for d_n in self.dac_names]
               #BIFEED, BIPRE, ADC_BIAS
               self.dacs[4:4] = [15, 6, int(self.imuxChipResult['ADC_RANGE_BEST'])]
               self.chip += "       " + "\t".join("%d" % d for d in self.dacs) + "\n"
               self.chip += "######\n"
               self.hybridConfig+=self.chip

          #save the config
          self.outDir = pathlib.Path(args.outDir)
          if not os.path.exists(self.outDir):
               os.mkdir(self.outDir)
          #current itsdaq doesn't like module name starting with 2
          #also useful to let it know it's a serial number
          self.outFile = self.outDir / ('SN'+self.sernum+'.det')
          with open(self.outFile,"w") as f:
               f.write(self.hybridConfig)
          messagebox.showinfo(title="Success!",message=f"Saving ITSDAQ config to {self.outFile}")
          sys.exit()
              
###################################################
###################################################
###################################################

    #function to create and save config file for long strips
    def getConfigLong(self):

        #Serial of hybrid
        self.serial =[
             self.serialJ1.get(),self.serialJ2.get(),self.serialJ3.get(),self.serialJ4.get(),self.serialJ5.get(),self.serialJ6.get(),
             self.serialJ7.get(),self.serialJ8.get(),self.serialJ9.get(),self.serialJ10.get(),self.serialJ11.get(),self.serialJ12.get(),
             self.serialJ13.get(),self.serialJ14.get(),self.serialL1.get(),self.serialL2.get(),self.serialL3.get(),self.serialL4.get(),
             self.serialL5.get(),self.serialL6.get(),self.serialL7.get(),self.serialL8.get(),self.serialL9.get(),self.serialL10.get(),
             self.serialL11.get(),self.serialL12.get(),self.serialL13.get(),self.serialL14.get()
             ]
        self.sernum = 0
        for i in range(len(self.serial)):
            if len(self.serial[i])==14:
                  self.sernum = self.serial[i]
        #error if no serial number or wrong format
        if self.sernum==0:
            messagebox.showerror(title="Serial Error",message="No valid Serial Number. Please check Serial Number.")
            return
        else:

          #get test results for all ABCs on the hybrid  
          self.testType = "DAC_TEST"
          self.testResults = self.getAsicTestResults(self.sernum,self.testType)

          self.testType = "IMUX_TEST"
          self.imuxResults = self.getAsicTestResults(self.sernum,self.testType)

          #maintain order should be 9 to 0
          self.testResults = sorted(self.testResults,key=lambda d: d['position'],reverse=True)

          self.positions = [d['position'] for d in self.testResults]

          #get number of ABCs for this hybrid type
          self.nABCs = len(self.testResults)

          #write itsdaq config
          self.hybridConfig = self.hybrid_header(self.nABCs,self.positions)
          for abc in self.testResults: #abc is a dictionary
               self.location = abc['position']
               #get just the vital info
               self.results = {result["code"]:result["value"] for result in abc['testJSON']['results']}

               self.imuxChipResult = {res["code"]:res["value"] for iabc in self.imuxResults for res in iabc['testJSON']['results'] if iabc['position']==self.location}

               self.chip = "###### \n"
               self.chip =  f"Chip {self.location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
               self.chip += "            1    0     0       0      4     1  1  134\n"
               self.chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
               self.chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
               self.chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

               self.dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
               self.dacs = [int(self.results[d_n]) for d_n in self.dac_names]
               #BIFEED, BIPRE, ADC_BIAS
               self.dacs[4:4] = [15, 6, int(self.imuxChipResult['ADC_RANGE_BEST'])]
               self.chip += "       " + "\t".join("%d" % d for d in self.dacs) + "\n"
               self.chip += "######\n"
               self.hybridConfig+=self.chip

          #save the config
          self.outDir = pathlib.Path(args.outDir)
          if not os.path.exists(self.outDir):
               os.mkdir(self.outDir)
          #current itsdaq doesn't like module name starting with 2
          #also useful to let it know it's a serial number
          self.outFile = self.outDir / ('SN'+self.sernum+'.det')
          with open(self.outFile,"w") as f:
               f.write(self.hybridConfig)
          messagebox.showinfo(title="Success!",message=f"Saving ITSDAQ config to {self.outFile}")
          sys.exit()
              
###################################################
###################################################
###################################################

    #function to create and save system config file for short strips
    def getSysConfigShort(self):
        
        #IP address and port number
        self.ip = self.ip
        self.port = self.port

        # Serial numbers
        self.serial =[
             self.serialJ1.get(),self.serialJ2.get(),self.serialJ3.get(),self.serialJ4.get(),self.serialJ5.get(),self.serialJ6.get(),
             self.serialJ7.get(),self.serialJ8.get(),self.serialJ9.get(),self.serialJ10.get(),self.serialJ11.get(),self.serialJ12.get(),
             self.serialJ13.get(),self.serialJ14.get(),self.serialJ15.get(),self.serialJ16.get(),self.serialJ17.get(),self.serialJ18.get(),
             self.serialJ19.get(),self.serialJ20.get(),self.serialJ21.get(),self.serialJ22.get(),self.serialJ23.get(),self.serialJ24.get(),
             self.serialJ25.get(),self.serialJ26.get(),self.serialJ27.get(),self.serialJ28.get(),self.serialL1.get(),self.serialL2.get(),
             self.serialL3.get(),self.serialL4.get(),self.serialL5.get(),self.serialL6.get(),self.serialL7.get(),self.serialL8.get(),
             self.serialL9.get(),self.serialL10.get(),self.serialL11.get(),self.serialL12.get(),self.serialL13.get(),self.serialL14.get(),
             self.serialL15.get(),self.serialL16.get(),self.serialL17.get(),self.serialL18.get(),self.serialL19.get(),self.serialL20.get(),
             self.serialL21.get(),self.serialL22.get(),self.serialL23.get(),self.serialL24.get(),self.serialL25.get(),self.serialL26.get(),
             self.serialL27.get(),self.serialL28.get()
             ]
        
        #error if no serial number or wrong format
        self.sercheck = 0
        for i in range(len(self.serial)):
            if len(self.serial[i])==14:
                  self.sercheck += 1
        if self.sercheck==0:
            messagebox.showerror(title="Serial Error",message="No valid Serial Number. Please check Serial Numbers.")
            return
        else:
             self. result = messagebox.askyesno(title="Serial Number Check", message=f"Generate config file with {str(self.sercheck)} serial numbers?")
             if self.result==False:
                  return
             else:

               #individual configs
               for j in range (len(self.serial)):
          
                    #Serial of hybrid
                    self.sernum = self.serial[j]

                    #create file
                    if len(self.sernum)==14:
                         #get test results for all ABCs on the hybrid  
                         self.testType = "DAC_TEST"
                         self.testResults = self.getAsicTestResults(self.sernum,self.testType)

                         self.testType = "IMUX_TEST"
                         self.imuxResults = self.getAsicTestResults(self.sernum,self.testType)

                         #maintain order should be 9 to 0
                         self.testResults = sorted(self.testResults,key=lambda d: d['position'],reverse=True)

                         self.positions = [d['position'] for d in self.testResults]

                         #get number of ABCs for this hybrid type
                         self.nABCs = len(self.testResults)

                         #write itsdaq config
                         self.hybridConfig = self.hybrid_header(self.nABCs,self.positions)
                         for abc in self.testResults: #abc is a dictionary
                              self.location = abc['position']
                              #get just the vital info
                              self.results = {result["code"]:result["value"] for result in abc['testJSON']['results']}

                              self.imuxChipResult = {res["code"]:res["value"] for iabc in self.imuxResults for res in iabc['testJSON']['results'] if iabc['position']==self.location}

                              self.chip = "###### \n"
                              self.chip =  f"Chip {self.location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
                              self.chip += "            1    0     0       0      4     1  1  134\n"
                              self.chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
                              self.chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
                              self.chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

                              self.dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
                              self.dacs = [int(self.results[d_n]) for d_n in self.dac_names]
                              #BIFEED, BIPRE, ADC_BIAS
                              self.dacs[4:4] = [15, 6, int(self.imuxChipResult['ADC_RANGE_BEST'])]
                              self.chip += "       " + "\t".join("%d" % d for d in self.dacs) + "\n"
                              self.chip += "######\n"
                              self.hybridConfig+=self.chip

                         #save the config
                         self.outDir = pathlib.Path(args.outDir)
                         if not os.path.exists(self.outDir):
                              os.mkdir(self.outDir)

                         self.outFile = self.outDir / ('star_stave_pos'+str(j)+'_y.det')
                         with open(self.outFile,"w") as f:
                              f.write(self.hybridConfig)

                    else:
                         continue

               #create sys configs
               #header
               self.config = f"DAQ upd {self.ip} {self.port},{self.port}\n \n \n"
               self.config += "           Detector     LV    HV    SLOG             MuSTARD           Module\n"
               self.config += "           id    pr ac  cr ch id ch id - - cm0  - -  id s0  s1  d0 d1  Filename           Device Type\n"
               self.config += "         ------------------------------------------------------------------------------------------\n"

               self.config += "#side J\n\n"
        
               #individual module information
               self.moduleText = [
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  28  -1 50 50  star_stave_pos0   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  30  -1 50 50  star_stave_pos1   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  32  -1 50 50  star_stave_pos2   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  36  -1 50 50  star_stave_pos3   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  0   -1 50 50  star_stave_pos4   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  2   -1 50 50  star_stave_pos5   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  4   -1 50 50  star_stave_pos6   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  6   -1 50 50  star_stave_pos7   Star_Test \n\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  52  -1 50 50  star_stave_pos8   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  54  -1 50 50  star_stave_pos9   Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  38  -1 50 50  star_stave_pos10  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  40  -1 50 50  star_stave_pos11  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  8   -1 50 50  star_stave_pos12  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  24  -1 50 50  star_stave_pos13  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  10  -1 50 50  star_stave_pos14  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  12  -1 50 50  star_stave_pos15  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  42  -1 50 50  star_stave_pos16  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  44  -1 50 50  star_stave_pos17  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  50  -1 50 50  star_stave_pos18  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  48  -1 50 50  star_stave_pos19  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  46  -1 50 50  star_stave_pos20  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  14  -1 50 50  star_stave_pos21  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  16  -1 50 50  star_stave_pos22  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  18  -1 50 50  star_stave_pos23  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  20  -1 50 50  star_stave_pos24  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  22  -1 50 50  star_stave_pos25  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 100  1 0  0  34  -1 50 50  star_stave_pos26  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 100  1 0  0  26  -1 50 50  star_stave_pos27  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  92  -1 50 50  star_stave_pos28  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  94  -1 50 50  star_stave_pos29  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  96  -1 50 50  star_stave_pos30  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  98  -1 50 50  star_stave_pos31  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  64  -1 50 50  star_stave_pos32  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  66  -1 50 50  star_stave_pos33  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  76  -1 50 50  star_stave_pos34  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  78  -1 50 50  star_stave_pos35  Star_Test \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  102 -1 50 50  star_stave_pos36  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  118 -1 50 50  star_stave_pos37  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  104 -1 50 50  star_stave_pos38  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  100 -1 50 50  star_stave_pos39  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  72  -1 50 50  star_stave_pos40  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  80  -1 50 50  star_stave_pos41  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  74  -1 50 50  star_stave_pos42  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  70  -1 50 50  star_stave_pos43  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  106 -1 50 50  star_stave_pos44  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  108 -1 50 50  star_stave_pos45  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  110 -1 50 50  star_stave_pos46  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  112 -1 50 50  star_stave_pos47  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  114 -1 50 50  star_stave_pos48  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  68  -1 50 50  star_stave_pos49  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  86  -1 50 50  star_stave_pos50  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  84  -1 50 50  star_stave_pos51  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  90  -1 50 50  star_stave_pos52  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  82  -1 50 50  star_stave_pos53  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 108  1 0  0  116 -1 50 50  star_stave_pos54  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 108  1 0  0  88  -1 50 50  star_stave_pos55  Star_Test  \n\n"
                    ]

               for k in range(0,28):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"
        
               self.config += "#side L\n\n"

               for k in range(28,56):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"

               #save the config
               self.outDir = pathlib.Path(args.outDir)
               self.outFile = self.outDir / ('st_system_config.dat')
               with open(self.outFile,"w") as f:
                 f.write(self.config)
               messagebox.showinfo(title="Success",message=f"Saving ITSDAQ configs to {self.outDir}")
               sys.exit()

#####################################################
#####################################################
#####################################################

    #function to create and save system config file for long strips
    def getSysConfigLong(self):
        
        #IP address and port number
        self.ip = self.ip
        self.port = self.port

        # Serial numbers
        self.serial =[
             self.serialJ1.get(),self.serialJ2.get(),self.serialJ3.get(),self.serialJ4.get(),self.serialJ5.get(),self.serialJ6.get(),
             self.serialJ7.get(),self.serialJ8.get(),self.serialJ9.get(),self.serialJ10.get(),self.serialJ11.get(),self.serialJ12.get(),
             self.serialJ13.get(),self.serialJ14.get(),self.serialL1.get(),self.serialL2.get(),self.serialL3.get(),self.serialL4.get(),
             self.serialL5.get(),self.serialL6.get(),self.serialL7.get(),self.serialL8.get(),self.serialL9.get(),self.serialL10.get(),
             self.serialL11.get(),self.serialL12.get(),self.serialL13.get(),self.serialL14.get()
             ]
        
        #error if no serial number or wrong format
        self.sercheck = 0
        for i in range(len(self.serial)):
            if len(self.serial[i])==14:
                  self.sercheck += 1
        if self.sercheck==0:
            messagebox.showerror(title="Serial Error",message="No valid Serial Number. Please check Serial Numbers.")
            return
        else:
             self. result = messagebox.askyesno(title="Serial Number Check", message=f"Generate config file with {str(self.sercheck)} serial numbers?")
             if self.result==False:
                  return
             else:

               #individual configs
               for j in range (len(self.serial)):
          
                    #Serial of hybrid
                    self.sernum = self.serial[j]

                    #create file
                    if len(self.sernum)==14:
                         #get test results for all ABCs on the hybrid  
                         self.testType = "DAC_TEST"
                         self.testResults = self.getAsicTestResults(self.sernum,self.testType)

                         self.testType = "IMUX_TEST"
                         self.imuxResults = self.getAsicTestResults(self.sernum,self.testType)

                         #maintain order should be 9 to 0
                         self.testResults = sorted(self.testResults,key=lambda d: d['position'],reverse=True)

                         self.positions = [d['position'] for d in self.testResults]

                         #get number of ABCs for this hybrid type
                         self.nABCs = len(self.testResults)

                         #write itsdaq config
                         self.hybridConfig = self.hybrid_header(self.nABCs,self.positions)
                         for abc in self.testResults: #abc is a dictionary
                              self.location = abc['position']
                              #get just the vital info
                              self.results = {result["code"]:result["value"] for result in abc['testJSON']['results']}

                              self.imuxChipResult = {res["code"]:res["value"] for iabc in self.imuxResults for res in iabc['testJSON']['results'] if iabc['position']==self.location}

                              self.chip = "###### \n"
                              self.chip =  f"Chip {self.location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
                              self.chip += "            1    0     0       0      4     1  1  134\n"
                              self.chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
                              self.chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
                              self.chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

                              self.dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
                              self.dacs = [int(self.results[d_n]) for d_n in self.dac_names]
                              #BIFEED, BIPRE, ADC_BIAS
                              self.dacs[4:4] = [15, 6, int(self.imuxChipResult['ADC_RANGE_BEST'])]
                              self.chip += "       " + "\t".join("%d" % d for d in self.dacs) + "\n"
                              self.chip += "######\n"
                              self.hybridConfig+=self.chip

                         #save the config
                         self.outDir = pathlib.Path(args.outDir)
                         if not os.path.exists(self.outDir):
                              os.mkdir(self.outDir)
                         self.outFile = self.outDir / ('star_stave_pos'+str(j)+'.det')
                         with open(self.outFile,"w") as f:
                              f.write(self.hybridConfig)

                    else:
                         continue

               #create sys configs
               #header
               self.config = f"DAQ upd {self.ip} {self.port},{self.port}\n \n \n"
               self.config += "           Detector     LV    HV    SLOG             MuSTARD           Module\n"
               self.config += "           id    pr ac  cr ch id ch id - - cm0  - -  id s0  s1  d0 d1  Filename         Device Type\n"
               self.config += "         ------------------------------------------------------------------------------------------\n"

               self.config += "#side J\n\n"
        
               #individual module information
               self.moduleText = [
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  0   1  50 50  star_stave_pos0   Star_Test   #HCC 4204 OK AMAC 0  (CCR 103)\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  2   3  50 50  star_stave_pos1   Star_Test   #HCC 4201 OK AMAC 1 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  4   5  50 50  star_stave_pos2   Star_Test   #HCC 421a OK AMAC 2 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  6   7  50 50  star_stave_pos3   Star_Test   #HCC 420b OK AMAC 3 \n\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  8   9  50 50  star_stave_pos4   Star_Test   #HCC 421e OK AMAC 4  (CCR 101)\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  24  25 50 50  star_stave_pos5   Star_Test   #HCC 421c OK AMAC 5 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  10  11 50 50  star_stave_pos6   Star_Test   #HCC 4220 OK AMAC 6 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  12  13 50 50  star_stave_pos7   Star_Test   #HCC 421f OK AMAC 7 \n\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  14  15 50 50  star_stave_pos8   Star_Test   #HCC 4219 OK AMAC 8  (CCR 102)\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  16  17 50 50  star_stave_pos9   Star_Test   #HCC 421b OK AMAC 9 \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  18  19 50 50  star_stave_pos10  Star_Test   #HCC 421d OK AMAC 10\n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  20  21 50 50  star_stave_pos11  Star_Test   #HCC 4211 OK AMAC 11\n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  22  23 50 50  star_stave_pos12  Star_Test   #HCC 420f OK AMAC 12\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 100  1 0  0  26  27 50 50  star_stave_pos13  Star_Test   #HCC 420c OK AMAC 13 (CCR 100)\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  50  51 50 50  star_stave_pos14  Star_Test   #HCC 420d OK AMAC 14 (CCR 106)\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  54  55 50 50  star_stave_pos15  Star_Test   #HCC 4212 OK AMAC 15\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  48  49 50 50  star_stave_pos16  Star_Test   #HCC 422c OK AMAC 16\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  46  47 50 50  star_stave_pos17  Star_Test   #HCC 422b OK AMAC 17\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  44  45 50 50  star_stave_pos18  Star_Test   #HCC 4214 OK AMAC 18 (CCR 105)\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  42  43 50 50  star_stave_pos19  Star_Test   #HCC 4203 OK AMAC 19\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  40  41 50 50  star_stave_pos20  Star_Test   #HCC 4232 OK AMAC 20\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  38  39 50 50  star_stave_pos21  Star_Test   #HCC 4233 OK AMAC 21\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  36  37 50 50  star_stave_pos22  Star_Test   #HCC 4234 OK AMAC 22 (CCR 104)\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  32  33 50 50  star_stave_pos23  Star_Test   #HCC 422e OK AMAC 23\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  30  31 50 50  star_stave_pos24  Star_Test   #HCC 422f OK AMAC 24\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  34  35 50 50  star_stave_pos25  Star_Test   #HCC 1a20 OK AMAC 25\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  28  29 50 50  star_stave_pos26  Star_Test   #HCC 1a38 OK AMAC 26\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 107  1 0  0  52  53 50 50  star_stave_pos27  Star_Test   #HCC 1a39 OK AMAC 27 (CCR 107)"
                    ]

               for k in range(0,14):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"
        
               self.config += "#side L\n\n"

               for k in range(14,28):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"

               #save the config
               self.outDir = pathlib.Path(args.outDir)
               self.outFile = self.outDir / ('st_system_config.dat')
               with open(self.outFile,"w") as f:
                 f.write(self.config)
               messagebox.showinfo(title="Success",message=f"Saving ITSDAQ configs to {self.outDir}")
               sys.exit()
        
####################################################
####################################################
####################################################

    #creates config files from file input for short staves 
    def createConfigShort(self):
          
        #open designated file and extract serial numbers
        self.serial = []
        with open(self.filename) as self.serialFile:
             #for line in self.serialFile.readlines([5:18],[22:35]):
              #    self.searchResult = re.search(r"20USBH[X-Y]\d{7}",line)
               #   self.serial.append(self.searchResult.group(0))
               self.search = self.serialFile.readlines()
               for line in range(7,35):
                   self.searchResult = re.search(r"20USBH[X-Y]\d{7}",self.search[line])
                   if self.searchResult != None:
                    self.serial.append(self.searchResult.group(0))
                   else:
                       self.serial.append("None")
               for line in range(38,66):
                   self.searchResult = re.search(r"20USBH[X-Y]\d{7}",self.search[line])
                   if self.searchResult != None:
                    self.serial.append(self.searchResult.group(0))
                   else:
                       self.serial.append("None")
                       
        #error if no serial number or wrong format
        self.sercheck = 0
        for i in range(len(self.serial)):
            if len(self.serial[i])==14:
                  self.sercheck += 1
        if self.sercheck==0:
            messagebox.showerror(title="Serial Error",message="No valid Serial Number. Please check Serial Numbers.")
            return
        else:
             self. result = messagebox.askyesno(title="Serial Number Check", message=f"Generate config file with {str(self.sercheck)} serial numbers?")
             if self.result==False:
                  return
             else:

               #individual configs
               for j in range (len(self.serial)):
          
                    #Serial of hybrid
                    self.sernum = self.serial[j]

                    #create file
                    if len(self.sernum)==14:
                         #get test results for all ABCs on the hybrid  
                         self.testType = "DAC_TEST"
                         self.testResults = self.getAsicTestResults(self.sernum,self.testType)

                         self.testType = "IMUX_TEST"
                         self.imuxResults = self.getAsicTestResults(self.sernum,self.testType)

                         #maintain order should be 9 to 0
                         self.testResults = sorted(self.testResults,key=lambda d: d['position'],reverse=True)

                         self.positions = [d['position'] for d in self.testResults]

                         #get number of ABCs for this hybrid type
                         self.nABCs = len(self.testResults)

                         #write itsdaq config
                         self.hybridConfig = self.hybrid_header(self.nABCs,self.positions)
                         for abc in self.testResults: #abc is a dictionary
                              self.location = abc['position']
                              #get just the vital info
                              self.results = {result["code"]:result["value"] for result in abc['testJSON']['results']}

                              self.imuxChipResult = {res["code"]:res["value"] for iabc in self.imuxResults for res in iabc['testJSON']['results'] if iabc['position']==self.location}

                              self.chip = "###### \n"
                              self.chip =  f"Chip {self.location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
                              self.chip += "            1    0     0       0      4     1  1  134\n"
                              self.chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
                              self.chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
                              self.chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

                              self.dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
                              self.dacs = [int(self.results[d_n]) for d_n in self.dac_names]
                              #BIFEED, BIPRE, ADC_BIAS
                              self.dacs[4:4] = [15, 6, int(self.imuxChipResult['ADC_RANGE_BEST'])]
                              self.chip += "       " + "\t".join("%d" % d for d in self.dacs) + "\n"
                              self.chip += "######\n"
                              self.hybridConfig+=self.chip

                         #save the config
                         self.outDir = pathlib.Path(args.outDir)
                         if not os.path.exists(self.outDir):
                              os.mkdir(self.outDir)
                         self.outFile = self.outDir / ('star_stave_pos'+str(j)+'.det')
                         with open(self.outFile,"w") as f:
                              f.write(self.hybridConfig)

                    else:
                         continue

               #create sys configs
               #header
               self.config = f"DAQ upd {self.ip} {self.port},{self.port}\n \n \n"
               self.config += "           Detector     LV    HV    SLOG             MuSTARD           Module\n"
               self.config += "           id    pr ac  cr ch id ch id - - cm0  - -  id s0  s1  d0 d1  Filename         Device Type\n"
               self.config += "         ------------------------------------------------------------------------------------------\n"

               self.config += "#side J\n\n"
        
               #individual module information
               self.moduleText = [
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  28  -1 50 50  star_stave_pos0   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  30  -1 50 50  star_stave_pos1   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  32  -1 50 50  star_stave_pos2   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  36  -1 50 50  star_stave_pos3   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  0   -1 50 50  star_stave_pos4   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  2   -1 50 50  star_stave_pos5   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  4   -1 50 50  star_stave_pos6   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  6   -1 50 50  star_stave_pos7   Star_Test \n\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  52  -1 50 50  star_stave_pos8   Star_Test \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  54  -1 50 50  star_stave_pos9   Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  38  -1 50 50  star_stave_pos10  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  40  -1 50 50  star_stave_pos11  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  8   -1 50 50  star_stave_pos12  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  24  -1 50 50  star_stave_pos13  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  10  -1 50 50  star_stave_pos14  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  12  -1 50 50  star_stave_pos15  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  42  -1 50 50  star_stave_pos16  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  44  -1 50 50  star_stave_pos17  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  50  -1 50 50  star_stave_pos18  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  48  -1 50 50  star_stave_pos19  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  46  -1 50 50  star_stave_pos20  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  14  -1 50 50  star_stave_pos21  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  16  -1 50 50  star_stave_pos22  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  18  -1 50 50  star_stave_pos23  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  20  -1 50 50  star_stave_pos24  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  22  -1 50 50  star_stave_pos25  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 100  1 0  0  34  -1 50 50  star_stave_pos26  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 100  1 0  0  26  -1 50 50  star_stave_pos27  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  92  -1 50 50  star_stave_pos28  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  94  -1 50 50  star_stave_pos29  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  96  -1 50 50  star_stave_pos30  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  98  -1 50 50  star_stave_pos31  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  64  -1 50 50  star_stave_pos32  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  66  -1 50 50  star_stave_pos33  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  76  -1 50 50  star_stave_pos34  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 110  1 0  0  78  -1 50 50  star_stave_pos35  Star_Test \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  102 -1 50 50  star_stave_pos36  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  118 -1 50 50  star_stave_pos37  Star_Test \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  104 -1 50 50  star_stave_pos38  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  100 -1 50 50  star_stave_pos39  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  72  -1 50 50  star_stave_pos40  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  80  -1 50 50  star_stave_pos41  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  74  -1 50 50  star_stave_pos42  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 109  1 0  0  70  -1 50 50  star_stave_pos43  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  106 -1 50 50  star_stave_pos44  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  108 -1 50 50  star_stave_pos45  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  110 -1 50 50  star_stave_pos46  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  112 -1 50 50  star_stave_pos47  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  114 -1 50 50  star_stave_pos48  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  68  -1 50 50  star_stave_pos49  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  86  -1 50 50  star_stave_pos50  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  84  -1 50 50  star_stave_pos51  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  90  -1 50 50  star_stave_pos52  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 111  1 0  0  82  -1 50 50  star_stave_pos53  Star_Test  \n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 108  1 0  0  116 -1 50 50  star_stave_pos54  Star_Test  \n",
                    "1  1   -1 -1 -1 -1  0  0 1 108  1 0  0  88  -1 50 50  star_stave_pos55  Star_Test  \n\n"
                    ]


               for k in range(0,28):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"
        
               self.config += "#side L\n\n"

               for k in range(28,56):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"

               #save the config
               self.outDir = pathlib.Path(args.outDir)
               self.outFile = self.outDir / ('st_system_config.dat')
               with open(self.outFile,"w") as f:
                 f.write(self.config)
               messagebox.showinfo(title="Success",message=f"Saving ITSDAQ configs to {self.outDir}")
               sys.exit()
          

###################################################
###################################################
###################################################

    #creates config files from file input for long staves 
    def createConfigLong(self):
          
        #open designated file and extract serial numbers
        self.serial = []
        with open(self.filename) as self.serialFile:
             #for line in self.serialFile.readlines([5:18],[22:35]):
              #    self.searchResult = re.search(r"20USBH[X-Y]\d{7}",line)
               #   self.serial.append(self.searchResult.group(0))
               self.search = self.serialFile.readlines()
               for line in range(7,21):
                   self.searchResult = re.search(r"20USBH[X-Y]\d{7}",self.search[line])
                   if self.searchResult != None:
                    self.serial.append(self.searchResult.group(0))
                   else:
                       self.serial.append("None")
               for line in range(24,38):
                   self.searchResult = re.search(r"20USBH[X-Y]\d{7}",self.search[line])
                   if self.searchResult != None:
                    self.serial.append(self.searchResult.group(0))
                   else:
                       self.serial.append("None")
                       
        #error if no serial number or wrong format
        self.sercheck = 0
        for i in range(len(self.serial)):
            if len(self.serial[i])==14:
                  self.sercheck += 1
        if self.sercheck==0:
            messagebox.showerror(title="Serial Error",message="No valid Serial Number. Please check Serial Numbers.")
            return
        else:
             self. result = messagebox.askyesno(title="Serial Number Check", message=f"Generate config file with {str(self.sercheck)} serial numbers?")
             if self.result==False:
                  return
             else:

               #individual configs
               for j in range (len(self.serial)):
          
                    #Serial of hybrid
                    self.sernum = self.serial[j]

                    #create file
                    if len(self.sernum)==14:
                         #get test results for all ABCs on the hybrid  
                         self.testType = "DAC_TEST"
                         self.testResults = self.getAsicTestResults(self.sernum,self.testType)

                         self.testType = "IMUX_TEST"
                         self.imuxResults = self.getAsicTestResults(self.sernum,self.testType)

                         #maintain order should be 9 to 0
                         self.testResults = sorted(self.testResults,key=lambda d: d['position'],reverse=True)

                         self.positions = [d['position'] for d in self.testResults]

                         #get number of ABCs for this hybrid type
                         self.nABCs = len(self.testResults)

                         #write itsdaq config
                         self.hybridConfig = self.hybrid_header(self.nABCs,self.positions)
                         for abc in self.testResults: #abc is a dictionary
                              self.location = abc['position']
                              #get just the vital info
                              self.results = {result["code"]:result["value"] for result in abc['testJSON']['results']}

                              self.imuxChipResult = {res["code"]:res["value"] for iabc in self.imuxResults for res in iabc['testJSON']['results'] if iabc['position']==self.location}

                              self.chip = "###### \n"
                              self.chip =  f"Chip {self.location} : Act. Comp. T_range Mask_r Drive PR LP LCB_Threshold\n"
                              self.chip += "            1    0     0       0      4     1  1  134\n"
                              self.chip += "Delay: Delay DelStep VThr VCal CalPol Latency BCOffset MaxCluster\n"
                              self.chip += "       13\t2\t13\t0\t0\t3\t65\t-1\n"
                              self.chip += "Bias : BVREF\tBIREF\tB8REF\tCOMBIAS\tBIFEED\tBIPRE\tADC_BIAS\tLDOD\tLDOA\n"

                              self.dac_names = ['VREF_DAC', 'IREF_DAC', 'R8B_DAC', 'COM_DAC', 'LDOD_DAC', 'LDOA_DAC']
                              self.dacs = [int(self.results[d_n]) for d_n in self.dac_names]
                              #BIFEED, BIPRE, ADC_BIAS
                              self.dacs[4:4] = [15, 6, int(self.imuxChipResult['ADC_RANGE_BEST'])]
                              self.chip += "       " + "\t".join("%d" % d for d in self.dacs) + "\n"
                              self.chip += "######\n"
                              self.hybridConfig+=self.chip

                         #save the config
                         self.outDir = pathlib.Path(args.outDir)
                         if not os.path.exists(self.outDir):
                              os.mkdir(self.outDir)
                         self.outFile = self.outDir / ('star_stave_pos'+str(j)+'.det')
                         with open(self.outFile,"w") as f:
                              f.write(self.hybridConfig)

                    else:
                         continue

               #create sys configs
               #header
               self.config = f"DAQ upd {self.ip} {self.port},{self.port}\n \n \n"
               self.config += "           Detector     LV    HV    SLOG             MuSTARD           Module\n"
               self.config += "           id    pr ac  cr ch id ch id - - cm0  - -  id s0  s1  d0 d1  Filename         Device Type\n"
               self.config += "         ------------------------------------------------------------------------------------------\n"

               self.config += "#side J\n\n"
        
               #individual module information
               self.moduleText = [
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  0   1  50 50  star_stave_pos0   Star_Test   #HCC 4204 OK AMAC 0  (CCR 103)\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  2   3  50 50  star_stave_pos1   Star_Test   #HCC 4201 OK AMAC 1 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  4   5  50 50  star_stave_pos2   Star_Test   #HCC 421a OK AMAC 2 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 103  1 0  0  6   7  50 50  star_stave_pos3   Star_Test   #HCC 420b OK AMAC 3 \n\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  8   9  50 50  star_stave_pos4   Star_Test   #HCC 421e OK AMAC 4  (CCR 101)\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  24  25 50 50  star_stave_pos5   Star_Test   #HCC 421c OK AMAC 5 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  10  11 50 50  star_stave_pos6   Star_Test   #HCC 4220 OK AMAC 6 \n",
                    " 1  1   -1 -1 -1 -1  0  0 1 101  1 0  0  12  13 50 50  star_stave_pos7   Star_Test   #HCC 421f OK AMAC 7 \n\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  14  15 50 50  star_stave_pos8   Star_Test   #HCC 4219 OK AMAC 8  (CCR 102)\n",
                    " 1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  16  17 50 50  star_stave_pos9   Star_Test   #HCC 421b OK AMAC 9 \n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  18  19 50 50  star_stave_pos10  Star_Test   #HCC 421d OK AMAC 10\n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  20  21 50 50  star_stave_pos11  Star_Test   #HCC 4211 OK AMAC 11\n",
                    "1  1   -1 -1 -1 -1  0  0 1 102  1 0  0  22  23 50 50  star_stave_pos12  Star_Test   #HCC 420f OK AMAC 12\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 100  1 0  0  26  27 50 50  star_stave_pos13  Star_Test   #HCC 420c OK AMAC 13 (CCR 100)\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  50  51 50 50  star_stave_pos14  Star_Test   #HCC 420d OK AMAC 14 (CCR 106)\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  54  55 50 50  star_stave_pos15  Star_Test   #HCC 4212 OK AMAC 15\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  48  49 50 50  star_stave_pos16  Star_Test   #HCC 422c OK AMAC 16\n",
                    "1  1   -1 -1 -1 -1  0  0 1 106  1 0  0  46  47 50 50  star_stave_pos17  Star_Test   #HCC 422b OK AMAC 17\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  44  45 50 50  star_stave_pos18  Star_Test   #HCC 4214 OK AMAC 18 (CCR 105)\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  42  43 50 50  star_stave_pos19  Star_Test   #HCC 4203 OK AMAC 19\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  40  41 50 50  star_stave_pos20  Star_Test   #HCC 4232 OK AMAC 20\n",
                    "1  1   -1 -1 -1 -1  0  0 1 105  1 0  0  38  39 50 50  star_stave_pos21  Star_Test   #HCC 4233 OK AMAC 21\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  36  37 50 50  star_stave_pos22  Star_Test   #HCC 4234 OK AMAC 22 (CCR 104)\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  32  33 50 50  star_stave_pos23  Star_Test   #HCC 422e OK AMAC 23\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  30  31 50 50  star_stave_pos24  Star_Test   #HCC 422f OK AMAC 24\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  34  35 50 50  star_stave_pos25  Star_Test   #HCC 1a20 OK AMAC 25\n",
                    "1  1   -1 -1 -1 -1  0  0 1 104  1 0  0  28  29 50 50  star_stave_pos26  Star_Test   #HCC 1a38 OK AMAC 26\n\n",
                    "1  1   -1 -1 -1 -1  0  0 1 107  1 0  0  52  53 50 50  star_stave_pos27  Star_Test   #HCC 1a39 OK AMAC 27 (CCR 107)"
                    ]

               for k in range(0,14):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"
        
               self.config += "#side L\n\n"

               for k in range(14,28):
                 if len(self.serial[k])==14:
                      self.config += f"Module     {str(k)}    {self.moduleText[k]}"
                 else:
                      # comment out module if serial isn't given
                      self.config += f"#Module    {str(k)}    {self.moduleText[k]}"

               #save the config
               self.outDir = pathlib.Path(args.outDir)
               self.outFile = self.outDir / ('st_system_config.dat')
               with open(self.outFile,"w") as f:
                 f.write(self.config)
               messagebox.showinfo(title="Success",message=f"Saving ITSDAQ configs to {self.outDir}")
               sys.exit()
          

####################################################
####################################################
####################################################

if __name__ == "__main__":
     AsicGui()