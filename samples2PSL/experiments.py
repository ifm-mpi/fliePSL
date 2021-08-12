import pdb
from z3 import *
import argparse
from .SATEncoding import *
import os
from .satQuerying import get_models
from .Traces import Trace, ExperimentTraces
import logging
import time
import csv

def generate_info(tracesFileName, maxDepth, maxRegexDepth, only_ltl, finiteSemantics):
    
    t0=time.time()

    traces = ExperimentTraces()
    traces.readTracesFromFile(tracesFileName)


    formulas = get_models(maxDepth, maxRegexDepth, traces, only_ltl, finiteSemantics)
    
    t1=time.time()
    timePassed=t1-t0

    if formulas==[]:
        print('Formula:', 'Nope!')
        print('Time:', timePassed)

        return [None, str(timePassed)]
    form=formulas[0]

    
    print('Formula:', form.prettyPrint())

    print('Time:', timePassed)


    return [form, str(timePassed)]



def run_single_file(tracesFileName, maxDepth=10, maxRegexDepth=5, outputFile='out', only_ltl=True, finiteSemantics=True):
          

        #csvInfo.append(generate_info(tracesFileName, maxDepth, maxRegexDepth, only_ltl, finiteSemantics))
        
        #writer.writerows(csvInfo)
    return generate_info(tracesFileName, maxDepth, maxRegexDepth, only_ltl, finiteSemantics)

    
def run_multiple_file(tracesFolderName, maxDepth, maxRegexDepth, outputFile, finiteSemantics):
    
    with open(tracesFolderName+'-'+outputFile+'.csv', 'w') as file:
        for root, dirs, files in os.walk(tracesFolderName):
            for file in files:
                if file.endswith(".trace"):
                    tracesFileList.append(str(os.path.join(root, file)))

        csvInfo = [['File Name', 'Time Passed', 'Formula Size', 'PSL formula']]
        for tracesFileName in tracesFileList:
            csvInfo.append(generate_info(tracesFileName, maxDepth, maxRegexDepth, finiteSemantics))

        writer.writerows(csvInfo)
