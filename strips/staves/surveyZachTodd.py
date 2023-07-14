#!/usr/bin/env /Users/zschillaci/Software/miniconda3/envs/pyenv/bin/python
import collections
import math as mt
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def StrRound(val, floating=2):
    return str(round(val, floating))

def StringtoFlt(string):
    flt = None
    if ("\n" in string):
        string.replace("\n", "")
    if ("=" in string):
        string = string[string.find("=") + 1:]
    try:
        flt = float(string)
    except ValueError:
        print("Cannot convert string to float!")
    return flt

def SetYlim(ylim, yticks):
    #Set y-limits of plot based upon min. and max. of plots
    tick = abs(yticks[0][1] - yticks[0][0])
    low = ylim[0] - 1.55 * tick
    high = ylim[-1] + 1.55 * tick
    return low, high

def SavePlot(path, fname):
    if not os.path.isdir(path):
        os.makedirs(path)
    plt.savefig(path + '/' + fname + '.pdf')
    plt.close()

def PlotHistogram(placements, corners, stave, results_dir='./'):
    for dim in placements:
        fig = plt.figure("Histogram - " + dim,(10,10))
        ax = fig.add_subplot(111)

        bins = np.arange(-30, 35, 7.5)
        plt.hist(placements[dim], bins=bins)
        plt.xlabel('$\Delta$' + dim + ' [$\mu$m]', fontsize=18)
        plt.ylabel('Counts / ' + StrRound(abs(bins[0] - bins[1])) + ' $\mu$m', fontsize=18)
        plt.xticks(np.arange(-50, 55, 10))
        plt.xlim(-52.5, 52.5)
        # plt.ylim(0, 15.5)

        _, high = SetYlim(plt.ylim(), plt.yticks())
        plt.ylim(0, high)

        ax.annotate('$\mu$ = ' + StrRound(np.mean(placements[dim])) + ' $\mu$m',xy=(0.995,0.965),xycoords='axes fraction',fontsize=16,horizontalalignment='right',verticalalignment='bottom')
        ax.annotate('$\sigma$ = ' + StrRound(np.std(placements[dim])) + ' $\mu$m',xy=(0.995,0.925),xycoords='axes fraction',fontsize=16,horizontalalignment='right',verticalalignment='bottom')
        SavePlot(results_dir + stave, dim + '-Corners' + corners + '-histogram')

class TheSurvey(object):
    def __init__(self, module, stave, indir):
        #Meta-data
        self.module = module
        self.stave = stave
        self.indir = indir
        self.name = 'Module_' + str(module)
        self.infile = indir #self.indir + self.stave + '/' + self.name + '.txt'
        self.dimensions = ['X', 'Y']
        self.tolerance = 25

        #Data
        self.GetLines()
        self.GetCorners()
        self.GetStages()
        self.GetResults()
        #self.GetAngles()
        self.GetFlags()
        self.GetDates()
        self.GetAssemblerName()
        self.GetGlueBatchID()

    def Dump(self):
        print('##### SURVEY RESULT #####')
        print('Module:', self.module)
        print('Stave:', self.stave)
        print('File:', self.infile)
        print('')
        self.PrintOverview()

    def GetLines(self):
        infile = open(self.infile,"r")
        self.lines = infile.readlines()
        infile.close()

    def GetCorners(self):
        indA, indB, indC, indD = 0, 0, 0, 0
        for ind, line in enumerate(self.lines):
            if ("CornerA" in line):
                indA = ind + 1
            elif ("CornerB" in line):
                indB = ind + 1
            elif ("CornerC" in line):
                indC = ind + 1
            elif ("CornerD" in line):
                indD = ind + 1

        self.corners = collections.OrderedDict()
        self.corners['A'] = self.lines[indA : indB - 2]
        self.corners['B'] = self.lines[indB : indC - 2]
        self.corners['C'] = self.lines[indC : indD - 2]
        self.corners['D'] = self.lines[indD : ]

    def GetDates(self):
        date_lines = [s for s in self.lines if 'Date_' in s]
        self.dates = collections.OrderedDict()

        for s in date_lines:
            # left side should have the 'Date_' and the label to be used
            # while the right side of this split should have the acutal date
            split_date = s.split('=')
            key_date = split_date[0][5:].strip()

            # look for the 'M' in 'PM' and 'AM' and copy up to the 'M'
            # and ignore the rest of the string (including the temp)
            date_str_end = split_date[1].find('M')
            item_date = split_date[1][1:(date_str_end+1)].strip('"')

            self.dates[key_date] = item_date

    def RenameStages(self):
        stages = []
        for stage in self.stages:
            stage = stage.replace(' ', '')
            stage = stage.lower()
            if ('aftergluing' in stage) or ('afterglue' in stage) or ('ag' in stage):
                stage = 'AG'
            elif ('beforebridgeremoval' in stage) or ('bbr' in stage):
                stage = 'BBR'
            elif ('afterbridgeremoval' in stage) or ('abr' in stage):
                stage = 'ABR'
            else:
                stage = stage.capitalize()
            stages.append(stage)
        self.stages = stages

    def GetStages(self, rename=False):
        self.stages = []
        for line in self.corners['A']:
            stage = line[line.find("_") + 1: line.find("=") - 1]
            if (stage not in self.stages):
                self.stages.append(stage)
        # self.stages = RenameStages(self.stages)

        #print(self.stages)

        return self.stages

    def GetResults(self):
        xdf, ydf = collections.OrderedDict(), collections.OrderedDict()
        for corner, coords in self.corners.items():
            xvals, yvals = [], []
            for i in range(len(self.stages)):
                xvals.append(StringtoFlt(coords[(3 * i)]))
                yvals.append(StringtoFlt(coords[(3 * i) + 1]))
            xdf[corner] = xvals
            ydf[corner] = yvals

        self.xdf = pd.DataFrame(xdf, index=self.stages)
        self.ydf = pd.DataFrame(ydf, index=self.stages)
        self.results = {'X' : self.xdf, 'Y' : self.ydf}

    def GetAngle(self, corners, stage):
        c1, c2 = corners
        dx = self.xdf[c1][stage] - self.xdf[c2][stage]
        dy = self.ydf[c1][stage] - self.ydf[c2][stage]
        try:
            angle = 1000 * mt.atan(dy / dx)
        except:
            return -999
        return angle

    def GetAngles(self):
        angles = collections.OrderedDict()
        angles['AB'] = [self.GetAngle('AB', stage) for stage in self.stages]
        angles['CD'] = [self.GetAngle('CD', stage) for stage in self.stages]
        self.angles = pd.DataFrame(angles, index=self.stages)

    def GetRelative(self, df):
#        print(df)
        df = pd.DataFrame(df - df.iloc[0])
        df = 1000 * df
#        print("~~~\n~~~")
#        print(df)
        return df

    def GetFlags(self):
        self.passed = True
        self.failures = []
        for dim in self.dimensions:
            df = self.GetRelative(self.results[dim])
            for corner in self.corners:
                if (abs(df[corner][-1]) >= self.tolerance):
                    self.passed = False
                    self.failures.append(corner + ': delta' + dim + ' = ' + StrRound(df[corner][-1]) + ' um')

    def PrintOverview(self):
        if self.passed:
            print("---> Passed! All surveys within " + StrRound(self.tolerance) + " um tolerance.")
        else:
            print("---> Failed! The following corners are out of " + StrRound(self.tolerance) + " um tolerance: ")
            for failure in self.failures:
                print(failure)
        print('')

    def PopulateHistograms(self, placements, stage, corners='ABCD'):
        for dim in self.dimensions:
            df = self.GetRelative(self.results[dim])
            for corner in self.corners:
                if (corner in corners):
                    placements[dim].append(round(df[corner][stage],1))

    def PlotMovement(self, reference="relative", printOut=True, results_dir='./'):
        plt.figure("Movement - " + reference, (10, 10))
        for n, dim in enumerate(self.dimensions):
            plt.subplot(211 + n)

            df = self.results[dim]
            if (reference == 'relative'):
                df = self.GetRelative(df)

            for corner in self.corners:
                plt.plot(np.arange(len(df[corner])), df[corner], linestyle='--', marker='o', label=corner)

            units = ('[$\mu$m]' if (reference == 'relative') else '[mm]')
            if printOut:
                print('-----' + dim + ' ' + units + '-----')
                print(df)
                print('--------------------' + '\n')

            low, high = SetYlim(plt.ylim(), plt.yticks())
            plt.ylim(low, high)
            plt.ylim(-50.5, 50.5)

            plt.xlabel('Stage in Process')
            plt.xticks(np.arange(len(self.stages)), self.stages)
            plt.ylabel(dim + ' ' + units)
            plt.legend(loc=9, ncol=4)
            plt.grid()
        SavePlot(results_dir + self.stave, 'position-' + reference + '-' + self.name)

    def PlotAngle(self, reference="relative", printOut=True, results_dir='./'):
        plt.figure("Angle Movement", (10, 10))

        df = self.angles
        if (reference == 'relative'):
            df = self.GetRelative(df)

        for col in self.angles.columns:
            plt.plot(np.arange(len(df[col])), df[col], linestyle='--', marker='o', label=col)

        units = ('[$\mu$rad]' if (reference == 'relative') else '[mrad]')
        if printOut:
            print('----- Angle ' + units + '-----')
            print(df)
            print('--------------------' + '\n')

        low, high = SetYlim(plt.ylim(), plt.yticks())
        plt.ylim(low, high)

        plt.xlabel('Stage in Process')
        plt.xticks(np.arange(len(self.stages)), self.stages)
        plt.ylabel('Angle ' + units)
        plt.legend(loc=9, ncol=4)
        SavePlot(results_dir + self.stave, 'angle-' + reference + '-' + self.name)


    def GetFlags_database(self,tolerance=100.0):
        passed={}
        positions={}
        for dim in self.dimensions:
            df = self.GetRelative(self.results[dim])
            passed[dim]=True
            for corner in self.corners:
                """
                Basic structure of positions should be:

                keys are the corners: i.e. keys are A, B, C, D

                """
                if (corner not in positions):
		#if corner is already in dictionary,
                #don't want to wipe the existing dictionary in it
                    positions[corner]=[]#each corner has its own dictionary
                positions[corner].append(round(df[corner][-1],1))

                if (abs(df[corner][-1])>= tolerance):
                    passed[dim]=False
        return positions,passed

    def GetAssemblerName(self):

        assembler_name = "assembler name not found"

        for line in self.lines:
            if "Assemblers" in line:
                ind=line.index('=')+1
                assembler_name = line[ind:-1].replace('\"',"").replace("\'","")
                break

        self.assembler_name = assembler_name

    def GetGlueBatchID(self):

        GlueBatchID = "glue batch ID not found"

        for line in self.lines:
            if "GlueBatchID" in line:
                ind=line.index('=')+1
                GlueBatchID = line[ind:-1].replace('\"',"").replace("\'","")
                break

        self.GlueBatchID = GlueBatchID



# PARAMETERS #

# Input and output directories
#INPUT_DIR = '/home/douglas/Surveys-master/input/'
#results_dir = '/home/douglas/Surveys-master/new_results/'

# Stave name (matching a sub-directory in INPUT_DIR)
#STAVE = 'ElectricalStave_8'
# List of module numbers on the stave (corresponding to survey files in STAVE sub-directory)
#MODULES = np.arange(1,14,1)

# Plot placement histograms of all modules for specified corners (e.g. ['AB', 'CD', 'AC', 'AD', 'BC', 'BD', 'ABCD'])
#CORNERS = 'ABCD'
#PLACEMENTS = {'X': [], 'Y': []}

# Plot and printout all survey results, highlighting any failures (placements outside tolerance)
#for module in MODULES:
#    print("\n{}\n".format(module))
#    survey = TheSurvey(module, STAVE, INPUT_DIR)
#    survey.Dump()
#
#    survey.PlotMovement(reference='relative', printOut=True, results_dir=results_dir)
#    x,y=survey.GetFlags_database(tolerance=100.0)
#    print(x)
#    print(y)
    #survey.PlotAngle(reference='absolute', printOut=True)

#    survey.PopulateHistograms(PLACEMENTS, survey.stages[-1], CORNERS)
#print(PLACEMENTS)
#PlotHistogram(PLACEMENTS, CORNERS, STAVE)
