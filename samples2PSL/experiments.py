import pdb
from z3 import *
import argparse
from samples2PSL.SATEncoding import *
import os
from samples2PSL.satQuerying import get_models
from samples2PSL.Traces import Trace, ExperimentTraces
import logging
import time
import csv

 
def producePSL(tracesFileName, maxDepth=10, maxRegexDepth=5, dfaSize=2, numFormulas=1, description=''):
    
    
    """
    traces is 
     - list of different recorded values (traces)
     - each trace is a list of recordings at time units (time points)
     - each time point is a list of variable values (x1,..., xk) 
    """    
    with open(tracesFileName+'-'+description+'.csv', 'w') as file:
        t0=time.time()

        traces = ExperimentTraces(dfaSize=dfaSize)
        traces.readTracesFromFile(tracesFileName)

        formulas = get_models(finalDepth=maxDepth, maxRegexDepth=maxRegexDepth, traces=traces, dfaSize=dfaSize)
        form=formulas[0]

        t1=time.time()
        timePassed=t1-t0

        writer = csv.writer(file)

        print(form.prettyPrint(), timePassed)
        writer.writerow([tracesFileName, 'PSL', str(timePassed), str(form.getNumberOfSubformulas()), str(form.prettyPrint())])



    


