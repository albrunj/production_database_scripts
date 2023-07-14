#!/usr/bin/env python
# testPlots.py -- generate plots of comparison between tests in the ITkPD
#created 26/02/20
# Created by Mitch Norfolk, most of the code adapted from Matt Basso's generatePlots.py
import csv
import os
import sys

from itk_pdb.databaseUtilities import ERROR
from itk_pdb.databaseUtilities import INFO
from itk_pdb.databaseUtilities import STATUS
from itk_pdb.databaseUtilities import WARNING
from itk_pdb.dbAccess import ITkPDSession

# Try to import matplotlib
try:
    global matplotlib
    import matplotlib.pyplot as plt
except ImportError:
    ERROR('Python module \'matplotlib\' is not installed.')
    INFO('To install, please type \'sudo apt-get install python-matplotlib\' for Python 2.')
    INFO('For Python 3, type \'sudo apt-get install python3-matplotlib\'.')
    STATUS('Finished with error', False)
    sys.exit(1)

class TestPlotter (ITkPDSession):

    def __init__(self, verbose):
        # Inherit from ITkPDSession and set verbosity
        super(TestPlotter, self).__init__()
        self.verbose = verbose
        self.testIDs = []
        self.resultsDict = []

    # This is where the test information is pulled from the DB and put in the results dictionary, 
    # for most tests you will just need this dictionary to plot but for others E.g metrology you will need the datain a different form, this is done here aswell
    def infoPull(self, testType):

        ### Fill results dictionary regardless of test
        for test_number, test in enumerate(self.testIDs): 
            testInfo = self.doSomething('getTestRun', 'GET', data = {'testRun': test})

            for i in range (len(testInfo['results'])):
                self.resultsDict[test_number]['results'][kwargs['testType']][str(testInfo['results'][i]['name'])] = testInfo ['results'][i]['value']

            self.resultsDict[test_number]['extraData']['institution'] = testInfo['institution']['code']
            self.resultsDict[test_number]['extraData']['date'] = testInfo['date']

        if self.verbose:
            INFO('The Dictionary of results has been filled: ' + str(self.resultsDict))

        ### Fill dictionary for all metrology information  
        ########################################################################################################################################################################################
        ### IMPORTANT NOTE ON METROLOGY: The output to the DB is not standardized, the numbers could refer to any component so this below is guesswork which will need to be corrected later ###
        ########################################################################################################################################################################################
        #notes on below: -ASIC Bow is one number according to database? I was expecting a bow for each ASIC, is there a bow for each hybrid?  
        
        if testType == 'MMETROLOGY':
            self.moduleMetrologyData = {'institutionList':[], 'Hybrid 1 Glue Height':[], 'Hybrid 2 Glue Height':[], 'Powerboard Glue Height':[], 'Bow':[]}#, 'Hybrid 2 Bow':[]}

            for i in range (len(self.resultsDict)):
                self.moduleMetrologyData['institutionList'].append(self.resultsDict[i]['extraData']['institution'])
                    
                self.moduleMetrologyData['Hybrid 1 Bow'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module Bow'])
                # if len(self.resultsDict[i]['results']['MMETROLOGY']['Module Bow']) == 2:
                #     self.moduleMetrologyData['Hybrid 2 Bow'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module Bow'][1])

                if len(self.resultsDict[i]['results']['MMETROLOGY']['Module-Sensor Glue Height']) == 3:
                    self.moduleMetrologyData['Hybrid 1 Glue Height'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module-Sensor Glue Height'][0])
                    self.moduleMetrologyData['Hybrid 2 Glue Height'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module-Sensor Glue Height'][1])
                    self.moduleMetrologyData['Powerboard Glue Height'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module-Sensor Glue Height'][2])
                else:
                    self.moduleMetrologyData['Hybrid 1 Glue Height'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module-Sensor Glue Height'][0])
                    self.moduleMetrologyData['Hybrid 2 Glue Height'].append(0)
                    self.moduleMetrologyData['Powerboard Glue Height'].append(self.resultsDict[i]['results']['MMETROLOGY']['Module-Sensor Glue Height'][1])

                self.metrologyData = self.moduleMetrologyData

            if testType == 'HYBRID_METROLOGY':
                self.hybridMetrologyData = {'institutionList':[],  'Bow':[]}
                for i in range (len(self.resultsDict)):
                    self.hybridMetrologyData['institutionList'].append(self.resultsDict[i]['extraData']['institution'])
                    self.hybridMetrologyData['Bow'].append(self.resultsDict[i]['results']['HYBRID_METROLOGY']['Bow'])
                    for j, heightVal in enumerate(self.resultsDict[0]['results']['HYBRID_METROLOGY']['Height']):
                        self.hybridMetrologyData['ASIC {0} Glue Height'.format(j)] =[]
                        self.hybridMetrologyData['ASIC {0} Glue Height'.format(j)].append(heightVal)
                        
                self.metrologyData = self.hybridMetrologyData

            if self.verbose:
                if kwargs['testType'] in ['MMETROLOGY', 'HYBRID_METROLOGY']:
                    INFO('The metrology dictionary has been filled: ' + str(self.metrologyData))

    # This is where the test runs are pulled from the DB and the reuslts dictionary is initialied and the plots are made. These are then placed into drawplots.   
    def makePlots (self, **kwargs):

        INFO('Making ' + str(kwargs['testType']) + ' plots')

        # get the test run ID's regardless of what test it is
        if kwargs['serialNumber'] != None:
            componentTestRuns = self.doSomething('listTestRunsByComponent', 'GET', data = {'component': kwargs['serialNumber'], 'testType': kwargs['testType']})

            for i in componentTestRuns:
                self.testIDs.append(i['id'])
                self.resultsDict.append({'results': {'STROBE_DELAY':{}, 'THREE_POINT_GAIN': {}, 'RESPONSE_CURVE': {}, 'NOISE_OCCUPANCY': {}, 'MMETROLOGY':{}, 'HYBRID_METROLOGY':{}}, 'extraData':{}})

            self.infoPull(kwargs['testType'])

            # protect against it carrying on with no data
            if self.verbose:
                INFO('There are '+ str(len(self.resultsDict)) + ' ' + str(kwargs['testType']) + ' test associated with this component')

            if len(self.resultsDict) == 0:
                ERROR('There are either no ' + str(kwargs['testType']) +' tests associated with this component or cant extract information from database')
                sys.exit()

            self.drawPlots(self.resultsDict, **kwargs)

    def CSVOutput(self):
        if kwargs['testType'] not in ['MMETROLOGY', 'HYBRID_METROLOGY']:
            WARNING ('No CSV functionality for ' + kwargs ['testType'])
            return  
        with open ('{0}/ITkPDTestComparison_{1}.csv'.format(os.getcwd(), startTime4SavePath), 'w', newline = '') as f:
            writer = csv.writer(f)
            writer.writerow(self.metrologyData.keys())
            writer.writerows(zip(*self.metrologyData.values()))
        if self.verbose:
            INFO('Written data to CSV file named' + '{0}/ITkPDTestComparison_{1}.csv'.format(os.getcwd(), startTime4SavePath))

    # The plotting is such that if you want 3PG plots I want to plot all 22 plots but in like sets of two on each page. This function handles all the plotting technicalities
    # This is very hard coded, maybe I can clean this up a little?
    def plotFramework(self, title1, title2, testType):
      
        ##############################
        #### Common                ###
        ##############################
      
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)

        ax1 = fig.add_subplot(211)
        ax1.set_title(label = title1)

        ax2 = fig.add_subplot(212)
        ax2.set_title(label = title2)

        ##############################
        #### SD, 3PG, RC, NO Tests ###
        ##############################

        if kwargs['testType'] not in ['MMETROLOGY', 'HYBRID_METROLOGY']:

            plt.xticks(list(range(1,11)))
            ax.set_xlabel('Chip Number')
            ax.set_ylabel(kwargs['testType'])

            # Its a bit messy here but this is to see overlapping results on the plot.
            for i in range (len(self.resultsDict)):
                ax1.plot(list(range(1,len(self.resultsDict[i]['results'][testType][title1])+1)), self.resultsDict[i]['results'][testType][title1] ,'-o', alpha = 0.6,  label = self.resultsDict[i]['extraData']['institution'] + ' ' + self.resultsDict[i]['extraData']['date'], markersize = float((2*len(self.resultsDict)+1)-2*i), linewidth = float((2*len(self.resultsDict)+1)-2*i)) 
                ax1.legend(frameon = False, prop= {'size': 6})

            for i in range (len(self.resultsDict)):
                ax2.plot(list(range(1,len(self.resultsDict[i]['results'][testType][title2])+1)), self.resultsDict[i]['results'][testType][title2], '-o', alpha = 0.6, markersize = float((2*len(self.resultsDict)+1)-2*i), linewidth = float((2*len(self.resultsDict)+1)-2*i))

        ##################
        #### Metrology ###
        ##################

        if kwargs['testType'] in ['MMETROLOGY', 'HYBRID_METROLOGY']:
       
            ax1.set_ylabel('Glue thickness $\mu$m')
            ax.set_xlabel('Institution')
            ax2.set_ylabel('Bow')
            # In this case I think it is better to show how the metrology is changing by institution so I have to extract the data from the dictionary and put it into a dedicated metrology dictionary
            print(self.metrologyData)           
            for keys in self.metrologyData.keys():
                if keys == 'institutionList':
                    continue
                elif keys != 'Bow':
                    ax1.plot(self.metrologyData['institutionList'], self.metrologyData[keys], 'o-', label = keys)
                    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                elif keys == 'Bow':
                    ax2.plot(self.metrologyData['institutionList'], self.metrologyData[keys], 'o-', label = keys)
                    ax2.legend()

        plt.tight_layout()

        return fig

    # This is where the plots are drawn for each test. 
    def drawPlots (self, resultsDict, **kwargs):

        from matplotlib.backends.backend_pdf import PdfPages
        Pages = []
        keys = list(resultsDict[0]['results'][str(kwargs['testType'])])

        if self.verbose:
            INFO('Names of Plots:\n '+ str(keys) + '\n Number of plots: ' + str(len(keys)))

        if kwargs['testType'] == 'STROBE_DELAY':
            Pages.append(self.plotFramework(title1 = 'Stream0 Delays', title2 ='Stream1 Delays', testType = kwargs ['testType'] ))

        if kwargs ['testType'] == 'THREE_POINT_GAIN':
            for i in range(0, len(keys), 2):
                if i == 20: 
                    break
                Pages.append(self.plotFramework(title1 = keys[i], title2 = keys[i+1], testType = kwargs ['testType']))

        if kwargs['testType'] == 'RESPONSE_CURVE':
            for i in range(0, len(keys), 2):
                if i == 24:
                    break
                Pages.append(self.plotFramework(title1 = keys[i], title2 = keys[i+1], testType = kwargs ['testType']))

        if kwargs['testType'] == 'NOISE_OCCUPANCY':
            Pages.append(self.plotFramework(title1 = 'Stream0 EstENC', title2 = 'Stream1 EstENC', testType= kwargs['testType']))

        if kwargs['testType'] in ['MMETROLOGY','HYBRID_METROLOGY']:
            Pages.append(self.plotFramework(title1 = 'Glue heights', title2 = 'Module Bow', testType = kwargs['testType']))

        # Save the pages in a pdf, maybe i'll add functionality to save individuals as pngs?
        if kwargs['saveCSV'] == True:
            self.CSVOutput()
        if kwargs['savePath'][-4:] == '.pdf':
            if self.verbose:
                INFO('Saving plots to file ' + str(kwargs['savePath']))
            pp = PdfPages(kwargs['savePath'])
            for i in Pages:
                pp.savefig(i)
            pp.close()

if __name__ == '__main__':

    try:

        # Get our start time of the script
        from time import strftime
        startTime = strftime('%Y/%m/%d-%H:%M:%S')
        startTime4SavePath = ''.join(startTime.split('-')[0].split('/')) + '-' + ''.join(startTime.split('-')[1].split(':'))

        # Define our parser
        import argparse
        parser = argparse.ArgumentParser(description = 'Generate plots to compare component tests', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
        parser._action_groups.pop()

        # Define our required arguments
        required = parser.add_argument_group('required arguments')
        required.add_argument('-SN', '--serialNumber', dest = 'serialNumber', type = str, help = 'Serial number of component of interest')
        required.add_argument('-t', '--testType', dest = 'testType', choices = ['STROBE_DELAY', 'THREE_POINT_GAIN', 'NOISE_OCCUPANCY', 'RESPONSE_CURVE', 'MODULE_METROLOGY', 'HYBRID_METROLOGY'], type = str, help = 'Test of interest')
        required.add_argument('-S', '--savePath', dest = 'savePath', type = str, default = '{0}/ITkPDTestComparison_{1}.pdf'.format(os.getcwd(), startTime4SavePath), help = 'Path to save file')

        ######################################################################################################################################################################################
        ### Not 100% sure what I will need as my optinal arguments? Maybe if you want to search for a component? Or definitely if you want to add a cut or change the plotting preferences ###
        #####################################################################################################################################################################################

        optional = parser.add_argument_group('optional arguments')

        optional.add_argument('-v', '--verbose', dest = 'verbose', action = 'store_true', help = 'enable detailed printout')
        optional.add_argument('-c', '--CSV', dest = 'CSV', action = 'store_true', help = 'Pipe relevant data to CSV file')

        # Fetch our args and generate our kwargs dict
        args = parser.parse_args()

        print('***compareTests.py***')
        INFO('Parsing Arguments')

        #write something to see if it is a hybrid or a module?
        if args.testType == 'MODULE_METROLOGY':
            args.testType = 'MMETROLOGY'
        kwargs = { 'serialNumber': args.serialNumber,
                   'startTime':    startTime,
                   'testType':     args.testType,
                   'savePath':     args.savePath,
                   'saveCSV':      args.CSV
                 }

         # Generate our PlotMaker object and make our plots
        testPlotter = TestPlotter(args.verbose)
        testPlotter.authenticate()
        testPlotter.makePlots(**kwargs)
        STATUS('Finished successfully.', True)
        sys.exit(0)

        # In the case of a keyboard interrupt, quit with error
    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        STATUS('Finished with error.', False)
        sys.exit(1)
