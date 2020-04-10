from samples2PSL.experiments import run_single_file, run_multiple_file
import glob
import time
import signal
import subprocess
import argparse



def main():

    #Allowed arguments for the learner
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--traces_file", dest="tracesFileName", default="allTraces/dummy.trace",\
                            help='specifies the name of the file to run the PSL learner')
    parser.add_argument("-tf", "--traces_folder", dest="tracesFolderName", default=None,\
                            help='specifies the name of the folder containing .trace files to run the PSL learner')
    parser.add_argument("-d", "--max_depth", dest="maxDepth", default='10',\
                            help='specifies the maximum depth of the output formula')
    parser.add_argument("-rd", "--max_regexDepth", dest="maxRegexDepth", default='5',\
                            help='specifies the maximum depth of the regular expression in the output formula')
    parser.add_argument("-o", "--output_file", dest="outputFile", default='out',\
                            help='specifies the name of the output csv file')
    args,unknown = parser.parse_known_args()

    tracesFileName = args.tracesFileName
    tracesFolderName = args.tracesFolderName
    maxDepth = int(args.maxDepth)
    maxRegexDepth =int(args.maxRegexDepth)
    outputFile = args.outputFile 
    
    if (tracesFolderName==None):
        run_single_file(tracesFileName=tracesFileName, maxDepth=maxDepth, maxRegexDepth=maxRegexDepth, outputFile=outputFile)
    else:       
        run_multiple_file(tracesFolderName=tracesFolderName, maxDepth=maxDepth, outputFile=outputFile)



if __name__ == '__main__':
    main()


