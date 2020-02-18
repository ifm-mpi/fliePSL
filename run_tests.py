from samples2PSL.experiments import producePSL
import matplotlib.pyplot as plt
import glob
import multiprocessing
import time
import signal
import subprocess
import argparse
import subprocess
'''
def auxfun(func, arg, auxList):
	p=func(arg)
	auxList.append(p)

#takes function 'func' and its arguments 'arg' and produces a timeout after 'time' secs and return default otherwise
def timeout(func, arg, time, default):
    
    # Start bar as a process
    p = multiprocessing.Process(target=func, args=(arg,))
    p.start()

    # Wait for 10 seconds or until process finishes
    p.join(time)

    # If thread is still active
    if p.is_alive():
        print("running... let's kill it...")
        # Terminate
        p.terminate()
        p.join()
       	return default
'''

def subprocess_calls(tracesFileName, formulaSyntax, description):
    cmd=['python', 'run_tests.py', '--traces', tracesFileName, '--formula_syntax', formulaSyntax, '--file_description', description]
    subprocess.run(cmd)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", dest="tracesFileName", default="allTests/dummy.trace")
    parser.add_argument("--max_depth", dest="maxDepth", default='10')
    parser.add_argument("--max_regexDepth", dest="maxRegexDepth", default='5')
    parser.add_argument("--formula_syntax", dest="formulaSyntax", default='PSL')
    parser.add_argument("--dfa_size", dest="dfaSize", default='3')
    parser.add_argument("--max_num_formulas", dest="numFormulas", default='1')
    parser.add_argument("--file_description", dest="fileDescription", default='output')
    args,unknown = parser.parse_known_args()

    tracesFileName = args.tracesFileName
    maxDepth = int(args.maxDepth)
    maxRegexDepth =int(args.maxRegexDepth)
    numFormulas = int(args.numFormulas)
    formulaSyntax = args.formulaSyntax
    dfaSize = int(args.dfaSize)
    description = args.fileDescription 
    
    if (formulaSyntax=='PSL'):
        producePSL(tracesFileName=tracesFileName, maxDepth=maxDepth, maxRegexDepth=maxRegexDepth, dfaSize=dfaSize, description=description)
    else:
        print("Wrong choice. Try again")

if __name__ == '__main__':
    main()


