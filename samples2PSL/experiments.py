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

def generate_info(tracesFileName, maxDepth, maxRegexDepth, finiteSemantics):
    
    t0=time.time()

    traces = ExperimentTraces()
    traces.readTracesFromFile(tracesFileName)

    formulas = get_models(maxDepth, maxRegexDepth, traces, finiteSemantics)
    form=formulas[0]

    t1=time.time()
    timePassed=t1-t0

    print('Formula:', form.prettyPrint(), 'Time:', timePassed)
    return [tracesFileName, str(timePassed), str(form.getNumberOfSubformulas()), str(form.prettyPrint())]



def run_single_file(tracesFileName, maxDepth, maxRegexDepth, outputFile, finiteSemantics):
          
    with open(tracesFileName+'-'+outputFile+'.csv', 'a') as file:
        writer = csv.writer(file)

        csvInfo = [['File Name', 'Time Passed', 'Formula Size', 'PSL formula']]
        csvInfo.append(generate_info(tracesFileName, maxDepth, maxRegexDepth, finiteSemantics))
        
        writer.writerows(csvInfo)


    
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








