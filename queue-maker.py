from run_tests import subprocess_calls
from rq import Queue, Worker, Connection
from redis import Redis
import csv
import os
import glob
import argparse

'''
Run the following commands to run experiments from a traces folder concurrently using multi-core processor

- Install redis servers using sudo apt-get install 

-First run the queue-maker with the desired arguments (check --help for more arguments)

python queue-maker.py -tf <foldername> -o <outputfilename> -k <timeout> -nw <numberworkers>


-Then, run the desired number of workers (default is 5) for running flie-PSL on different threads

rq worker -b -q flie-PSL &


-Now, modify the main-function in queue-maker: Comment out m.populate_queue() and uncomment m.compile_results()


-Finally, run queuemaker again, with the same arguments as in the first step, to compile the results

python queue-maker.py -tf <foldername> -o <outputfilename> -k <timeout> -nw <numberworkers>

'''
class multiprocess:

	def __init__(self, tracesFolderName, outputFile, maxDepth, maxRegexDepth, numWorkers, timeOut, finiteSemantics):
		
		self.tracesFolderName = tracesFolderName
		self.outputFile = outputFile
		self.maxDepth = maxDepth
		self.maxRegexDepth = maxRegexDepth
		self.numWorkers = numWorkers
		self.timeOut = timeOut
		self.finiteSemantics = str(finiteSemantics)
		self.fullOutputFile = self.outputFile + '-' + self.numWorkers + 'workers'
		self.tracesFileList = []
		for root, dirs, files in os.walk(self.tracesFolderName):
			for file in files:
				if file.endswith('.trace'):
					self.tracesFileList.append(str(os.path.join(root, file)))



	def populate_queue(self):
		redis_conn= Redis()
		q = Queue('flie-PSL', connection=redis_conn)
		q.empty()

		for tracesFileName in self.tracesFileList:
			q.enqueue(subprocess_calls, args=(tracesFileName, self.fullOutputFile, self.maxDepth,\
			 self.maxRegexDepth, self.finiteSemantics), job_timeout=self.timeOut, job_id=tracesFileName+self.fullOutputFile)

		print('Length of queue', len(q))

	def compile_results(self):

		with open(self.tracesFolderName+'-compiled-'+self.numWorkers+'.csv', 'w') as file1:
			writer = csv.writer(file1)
			csvInfo = [['File Name', 'Time Passed', 'Formula Size', 'PSL formula']]
			for tracesFileName in self.tracesFileList:
				with open(tracesFileName+'-'+self.fullOutputFile+'.csv', 'r') as file2:
					rows = csv.reader(file2)
					row_list = list(rows)
					
					if row_list == []:
						csvInfo.append([tracesFileName, self.timeOut])#this file has timed out
					else:
						csvInfo.append(row_list[1])#this file has not timed out
			writer.writerows(csvInfo)




def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-tf', '--traces_folder', default='allSamples/generatedFromPSL/smallSamples',\
							help='specify the name of the folder containing trace files')
	parser.add_argument('-nw', '--num_workers', dest='numWorkers', default='20',\
							help='specify the number of redis worker spawned for running experiments')
	parser.add_argument('-d', '--max_depth', default='10',\
                            help='specify the maximum depth of the output formula')
	parser.add_argument('-rd', '--max_regex_depth', default='5',\
                            help='specify the maximum depth of the regular expression in the output formulas')
	parser.add_argument('-k', '--kill_after', default='1800',\
							help='specify the time after with a redis worker would be killed')
	parser.add_argument('-o', '--output_file', default='out',\
                            help='specify the name of the output csv file')
	parser.add_argument("-f", "--finite_semantics", default=False, action="store_true",\
                            help='specify this option if the traces are of finite length')

	args,unknown = parser.parse_known_args()


	tracesFolderName = args.traces_folder
	maxDepth = args.max_depth
	maxRegexDepth =args.max_regex_depth
	outputFile = args.output_file
	timeOut = int(args.kill_after)
	numWorkers=args.numWorkers
	finiteSemantics = args.finite_semantics

	tracesFileList = []
	for root, dirs, files in os.walk(tracesFolderName):
		for file in files:
			if file.endswith('.trace'):
				tracesFileList.append(str(os.path.join(root, file)))

	m = multiprocess(tracesFolderName, outputFile, maxDepth, maxRegexDepth, numWorkers, timeOut, finiteSemantics)

	
	m.populate_queue()#comment this out for compiling results
	#m.compile_results()#uncomment this for compiling results



if __name__ == '__main__':
    main()




