import sys
import scipy.io as sio
import numpy as np
import warnings, copy, cplex
from cplex.exceptions import CplexError
import Solution_leaf


if sys.platform == "darwin":
    sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
elif sys.platform == "win32":
    sys.path.append("C:\Program Files\IBM\ILOG\CPLEX_Studio128\cplex\python\3.6\x64_win64")
else:
    raise Exception('What is your platform?')


class set(object):
    def __init__(self, inLPModel):

        self.objectiveScale = np.float64(1)
        self.lpModel = inLPModel
        self.candidateSolution = Solution_leaf.set(self.lpModel)

    def SubProblem(self, x_parent):
        Sub_c = self.lpModel['obj']
        Sub_A = self.lpModel['A_coef']
        Sub_b = self.lpModel['rhs']
        Sub_l = self.lpModel['lb']
        Sub_u = self.lpModel['ub']
        Sub_sense = self.lpModel['sense']
        Sub_B = self.lpModel['B']


        try:
            mdl_sub = cplex.Cplex()
            mdl_sub.parameters.lpmethod.set(mdl_sub.parameters.lpmethod.values.auto)
            mdl_sub.variables.add(obj=Sub_c, lb=Sub_l, ub=Sub_u)
            mdl_sub.linear_constraints.add(senses=Sub_sense,rhs=Sub_b+ Sub_B*x_parent)
            mdl_sub.linear_constraints.set_coefficients(Sub_A)
            mdl_sub.set_results_stream(None)
            mdl_sub.solve()

            solution = mdl_sub.solution
            exitFlag = solution.get_status()

            currentCandidate = np.array(solution.get_values())
            fval = np.float64(solution.get_objective_value())
            pi = np.array(solution.get_dual_values())

            if exitFlag == mdl_sub.solution.status.unbounded:
                raise Exception("Leaf: Model is unbounded")
            if exitFlag == mdl_sub.solution.status.infeasible:
                raise Exception("Leaf: Model is infeasible")
            if exitFlag == mdl_sub.solution.status.infeasible_or_unbounded:
                raise Exception("Leaf: Model is infeasible or unbounded")

        except CplexError as exc:
            print(exc)

        self.candidateSolution.SetX(currentCandidate)
        self.candidateSolution.SetFval(fval)
        self.candidateSolution.SetPi(pi)

    def GetMasterB(self):
        BOut = self.lpModel['B']
        return BOut

    def GetMasterb(self):
        bOut = self.lpModel['rhs']
        return bOut

if __name__ == "__main__":
    data = "first_second_third_news2.mat"
    data1 = "fourth1_news2.mat"
    data2 = "fourth2_news2.mat"
    data3 = "fourth3_news2.mat"

    mat_data = sio.loadmat(os.getcwd() + "/mat_data/" + data)
    fourth1 = sio.loadmat(os.getcwd() + "/mat_data/" + data1)
    fourth2 = sio.loadmat(os.getcwd() + "/mat_data/" + data2)
    fourth3 = sio.loadmat(os.getcwd() + "/mat_data/" + data3)
    # set lp data
    lp = lp_reader.set(mat_data, fourth1, fourth2, fourth3)
    philp = set(lp.second[0])
    philp.SubProblem(x_parent=0)
    print(philp.candidateSolution.Fval())
