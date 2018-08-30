import sys
import scipy.io as sio
import numpy as np
from scipy.stats import chi2
import warnings, copy, cplex
from cplex.exceptions import CplexError
import Solution

if sys.platform == "darwin":
    sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
elif sys.platform == "win32":
    sys.path.append("C:\Program Files\IBM\ILOG\CPLEX_Studio128\cplex\python\3.6\x64_win64")
else:
    raise Exception('What is your platform?')


class set(object):
    def __init__(self, inLPModel, inPhi, inNumObsPerScen, inRho, inOptimizer='cplex', inCutType='multi'):
        self.objectiveScale = np.float64(1)
        self.lambdaLowerBound = np.float64(1e-6)

        self.lpModel = inLPModel
        self.phi = inPhi
        self.numObsPerScen = np.array(inNumObsPerScen)
        self.numObsTotal = self.lpModel['numScenarios']

        if inRho < 0:
            phi2deriv = np.float64(self.phi.SecondDerivativeAt1())
            if np.isfinite(phi2deriv) and phi2deriv > 0:
                inRho = (phi2deriv / (2 * self.numObsTotal)) * chi2.ppf(0.95, self.lpModel.numScenarios - 1)
            else:
                raise Exception('Second derivative of phi(t) does not allow for automatically setting rho')

        # if self.lpModel.numStages != 2:
        #     raise Exception('Must use a 2 Stage LP')
        if len(inNumObsPerScen) != self.lpModel['numScenarios']:
            raise Exception('Size of observations differs from number of scenarios')

        self.rho = inRho
        self.phi.SetComputationLimit(self.numObsPerScen, self.rho)

        self.optimizer = inOptimizer

        self.LAMBDA = self.lpModel['obj'].size
        self.MU = self.LAMBDA + 1

        if inCutType == "multi":
            thetaOffset = np.arange(1, self.lpModel['numScenarios'] + 1)
        elif inCutType == "single":
            thetaOffset = 1
        else:
            raise Exception('Cut types available: single and multi')
        self.THETA = self.MU + thetaOffset

        self.SLOPE = 0
        self.INTERCEPT = 1

        self.candidateSolution = Solution.set(self.lpModel, self.phi, self.numObsPerScen, self.lambdaLowerBound, inCutType='multi')

    # InitializeBenders:
        self.objectiveCutsMatrix = np.array([], dtype=np.float64).reshape(0, self.lpModel['obj'].size + 2 + self.THETA.size)
        self.objectiveCutsRHS = np.array([])
        for i in range(self.THETA.size):
            objectiveCutsMatrix_tmp = np.zeros((self.lpModel['obj'].size + 2 + self.THETA.size), dtype=np.float64)
            objectiveCutsMatrix_tmp[self.THETA[i]] = -1
            objectiveCutsRHS_tmp = np.float64(0)
            self.objectiveCutsMatrix = np.vstack([self.objectiveCutsMatrix, objectiveCutsMatrix_tmp])
            self.objectiveCutsRHS = np.append(self.objectiveCutsRHS, objectiveCutsRHS_tmp)

        self.feasibilityCutsMatrix = np.array([], dtype=np.float64).reshape(0, self.lpModel['obj'].size + 2 + self.THETA.size)
        self.feasibilityCutsRHS = np.array([])



    def SubProblem(self, x_parent):
        self.ResetSecondStageSolutions()
        cMaster = self.GetMasterc()
        AMaster = self.GetMasterA()
        bMaster = self.GetMasterb()
        lMaster = self.GetMasterl()
        uMaster = self.GetMasteru()
        senseMaster = self.GetMastersense()
        BMaster = self.GetMasterB()
        CutMatrix = np.vstack((self.objectiveCutsMatrix, self.feasibilityCutsMatrix))
        rows, cols = CutMatrix.nonzero()
        idx = list(zip(rows, cols))
        CutMatrix_coefficients = [(int(rows[i] + bMaster.size), int(cols[i]), CutMatrix[idx[i]]) for i in
                                  range(len(idx))]
        CutMatrixRHS = np.hstack((self.objectiveCutsRHS, self.feasibilityCutsRHS))
        CutSense = ["L"] * CutMatrixRHS.size

        try:
            mdl_sub = cplex.Cplex()
            mdl_sub.parameters.lpmethod.set(mdl_sub.parameters.lpmethod.values.auto)
            mdl_sub.variables.add(obj=cMaster, lb=lMaster, ub=uMaster)
            mdl_sub.linear_constraints.add(senses=senseMaster + CutSense,
                                              rhs=np.hstack((bMaster + BMaster * x_parent, CutMatrixRHS)))
            mdl_sub.linear_constraints.set_coefficients(list(AMaster) + CutMatrix_coefficients)
            mdl_sub.set_results_stream(None)
            mdl_sub.solve()

            solution = mdl_sub.solution
            exitFlag = solution.get_status()

            currentCandidate = np.array(solution.get_values())
            fval = np.float64(solution.get_objective_value())
            pi = np.array(solution.get_dual_values())



            if exitFlag == mdl_sub.solution.status.unbounded:
                raise Exception("Model is unbounded")
            if exitFlag == mdl_sub.solution.status.infeasible:
                raise Exception("Model is infeasible")
            if exitFlag == mdl_sub.solution.status.infeasible_or_unbounded:
                raise Exception("Model is infeasible or unbounded")

        except CplexError as exc:
            print(exc)

        self.candidateSolution.SetX(currentCandidate[range(currentCandidate.size - 2 - self.THETA.size)])
        self.candidateSolution.SetLambda(currentCandidate[self.LAMBDA])
        self.candidateSolution.SetMu(currentCandidate[self.MU])
        self.candidateSolution.SetMu_true(currentCandidate[self.MU])
        self.candidateSolution.SetTheta(currentCandidate[self.THETA], 'master')
        self.candidateSolution.SetFval(fval)
        self.candidateSolution.SetPi(pi)

        return exitFlag

    def SetChildrenStage(self, child_philp):
        self.candidateSolution.ResetSecondStages()
        for scenarioNum in range(self.lpModel['numScenarios']):
            BMaster = child_philp[scenarioNum].GetMasterB()
            bMaster = child_philp[scenarioNum].GetMasterb()
            y = child_philp[scenarioNum].candidateSolution.X()
            fval = child_philp[scenarioNum].candidateSolution.Fval()
            pi = child_philp[scenarioNum].candidateSolution.Pi()
            xLocal = self.candidateSolution.X()

            self.candidateSolution.SetSecondStageSolution(scenarioNum, y)
            self.candidateSolution.SetSecondStageValue(scenarioNum, fval)
            self.candidateSolution.SetSecondStageDual(scenarioNum, pi[:bMaster.size]*BMaster, 'slope')
            self.candidateSolution.SetSecondStageDual(scenarioNum, fval - np.matmul(pi[:bMaster.size]*BMaster, xLocal), 'int')


    def GenerateCuts(self):
        if ~self.candidateSolution.MuFeasible():
            self.GenerateFeasibilityCut()
            self.FindFeasibleMu()
        self.FindExpectedSecondStage()
        self.GenerateObjectiveCut()

    def GenerateObjectiveCut(self):
        xLocal = self.candidateSolution.X()
        lambdaLocal = self.candidateSolution.Lambda()
        muLocal = self.candidateSolution.Mu()

        lambdaZero = False
        if lambdaLocal == 0:
            lambdaZero = True
            lower = self.GetMasterl()
            self.candidateSolution.SetLambda(lower[self.LAMBDA])
            # self.candidateSolution.SetLambda(np.float64(1e-6))
            lambdaLocal = self.candidateSolution.Lambda()
        s = self.candidateSolution.S()
        conjVals = self.phi.Conjugate(s)
        conjDerivs = self.phi.ConjugateDerivative(s)
        intermediateSlope = np.array([np.hstack((conjDerivs[ii] * self.candidateSolution.SecondStageSlope(ii),
                                                 np.array(self.rho + conjVals[ii] - conjDerivs[ii] * s[ii]),
                                                 np.array(1 - conjDerivs[ii]))) for ii in
                                      range(self.lpModel['numScenarios'])])
        intermediateSlope[np.where(self.numObsPerScen == 0)[0]] = 0
        if self.THETA.size == self.lpModel['numScenarios']:
            slope = intermediateSlope
        elif self.THETA.size == 1:
            slope = np.matmul(self.numObsPerScen / self.numObsTotal, intermediateSlope)
        else:
            raise Exception('Wrong size of obj.THETA.  This should not happen')
        intercept = self.candidateSolution.ThetaTrue() - np.matmul(slope, np.transpose(
            np.hstack((xLocal, lambdaLocal, muLocal))))
        self.objectiveCutsMatrix = np.vstack([self.objectiveCutsMatrix, np.hstack((slope, -np.eye(self.THETA.size)))])
        self.objectiveCutsRHS = np.append(self.objectiveCutsRHS, -intercept)


        if lambdaZero:
            self.candidateSolution.SetLambda(0)

    def GenerateFeasibilityCut(self):
        hIndex = np.argmax(self.candidateSolution.SecondStageValues())
        limit = np.minimum(self.phi.limit(), self.phi.computationLimit)
        feasSlope = np.concatenate(
            [self.candidateSolution.SecondStageSlope(hIndex), -limit, np.array([-1],dtype=float), np.zeros(self.THETA.size)])
        feasInt = self.candidateSolution.SecondStageIntercept(hIndex)
        self.feasibilityCutsMatrix = np.vstack([self.feasibilityCutsMatrix, feasSlope])
        self.feasibilityCutsRHS = np.append(self.feasibilityCutsRHS, -feasInt)

    def FindFeasibleMu(self):
        lambdaLocal = self.candidateSolution.Lambda()
        limit = np.minimum(self.phi.limit(), self.phi.computationLimit)
        localValues = self.candidateSolution.SecondStageValues()
        mu = np.float64(np.amax(localValues) - limit * np.float64(1 - 1e-3)* lambdaLocal)
        self.candidateSolution.SetMu(mu)


    # needed for upper bound
    def FindFeasibleMu_true(self):
        lambdaLocal = self.candidateSolution.Lambda()
        limit = np.minimum(self.phi.limit(), self.phi.computationLimit)
        localValues = self.candidateSolution.SecondStageValues_true()
        mu = np.float64(np.max(localValues) - limit * np.float64(1 - 1e-3) * lambdaLocal)
        self.candidateSolution.SetMu_true(mu)

    # needed for upper bound
    def MuFeasible_for_upperbound(self):
        if ~self.candidateSolution.MuFeasibleTrue():
            self.FindFeasibleMu_true()

    def FindExpectedSecondStage(self):
        inSolution = self.candidateSolution
        if np.isnan(inSolution.MuFeasible()):
            raise Exception(
                'Must determine whether candidate mu is feasible before finding expected second stage value')
        if not all(inSolution.SecondStageValues() > -cplex.infinity):
            raise Exception('Must set second stage values before calculating expectation')
        lambdaLocal = inSolution.Lambda()
        muLocal = inSolution.Mu()
        rawTheta = muLocal + lambdaLocal*self.rho + lambdaLocal*self.phi.Conjugate(inSolution.S())

        rawTheta[np.where(self.numObsPerScen == 0)[0]] = 0
        rawTheta[np.where(rawTheta == cplex.infinity)[0]] = cplex.infinity
        if not all(np.isreal(rawTheta)):
            raise Exception('Possible scaling error')
        if not all(np.isfinite(rawTheta)):
            raise Exception('Nonfinite theta, lambda = ' + str(lambdaLocal))

        if self.THETA.size == self.lpModel['numScenarios']:
            inSolution.SetTheta(rawTheta, 'true')
        elif self.THETA.size == 1:
            inSolution.SetTheta(np.dot(self.numObsPerScen / self.numObsTotal, rawTheta), 'true')
        else:
            raise Exception('Wrong size of obj.THETA.  This should not happen')
    # needed for upper bound
    def Get_h_True(self):
        inSolution = self.candidateSolution
        cLocal = self.lpModel['obj'] * self.objectiveScale
        xLocal = inSolution.X()
        muLocal = inSolution.Mu_true()
        lambdaLocal = inSolution.Lambda()
        rhoLocal = self.rho
        SLocal = inSolution.S_True()
        q = self.numObsPerScen / self.numObsTotal
        h_True = np.matmul(cLocal, xLocal) \
                 + np.matmul(q,(muLocal + rhoLocal*lambdaLocal + lambdaLocal*self.phi.Conjugate(SLocal)))
        return h_True

    def ResetSecondStageSolutions(self):
        self.candidateSolution.ResetSecondStages()
        self.newSolutionAccepted = False
        self.zLowerUpdated = False

    def CalculateProbability(self):
        q = self.numObsPerScen / self.numObsTotal
        s = self.bestSolution.S()
        self.pWorst = np.multiply(q, self.phi.ConjugateDerivative(s))
        self.pWorst[np.where(q == 0)[0]] = 0
        limitCases = np.abs(s - self.phi.limit()) <= np.float64(1e-6)
        if np.count_nonzero(limitCases) > 0:
            self.pWorst[limitCases] = (1 - np.sum(self.pWorst[np.logical_not(limitCases)])) / np.count_nonzero( limitCases)
            # self.pWorst[limitCases] = (2 * q[limitCases] + self.rho - np.sqrt((2 * q[limitCases] * self.rho) ** 2 - 4 * q[limitCases] ** 2)) / 2
        self.calculatedDivergence = np.sum(self.phi.Contribution(self.pWorst, q))

    def GetMasterc(self):
        cOut = np.append(self.lpModel['obj'], np.zeros(2 + self.THETA.size)) * self.objectiveScale
        if self.THETA.size == self.lpModel['numScenarios']:
            cOut[self.THETA] = self.numObsPerScen / self.numObsTotal
        elif self.THETA.size == 1:
            cOut[self.THETA] = 1
        else:
            raise Exception('Wrong size of obj.THETA.  This should not happen')
        return cOut

    def GetMasterA(self):
        AOut = self.lpModel['A_coef']
        return AOut

    def GetMasterB(self):
        BOut = self.lpModel['B']
        return BOut

    def GetMasterb(self):
        bOut = self.lpModel['rhs']
        return bOut

    def GetMasterl(self):
        lOut = np.append(self.lpModel['lb'], np.zeros(2 + self.THETA.size))
        lOut[self.LAMBDA] = self.lambdaLowerBound
        lOut[self.MU] = -cplex.infinity
        lOut[self.THETA] = -cplex.infinity
        return lOut

    def GetMasteru(self):
        uOut = np.append(self.lpModel['ub'], np.zeros(2 + self.THETA.size))
        uOut[self.LAMBDA] = cplex.infinity
        uOut[self.MU] = cplex.infinity
        uOut[self.THETA] = cplex.infinity
        return uOut

    def GetMastersense(self):
        uOut = self.lpModel['sense']
        return uOut




if __name__ == "__main__":
    mat_data = sio.loadmat(os.getcwd() + "/mat_data/news.mat")
    lp = lp_reader.set(mat_data)
    alpha = 0.01
    inPhi = PhiDivergence.set('burg')
    obs = lp.first['obs']
    inRho = inPhi.Rho(alpha, obs)
    philp = set([lp.first, lp.second], inPhi, obs, inRho)
