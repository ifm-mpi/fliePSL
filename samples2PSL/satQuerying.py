from .SATEncoding import *
from z3 import *
import sys
import time
import traceback
import logging
from samples2PSL.SimpleTree import Formula


#change this order for the change in iteration order
def genIterationSeq(max_i, max_j):
    iteration_seq=[(1,0)]
    for i in range(2, max_i):
        end_j=min(i-1, max_j)
        for j in range(0, end_j):
                iteration_seq.append((i,j))
    return iteration_seq



def get_models(maxDepth, maxRegexDepth, traces, finiteSemantics, chooseOperators):
    results = []
    iteration_seq = genIterationSeq(maxDepth, maxRegexDepth)
    
    for (depth,regexDepth) in iteration_seq:
        
        t_create=time.time()

        fg = SATEncoding(depth, regexDepth, traces, finiteSemantics, chooseOperators)
        fg.encodeFormula()
        t_create=time.time()-t_create
        
        t_solve=time.time()
        solverRes = fg.solver.check()
        t_solve=time.time()-t_solve

        #Print this to see constraint creation time and constraint solving time separately
        print(depth, regexDepth)
        #print((i,j), "Creating time:", t_create, "Solving time:", t_solve)
        
        if solverRes == sat:
            solverModel = fg.solver.model()
            formula = fg.reconstructWholeFormula(solverModel)
            results.append(formula)
            break


    return results


        
    