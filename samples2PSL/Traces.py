#coverts traces from file to class Trace 	type
def lineToTrace(line, dfaSize):
    lassoStart = None
    try:
        traceData, lassoStart = line.split('::')
    except:
        traceData = line
    traceVector = [[bool(int(varValue)) for varValue in varsInTimestep.split(',')] for varsInTimestep in
                   traceData.split(';')]
    trace = Trace(traceVector, lassoStart, dfaSize)
    return trace


class Trace:
    def __init__(self, traceVector, lassoStart=None, dfaSize=3):
        self.lengthOfTrace = len(traceVector)
        if lassoStart != None:
            self.lassoStart = int(lassoStart)
            if self.lassoStart >= self.lengthOfTrace:
                raise Exception(
                    "lasso start = %s is greater than any value in trace (trace length = %s) -- must be smaller" % (
                    self.lassoStart, self.lengthOfTrace))
        else:
            self.lassoStart = 0
        assert self.lengthOfTrace > 0 and self.lassoStart <= self.lengthOfTrace
        self.vLength=self.lengthOfTrace - self.lassoStart
        self.uLength= self.lengthOfTrace - self.vLength
        self.numVariables = len(traceVector[0])
        self.traceVector = traceVector
        #self.extendedTraceVector=self.extendedTrace(dfaSize)
        self.literals = ["x" + str(i) for i in range(self.numVariables)]
        
        
    def __repr__(self):
        return repr(self.traceVector) + "\n" + repr(self.lassoStart) + "\n\n"
#loops around in lasso needs to be changed
    def nextPos(self, currentPos):
        if currentPos == self.lengthOfTrace - 1:
            return self.lassoStart
        else:
            return currentPos + 1


    def futurePos(self, currentPos):
        futurePositions = []
        alreadyGathered = set()
        while currentPos not in alreadyGathered:
            futurePositions.append(currentPos)
            alreadyGathered.add(currentPos)
            currentPos = self.nextPos(currentPos)
        # always add a new one so that all the next-relations are captured
        futurePositions.append(currentPos)
        return futurePositions

    def extendedTrace(self, dfaSize):
        extTrace=self.traceVector
        b=dfaSize
        v=[self.traceVector[i] for i in range(self.lassoStart, self.lengthOfTrace)]
        extTrace=extTrace+(v*b)
        self.extendedTraceLength=len(extTrace)
        self.extendedTraceVector=extTrace
        return extTrace

    def inTracePosition(self, currentpos):
        if currentpos<self.lengthOfTrace:
            return currentpos
        else:
            modpos=self.uLength + ((currentpos-self.uLength)%self.vLength)
            return modpos


class ExperimentTraces:
    def __init__(self, tracesToAccept=None, tracesToReject=None, dfaSize=None):
        if tracesToAccept != None:
            self.acceptedTraces = tracesToAccept
        else:
            self.acceptedTraces = []

        if tracesToReject != None:
            self.rejectedTraces = tracesToReject
        else:
            self.rejectedTraces = []
        if dfaSize != None:
        	self.dfaSize = dfaSize
        else:
        	self.dfaSize =dfaSize


 


    def __repr__(self):
        returnString = ""
        returnString += "accepted traces:\n"
        for trace in self.acceptedTraces:
            returnString += repr(trace)
        returnString += "\nrejected traces:\n"

        for trace in self.rejectedTraces:
            returnString += repr(trace)
        return returnString



    def readTracesFromStream(self, stream):
        readingMode = 0
        for line in stream:
            lassoStart = None
            if '---' in line:
                readingMode += 1
            else:
                if readingMode == 0:

                    trace = lineToTrace(line, self.dfaSize)
                    trace.intendedEvaluation = True

                    self.acceptedTraces.append(trace)

                elif readingMode == 1:
                    trace = lineToTrace(line, self.dfaSize)
                    trace.intendedEvaluation = False
                    self.rejectedTraces.append(trace)
                else:
                    break
        try:
            self.numVariables = self.acceptedTraces[0].numVariables
        except:
            self.numVariables = self.rejectedTraces[0].numVariables


    def readTracesFromFile(self, tracesFileName):
        with open(tracesFileName) as tracesFile:
            self.readTracesFromStream(tracesFile)
