#!/usr/bin/env python
""" This module is designed to read in a DAGE CSV file and output a results file that can be uploaded to the database"""

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import json
import pandas as pd
import numpy as np
import csv

import sys
sys.path.append('..')

# Initialize values --------------------------------------------
data = {}
data['runNumber']   = "0-0"
data['component']   = "20UPG3D0000005"
data["testType"]    = "WIREBOND"
data["institution"] = "SLAC"
data["passed"]      = False
data["problem"]     = False


data["properties"] = {
        "MACHINE": "DAGE",
        "LOAD": 0.0,
        "OPERATOR": "Fred",
        "SPEED": 0.0,
        "SHEAR": 0.0
    }

data['results'] = {
        "PERCENT_HEEL_BREAKS": 0.0,
        "IND_RESULTS": [0.0],
        "MEAN_LOAD": 0.0,
        "STD_DEV_LOAD": 0.0,
        "MAX_LOAD": 0.0,
        "MIN_LOAD": 0.0
    }
# Parse the DAGE csv file ----------------------------------------

test_results = [] # for storing the results from the csv
test_speed = 0.0
test_load = 0.0

# Read in csv file
with open("sample_wirebond_data.csv", "r") as file:
    reader = csv.reader(file, delimiter=",")
    # Read in file line by line
    for i, line in enumerate(reader):
        #print(line)
        if line: # Make sure there is a line to read
            if line[0] == 'TEST': # all the results we want start with 'TEST'
                test_results.append(line)
            elif line[0] == "TESTSPEED": # parameter
                test_speed = float(line[1])
            elif line[0] == "TESTLOAD": # parameter
                test_load = float(line[1])



# Analyze and store results ------------------------------------------------

df = pd.DataFrame(test_results, columns=["name","","","load","","",""])
df["load"] = df["load"].astype('float')

data["properties"] = {
        "MACHINE": "DAGE",
        "LOAD": test_load,
        "OPERATOR": "Fred",
        "SPEED": test_speed,
        "SHEAR": 0.0
    }

data['results'] = {
        "PERCENT_HEEL_BREAKS": 0.0,
        "MEAN_LOAD": np.mean(df["load"]),
        "STD_DEV_LOAD": np.std(df["load"], ddof=1),
        "MAX_LOAD": max(df["load"]),
        "MIN_LOAD": min(df["load"])
    }

# Make an initial decision about whether a module passes the test or not
# This should be overwritten if a threshold has already been set as part of the test
if data['results']["MIN_LOAD"] > 15.0:
	data["passed"]      = True
else:
	data["passed"]      = False


# Save results output file in json format -----------------------

file_name = 'prototype_WIREBOND_DAGE.json'
print("Saving json file as "+file_name)
with open(file_name, 'w') as outfile:
    json.dump(data, outfile)
