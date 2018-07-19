import sys, os
import numpy as np
import cplex
from cplex.exceptions import CplexError
from cplex.callbacks import SimplexCallback
import scipy.io as sio
from scipy.sparse import find

if sys.platform == "darwin":
    sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
elif sys.platform == "win32":
    sys.path.append("/Applications/CPLEX_Studio128/cplex/python/3.6/x86-64_osx")
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
    def __init__(self, mat_data):
        self.numStages = mat_data['numStages'][0, 0].astype(int)
        # First stage
        self.first = {'numScenarios': mat_data['first'][0, 0]['numScenarios'][0][0].astype(int),
                      'obs': mat_data['first'][0, 0]['obs'][0].astype(float),
                      'obj': mat_data['first'][0, 0]['obj'][0].astype(float),
                      'lb': mat_data['first'][0, 0]['lb'][0].astype(float),
                      'ub': mat_data['first'][0, 0]['ub'][0].astype(float),
                      'rhs': mat_data['first'][0, 0]['rhs'][0].astype(float),
                      'A': mat_data['first'][0, 0]['A'].astype(float)}
        self.first['ub'][np.isinf(self.first['ub'])] = cplex.infinity
        self.first['sense'] = ["E"] * self.first['rhs'].size
        self.first['A_coef'] = list(zip(find(self.first['A'])[0].tolist(),
                                        find(self.first['A'])[1].tolist(),
                                        find(self.first['A'])[2].tolist()))

        # Second stage
        self.second = [[] for i in range(self.first['numScenarios'])]
        for i in range(self.first['numScenarios']):
            self.second[i] = {
                'numScenarios': np.array(mat_data['second'][0, 0]['numScenarios'][i, 0][0, 0], dtype=int),
                'obs': np.array(mat_data['second'][0, 0]['obs'][i, 0][0], dtype=float),
                'obj': mat_data['second'][0, 0]['obj'][i, 0][0].astype(float),
                'lb': mat_data['second'][0, 0]['lb'][i, 0][0].astype(float),
                'ub': mat_data['second'][0, 0]['ub'][i, 0][0].astype(float),
                'rhs': mat_data['second'][0, 0]['rhs'][i, 0][0].astype(float),
                'A': mat_data['second'][0, 0]['A'][i][0].astype(float),
                'B': mat_data['second'][0, 0]['B'][i][0].astype(float)}
            self.second[i]['ub'][np.isinf(self.second[i]['ub'])] = cplex.infinity
            self.second[i]['sense'] = ["E"] * self.second[i]['rhs'].size
            self.second[i]['A_coef'] = list(zip(find(self.second[i]['A'])[0].tolist(),
                                                find(self.second[i]['A'])[1].tolist(),
                                                find(self.second[i]['A'])[2].tolist()))

        # Third stage
        self.third = [[[] for j in range(self.second[i]['numScenarios'])]
                      for i in range(self.first['numScenarios'])]
        for i in range(self.first['numScenarios']):
            for j in range(self.second[i]['numScenarios']):
                self.third[i][j] = {
                    'numScenarios': np.array(mat_data['third'][0, 0]['numScenarios'][i, j][0, 0], dtype=int),
                    'obs': np.array(mat_data['third'][0, 0]['obs'][i, j][0], dtype=float),
                    'obj': mat_data['third'][0, 0]['obj'][i, j][0].astype(float),
                    'lb': mat_data['third'][0, 0]['lb'][i, j][0].astype(float),
                    'ub': mat_data['third'][0, 0]['ub'][i, j][0].astype(float),
                    'rhs': mat_data['third'][0, 0]['rhs'][i, j][0].astype(float),
                    'A': mat_data['third'][0, 0]['A'][i, j].astype(float),
                    'B': mat_data['third'][0, 0]['B'][i, j].astype(float)}
                self.third[i][j]['ub'][np.isinf(self.third[i][j]['ub'])] = cplex.infinity
                self.third[i][j]['sense'] = ["E"] * self.third[i][j]['rhs'].size
                self.third[i][j]['A_coef'] = list(zip(find(self.third[i][j]['A'])[0].tolist(),
                                                      find(self.third[i][j]['A'])[1].tolist(),
                                                      find(self.third[i][j]['A'])[2].tolist()))

        # Fourth stage
        self.fourth = [[[[i, j, k] for k in range(self.third[i][j]['numScenarios'])]
                        for j in range(self.second[i]['numScenarios'])]
                       for i in range(self.first['numScenarios'])]
        for i in range(self.first['numScenarios']):
            for j in range(self.second[i]['numScenarios']):
                for k in range(self.third[i][j]['numScenarios']):
                    self.fourth[i][j][k] = {
                        'obj': mat_data['fourth'][0, 0]['obj'][i, j, k][0].astype(float),
                        'lb': mat_data['fourth'][0, 0]['lb'][i, j, k][0].astype(float),
                        'ub': mat_data['fourth'][0, 0]['ub'][i, j, k][0].astype(float),
                        'rhs': mat_data['fourth'][0, 0]['rhs'][i, j, k][0].astype(float),
                        'A': mat_data['fourth'][0, 0]['A'][i, j, k].astype(float),
                        'B': mat_data['fourth'][0, 0]['B'][i, j, k].astype(float)}
                    self.fourth[i][j][k]['ub'][np.isinf(self.fourth[i][j][k]['ub'])] = cplex.infinity
                    self.fourth[i][j][k]['sense'] = ["E"] * self.fourth[i][j][k]['rhs'].size
                    self.fourth[i][j][k]['A_coef'] = list(zip(find(self.fourth[i][j][k]['A'])[0].tolist(),
                                                              find(self.fourth[i][j][k]['A'])[1].tolist(),
                                                              find(self.fourth[i][j][k]['A'])[2].tolist()))


if __name__ == "__main__":
    # test
    try:
        mat_data = sio.loadmat(os.getcwd() + "/mat_data/watertest.mat")

        lp = set(mat_data)
        mdl = cplex.Cplex()
        mdl.set_problem_name("mdl")
        mdl.parameters.lpmethod.set(mdl.parameters.lpmethod.values.auto)

        mdl.objective.set_sense(mdl.objective.sense.minimize)
        mdl.variables.add(obj=lp.first['obj'], lb=lp.first['lb'], ub=lp.first['ub'])
        mdl.linear_constraints.add(senses=lp.first['sense'], rhs=lp.first['rhs'])
        mdl.linear_constraints.set_coefficients(lp.first['A_coef'])

        mdl.solve()
        mdl.register_callback(MyCallback)
        solution = mdl.solution

        numvars = mdl.variables.get_num()
        numlinconstr = mdl.linear_constraints.get_num()

        x = np.array(solution.get_values(0, numvars - 1))

        second_lp = lp.second[0]
        mdl_2nd = cplex.Cplex()
        mdl_2nd.set_problem_name("mdl_2nd")
        mdl_2nd.parameters.lpmethod.set(mdl_2nd.parameters.lpmethod.values.auto)

        mdl_2nd.objective.set_sense(mdl_2nd.objective.sense.minimize)
        mdl_2nd.variables.add(obj=second_lp['obj'], lb=second_lp['lb'], ub=second_lp['ub'])

        mdl_2nd.linear_constraints.add(senses=second_lp['sense'],
                                       rhs=second_lp['rhs'] + x * second_lp['B'].transpose())
        mdl_2nd.linear_constraints.set_coefficients(second_lp['A_coef'])
        mdl_2nd.solve()
        mdl_2nd.register_callback(MyCallback)
        solution = mdl_2nd.solution

        numvars = mdl_2nd.variables.get_num()
        numlinconstr = mdl_2nd.linear_constraints.get_num()

        y = np.array(solution.get_values(0, numvars - 1))
        pi = solution.get_dual_values()


    except CplexError as exc:
        print(exc)

    print(lp.first)
