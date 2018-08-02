'''
PhiLP solves a 2 Stage ﻿Data-Driven Stochastic Programming Using Phi-Divergences with Recourse (PhiLP-2)
via the modified Bender's Decomposition proposed by David Love.
This class uses the lp.set class to create and store the LP data.
required modules
1. numpy, scipy.stats
2. warnings, copy
3. cplex, cplex.exceptions, cplex.callbacks
4. lp, ExtensiveForm, PhiDivergence, Solution
'''
import sys, os
import scipy.io as sio
# from scipy.sparse import csr_matrix, find, coo_matrix, hstack, vstack
import numpy as np
from scipy.stats import chi2
import warnings, copy
import cplex
from cplex.exceptions import CplexError
from cplex.callbacks import SimplexCallback
import lp_read, PhiDivergence, Solution
import copy

if sys.platform == "darwin":
    sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
elif sys.platform == "win32":
    sys.path.append("C:\Program Files\IBM\ILOG\CPLEX_Studio128\cplex\python\3.6\x64_win64")
else:
    raise Exception('What is your platform?')


class MyCallback(SimplexCallback):
    def __call__(self):
        print("CB Iteration ", self.get_num_iterations(), " : ", end=' ')
        if self.is_primal_feasible():
            print("CB Objective = ", self.get_objective_value())
        else:
            print("CB Infeasibility measure = ",
                  self.get_primal_infeasibility())


class set(object):
    def __init__(self, inLPModel, inPhi, inNumObsPerScen, inRho, inOptimizer='cplex', inCutType='multi'):

        self.lambdaLowerBound = np.float64(1e-6)
        # self.lambdaLowerBound = np.float64(0)

        self.lpModel = inLPModel
        self.lpModel_parent = inLPModel[0]
        self.lpModel_children = inLPModel[1]
        self.phi = inPhi
        self.numObsPerScen = np.array(inNumObsPerScen)
        self.numObsTotal = np.sum(self.numObsPerScen)

        if inRho < 0:
            phi2deriv = np.float64(self.phi.SecondDerivativeAt1())
            if np.isfinite(phi2deriv) and phi2deriv > 0:
                inRho = (phi2deriv / (2 * self.numObsTotal)) * chi2.ppf(0.95, self.lpModel.numScenarios - 1)
            else:
                raise Exception('Second derivative of phi(t) does not allow for automatically setting rho')

        # if self.lpModel.numStages != 2:
        #     raise Exception('Must use a 2 Stage LP')
        if len(inNumObsPerScen) != self.lpModel_parent['numScenarios']:
            raise Exception('Size of observations differs from number of scenarios')

        self.rho = inRho
        self.phi.SetComputationLimit(self.numObsPerScen, self.rho)

        self.optimizer = inOptimizer

        self.objectiveTolerance = np.float64(1e-6)
        self.probabilityTolerance = np.float64(5e-3)

        self.LAMBDA = self.lpModel_parent['obj'].size
        self.MU = self.LAMBDA + 1

        if inCutType == "multi":
            thetaOffset = np.arange(1, self.lpModel_parent['numScenarios'] + 1)
        elif inCutType == "single":
            thetaOffset = 1
        else:
            raise Exception('Cut types available: single and multi')
        self.THETA = self.MU + thetaOffset

        self.SLOPE = 0
        self.INTERCEPT = 1

        self.candidateSolution = Solution.set(self.lpModel, self.phi, self.numObsPerScen, inCutType='multi')

    def InitializeBenders(self, type='1-2stage', x_parent=0):
        self.objectiveCutsMatrix = np.zeros((self.lpModel_parent['obj'].size + 2 + self.THETA.size), dtype=np.float64)
        self.objectiveCutsMatrix[self.THETA] = -1
        self.objectiveCutsRHS = np.array([0])
        self.feasibilityCutsMatrix = np.array([], dtype=np.float64).reshape(0, self.lpModel_parent['obj'].size + 2 + self.THETA.size)
        self.feasibilityCutsRHS = np.array([])
        self.objectiveScale = np.float64(1)

        exitFlag, x0, fval, pi, dj = self.SolveMasterProblem_Initial(type, x_parent)

        if exitFlag != 1:
            raise Exception('Could not solve first stage LP')
        cols = self.lpModel_parent['obj'].size
        x0 = x0[0:cols]

        self.candidateSolution.SetX(x0)
        self.candidateSolution.SetFval(fval)
        self.candidateSolution.SetPi(pi)
        self.candidateSolution.SetDj(dj)
        self.candidateSolution.SetLambda(np.float64(1))
        self.candidateSolution.SetMu(np.float64(0))

        if type == '1-2stage':
            self.zLower = -np.inf
            self.zUpper = np.inf
            self.bestSolution = np.array([])
            self.secondBestSolution = np.array([])
            self.newSolutionAccepted = True



    def SolveMasterProblem_Initial(self, type='1-2stage', x_parent=0):
        self.ResetSecondStageSolutions()
        cMaster = self.GetMasterc()
        AMaster = self.GetMasterA()
        bMaster = self.GetMasterb()
        lMaster = self.GetMasterl()
        uMaster = self.GetMasteru()
        senseMaster = self.GetMastersense()
        if type == '1-2stage':
            BMaster = 0
        elif not type == '1-2stage':
            BMaster = self.GetMasterB()

        CutMatrix = np.vstack((self.objectiveCutsMatrix, self.feasibilityCutsMatrix))
        rows, cols = CutMatrix.nonzero()
        idx = list(zip(rows, cols))
        CutMatrix_coefficients = [(int(rows[i] + bMaster.size), int(cols[i]), CutMatrix[idx[i]]) for i in range(len(idx))]
        CutMatrixRHS = np.hstack((self.objectiveCutsRHS, self.feasibilityCutsRHS))
        CutSense = ["L"] * CutMatrixRHS.size

        try:
            mdl_master = cplex.Cplex()
            mdl_master.set_problem_name("mdl_master")
            mdl_master.parameters.lpmethod.set(mdl_master.parameters.lpmethod.values.auto)
            mdl_master.objective.set_sense(mdl_master.objective.sense.minimize)
            mdl_master.variables.add(obj=cMaster, lb=lMaster, ub=uMaster)
            mdl_master.linear_constraints.add(senses=senseMaster + CutSense,
                                              rhs=np.hstack((bMaster + BMaster * x_parent, CutMatrixRHS)))
            mdl_master.linear_constraints.set_coefficients(list(AMaster) + CutMatrix_coefficients)
            mdl_master.set_results_stream(None)
            mdl_master.solve()
            mdl_master.register_callback(MyCallback)

            solution = mdl_master.solution

            exitFlag = solution.get_status()
            x = np.array(solution.get_values())
            fval = np.float64(solution.get_objective_value())
            pi = np.array(solution.get_dual_values())
            dj = np.array(solution.get_reduced_costs())
        except CplexError as exc:
            print(exc)

        return (exitFlag, x, fval, pi, dj)


    def SolveMasterProblem_forward(self, type='1-2stage', x_parent=0):
        self.ResetSecondStageSolutions()
        cMaster = self.GetMasterc()
        AMaster = self.GetMasterA()
        bMaster = self.GetMasterb()
        lMaster = self.GetMasterl()
        uMaster = self.GetMasteru()
        senseMaster = self.GetMastersense()
        if type == '1-2stage':
            BMaster = 0
        elif not type == '1-2stage':
            BMaster = self.GetMasterB()
        CutMatrix = np.vstack((self.objectiveCutsMatrix, self.feasibilityCutsMatrix))
        rows, cols = CutMatrix.nonzero()
        idx = list(zip(rows, cols))
        CutMatrix_coefficients = [(int(rows[i] + bMaster.size), int(cols[i]), CutMatrix[idx[i]]) for i in
                                  range(len(idx))]
        CutMatrixRHS = np.hstack((self.objectiveCutsRHS, self.feasibilityCutsRHS))
        CutSense = ["L"] * CutMatrixRHS.size

        if type == '1-2stage':
            currentBest = self.GetDecisions(self.bestSolution)

        try:
            mdl_master = cplex.Cplex()
            mdl_master.set_problem_name("mdl_master")
            mdl_master.parameters.lpmethod.set(mdl_master.parameters.lpmethod.values.auto)
            mdl_master.objective.set_sense(mdl_master.objective.sense.minimize)
            mdl_master.variables.add(obj=cMaster, lb=lMaster, ub=uMaster)
            mdl_master.linear_constraints.add(senses=senseMaster + CutSense,
                                              rhs=np.hstack((bMaster + BMaster * x_parent, CutMatrixRHS)))
            mdl_master.linear_constraints.set_coefficients(list(AMaster) + CutMatrix_coefficients)

            mdl_master.set_results_stream(None)
            mdl_master.solve()
            mdl_master.register_callback(MyCallback)

            solution = mdl_master.solution

            exitFlag = solution.get_status()

            currentCandidate = np.array(solution.get_values())
            fval = np.float64(solution.get_objective_value())
            pi = np.array(solution.get_dual_values())
            dj = np.array(solution.get_reduced_costs())
        except CplexError as exc:
            print(exc)
        if currentCandidate[self.LAMBDA] < lMaster[self.LAMBDA]:
            if self.phi.Conjugate(-np.inf) == -np.inf:
                currentCandidate[self.LAMBDA] = lMaster[self.LAMBDA]
            elif currentCandidate[self.LAMBDA] < 0:
                currentCandidate[self.LAMBDA] = 0
            self.lambdaLowerBound = self.lambdaLowerBound * np.float64(1e-3)
        self.candidateSolution.SetX(currentCandidate[range(currentCandidate.size - 2 - self.THETA.size)])
        self.candidateSolution.SetLambda(currentCandidate[self.LAMBDA])
        self.candidateSolution.SetMu(currentCandidate[self.MU])
        self.candidateSolution.SetTheta(currentCandidate[self.THETA], 'master')

        self.candidateSolution.SetFval(fval)
        self.candidateSolution.SetPi(pi)
        self.candidateSolution.SetDj(dj)


        if type == '1-2stage':
            if exitFlag != 1 or np.matmul(cMaster, currentBest - currentCandidate) < -1e-4 * np.matmul(cMaster,
                                                                                                       currentBest):
                if exitFlag == 1:
                    print('Current Best solution value:', str(np.matmul(cMaster, currentBest)),
                          ', Candidate solution value:', str(np.matmul(cMaster, currentCandidate)))
                    exitFlag = -50
                return exitFlag

            if not (exitFlag != 1 or np.matmul(cMaster, currentBest - currentCandidate) >= -1e-4 * np.matmul(cMaster,
                                                                                                             currentBest)):
                raise Exception('Actual objective drop = ' + str(np.matmul(cMaster, (currentBest - currentCandidate))))

        return exitFlag

    def SetChildrenStage_backward(self, child_philp):
        self.candidateSolution.ResetSecondStages()
        for scenarioNum in range(self.lpModel_parent['numScenarios']):
            BMaster = child_philp[scenarioNum].GetMasterB()
            bMaster = child_philp[scenarioNum].GetMasterb()
            lMaster = child_philp[scenarioNum].GetMasterl()
            uMaster = child_philp[scenarioNum].GetMasteru()

            y = child_philp[scenarioNum].candidateSolution.X()
            fval = child_philp[scenarioNum].candidateSolution.Fval()
            pi = child_philp[scenarioNum].candidateSolution.Pi()
            dj = child_philp[scenarioNum].candidateSolution.Dj()
            dj_l = copy.copy(dj)
            dj_l[dj_l < 0] = 0
            dj_u = copy.copy(dj)
            dj_u[dj_u > 0] = 0

            self.candidateSolution.SetSecondStageSolution(scenarioNum, y)
            self.candidateSolution.SetSecondStageDual(scenarioNum, np.transpose(pi[:bMaster.size]) * BMaster, 'slope')
            self.candidateSolution.SetSecondStageDual(scenarioNum, np.matmul(np.transpose(pi[:bMaster.size]), bMaster) +
                                                      np.matmul(np.transpose(dj_u[uMaster < cplex.infinity]),
                                                                uMaster[uMaster < cplex.infinity]) -
                                                      np.matmul(np.transpose(dj_l[lMaster != 0]),
                                                                lMaster[lMaster != 0]),
                                                      'int')
            self.candidateSolution.SetSecondStageValue(scenarioNum, fval)

    def SolveSubProblems(self):
        solution = self.candidateSolution
        for scenarioNum in range(self.lpModel_parent['numScenarios']):
            self.SubProblem(scenarioNum, solution)

    def SubProblem(self, inScenNumber, inSolution):
        q = self.lpModel_children[inScenNumber]['obj'] * self.objectiveScale
        D = self.lpModel_children[inScenNumber]['A_coef']
        d = self.lpModel_children[inScenNumber]['rhs']
        B = self.lpModel_children[inScenNumber]['B']
        l = self.lpModel_children[inScenNumber]['lb']
        u = self.lpModel_children[inScenNumber]['ub']
        sense = self.lpModel_children[inScenNumber]['sense']

        xLocal = inSolution.X()

        try:
            mdl_sub = cplex.Cplex()
            mdl_sub.set_problem_name("mdl_sub")
            mdl_sub.parameters.lpmethod.set(mdl_sub.parameters.lpmethod.values.auto)

            mdl_sub.objective.set_sense(mdl_sub.objective.sense.minimize)
            mdl_sub.variables.add(obj=q, lb=l, ub=u)
            mdl_sub.linear_constraints.add(senses=sense, rhs=d + B * xLocal)
            mdl_sub.linear_constraints.set_coefficients(D)
            mdl_sub.set_results_stream(None)
            mdl_sub.solve()
            mdl_sub.register_callback(MyCallback)
            solution = mdl_sub.solution

            exitFlag = solution.get_status()
        except CplexError as exc:
            print(exc)
        if exitFlag != 1:
            warnings.warn("'***Scenario '" + str(inScenNumber) + "' exited with flag '" + str(exitFlag) + "'")

        y = np.array(solution.get_values())
        fval = np.float64(solution.get_objective_value())
        pi = np.array(solution.get_dual_values())
        dj = np.array(solution.get_reduced_costs())
        dj_l = copy.copy(dj)
        dj_l[dj_l < 0] = 0
        dj_u = copy.copy(dj)
        dj_u[dj_u > 0] = 0

        inSolution.SetSecondStageSolution(inScenNumber, y)
        inSolution.SetSecondStageDual(inScenNumber, np.transpose(pi) * B, 'slope')
        inSolution.SetSecondStageDual(inScenNumber, np.matmul(np.transpose(pi), d) +
                                      np.matmul(np.transpose(dj_u[u < cplex.infinity]), u[u < cplex.infinity]) -
                                      np.matmul(np.transpose(dj_l[l != 0]), l[l != 0]), 'int')
        inSolution.SetSecondStageValue(inScenNumber, fval)

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
                                      range(self.lpModel_parent['numScenarios'])])
        intermediateSlope[np.where(self.numObsPerScen == 0)[0]] = 0
        if self.THETA.size == self.lpModel_parent['numScenarios']:
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
            [self.candidateSolution.SecondStageSlope(hIndex), -limit, np.array([-1]), np.zeros(self.THETA.size)])
        feasInt = self.candidateSolution.SecondStageIntercept(hIndex)

        self.feasibilityCutsMatrix = np.vstack([self.feasibilityCutsMatrix, feasSlope])
        self.feasibilityCutsRHS = np.append(self.feasibilityCutsRHS, -feasInt)

    def FindFeasibleMu(self):
        lambdaLocal = self.candidateSolution.Lambda()
        limit = np.minimum(self.phi.limit(), self.phi.computationLimit)
        localValues = self.candidateSolution.SecondStageValues()
        mu = np.float64(np.max(localValues) - limit * np.float64(1 - 1e-3) * lambdaLocal)
        self.candidateSolution.SetMu(mu)

    # needed for upper bound
    def FindFeasibleMu_true(self):
        lambdaLocal = self.candidateSolution.Lambda()
        limit = np.minimum(self.phi.limit(), self.phi.computationLimit)
        localValues = self.candidateSolution.SecondStageValues_true()
        mu = np.float64(np.max(localValues) - limit * np.float64(1 - 1e-3) * lambdaLocal)
        self.candidateSolution.SetMu(mu)

    # needed for upper bound
    def MuFeasible_for_upperbound(self):
        if ~self.candidateSolution.MuFeasibleTrue():
            self.FindFeasibleMu_true()

    def FindExpectedSecondStage(self):
        inSolution = self.candidateSolution
        if np.isnan(inSolution.MuFeasible()):
            raise Exception(
                'Must determine whether candidate mu is feasible before finding expected second stage value')
        if not all(inSolution.SecondStageValues() > -np.inf):
            raise Exception('Must set second stage values before calculating expectation')
        lambdaLocal = inSolution.Lambda()
        muLocal = inSolution.Mu()

        rawTheta = muLocal + lambdaLocal * self.rho + lambdaLocal * self.phi.Conjugate(inSolution.S())
        # if not lambdaLocal == 0:
        #     rawTheta = muLocal + lambdaLocal * self.rho + lambdaLocal * self.phi.Conjugate(inSolution.S())
        # else:
        #     tmp = inSolution.secondStageValues - muLocal
        #     tmp1 = lambdaLocal * self.phi.Conjugate(inSolution.S())
        #     for i in range(len(inSolution.secondStageValues - muLocal)):
        #         if tmp[i]<=0:
        #             tmp1[i] = 0
        #         else:
        #             tmp1[i] = np.inf
        #     rawTheta = muLocal + lambdaLocal * self.rho + tmp1


        rawTheta[np.where(self.numObsPerScen == 0)[0]] = 0
        rawTheta[np.where(rawTheta == np.inf)[0]] = np.inf
        if not all(np.isreal(rawTheta)):
            raise Exception('Possible scaling error')
        if not all(np.isfinite(rawTheta)):
            raise Exception('Nonfinite theta, lambda = ' + str(lambdaLocal))

        if self.THETA.size == self.lpModel_parent['numScenarios']:
            inSolution.SetTheta(rawTheta, 'true')
        elif self.THETA.size == 1:
            inSolution.SetTheta(np.dot(self.numObsPerScen / self.numObsTotal, rawTheta), 'true')
        else:
            raise Exception('Wrong size of obj.THETA.  This should not happen')
    # needed for upper bound
    def Get_h_True(self):
        inSolution = self.candidateSolution
        cLocal = self.lpModel_parent['obj']
        xLocal = inSolution.X()
        muLocal = inSolution.Mu()
        lambdaLocal = inSolution.Lambda()
        rhoLocal = self.rho
        SLocal = inSolution.S_True()
        q = self.numObsPerScen / self.numObsTotal

        h_True = np.matmul(cLocal, xLocal) + np.sum(
            q * (muLocal + rhoLocal * lambdaLocal + lambdaLocal * self.phi.Conjugate(SLocal)))

        # if not lambdaLocal == 0:
        #     h_True = np.matmul(cLocal, xLocal) + np.sum(
        #         q * (muLocal + rhoLocal * lambdaLocal + lambdaLocal * self.phi.Conjugate(SLocal)))
        # else:
        #     tmp = inSolution.secondStageValues_true - muLocal
        #     tmp1 = lambdaLocal * self.phi.Conjugate(inSolution.S_True())
        #     for i in range(len(inSolution.secondStageValues - muLocal)):
        #         if tmp[i] <= 0:
        #             tmp1[i] = 0
        #         else:
        #             tmp1[i] = np.inf
        #     h_True = np.matmul(cLocal, xLocal) + np.sum(
        #         q * (muLocal + rhoLocal * lambdaLocal + tmp1  ))
        return h_True


    def UpdateBestSolution(self):
        if self.newSolutionAccepted:
            if not np.array_equal(self.bestSolution, []):
                self.secondBestSolution = copy.copy(self.bestSolution)
            self.bestSolution = copy.copy(self.candidateSolution)
            self.CalculateProbability()

    def UpdateSolutions(self, philp1, philp2):
        for i in range(self.lpModel_parent['numScenarios']):
            for j in range(philp1[i].lpModel_parent['numScenarios']):
                for k in range(philp2[i][j].lpModel_parent['numScenarios']):
                    fval_true = philp2[i][j].candidateSolution.secondStageValues[k]
                    philp2[i][j].candidateSolution.SetSecondStageValue_true(k, fval_true)
                philp2[i][j].MuFeasible_for_upperbound()
                philp1[i].candidateSolution.SetSecondStageValue_true(j, philp2[i][j].Get_h_True())
            philp1[i].MuFeasible_for_upperbound()
            self.candidateSolution.SetSecondStageValue_true(i, philp1[i].Get_h_True())
        self.MuFeasible_for_upperbound()

        upper_candidate = self.Get_h_True()
        lower_candidate = self.candidateSolution.fval

        if upper_candidate < self.zUpper:
            self.newSolutionAccepted = True
            self.UpdateBestSolution()
            self.zUpper = upper_candidate

        if self.candidateSolution.MuFeasible():
            self.zLowerUpdated = True
            self.zLower = lower_candidate
        else:
            self.zLowerUpdated = False


    def WriteProgress(self):
        print("=" * 100)
        print(self.phi.divergence, ', rho = ', str(self.rho))
        print('Observations: ', str(self.numObsPerScen))
        print(str(self.NumObjectiveCuts()), ' objective cuts, ', str(self.NumFeasibilityCuts()), ' feasibility cuts.')

        if self.candidateSolution.MuFeasible():
            print('No feasibility cut generated')
        else:
            print('Feasibility cut generated')

        if self.newSolutionAccepted:
            print('New solution, zupper = ', str(self.zUpper))
        else:
            print('No new solution accepted')

        if self.zLowerUpdated:
            print('New lower bound, zlower = ', str(self.zLower))
        else:
            print('No new lower bound found')
        print('Objective tolerance ', str(self.currentObjectiveTolerance))
        print('Probability tolerance ', str(self.currentProbabilityTolerance))

    def ForceAcceptSolution(self):
        self.newSolutionAccepted = True
        self.UpdateBestSolution()

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

    def UpdateTolerances(self):
        if self.zLower > -np.inf:
            self.currentObjectiveTolerance = (self.zUpper - self.zLower) / np.minimum(np.abs(self.zUpper),
                                                                                      np.abs(self.zLower))
        else:
            self.currentObjectiveTolerance = np.inf
        self.currentProbabilityTolerance = np.abs(1 - np.sum(self.pWorst))

    def ResetSecondStageSolutions(self):
        self.candidateSolution.Reset()
        self.newSolutionAccepted = False
        self.zLowerUpdated = False

    def GetMasterc(self):
        cOut = np.append(self.lpModel_parent['obj'], np.zeros(2 + self.THETA.size)) * self.objectiveScale
        cOut[self.LAMBDA] = 0
        cOut[self.MU] = 0
        if self.THETA.size == self.lpModel_parent['numScenarios']:
            cOut[self.THETA] = self.numObsPerScen / self.numObsTotal
        elif self.THETA.size == 1:
            cOut[self.THETA] = 1
        else:
            raise Exception('Wrong size of obj.THETA.  This should not happen')
        return cOut

    def GetMasterA(self):
        AOut = self.lpModel_parent['A_coef']
        return AOut

    def GetMasterB(self):
        BOut = self.lpModel_parent['B']
        return BOut

    def GetMasterb(self):
        bOut = self.lpModel_parent['rhs']
        return bOut

    def GetMasterl(self):
        lOut = np.append(self.lpModel_parent['lb'], np.zeros(2 + self.THETA.size))
        lOut[self.LAMBDA] = self.lambdaLowerBound
        lOut[self.MU] = -cplex.infinity
        lOut[self.THETA] = -cplex.infinity
        return lOut

    def GetMasteru(self):
        uOut = np.append(self.lpModel_parent['ub'], np.zeros(2 + self.THETA.size))
        uOut[self.LAMBDA] = cplex.infinity
        uOut[self.MU] = cplex.infinity
        uOut[self.THETA] = cplex.infinity
        return uOut

    def GetMastersense(self):
        uOut = self.lpModel_parent['sense']
        return uOut

    def GetDecisions(self, solution, inType='true'):
        vOut = np.append(solution.X(), np.zeros(2 + self.THETA.size))
        vOut[self.LAMBDA] = solution.Lambda()
        vOut[self.MU] = solution.Mu()
        if inType == 'master':
            vOut[self.THETA] = solution.ThetaMaster()
        elif inType == 'true':
            vOut[self.THETA] = solution.ThetaTrue()
        else:
            raise Exception('Only accepts ''master and ''true''')
        return vOut

    def CandidateVector(self):
        outCV = self.GetDecisions(self.candidateSolution, 'master')
        return outCV

    def NumObjectiveCuts(self):
        outNum = self.objectiveCutsMatrix.shape[0]
        return outNum

    def NumFeasibilityCuts(self):
        outNum = self.feasibilityCutsMatrix.shape[0]
        return outNum

    def ObjectiveValue(self):
        outValue = self.zUpper
        return outValue

    def DoubleIterations(self):
        print('Max Iterations, not available to the Cplex solver ', )

    def DeleteOldestCut(self):
        self.objectiveCutsMatrix = self.objectiveCutsMatrix[self.THETA.size:]
        self.objectiveCutsRHS = self.objectiveCutsRHS[self.THETA.size:]

    def DeleteOldestFeasibilityCut(self):
        self.feasibilityCutsMatrix = self.feasibilityCutsMatrix[1:]
        self.feasibilityCutsRHS = self.feasibilityCutsRHS[1:]


if __name__ == "__main__":
    mat_data = sio.loadmat(os.getcwd() + "/mat_data/news.mat")
    lp = lp_read.set(mat_data)
    alpha = 0.01
    inPhi = PhiDivergence.set('burg')
    obs = lp.first['obs']
    inRho = inPhi.Rho(alpha, obs)
    philp = set([lp.first, lp.second], inPhi, obs, inRho)