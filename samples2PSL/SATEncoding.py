from z3 import *
from .Traces import Trace, ExperimentTraces
from .SimpleTree import SimpleTree, Formula


'''
SATEncoding contains all the constraints for encoding the Learning Problem
'''
def intersection(list1, list2):
  return list(set(list1)&set(list2))




class SATEncoding:

    def __init__(self, formulaDepth, regexDepth, testTraces, finiteSemantics, chooseOperators): 
        
        #all PSL operators
        self.Operators = ['G', 'F', '!', 'U', '&','|', '->', 'X', '|->','+', '.', '*']
        self.unaryOperators = ['G', 'F', '!', 'X', '*']
        self.binaryOperators = ['&', '|', 'U', '->', '|->', '+', '.']
        self.pslOperators= ['G', 'F', '!', 'U', '&', '|', '->', 'X', '|->']
        self.regexOperators= ['+', '.', '*', '&', '|']
        
        


        if chooseOperators:
          self.chosenOperators = testTraces.operators
          self.Operators = self.chosenOperators
          self.unaryOperators = intersection(self.Operators, self.unaryOperators)
          self.binaryOperators = intersection(self.Operators, self.binaryOperators)
          self.pslOperators = intersection(self.Operators, self.pslOperators)
          self.regexOperators = intersection(self.Operators, self.regexOperators)

        self.solver = Solver()
        self.formulaDepth = formulaDepth
        self.regexDepth = regexDepth
        self.finiteSemantics = finiteSemantics


        self.traces = testTraces        
        self.pslVariables = [i for i in range(self.traces.numVariables)]+['true']
        self.regexVariables = self.pslVariables+['epsilon']
        self.variables=self.regexVariables

        for trace in (self.traces.acceptedTraces + self.traces.rejectedTraces):
          if self.finiteSemantics:
            nfaSize = 0
          else:
            nfaSize = 2*(self.regexDepth)+3 # change this for a better bound for unrolling words
          trace.extendedTrace(nfaSize)
        

    def getInformativeVariables(self):
        res = []
        res += [v for v in self.x.values()]
        res += [v for v in self.l.values()]
        res += [v for v in self.r.values()]
        res += [v for v in self.y.values()]
        res += [v for v in self.z.values()]

        return res
    '''    
    the working variables are 
        - x[p][o]: p is a subformula (row) identifier, o is an operator or a propositional variable. Meaning is "subformula is an operator (variable) o"
        - l[p][q]:  "left operand of subformula i is subformula j"
        - r[p][q]: "right operand of subformula i is subformula j"
        - y[i][p][traceId]: semantics of formula at p in time point i of trace number traceId
      	- z[i][j][p][traceId]: semantics of regex at p in i subword (i,j) of trace traceId
    '''
    
    def encodeFormula(self, unsatCore=True):
        self.operatorsAndVariables = self.Operators + self.variables
 
        #1 to m is regexoperators and variables
        #m to n is psloperators and variables

        self.x = { (p, o) : Bool('x_'+str(p)+'_'+str(o)) for p in range(self.formulaDepth) for o in self.operatorsAndVariables }
        self.l = {(p, q) : Bool('l_'+str(p)+'_'+str(q))\
                                                 for p in range(self.formulaDepth)\
                                                 for q in range(p)}
        self.r = {(p, q) : Bool('r_'+str(p)+'_'+str(q))\
                                                 for p in range(1, self.formulaDepth)\
                                                 for q in range(p)}

        self.y = { (i, p, traceId) : Bool('y_'+str(i)+'_'+str(p)+'_'+str(traceId))\
                  for traceId, trace in enumerate(self.traces.acceptedTraces + self.traces.rejectedTraces)
                  for i in range(trace.lengthOfTrace)\
                  for p in range(self.regexDepth, self.formulaDepth)}
                    
        self.z = { (i, j, p, traceId) : Bool('z_'+str(i)+'_'+str(j)+'_'+str(p)+'_'+str(traceId))\
                  for traceId, trace in enumerate(self.traces.acceptedTraces + self.traces.rejectedTraces)
                  for i in range(trace.extendedTraceLength+1)\
                  for j in range(i,trace.extendedTraceLength+1)\
                  for p in range(self.regexDepth)}

        self.solver.set(unsat_core=unsatCore)

        
        #structural constriaints
        self.exactlyOneOperator()       
        self.firstOperatorVariable()
        self.lastOperatorPSL()
        self.operatorOrdering()
        self.noDanglingVariables()
        
        #constraints for consistency
        self.variableSemantics()
        self.operatorsSemantics() 
        self.solver.assert_and_track(And( [ self.y[(0, self.formulaDepth - 1, traceId)]\
                                                  for traceId in range(len(self.traces.acceptedTraces))] ),\
                                           'accepted traces should be accepting')
        self.solver.assert_and_track(And([ Not(self.y[(0, self.formulaDepth - 1, traceId)])\
                                                  for traceId in range(len(self.traces.acceptedTraces), len(self.traces.acceptedTraces+self.traces.rejectedTraces))] ),\
                                          'rejecting traces should be rejected')
        
    
    def exactlyOneOperator(self):
        self.solver.assert_and_track(And([\
                                              AtMost( [self.x[k] for k in self.x if k[0] == p] +[1])\
                                              for p in range(self.formulaDepth)\
                                              ]),\
                                              "at most one operator per subformula"\
            )
            
        self.solver.assert_and_track(And([\
                                              AtLeast( [self.x[k] for k in self.x if k[0] == p] +[1])\
                                              for p in range(self.formulaDepth)\
                                              ]),\
                                              "at least one operator per subformula"\
            )
            
        if (self.formulaDepth > 0):
            self.solver.assert_and_track(And([\
                                                Implies(
                                                    Or(
                                                        [self.x[(p, op)] for op in self.binaryOperators+self.unaryOperators]
                                                    ),
                                                    AtMost([self.l[k] for k in self.l if k[0] == p] +[1])\
                    )
                                              for p in range(1,self.formulaDepth)\
                                              ]),\
                                              "at most one left operator for binary and unary operators"\
            )
            
        if (self.formulaDepth > 0):
            self.solver.assert_and_track(And([\
                                                Implies(
                                                    Or(
                                                        [self.x[(p, op)] for op in self.binaryOperators + self.unaryOperators]
                                                    ),
                                                    AtLeast( [self.l[k] for k in self.l if k[0] == p] +[1])\
                                                    )
                                              for p in range(1,self.formulaDepth)\
                                              ]),\
                                              "at least one left operator for binary and unary operators"\
            )

        if (self.formulaDepth > 0):
            self.solver.assert_and_track(And([ \
                    Implies(
                        Or(
                            [self.x[(p, op)] for op in self.binaryOperators]
                        ),
                        AtMost([self.r[k] for k in self.r if k[0] == p] + [1]) \
                        )
                    for p in range(1, self.formulaDepth) \
                    ]), \
                    "at most one right operator for binary" \
                    )

        if (self.formulaDepth > 0):
            self.solver.assert_and_track(And([ \
                    Implies(
                        Or(
                            [self.x[(p, op)] for op in self.binaryOperators]
                        ),
                        AtLeast([self.r[k] for k in self.r if k[0] == p] + [1]) \
                        )
                    for p in range(1, self.formulaDepth) \
                    ]), \
                    "at least one right operator for binary" \
                    )

        if (self.formulaDepth > 0):
            self.solver.assert_and_track(And([ \
                    Implies(\
                        Or(\
                            [self.x[(p, op)] for op in self.unaryOperators]\
                        ),\
                        Not(
                            Or([self.r[k] for k in self.r if k[0] == p]) \
                        )\
                    )\
                   for p in range(1, self.formulaDepth) \
                    ]), \
                    "no right operators for unary" \
                    )

        if (self.formulaDepth > 0):
            self.solver.assert_and_track(And([ \
                    Implies(\
                        Or(\
                            [self.x[(p, op)] for op in\
                             self.regexVariables+self.pslVariables]\
                        ),\
                        Not(\
                            Or(\
                                Or([self.r[k] for k in self.r if k[0] == p]), \
                                Or([self.l[k] for k in self.l if k[0] == p])\
                            )\

                        )\
                    )\
                    for p in range(self.formulaDepth) \
                    ]), \
                    "no left or right children for variables" \
                    )  

  



    def firstOperatorVariable(self):
        self.solver.assert_and_track(Or([self.x[k] for k in self.x if k[0] == 0 and k[1] in (self.regexVariables)]),\
                                     'first operator a variable or epsilon')

    def lastOperatorPSL(self):

        self.solver.assert_and_track(Or([self.x[k] for k in self.x if k[0] == (self.formulaDepth-1) and k[1] in (self.pslOperators+self.pslVariables)]),\
                                     'Last operator a PSL Operators')
    
    def operatorOrdering(self):
        self.solver.assert_and_track(And([\
                                              Or([self.x[k] for k in self.x if k[0] == p and k[1] in (self.regexOperators +self.regexVariables)])\
                                              for p in range(self.regexDepth)\
                                              ]),\
                                              "regex operators in the lower indices of the tree")

        self.solver.assert_and_track(And([\
                                              Or([self.x[k] for k in self.x if k[0] == p and k[1] in (self.pslOperators+self.pslVariables)])\
                                              for p in range(self.regexDepth, self.formulaDepth)\
                                              ]),\
                                              "PSL operators in the higher indices of the tree")
        
    
        for p in range(self.regexDepth):
          for o in self.regexOperators:
            self.solver.assert_and_track(Implies(self.x[(p, o)],\
                                                            Or([self.l[(p, q)] for q in range(p)]),\
                                                                   ),\
                                                             "regex operator" +str(o)+ "leftChild is regex operator at "+str(p))
          for o in intersection(self.regexOperators, self.binaryOperators):
            self.solver.assert_and_track(Implies(self.x[(p, o)],\
                                                            Or([self.r[(p, q)] for q in range(p)]),\
                                                                   ),\
                                                             "regex binary operator" +str(o)+ " rightchild is regex operator at "+str(p))




        for p in range(self.regexDepth, self.formulaDepth):
          if '|->' in self.Operators:
            self.solver.assert_and_track(Implies(self.x[(p, '|->')],\
                                                            Or([self.l[(p, q)] for q in range(self.regexDepth)]),\
                                                                   ),\
                                                             "PSL operator |->  leftChild is regex operator at "+str(p))

            self.solver.assert_and_track(Implies(self.x[(p, '|->')],\
                                                            Or([self.r[(p, q)] for q in range(self.regexDepth, p)]),\
                                                                   ),\
                                                             "PSL operator |-> rightChild is PSL operator at "+str(p))
 

          for o in intersection(['G', 'F', '!', 'U', '&', '|', '->', 'X'], self.Operators):
            self.solver.assert_and_track(Implies(self.x[(p, o)],\
                                                            Or([self.l[(p, q)] for q in range(self.regexDepth, p)]),\
                                                                   ),\
                                                             "PSL operator "+str(o)+" leftChild is PSL operator"+str(p))
          for o in intersection(['U', '&', '|', '->'], self.Operators):
            self.solver.assert_and_track(Implies(self.x[(p, o)],\
                                                            Or([self.r[(p, q_prime)] for q_prime in range(self.regexDepth, p)]),\
                                                                   ),\
                                                             "PSL binary operator "+str(o)+" rightChild is PSL operator"+str(p))


       

    def noDanglingVariables(self):
        if self.formulaDepth > 0:
            self.solver.assert_and_track(
                And([
                    Or(
                        AtLeast([self.l[(p, q)] for p in range(q+1, self.formulaDepth)]+ [1]),
                        AtLeast([self.r[(p, q)] for p in range(q+1, self.formulaDepth)] + [1])
                    )
                    for q in range(self.formulaDepth - 1)]
                ),
                "no dangling variables") 
    
    def variableSemantics(self):
        for p in range(self.regexDepth):
            for var in self.regexVariables:
                for traceId, trace in enumerate(self.traces.acceptedTraces + self.traces.rejectedTraces):
                   
                  if var=='epsilon':
                    self.solver.assert_and_track(Implies(self.x[(p, var)],\
                                                          And([ self.z[(i, j, p, traceId)] == (i==j)\
                                                               for i in range(trace.extendedTraceLength+1) for j in range(i, trace.extendedTraceLength+1)])),\
                                                          "semantics of regex variable depth_"+str(p)+' var _'+'epsilon'+'_trace_'+str(traceId))
                    
                  elif var=='true':  
                    self.solver.assert_and_track(Implies(self.x[(p, var)],\
                                                          And([ self.z[(i, j, p, traceId)] == (i+1==j)\
                                                               for i in range(trace.extendedTraceLength+1) for j in range(i, trace.extendedTraceLength+1)])),\
                                                          "semantics of regex variable depth_"+str(p)+' var _'+'true'+'_trace_'+str(traceId))
                  else:
                    self.solver.assert_and_track(Implies(self.x[(p, var)],\
                                                          And([ self.z[(i, j, p, traceId)] if (i+1==j) and (trace.extendedTraceVector[i][var] == True) else Not(self.z[(i, j, p, traceId)])\
                                                               for i in range(trace.extendedTraceLength+1) for j in range(i, trace.extendedTraceLength+1)])),\
                                                          "semantics of regex variable depth_"+str(p)+' var _'+str(var)+'_trace_'+str(traceId))
  

        for p in range(self.regexDepth, self.formulaDepth):
            for var in self.pslVariables:
                for traceId, trace in enumerate(self.traces.acceptedTraces + self.traces.rejectedTraces):
                    if var=='true':
                      self.solver.assert_and_track(Implies(self.x[(p, var)],\
                                                          And([ self.y[(i, p, traceId)]\
                                                               for i in range(trace.lengthOfTrace)])),\
                                                          "semantics of PSL variable depth_"+str(p)+' var _'+'true'+'_trace_'+str(traceId))
                    
                    else:
                      self.solver.assert_and_track(Implies(self.x[(p, var)],\
                                                          And([ self.y[(i, p, traceId)] if trace.traceVector[i][var] == True else Not(self.y[(i, p, traceId)])\
                                                               for i in range(trace.lengthOfTrace)])),\
                                                          "semantics of PSL variable depth_"+str(p)+' var _'+str(var)+'_trace_'+str(traceId))  

                    




    def operatorsSemantics(self):

        for traceId, trace in enumerate(self.traces.acceptedTraces + self.traces.rejectedTraces):
            for p in range(1, self.regexDepth):
              self.regexOperatorSemantics(p, traceId, trace)
              
            for p in range(self.regexDepth, self.formulaDepth):
              self.booleanOperatorSemantics(p, traceId, trace)
              if self.finiteSemantics:
                self.finiteTemporalOperatorSemantics(p, traceId, trace)
              else:
                self.temporalOperatorSemantics(p, traceId, trace)
              self.triggersOperatorSemantics(p, traceId, trace)
                
              


    def regexOperatorSemantics(self, p, traceId, trace):
        if '+' in self.Operators:
              #union
              self.solver.assert_and_track(Implies(self.x[(p, '+')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [ self.z[(i, j, p, traceId)]\
                                                                        ==\
                                                                        Or(\
                                                                           [ self.z[(i, j, q, traceId)],\
                                                                            self.z[(i, j, q_prime, traceId)]]\
                                                                           )\
                                                                         for i in range(trace.extendedTraceLength+1)\
                                                                         for j in range(i,trace.extendedTraceLength+1)]\
                                                                       )\
                                                                   )\
                                                                  for q in range(p) for q_prime in range(p) ])),\
                                                     'semantics of plus operator for trace %d and depth %d'%(traceId, p))

        if '.' in self.Operators:
              #concat
              self.solver.assert_and_track(Implies(self.x[(p, '.')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [ self.z[(i, j, p, traceId)]\
                                                                        ==\
                                                                        Or(\
                                                                           [ And([self.z[(i, k, q, traceId)],\
                                                                            self.z[(k, j, q_prime, traceId)]])\
                                                                          for k in range(i,j+1)]\
                                                                           )\
                                                                         for i in range(trace.extendedTraceLength+1)\
                                                                         for j in range(i,trace.extendedTraceLength+1)]
                                                                       )\
                                                                   )\
                                                                  for q in range(p) for q_prime in range(p) ])),\
                                                     'semantics of concat operator for trace %d and depth %d'%(traceId, p))

        if '*' in self.Operators:
              #kleenestar
              self.solver.assert_and_track(Implies(self.x[(p, '*')],\
                                                    And([ Implies(self.l[(p, q)],\
                                                                   And(\
                                                                       [ self.z[(i, j, p, traceId)]\
                                                                        ==\
                                                                        Or((i==j),\
                                                                           Or([ And(self.z[(i, k, q, traceId)],\
                                                                                     self.z[(k, j, p, traceId)])\
                                                                                     for k in range(i+1,j+1)]\
                                                                             )\
                                                                          )\
                                                                         for i in range(trace.extendedTraceLength+1)\
                                                                         for j in range(i,trace.extendedTraceLength+1)]
                                                                       )\
                                                                   )\
                                                                  for q in range(p) ])),\
                                                     'semantics of Kleenestar operator for trace %d and depth %d'%(traceId, p))
        if '&' in self.Operators:
            self.solver.assert_and_track(Implies(self.x[(p, '&')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [ self.z[(i, j, p, traceId)]\
                                                                        ==\
                                                                        And(\
                                                                           [ self.z[(i, j, q, traceId)],\
                                                                            self.z[(i, j, q_prime, traceId)]]\
                                                                           )\
                                                                         for i in range(trace.extendedTraceLength+1)\
                                                                         for j in range(i,trace.extendedTraceLength+1)]\
                                                                       )\
                                                                   )\
                                                                  for q in range(p) for q_prime in range(p) ])),\
                                                     'semantics of regular conjunction for trace %d and depth %d'%(traceId, p))
        if '|' in self.Operators:
              self.solver.assert_and_track(Implies(self.x[(p, '|')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [self.z[(i, j, p, traceId)]\
                                                                        ==\
                                                                        Or(\
                                                                           [ self.z[(i, j, q, traceId)],\
                                                                            self.z[(i, j, q_prime, traceId)]]\
                                                                           )\
                                                                        for i in range(trace.extendedTraceLength+1)\
                                                                        for j in range(i,trace.extendedTraceLength+1)]\
                                                                       )\
                                                                   )\
                                                                  for q in range(p) for q_prime in range(p)])),\
                                                     'semantics of regular disjunction for trace %d and depth %d'%(traceId, p))
   
    def booleanOperatorSemantics(self, p, traceId, trace):
        if '|' in self.Operators:
            #disjunction
             self.solver.assert_and_track(Implies(self.x[(p, '|')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [self.y[(i, p, traceId)]\
                                                                        ==\
                                                                        Or(\
                                                                           [ self.y[(i, q, traceId)],\
                                                                            self.y[( i, q_prime, traceId)]]\
                                                                           )\
                                                                        for i in range(trace.lengthOfTrace)]\
                                                                       )\
                                                                   )\
                                                                  for q in range(self.regexDepth, p) for q_prime in range(self.regexDepth, p)])),\
                                                     'semantics of disjunction for trace %d and depth %d'%(traceId, p)) 

        if '&' in self.Operators:
              #conjunction
             self.solver.assert_and_track(Implies(self.x[(p, '&')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [ self.y[(i, p, traceId)]\
                                                                        ==\
                                                                        And(\
                                                                           [ self.y[(i, q, traceId)],\
                                                                            self.y[(i, q_prime, traceId)]]\
                                                                           )\
                                                                         for i in range(trace.lengthOfTrace)]\
                                                                       )\
                                                                   )\
                                                                  for q in range(self.regexDepth, p) for q_prime in range(self.regexDepth, p)])),\
                                                     'semantics of conjunction for trace %d and depth %d'%(traceId, p))
              
        if '->' in self.Operators:
               
              #implication
              self.solver.assert_and_track(Implies(self.x[(p, '->')],\
                                                    And([ Implies(\
                                                                   And(\
                                                                       [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                       ),\
                                                                   And(\
                                                                       [ self.y[(i, p, traceId)]\
                                                                        ==\
                                                                        Implies(\
                                                                          self.y[(i, q, traceId)],\
                                                                          self.y[(i, q_prime, traceId)]\
                                                                           )\
                                                                         for i in range(trace.lengthOfTrace)]\
                                                                       )\
                                                                   )\
                                                                  for q in range(self.regexDepth, p) for q_prime in range(self.regexDepth, p)])),\
                                                     'semantics of implication for trace %d and depth %d'%(traceId, p))
        
        if '!' in self.Operators:
              #negation
              self.solver.assert_and_track(Implies(self.x[(p, '!')],\
                                                   And([\
                                                       Implies(\
                                                                 self.l[(p,q)],\
                                                                 And([\
                                                                      self.y[(i, p, traceId)] == Not(self.y[(i, q, traceId)])\
                                                                      for i in range(trace.lengthOfTrace)\
                                                                      ])\
                                                                  )\
                                                       for q in range(self.regexDepth,p)\
                                                       ])\
                                                   ),\
                                           'semantics of negation for trace %d and depth %d' % (traceId, p)\
                                           )

    def finiteTemporalOperatorSemantics(self, p, traceId, trace):
        if 'G' in self.Operators:
            #globally                
            self.solver.assert_and_track(Implies(self.x[(p, 'G')],\
                                               And([\
                                                   Implies(\
                                                             self.l[(p,q)],\
                                                             And([\
                                                                  self.y[(i, p, traceId)] ==\
                                                                  And([self.y[(j, q, traceId)] for j in range(i, trace.lengthOfTrace) ])\
                                                                  for i in range(trace.lengthOfTrace)\
                                                                  ])\
                                                              )\
                                                   for q in range(self.regexDepth,p)\
                                                   ])\
                                               ),\
                                       'semantics of globally operator for trace %d and depth %d' % (traceId, p)\
                                       )

        if 'F' in self.Operators:                  
            #finally                
            self.solver.assert_and_track(Implies(self.x[(p, 'F')],\
                                               And([\
                                                   Implies(\
                                                             self.l[(p,q)],\
                                                             And([\
                                                                  self.y[(i, p, traceId)] ==\
                                                                  Or([self.y[(j, q, traceId)] for j in range(i, trace.lengthOfTrace) ])\
                                                                  for i in range(trace.lengthOfTrace)\
                                                                  ])\
                                                              )\
                                                   for q in range(self.regexDepth,p)\
                                                   ])\
                                               ),\
                                       'semantics of finally operator for trace %d and depth %d' % (traceId, p)\
                                       )


        if 'X' in self.Operators:
            #next 
            self.solver.assert_and_track(Implies(self.x[(p, 'X')],\
                                               And([\
                                                   Implies(\
                                                             self.l[(p,q)],\
                                                             And([self.y[(i, p, traceId)] ==\
                                                                  self.y[(trace.nextPos(i), q, traceId)]\
                                                                  for i in range(trace.lengthOfTrace-1)]+\
                                                                  [Not(self.y[(trace.lengthOfTrace-1, p, traceId)])])\
                                                              )\
                                                   for q in range(self.regexDepth,p)\
                                                   ])\
                                               ),\
                                       'semantics of neXt operator for trace %d and depth %d' % (traceId, p)\
                                       )

                                      
        if 'U' in self.Operators:
            #until
            self.solver.assert_and_track(Implies(self.x[(p, 'U')],\
                                              And([ Implies(\
                                                             And(\
                                                                 [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                 ),\
                                                             And([\
                                                                self.y[(i, p, traceId)] ==\
                                                                Or([\
                                                                    And(\
                                                                        [self.y[(j, q, traceId)] for j in range(i,k)]+\
                                                                        [self.y[(k, q_prime, traceId)]]\
                                                                        )\
                                                                    for k in range(i, trace.lengthOfTrace)\
                                                                    ])\
                                                                for i in range(trace.lengthOfTrace)]\
                                                                 )\
                                                             )\
                                                    for q in range(self.regexDepth, p) for q_prime in range(self.regexDepth, p)])),\
                                        'semantics of Until operator for trace %d and depth %d'%(traceId, p))


    def temporalOperatorSemantics(self, p, traceId, trace):
        if 'G' in self.Operators:
            #globally                
            self.solver.assert_and_track(Implies(self.x[(p, 'G')],\
                                               And([\
                                                   Implies(\
                                                             self.l[(p,q)],\
                                                             And([\
                                                                  self.y[(i, p, traceId)] ==\
                                                                  And([self.y[(futureTimestep, q, traceId)] for futureTimestep in trace.futurePos(i) ])\
                                                                  for i in range(trace.lengthOfTrace)\
                                                                  ])\
                                                              )\
                                                   for q in range(self.regexDepth,p)\
                                                   ])\
                                               ),\
                                       'semantics of globally operator for trace %d and depth %d' % (traceId, p)\
                                       )

        if 'F' in self.Operators:                  
            #finally                
            self.solver.assert_and_track(Implies(self.x[(p, 'F')],\
                                               And([\
                                                   Implies(\
                                                             self.l[(p,q)],\
                                                             And([\
                                                                  self.y[(i, p, traceId)] ==\
                                                                  Or([self.y[(futureTimestep, q, traceId)] for futureTimestep in trace.futurePos(i) ])\
                                                                  for i in range(trace.lengthOfTrace)\
                                                                  ])\
                                                              )\
                                                   for q in range(self.regexDepth,p)\
                                                   ])\
                                               ),\
                                       'semantics of finally operator for trace %d and depth %d' % (traceId, p)\
                                       )
      
        if 'X' in self.Operators:
            #next
            self.solver.assert_and_track(Implies(self.x[(p, 'X')],\
                                               And([\
                                                   Implies(\
                                                             self.l[(p,q)],\
                                                             And([\
                                                                  self.y[(i, p, traceId)] ==\
                                                                  self.y[(trace.nextPos(i), q, traceId)]\
                                                                  for i in range(trace.lengthOfTrace)\
                                                                  ])\
                                                              )\
                                                   for q in range(self.regexDepth,p)\
                                                   ])\
                                               ),\
                                       'semantics of neXt operator for trace %d and depth %d' % (traceId, p)\
                                       )
        if 'U' in self.Operators:
            #until
            self.solver.assert_and_track(Implies(self.x[(p, 'U')],\
                                              And([ Implies(\
                                                             And(\
                                                                 [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                 ),\
                                                             And([\
                                                                self.y[(i, p, traceId)] ==\
                                                                Or([\
                                                                    And(\
                                                                        [self.y[(futurePos, q, traceId)] for futurePos in trace.futurePos(i)[0:qIndex]]+\
                                                                        [self.y[(trace.futurePos(i)[qIndex], q_prime, traceId)]]\
                                                                        )\
                                                                    for qIndex in range(len(trace.futurePos(i)))\
                                                                    ])\
                                                                for i in range(trace.lengthOfTrace)]\
                                                                 )\
                                                             )\
                                                    for q in range(self.regexDepth, p) for q_prime in range(self.regexDepth, p)])),\
                                        'semantics of Until operator for trace %d and depth %d'%(traceId, p))

    def triggersOperatorSemantics(self, p, traceId, trace):
        if '|->' in self.Operators:
            #triggers
            self.solver.assert_and_track(Implies(self.x[(p, '|->')],\
                                              And([ Implies(\
                                                             And(\
                                                                 [self.l[(p, q)], self.r[(p, q_prime)]]\
                                                                 ),\
                                                             And(\
                                                                [self.y[(i, p, traceId)]\
                                                                  ==\
                                                                  And(\
                                                                    [Implies(self.z[(i, j, q, traceId)],\
                                                                      self.y[(trace.inTracePosition(j-1), q_prime, traceId)])
                                                                    for j in range(i+1,trace.extendedTraceLength+1)]\
                                                                     )\
                                                                for i in range(trace.lengthOfTrace)]\
                                                                 )\
                                                             )\
                                                            for q in range(self.regexDepth) for q_prime in range(self.regexDepth, p)])),\
                                               'semantics of triggers for trace %d and depth %d'%(traceId, p))    




    
    def reconstructWholeFormula(self, model):
        return self.reconstructFormula(self.formulaDepth-1, model)   
        
    

    def reconstructFormula(self, rowId, model):
        def getValue(row, vars):
            tt = [k[1] for k in vars if k[0] == row and model[vars[k]] == True]
            if len(tt) > 1:
                raise Exception("more than one true value")
            else:
                return tt[0]
        operator = getValue(rowId, self.x)

        if operator in (self.variables):
          if operator=='true' or operator=='epsilon':
            return Formula(operator)
          else:
            return Formula('x'+str(operator))
        elif operator in self.unaryOperators:
            leftChild = getValue(rowId, self.l)
            return Formula([operator, self.reconstructFormula(leftChild, model)])
        elif operator in self.binaryOperators:
            leftChild = getValue(rowId, self.l)
            rightChild = getValue(rowId, self.r)
            return Formula([operator, self.reconstructFormula(leftChild,model), self.reconstructFormula(rightChild, model)])
        