import sys, os
sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
import numpy as np
import lp
import cplex
from cplex.exceptions import CplexError
from cplex.callbacks import SimplexCallback
import scipy.io as sio
from scipy.sparse import csr_matrix, find,  hstack, vstack, block_diag

class MyCallback(SimplexCallback):
    def __call__(self):
        print("CB Iteration ", self.get_num_iterations(), " : ", end=' ')
        if self.is_primal_feasible():
            print("CB Objective = ", self.get_objective_value())
        else:
            print("CB Infeasibility measure = ",
                  self.get_primal_infeasibility())

def solve(parent, children):
    q = parent['obs']/np.sum(parent['numScenarios'])
    extensive_obj = parent['obj']
    for i in range(parent['numScenarios']):
        extensive_obj = np.append(extensive_obj,q[i]*children[i]['obj'])

    extensive_lb = parent['lb']
    for i in range(parent['numScenarios']):
        extensive_lb = np.append(extensive_lb,children[i]['lb'])

    extensive_ub = parent['ub']
    for i in range(parent['numScenarios']):
        extensive_ub = np.append(extensive_ub,children[i]['ub'])

    extensive_rhs = parent['rhs']
    for i in range(parent['numScenarios']):
        extensive_rhs = np.append(extensive_rhs,children[i]['rhs'])

    extensive_sense = parent['sense']
    for i in range(parent['numScenarios']):
        extensive_sense = np.append(extensive_sense,children[i]['sense'])

    tmp = parent['A']
    for i in range(parent['numScenarios']):
        tmp = vstack([tmp,-children[i]['B']])

    tmp1 = csr_matrix(np.zeros((parent['rhs'].size, children[0]['obj'].size * parent['numScenarios'])))
    tmp2 = children[i]['A'][0]
    for i in range(1,parent['numScenarios']):
        tmp2 = block_diag((tmp2,children[i]['A']))
    tmp3 = vstack((tmp1,tmp2))
    extensive_A = hstack([tmp, tmp3])
    A_rows = find(extensive_A)[0].tolist()
    A_cols = find(extensive_A)[1].tolist()
    A_vals = find(extensive_A)[2].tolist()
    extensive_A_coefficients = zip(A_rows, A_cols, A_vals)

    try:
        mdl = cplex.Cplex()
        mdl.set_problem_name("mdl")
        mdl.parameters.lpmethod.set(mdl.parameters.lpmethod.values.auto)

        mdl.objective.set_sense(mdl.objective.sense.minimize)
        mdl.variables.add(obj=extensive_obj, lb=extensive_lb, ub=extensive_ub)
        mdl.linear_constraints.add(senses=extensive_sense, rhs=extensive_rhs)
        mdl.linear_constraints.set_coefficients(extensive_A_coefficients)
        mdl.set_results_stream(None)
        mdl.solve()
        mdl.register_callback(MyCallback)
        solution = mdl.solution

        x = solution.get_values()
        exitFlag = solution.get_status()
        return (x, exitFlag)
    except CplexError as exc:
        print(exc)


if __name__ == "__main__":
    mat_data = sio.loadmat(os.getcwd() + "/mat_data/watertest.mat")
    lp = lp.set(mat_data)
    x, exitFlag= solve(lp.first, lp.second)
    print(x)