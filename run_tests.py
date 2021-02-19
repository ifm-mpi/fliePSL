from samples2PSL.experiments import run_single_file, run_multiple_file
import glob
import time
import signal
import subprocess
import argparse


def subprocess_calls(tracesFileName, description, maxDepth, maxRegexDepth, finiteSemantics):
    cmd=['python', 'run_tests.py', '-t', tracesFileName, '-d', maxDepth, 'rd',\
                     maxRegexDepth, '-o', description, '-f', finiteSemantics]
    subprocess.run(cmd)



def main():

    #Allowed arguments for the learner
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--traces_file", default="allSamples/dummy.trace",\
                            help='specify the name of the file to run the PSL learner')
    parser.add_argument("-tf", "--traces_folder", default=None,\
                            help='specify the name of the folder containing .trace files to run the PSL learner')
    parser.add_argument("-d", "--max_depth", default='10',\
                            help='specify the maximum depth of the output formula')
    parser.add_argument("-rd", "--max_regex_depth", default='5',\
                            help='specify the maximum depth of the regular expression in the output formula')
    parser.add_argument("-o", "--output_file", default='out',\
                            help='specify the name of the output csv file')
    parser.add_argument("-f", "--finite_semantics", default=False, action="store_true",\
                            help='specify this option if the traces are of finite length')

    args,unknown = parser.parse_known_args()

    tracesFileName = args.traces_file
    tracesFolderName = args.traces_folder
    maxDepth = int(args.max_depth)
    maxRegexDepth =int(args.max_regex_depth)
    outputFile = args.output_file 
    finiteSemantics = bool(args.finite_semantics)
    
    
    if (tracesFolderName==None):
        run_single_file(tracesFileName, maxDepth, maxRegexDepth, outputFile, finiteSemantics)
    else:       
        run_multiple_file(racesFolderName, maxDepth, maxRegexDepth, outputFile, finiteSemantics)



if __name__ == '__main__':
    main()


