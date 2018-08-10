import sys, os
import numpy as np
import lp_read_large_fourth_stages
import cplex
from cplex.exceptions import CplexError
from cplex.callbacks import SimplexCallback
import scipy.io as sio
from scipy.sparse import csr_matrix, find, hstack, vstack
sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")

class MyCallback(SimplexCallback):
    def __call__(self):
        print("CB Iteration ", self.get_num_iterations(), " : ", end=' ')
        if self.is_primal_feasible():
            print("CB Objective = ", self.get_objective_value())
        else:
            print("CB Infeasibility measure = ",
                  self.get_primal_infeasibility())


def solve(parent, children, x_parent=0):
    q = np.array([parent['obs'] / np.sum(parent['numScenarios'])])
    children_obj = 0
    children_lb = 0
    children_ub = 0
    children_rhs = 0
    for i in range(parent['numScenarios']):
        children_obj = children_obj + q[0][i] * children[i]['obj']
        children_lb = children_lb + q[0][i] * children[i]['lb']
        children_ub = children_ub + q[0][i] * children[i]['ub']
        children_rhs = children_rhs + q[0][i] * children[i]['rhs']

    expected_obj = np.append(parent['obj'], children_obj)
    expected_lb = np.append(parent['lb'], children_lb)
    expected_ub = np.append(parent['ub'], children_ub)
    if 'B' in parent.keys():
        expected_rhs = np.append(parent['rhs'] + parent['B']* x_parent, children_rhs)
    else:
        expected_rhs = np.append(parent['rhs'], children_rhs)
    expected_sense = np.append(parent['sense'], children[0]['sense'])

    tmp = q[0][0] * (-children[0]['B'])
    tmp1 = q[0][0] * children[0]['A']
    for i in range(1, parent['numScenarios']):
        tmp = tmp + q[0][i] * (-children[i]['B'])
        tmp1 = tmp1 + q[0][i] * children[i]['A']

    tmp2 = vstack([parent['A'], tmp])
    tmp3 = csr_matrix(np.zeros((parent['rhs'].size, children[0]['obj'].size)))
    tmp4 = vstack([tmp3, tmp1])

    expected_A = hstack([tmp2, tmp4])
    A_rows = find(expected_A)[0].tolist()
    A_cols = find(expected_A)[1].tolist()
    A_vals = find(expected_A)[2].tolist()
    expected_A_coefficients = zip(A_rows, A_cols, A_vals)

    try:
        mdl = cplex.Cplex()
        mdl.set_problem_name("mdl")
        mdl.parameters.lpmethod.set(mdl.parameters.lpmethod.values.auto)

        mdl.objective.set_sense(mdl.objective.sense.minimize)
        mdl.variables.add(obj=expected_obj, lb=expected_lb, ub=expected_ub)

        mdl.linear_constraints.add(senses=expected_sense, rhs=expected_rhs)
        mdl.linear_constraints.set_coefficients(expected_A_coefficients)
        mdl.set_results_stream(None)
        mdl.solve()
        mdl.register_callback(MyCallback)
        solution = mdl.solution

        exitFlag = solution.get_status()

        slack = solution.get_linear_slacks()
        pi = solution.get_dual_values()
        x = solution.get_values()
        dj = solution.get_reduced_costs()
        return (np.array(x), exitFlag, np.array(slack), np.array(pi), np.array(dj))
    except CplexError as exc:
        print(exc)


if __name__ == "__main__":
    mat_data = sio.loadmat(os.getcwd() + "/mat_data/news.mat")
    lp = lp.set(mat_data)
    x, exitFlag, slack, pi, dj = solve(lp.first, lp.second)
    x, exitFlag, slack, pi, dj = solve(lp.second[0], lp.third[0][:], x[0:2])
    x, exitFlag, slack, pi, dj = solve(lp.third[0][0], lp.fourth[0][0][:], x[0:2])
    print(x)
