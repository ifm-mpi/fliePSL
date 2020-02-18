from run_tests import subprocess_calls
from rq import Queue, Worker, Connection
from redis import Redis
import glob
import time
import argparse
#Before running new commands check 1)Folder to run on  2)file_suffix 3)queue_suffix 4)formula_syntax



#change these parameters for PSL/LTL, numWorker for as many workers you want
parser = argparse.ArgumentParser()
parser.add_argument("--traces_folder", dest="tracesFolder", default="allTests/generatedTracesFromPSL/")
parser.add_argument("--file_suffix", dest="suffix", default="")
parser.add_argument("--num_workers", dest="numWorkers", default="20")
parser.add_argument("--formula_syntax", dest="formulaSyntax", default="PSL")
args,unknown = parser.parse_known_args()


tracesFolder=args.tracesFolder
suffix=args.suffix
formulaSyntax=args.formulaSyntax
numWorkers=int(args.numWorkers)



fileNames= []
redis_conn= Redis()
q = Queue('runningLTL', connection=redis_conn)
q.empty()
print(len(q))


folderNames=sorted(glob.glob(tracesFolder+'*'))
for folder in folderNames:
	folder1=folder+'/*.trace'
	fileNames+=sorted(glob.glob(folder1))


for tracesFileName in fileNames:
	description = formulaSyntax+ ':' +str(numWorkers)+'workers'+ suffix
	q.enqueue(subprocess_calls, args=(tracesFileName, formulaSyntax, description), job_timeout=1800, job_id=tracesFileName+description)





'''
for i in range(10):
	q.enqueue(wait_2sec, job_id='2'+str(i), job_timeout=6)
	q.enqueue(wait_10sec, job_id='10'+str(i), job_timeout=6)
	q.enqueue(wait_5sec, job_id='5'+str(i), job_timeout=6)
'''

print(len(q))




	

