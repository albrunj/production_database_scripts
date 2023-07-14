#!/usr/bin/env python
#exe_Load_a_STAVE_auto.py     -- execute Load_a_STAVE_auto.py while recording process
#                              -- script to be run by cron job
#Created by Jiayi Chen (Brandeis University) jennyz@brandeis.edu
#created 06/04/2019
#last update 06/04/2019
import subprocess  # nosec
import time
current_date = time.strftime('%m-%d-%Y')
current_time = time.strftime('%H:%M (%Z)')
filename="./AUTO/assembleSTAVE-ITkPD-"+current_date+".txt"

with open(filename, 'a') as f:
# Write (Append) output to a line
    f.write('\n')
    f.write("==================================")
    f.write("-------- ****New Log****----------")
    f.write("==================================")
    f.write("Assemble STAVE in ITk Production Database    " + current_date + '  ' + current_time + '\n')
    f.write('\n')

with open(filename,'a') as f:
    subprocess.call(["python", "./Load_a_STAVE_auto.py"], stdout=f) # nosec

with open(filename, 'a') as f:
    f.write("-------- ****Log End****----------\n")
