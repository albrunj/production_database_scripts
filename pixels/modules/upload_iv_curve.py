#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import json
import pandas as pd

import sys
sys.path.append('..')

df = pd.read_csv("sample_IV_curve.txt",delim_whitespace=True)

data = {}
data['runNumber']   = "0-1"
data['component']   = "20UPG000000003"
data["testType"]    = "IV CURVE"
data["institution"] = "SLAC"
data["passed"]      = True
data["problem"]     = False

data["properties"] = {}

data['results'] = {
        "VOLTAGE": list(df["U[V]"]),
        "CURRENT": list(df["Imean[uA]"])
    }

file_name = 'prototype_IV_CURVE.json'
print("Saving json file as "+file_name)
with open(file_name, 'w') as outfile:
    json.dump(data, outfile)
