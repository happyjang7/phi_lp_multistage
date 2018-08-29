import numpy as np
import sys
if sys.platform == "darwin":
    sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
elif sys.platform == "win32":
    sys.path.append("C:\Program Files\IBM\ILOG\CPLEX_Studio128\cplex\python\3.6\x64_win64")
else:
    raise Exception('What is your platform?')

import cplex

class set(object):
    def __init__(self, inLPModel, inPhi, inNumObsPerScen, lambdaLower, inCutType='multi'):
        self.lambdaLowerBound = lambdaLower
        self.lpModel = inLPModel
        self.phi = inPhi
        self.obs = inNumObsPerScen
        self.cutType = inCutType

        self.MASTER = 0
        self.TRUE = 1

        self.SLOPE = 0
        self.INTERCEPT = 1

        self.numVariables =self.lpModel['obj'].size
        self.numScen =self.lpModel['numScenarios']
        self.phiLimit = np.minimum(self.phi.limit(), self.phi.computationLimit)
        self.isObserved = self.obs > 0

        if inCutType == "single":
            self.numTheta = 1
        elif inCutType == "multi":
            self.numTheta = self.numScen
        else:
            raise Exception('Cut types available: single and multi')

        self.Reset()

    def Reset(self):
        self.solution = np.zeros_like(self.lpModel['obj'],dtype=float)
        self.lambda1 =np.float64(0)
        self.mu = np.float64(0)
        self.mu_true = np.float64(0)

        self.fval = np.float64(0)
        self.pi = np.zeros_like(self.lpModel['rhs'],dtype=float)
        self.theta = [-cplex.infinity*np.ones(self.numTheta), -cplex.infinity*np.ones(self.numTheta)]

        self.secondStageValues = -cplex.infinity*np.ones(self.numScen)
        self.secondStageDuals = [[np.array([]) for _ in range(self.numScen)], [np.array([]) for _ in range(self.numScen)]]
        self.secondStageSolutions = [np.array([]) for _ in range(self.numScen)]
        self.secondStageValues_true = -cplex.infinity * np.ones(self.numScen)

        self.muFeasible = False
        self.muFeasible_true = False

    def ResetSecondStages(self):
        self.secondStageValues = -cplex.infinity * np.ones(self.numScen)
        self.secondStageDuals = [[np.array([]) for _ in range(self.numScen)],
                                 [np.array([]) for _ in range(self.numScen)]]
        self.secondStageSolutions = [np.array([]) for _ in range(self.numScen)]
        self.secondStageValues_true = -cplex.infinity * np.ones(self.numScen)


    def SetFval(self, inFval):
        self.fval = np.float64(inFval)

    def SetPi(self, inPi):
        self.pi = np.array(inPi,dtype=float)

    def Fval(self):
        return self.fval

    def Pi(self):
        return self.pi



    def SetX(self, inX):
        if np.array(inX).size != self.numVariables:
            raise Exception('X has size '+str(np.array(inX).size)+', should be '+str(self.numVariables))
        self.solution = np.array(inX,dtype=float)

    def SetLambda(self, inLambda):
        if np.array(inLambda).size != 1:
            raise Exception('Lambda has size '+str(np.array(inLambda).size)+', should be 1')
        elif inLambda < 0:
            raise Exception('Lambda must be non-negative')
        self.lambda1 = np.float64(inLambda)

    def SetMu(self, inMu):
        if np.array(inMu).size != 1:
            raise Exception('Mu has size '+str(np.array(inMu).size)+', should be 1')
        self.mu = np.float64(inMu)

    def SetMu_true(self, inMu):
        if np.array(inMu).size != 1:
            raise Exception('Mu has size '+str(np.array(inMu).size)+', should be 1')
        self.mu_true = np.float64(inMu)

    def SetTheta(self, inTheta, inType):
        if np.array(inTheta).size != self.theta[0].size:
            raise Exception('Theta has size '+str(np.array(inTheta).size)+', should be '+str(self.numScen))
        if inType == 'master':
            typeN = self.MASTER
        elif inType == 'true':
            typeN = self.TRUE
        else:
            raise Exception('type must be ''master'' or ''true''')
        self.theta[typeN] = np.array(inTheta,dtype=float)

    def SetSecondStageValue(self, inScen, inValue):
        if inScen < 0 or inScen > self.numScen-1:
            raise Exception('Scenario number must be between 0 and '+str(self.numScen-1))
        self.secondStageValues[inScen] = np.array(inValue,dtype=float)

        if np.all(self.secondStageValues > -cplex.infinity):
            self.muFeasible = np.all((self.secondStageValues-self.mu)/self.lambda1 < self.phiLimit)


    def S(self):
        if self.lambda1 >  0:
            if self.phiLimit==1 and (np.amax(self.secondStageValues) - self.mu) / self.lambda1 >self.phiLimit :
                tmp_S2 = (self.secondStageValues -np.amax(self.secondStageValues)+ self.phiLimit * np.float64(1 - 1e-3) * self.lambda1) / self.lambda1
                return tmp_S2
            return (self.secondStageValues - self.mu) / self.lambda1
        else:
            relDiff = (self.secondStageValues - self.mu) / np.abs(self.mu)
            outS = np.zeros_like(self.secondStageValues, dtype=float)
            tol = np.float64(1e-6)
            outS[relDiff < -tol] = -cplex.infinity
            outS[relDiff > tol] = cplex.infinity
            return outS

    ## For upper bound: Start
    def SetSecondStageValue_true(self, inScen, inValue):
        if inScen < 0 or inScen > self.numScen - 1:
            raise Exception('Scenario number must be between 0 and ' + str(self.numScen - 1))
        self.secondStageValues_true[inScen] = np.array(inValue,dtype=float)
        if np.all(self.secondStageValues_true > -cplex.infinity):
            self.muFeasible_true = np.all((self.secondStageValues_true - self.mu_true)/self.lambda1 <  self.phiLimit)

    def S_True(self):
        if self.lambda1 > 0:
            if self.phiLimit==1 and (np.amax(self.secondStageValues_true) - self.mu_true) / self.lambda1 > self.phiLimit:
                tmp_S2 = (self.secondStageValues_true -np.amax(self.secondStageValues_true)+ self.phiLimit * np.float64(1 - 1e-3) * self.lambda1) / self.lambda1
                return tmp_S2
            return (self.secondStageValues_true - self.mu_true) / self.lambda1
        else:
            relDiff = (self.secondStageValues_true - self.mu_true) / np.abs(self.mu_true)
            outS = np.zeros_like(self.secondStageValues_true,dtype=float)
            tol = np.float64(1e-6)
            outS[relDiff < -tol] = -cplex.infinity
            outS[relDiff >  tol] = cplex.infinity
            return outS
    ## For upper bound: End


    def SetSecondStageDual(self, inScen, inDual, inType):
        if inScen < 0 or inScen > self.numScen-1:
            raise Exception('Scenario number must be between 0 and '+str(self.numScen-1))
        if inType == 'slope':
            type = self.SLOPE
        elif inType == 'int':
            type = self.INTERCEPT
        else:
            raise Exception('type must be ''slope'' or ''int''')
        self.secondStageDuals[type][inScen] = np.array(inDual,dtype=float)

    def SetSecondStageSolution(self, inScen, inSol):
        if inScen < 0 or inScen > self.numScen-1:
            raise Exception('Scenario number must be between 0 and '+str(self.numScen-1))
        self.secondStageSolutions[inScen] = np.array(inSol,dtype=float)

    def X(self):
        return self.solution

    def Lambda(self):
        return self.lambda1

    def Mu(self):
        return self.mu

    def Mu_true(self):
        return self.mu_true

    def ThetaMaster(self):
        return self.theta[self.MASTER]

    def ThetaTrue(self):
        return self.theta[self.TRUE]


    def Limit(self):
        return self.phiLimit

    def SecondStageValues(self):
        return self.secondStageValues

    def SecondStageValues_true(self):
        return self.secondStageValues_true

    def MuFeasible(self):
        return self.muFeasible

    def MuFeasibleTrue(self):
        return self.muFeasible_true

    def SecondStageSlope(self, inScen):
        return self.secondStageDuals[self.SLOPE][inScen]

    def SecondStageIntercept(self, inScen):
        return self.secondStageDuals[self.INTERCEPT][inScen]

    def SecondStageSolution(self, inScen):
        return self.secondStageSolutions[inScen]


