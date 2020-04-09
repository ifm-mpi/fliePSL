from run_tests import subprocess_calls
from rq import Queue, Worker, Connection
from redis import Redis
import os
import glob
import argparse


#Before running new commands check 1)Folder to run on  2)file_suffix 3)queue_suffix 4)formula_syntax
#change these parameters for PSL/LTL, numWorker for as many workers you want
parser = argparse.ArgumentParser()
parser.add_argument("-tf", "--traces_folder", dest="tracesFolderName", default="allTraces/generatedTracesFromPSL/",\
							help='specify the name of the folder containing trace files')
parser.add_argument("-nw", "--num_workers", dest="numWorkers", default="20",\
							help='specify the number of redis worker spawned for running experiments')
parser.add_argument("-d", "--max_depth", dest="maxDepth", default='10',\
                            help='specify the maximum depth of the output formula')
parser.add_argument("-rd", "--max_regex_depth", dest="maxRegexDepth", default='5',\
                            help='specify the maximum depth of the regular expression in the output formulas')
parser.add_argument("-k", "--kill_after", dest="timeOut",  default='1800',\
							help='specify the time after with a redis worker would be killed')
parser.add_argument("-o", "--output_file", dest="outputFile", default='out',\
                            help='specify the name of the output csv file')

args,unknown = parser.parse_known_args()


tracesFolderName = args.tracesFolderName
maxDepth = int(args.maxDepth)
maxRegexDepth =int(args.maxRegexDepth)
outputFile = args.outputFile 
timeOut = int(args.timeOut)
numWorkers=int(args.numWorkers)



fileNames= []
redis_conn= Redis()
q = Queue('flie-PSL', connection=redis_conn)
q.empty()

tracesFileList = []
for root, dirs, files in os.walk(tracesFolderName):
            for file in files:
                if file.endswith(".trace"):
                    tracesFileList.append(str(os.path.join(root, file)))

'''
folderNames=sorted(glob.glob(tracesFolder+'*'))
for folder in folderNames:
	folder1=folder+'/*.trace'
	fileNames+=sorted(glob.glob(folder1))
'''

for tracesFileName in tracesFileList:
	description = outputFile + '-' + str(numWorkers)+'workers'
	q.enqueue(subprocess_calls, args=(tracesFileName, description, maxDepth, maxRegexDepth)\
													, job_timeout=timeOut, job_id=tracesFileName+description)



print('Length of queue', len(q))




	

