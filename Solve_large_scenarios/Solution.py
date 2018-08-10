from __future__ import print_function
import numpy as np
import sys, os
sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
import cplex
import lp_read_large_fourth_stage, PhiDivergence
import scipy.io as sio
from scipy.sparse import csr_matrix, find, coo_matrix, hstack, vstack

class set(object):
    def __init__(self, inLPModel, inPhi, inNumObsPerScen, inCutType='multi'):
        self.lpModel = inLPModel
        self.lpModel_parent = inLPModel[0]
        self.lpModel_children = inLPModel[1]
        self.phi = inPhi
        self.obs = inNumObsPerScen
        self.cutType = inCutType

        self.MASTER = 0
        self.TRUE = 1

        self.SLOPE = 0
        self.INTERCEPT = 1

        self.numVariables =self.lpModel_parent['obj'].size
        self.numScen =self.lpModel_parent['numScenarios']
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
        self.solution = np.zeros_like(self.lpModel_parent['obj'],dtype=float)
        self.lambda1 =np.float64(1)
        self.mu = np.float64(0)

        self.fval = np.float64(1)
        self.pi = np.zeros_like(self.lpModel_parent['rhs'],dtype=float)
        self.dj = np.zeros_like(self.lpModel_parent['obj'],dtype=float)


        self.theta = [-np.inf*np.ones(self.numTheta), -np.inf*np.ones(self.numTheta)]

        self.secondStageValues = -np.inf*np.ones(self.numScen)
        self.secondStageDuals = [[np.array([]) for _ in range(self.numScen)], [np.array([]) for _ in range(self.numScen)]]
        self.secondStageSolutions = [np.array([]) for _ in range(self.numScen)]
        self.secondStageValues_true = -np.inf * np.ones(self.numScen)

        self.muFeasible = np.nan
        self.muFeasible_true = np.nan

    def ResetSecondStages(self):
        self.secondStageValues = -np.inf * np.ones(self.numScen)
        self.secondStageDuals = [[np.array([]) for _ in range(self.numScen)],
                                 [np.array([]) for _ in range(self.numScen)]]
        self.secondStageSolutions = [np.array([]) for _ in range(self.numScen)]
        self.secondStageValues_true = -np.inf * np.ones(self.numScen)





    def SetFval(self, inFval):
        self.fval = inFval

    def SetPi(self, inPi):
        self.pi = inPi

    def SetDj(self, inDj):
        self.dj = inDj

    def Fval(self):
        return self.fval

    def Pi(self):
        return self.pi

    def Dj(self):
        return self.dj







    def SetX(self, inX):
        if np.array(inX).size != self.numVariables:
            raise Exception('X has size '+str(np.array(inX).size)+', should be '+str(self.numVariables))
        self.solution = inX

    def SetLambda(self, inLambda):
        if np.array(inLambda).size != 1:
            raise Exception('Lambda has size '+str(np.array(inLambda).size)+', should be 1')
        elif inLambda < 0:
            raise Exception('Lambda must be non-negative')
        self.lambda1 = inLambda

    def SetMu(self, inMu):
        if np.array(inMu).size != 1:
            raise Exception('Mu has size '+str(np.array(inMu).size)+', should be 1')
        self.mu = inMu

    def SetTheta(self, inTheta, inType):
        if np.array(inTheta).size != self.theta[0].size:
            raise Exception('Theta has size '+str(np.array(inTheta).size)+', should be '+str(self.numScen))
        if inType == 'master':
            typeN = self.MASTER
        elif inType == 'true':
            typeN = self.TRUE
        else:
            raise Exception('type must be ''master'' or ''true''')
        self.theta[typeN] = inTheta

    def SetSecondStageValue(self, inScen, inValue):
        if inScen < 0 or inScen > self.numScen-1:
            raise Exception('Scenario number must be between 0 and '+str(self.numScen-1))
        self.secondStageValues[inScen] = inValue

        if np.all(self.secondStageValues > -cplex.infinity):
            tolerBound = np.float64(1e-6) * np.maximum(self.phiLimit, 1)
            self.muFeasible = np.all(self.S() < self.phiLimit + (~self.isObserved * 1.0) * tolerBound)
            # self.muFeasible = np.all((self.secondStageValues - self.mu) < self.lambda1*self.phiLimit + (~self.isObserved * 1.0) * tolerBound)


    def S(self):
        if self.lambda1 != 0:
            # python gives numerical error, ex) (1e-6*(1-1e-3))/1e-6 != 1e-6*((1-1e-3)/1e-6)
            if np.isfinite(self.phiLimit) and self.lambda1<=np.float64(1e-6) and self.MuFeasible() == False:
                if np.max((self.secondStageValues - self.mu) / self.lambda1)>1:
                    return ((self.secondStageValues - np.max(self.secondStageValues))/self.lambda1 + self.phiLimit*np.float64(1-1e-3))
            return (self.secondStageValues - self.mu) / self.lambda1
        else:
            relDiff = (self.secondStageValues - self.mu) / np.abs(self.mu)
            outS = np.zeros_like(self.secondStageValues, dtype=float)
            tol = np.float64(1e-6)
            outS[relDiff < -tol] = -np.inf
            outS[relDiff > tol] = np.inf
            return outS

    ## For upper bound: Start
    def SetSecondStageValue_true(self, inScen, inValue):
        if inScen < 0 or inScen > self.numScen - 1:
            raise Exception('Scenario number must be between 0 and ' + str(self.numScen - 1))
        self.secondStageValues_true[inScen] = inValue
        if np.all(self.secondStageValues_true > -cplex.infinity):
            tolerBound = np.float64(1e-6) * np.maximum(self.phiLimit, 1)
            self.muFeasible_true = np.all(self.S_True() < self.phiLimit + (~self.isObserved * 1.0) * tolerBound)
            # self.muFeasible_true = np.all((self.secondStageValues_true - self.mu) < self.lambda1*self.phiLimit + (~self.isObserved * 1.0) * tolerBound)

    def S_True(self):
        if self.lambda1 != 0:
            # python gives numerical error, ex) (1e-6*(1-1e-3))/1e-6 != 1e-6*((1-1e-3)/1e-6)
            if np.isfinite(self.phiLimit) and self.lambda1<=np.float64(1e-6) and self.MuFeasibleTrue() == False:
                if np.max((self.secondStageValues_true - self.mu) / self.lambda1)>1:
                    return ((self.secondStageValues_true - np.max(self.secondStageValues_true))/self.lambda1 + self.phiLimit*np.float64(1-1e-3))
            return (self.secondStageValues_true - self.mu) / self.lambda1
        else:
            relDiff = (self.secondStageValues_true - self.mu) / np.abs(self.mu)
            outS = np.zeros_like(self.secondStageValues_true,dtype=float)
            tol = np.float64(1e-6)
            outS[relDiff < -tol] = -np.inf
            outS[relDiff >  tol] = np.inf
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
        self.secondStageDuals[type][inScen] = inDual

    def SetSecondStageSolution(self, inScen, inSol):
        if inScen < 0 or inScen > self.numScen-1:
            raise Exception('Scenario number must be between 0 and '+str(self.numScen-1))
        self.secondStageSolutions[inScen] = inSol

    def X(self):
        return self.solution

    def Lambda(self):
        return self.lambda1

    def Mu(self):
        return self.mu

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


