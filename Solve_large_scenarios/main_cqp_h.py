import numpy as np
import lp_reader, PhiDivergence, PhiLP_root, PhiLP_child, PhiLP_leaf
import time, copy
import os,sys
import scipy.io as sio
import pickle
from scipy.sparse import lil_matrix,find,  hstack, vstack, block_diag
import cplex
from cplex.exceptions import CplexError

from math import fabs, sqrt
import sys
from cplex import six

# Default tolerance for testing KKT conditions. */
TESTTOL = 1e-9
# Default tolerance for barrier convergence. */
CONVTOL = 1e-9

# Marker for variables that are in a cone constraint but are not the cone
# head variable in that constraint.
NOT_CONE_HEAD = -1
# Marker for variables that are not in any cone constraint.
NOT_IN_CONE = -2
def run(inputPHI, alpha, matlab_input_data, matlab_input_data1, matlab_input_data2, matlab_input_data3,savefile):
    # read data from Matlab .mat file



    mat_data = sio.loadmat(os.getcwd() + "/mat_data/" + matlab_input_data)
    fourth1 = sio.loadmat(os.getcwd() + "/mat_data/" + matlab_input_data1)
    fourth2 = sio.loadmat(os.getcwd() + "/mat_data/" + matlab_input_data2)
    fourth3 = sio.loadmat(os.getcwd() + "/mat_data/" + matlab_input_data3)
    # set lp data
    lp = lp_reader.set(mat_data, fourth1, fourth2, fourth3)

    start1 = time.clock()
    # assumption: 1,2,3 stages have the same Phi-divergence
    inPhi = PhiDivergence.set(inputPHI)
    # set: Phi-lp2
    philp = PhiLP_root.set(lp.first, inPhi, lp.first['obs'], inPhi.Rho(alpha, lp.first['obs']))
    philp1 = [PhiLP_child.set(lp.second[i],
                              inPhi, lp.second[i]['obs'], inPhi.Rho(alpha, lp.second[i]['obs']))
              for i in range(lp.first['numScenarios'])]
    philp2 = [[PhiLP_child.set(lp.third[i][j],
                               inPhi, lp.third[i][j]['obs'], inPhi.Rho(alpha, lp.third[i][j]['obs']))
               for j in range(lp.second[i]['numScenarios'])]
              for i in range(lp.first['numScenarios'])]
    philp3 = [[[PhiLP_leaf.set(lp.fourth[i][j][k])
                for k in range(lp.third[i][j]['numScenarios'])]
               for j in range(lp.second[i]['numScenarios'])]
              for i in range(lp.first['numScenarios'])]

    # OBJ
    obj = np.append(philp.lpModel['obj'], [1, (philp.rho - 1)])
    q2 = philp.numObsPerScen / philp.numObsTotal
    for i in range(lp.first['numScenarios']):
        tmp = np.append(np.zeros_like(philp1[i].lpModel['obj']), [0, 0, q2[i]])
        obj = np.append(obj, tmp)

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            tmp = np.append(np.zeros_like(philp2[i][j].lpModel['obj']), [0, 0, 0])
            obj = np.append(obj, tmp)
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                tmp = np.append(np.zeros_like(philp3[i][j][k].lpModel['obj']), [0])
                obj = np.append(obj, tmp)

    # lb
    lb = np.append(philp.lpModel['lb'], [-cplex.infinity, 0])
    for i in range(lp.first['numScenarios']):
        tmp = np.append(philp1[i].lpModel['lb'], [-cplex.infinity, 0, -cplex.infinity])
        lb = np.append(lb, tmp)

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            tmp = np.append(philp2[i][j].lpModel['lb'], [-cplex.infinity, 0, -cplex.infinity])
            lb = np.append(lb, tmp)
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                tmp = np.append(philp3[i][j][k].lpModel['lb'], [-cplex.infinity])
                lb = np.append(lb, tmp)

    # ub
    ub = np.append(philp.lpModel['ub'], [cplex.infinity, cplex.infinity])
    for i in range(lp.first['numScenarios']):
        tmp = np.append(philp1[i].lpModel['ub'], [cplex.infinity, cplex.infinity, cplex.infinity])
        ub = np.append(ub, tmp)

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            tmp = np.append(philp2[i][j].lpModel['ub'],
                            [cplex.infinity, cplex.infinity, cplex.infinity])
            ub = np.append(ub, tmp)
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                tmp = np.append(philp3[i][j][k].lpModel['ub'], [cplex.infinity])
                ub = np.append(ub, tmp)

    # sense
    sense_linear = philp.lpModel['sense']
    for i in range(lp.first['numScenarios']):
        sense_linear = np.append(sense_linear, philp1[i].lpModel['sense'])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            sense_linear = np.append(sense_linear, philp2[i][j].lpModel['sense'])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                sense_linear = np.append(sense_linear, philp3[i][j][k].lpModel['sense'])

    sense_linear1 = []
    for i in range(lp.first['numScenarios']):
        sense_linear1 = np.append(sense_linear1, ['L'])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            sense_linear1 = np.append(sense_linear1, ['L'])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                sense_linear1 = np.append(sense_linear1, ['L'])


    # RHS
    rhs_linear = philp.lpModel['rhs']
    for i in range(lp.first['numScenarios']):
        rhs_linear = np.append(rhs_linear, philp1[i].lpModel['rhs'])

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            rhs_linear = np.append(rhs_linear, philp2[i][j].lpModel['rhs'])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                rhs_linear = np.append(rhs_linear, philp3[i][j][k].lpModel['rhs'])

    rhs_linear1 = []
    for i in range(lp.first['numScenarios']):
        rhs_linear1 = np.append(rhs_linear1, [0])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            rhs_linear1 = np.append(rhs_linear1, [0])
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                rhs_linear1 = np.append(rhs_linear1, [0])





    col_num = obj.shape[0]
    # Linear A1
    A1 = lil_matrix((philp.lpModel['A'].shape[0], col_num), dtype=np.float)
    row_A1 = np.arange(philp.lpModel['A'].shape[0])
    col_A1 = np.arange(philp.lpModel['A'].shape[1])
    A1[row_A1[0]:row_A1[-1]+1, col_A1[0]:col_A1[-1]+1] = philp.lpModel['A']


    # Linear A2
    A2 = lil_matrix((philp1[0].lpModel['A'].shape[0] * lp.first['numScenarios'], col_num), dtype=np.float)
    row_B2 = np.zeros_like(np.tile(np.arange(philp1[0].lpModel['B'].shape[0]), (lp.first['numScenarios'], 1)))
    col_A2 = np.zeros_like(np.tile(np.arange(philp1[0].lpModel['A'].shape[1]), (lp.first['numScenarios'], 1)))


    for i in range(lp.first['numScenarios']):
        row_B2[i] = np.arange(philp1[i].lpModel['B'].shape[0] * i, philp1[i].lpModel['B'].shape[0] * (i + 1))
        col_A2[i] = np.arange((philp.lpModel['A'].shape[1] + 2) + philp1[i].lpModel['A'].shape[1] * i + 3 * i,
                              (philp.lpModel['A'].shape[1] + 2) + philp1[i].lpModel['A'].shape[1] * (i + 1) + 3 * i)
        A2[row_B2[i][0]:row_B2[i][-1]+1, col_A1[0]:col_A1[-1]+1] = -philp1[i].lpModel['B']
        A2[row_B2[i][0]:row_B2[i][-1]+1, col_A2[i][0]:col_A2[i][-1]+1] = philp1[i].lpModel['A']

    # Linear A3
    A3 = lil_matrix(
        (philp2[0][0].lpModel['A'].shape[0] * lp.first['numScenarios'] * lp.second[0]['numScenarios'], col_num),
        dtype=np.float)

    row_B3 = np.zeros_like(np.tile(np.arange(philp2[0][0].lpModel['B'].shape[0]),
                                   (lp.first['numScenarios'] * lp.second[0]['numScenarios'], 1)))
    for t in range(lp.first['numScenarios'] * lp.second[0]['numScenarios']):
        row_B3[t] = np.arange(philp2[0][0].lpModel['B'].shape[0] * t, philp2[0][0].lpModel['B'].shape[0] * (t + 1))

    row_B3 = row_B3.reshape((lp.first['numScenarios'], lp.second[0]['numScenarios'], row_B3[0].size))

    col_A3 = np.zeros_like(np.tile(np.arange(philp2[0][0].lpModel['A'].shape[1]),
                                   (lp.first['numScenarios']*lp.second[0]['numScenarios'], 1)))
    for t in range(lp.first['numScenarios']*lp.second[0]['numScenarios']):
        col_A3[t] = np.arange((philp.lpModel['A'].shape[1] + 2 + (philp1[0].lpModel['A'].shape[1]+3)*lp.first['numScenarios']) + philp2[0][0].lpModel['A'].shape[1] * t + 3 * t,
                             (philp.lpModel['A'].shape[1] + 2 + (philp1[0].lpModel['A'].shape[1]+3)*lp.first['numScenarios']) + philp2[0][0].lpModel['A'].shape[1] * (t + 1) + 3 * t)
    col_A3= col_A3.reshape((lp.first['numScenarios'], lp.second[0]['numScenarios'],col_A3[0].size))


    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            A3[row_B3[i][j][0]:row_B3[i][j][-1]+1, col_A2[i][0]:col_A2[i][-1]+1] = -philp2[i][j].lpModel['B']
            A3[row_B3[i][j][0]:row_B3[i][j][-1]+1, col_A3[i][j][0]:col_A3[i][j][-1]+1] = philp2[i][j].lpModel['A']

    # Linear A4
    A4 = lil_matrix(
        (philp3[0][0][0].lpModel['A'].shape[0] * lp.first['numScenarios'] * lp.second[0]['numScenarios']* lp.third[0][0]['numScenarios'], col_num),
        dtype=np.float)
    row_B4 = np.zeros_like(np.tile(np.arange(philp3[0][0][0].lpModel['B'].shape[0]),
                                   (lp.first['numScenarios'] * lp.second[0]['numScenarios']* lp.third[0][0]['numScenarios'], 1)))
    for t in range(lp.first['numScenarios'] * lp.second[0]['numScenarios']* lp.third[0][0]['numScenarios']):
        row_B4[t] = np.arange(philp3[0][0][0].lpModel['B'].shape[0] * t, philp3[0][0][0].lpModel['B'].shape[0] * (t + 1))
    row_B4 = row_B4.reshape((lp.first['numScenarios'], lp.second[0]['numScenarios'], lp.third[0][0]['numScenarios'],row_B4[0].size))

    col_A4 = np.zeros_like(np.tile(np.arange(philp3[0][0][0].lpModel['A'].shape[1]),
                                   (lp.first['numScenarios'] * lp.second[0]['numScenarios']* lp.third[0][0]['numScenarios'], 1)))
    for t in range(lp.first['numScenarios'] * lp.second[0]['numScenarios']* lp.third[0][0]['numScenarios']):
        col_A4[t] = np.arange(
            (philp.lpModel['A'].shape[1] + 2 + (philp1[0].lpModel['A'].shape[1] + 3) * lp.first['numScenarios']+(philp2[0][0].lpModel['A'].shape[1] + 3)* lp.first['numScenarios'] * lp.second[0]['numScenarios']) +
            philp3[0][0][0].lpModel['A'].shape[1] * t + 1 * t,
            (philp.lpModel['A'].shape[1] + 2 + (philp1[0].lpModel['A'].shape[1] + 3) * lp.first['numScenarios']+(philp2[0][0].lpModel['A'].shape[1] + 3)* lp.first['numScenarios'] * lp.second[0]['numScenarios']) +
            philp3[0][0][0].lpModel['A'].shape[1] * (t + 1) + 1 * t)
    col_A4 = col_A4.reshape((lp.first['numScenarios'], lp.second[0]['numScenarios'], lp.third[0][0]['numScenarios'],col_A4[0].size))

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                A4[row_B4[i][j][k][0]:row_B4[i][j][k][-1]+1, col_A3[i][j][0]:col_A3[i][j][-1]+1] = -philp3[i][j][k].lpModel['B']
                A4[row_B4[i][j][k][0]:row_B4[i][j][k][-1]+1, col_A4[i][j][k][0]:col_A4[i][j][k][-1]+1] = philp3[i][j][k].lpModel['A']

    A = vstack([vstack([vstack([A1, A2]), A3]), A4])


    # linear_cqp
    A_lc2 = lil_matrix((lp.first['numScenarios'], col_num), dtype=np.float)
    row_lc2 = np.arange(lp.first['numScenarios'])
    for i in range(lp.first['numScenarios']):
        A_lc2[row_lc2[i], col_A1[-1]+1:col_A1[-1]+3] = np.array([-1,-1])
        A_lc2[row_lc2[i], col_A2[i]] = philp1[i].lpModel['obj']
        A_lc2[row_lc2[i], col_A2[i][-1]+1:col_A2[i][-1]+3] = np.array([1,(philp1[i].rho-1)])

        q3 = philp1[i].numObsPerScen / philp1[i].numObsTotal
        for j in range(lp.second[i]['numScenarios']):
            A_lc2[row_lc2[i], col_A3[i][j][-1]+3] = q3[j]



    A_lc3 = lil_matrix((lp.first['numScenarios']*lp.second[0]['numScenarios'], col_num), dtype=np.float)
    row_lc3 = np.zeros_like(np.tile(1,(lp.first['numScenarios'] * lp.second[0]['numScenarios'], 1)))
    for t in range(lp.first['numScenarios'] * lp.second[0]['numScenarios']):
        row_lc3[t] = np.arange(t, t + 1)
    row_lc3 = row_lc3.reshape((lp.first['numScenarios'], lp.second[0]['numScenarios'], row_lc3[0].size))
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            A_lc3[row_lc3[i][j], col_A2[i][-1]+1:col_A2[i][-1]+3] = np.array([-1,-1])
            A_lc3[row_lc3[i][j], col_A3[i][j]] = philp2[i][j].lpModel['obj']
            A_lc3[row_lc3[i][j], col_A3[i][j][-1]+1:col_A3[i][j][-1]+3] = np.array([1,(philp2[i][j].rho-1)])

            q4 = philp2[i][j].numObsPerScen / philp2[i][j].numObsTotal
            for k in range(lp.third[i][j]['numScenarios']):
                A_lc3[row_lc3[i][j], col_A4[i][j][k][-1] + 1] = q4[k]

    A_lc4 = lil_matrix((lp.first['numScenarios'] * lp.second[0]['numScenarios']*lp.third[0][0]['numScenarios'], col_num), dtype=np.float)
    row_lc4 = np.zeros_like(np.tile(1, (lp.first['numScenarios'] * lp.second[0]['numScenarios']*lp.third[0][0]['numScenarios'], 1)))
    for t in range(lp.first['numScenarios'] * lp.second[0]['numScenarios']*lp.third[0][0]['numScenarios']):
        row_lc4[t] = np.arange(t, t + 1)
    row_lc4 = row_lc4.reshape((lp.first['numScenarios'], lp.second[0]['numScenarios'], lp.third[0][0]['numScenarios'], row_lc4[0].size))
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                A_lc4[row_lc4[i][j][k], col_A3[i][j][-1] + 1:col_A3[i][j][-1] + 3] = np.array([-1, -1])
                A_lc4[row_lc4[i][j][k], col_A4[i][j][k]] = philp3[i][j][k].lpModel['obj']



    A_lc = vstack([vstack([A_lc2, A_lc3]), A_lc4])
    tmp = A_lc.toarray()

    extensive_A = vstack([A, A_lc])
    A_rows = find(extensive_A)[0].tolist()
    A_cols = find(extensive_A)[1].tolist()
    A_vals = find(extensive_A)[2].tolist()
    extensive_A_coefficients = zip(A_rows, A_cols, A_vals)


    mdl = cplex.Cplex()
    mdl.set_problem_name("mdl")
    mdl.parameters.lpmethod.set(mdl.parameters.lpmethod.values.auto)

    mdl.objective.set_sense(mdl.objective.sense.minimize)
    mdl.variables.add(obj=obj, lb=lb, ub=ub)
    mdl.linear_constraints.add(senses=sense_linear, rhs=rhs_linear)
    mdl.linear_constraints.add(senses=sense_linear1, rhs=rhs_linear1)

    mdl.linear_constraints.set_coefficients(extensive_A_coefficients)





    # A_q
    for i in range(lp.first['numScenarios']):
        A_q2_id1  = [int(col_A1[-1])+2, int(col_A1[-1])+1     ,int(col_A1[-1])+2     ]+list(col_A2[i].astype(int))+                                       [int(col_A2[i][-1]) + 1,int(col_A2[i][-1]) + 2]
        A_q2_id2  = [int(col_A1[-1])+2, int(col_A2[i][-1]) + 3,int(col_A2[i][-1]) + 3]+list((int(col_A2[i][-1]) + 3)*np.ones_like(col_A2[i]))+[int(col_A2[i][-1]) + 3,int(col_A2[i][-1]) + 3]
        A_q2_coef = [1,-1,-1]+list(philp1[i].lpModel['obj'])+[1,philp1[i].rho-1]
        q3 = philp1[i].numObsPerScen / philp1[i].numObsTotal
        for j in range(lp.second[i]['numScenarios']):
            A_q2_id1 = A_q2_id1 + [int(col_A3[i][j][-1]) + 3]
            A_q2_id2 = A_q2_id2 + [int(col_A2[i][-1]) + 3]
            A_q2_coef= A_q2_coef+ [q3[j]]
        A_q2_id1 = [ int(x) for x in A_q2_id1 ]
        A_q2_id2 = [ int(x) for x in A_q2_id2 ]
        q = cplex.SparseTriple(ind1=A_q2_id1, ind2=A_q2_id2, val=A_q2_coef)
        mdl.quadratic_constraints.add(quad_expr=q, rhs=0, sense="L")

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            A_q3_id1 = [int(col_A2[i][-1]) + 2, int(col_A2[i][-1]) + 1, int(col_A2[i][-1]) + 2] + list(col_A3[i][j].astype(int)) + \
                       [int(col_A3[i][j][-1]) + 1, int(col_A3[i][j][-1]) + 2]
            A_q3_id2 = [int(col_A2[i][-1]) + 2, int(col_A3[i][j][-1]) + 3, int(col_A3[i][j][-1]) + 3] + list((int(col_A3[i][j][-1]) + 3) * np.ones_like(col_A3[i][j])) + \
                       [int(col_A3[i][j][-1]) + 3, int(col_A3[i][j][-1]) + 3]
            A_q3_coef = [1, -1, -1] + list(philp2[i][j].lpModel['obj']) + [1, philp2[i][j].rho - 1]

            q4 = philp2[i][j].numObsPerScen / philp2[i][j].numObsTotal
            for k in range(lp.third[i][j]['numScenarios']):
                A_q3_id1 = A_q3_id1 + [int(col_A4[i][j][k][-1]) + 1]
                A_q3_id2 = A_q3_id2 + [int(col_A3[i][j][-1]) + 3]
                A_q3_coef = A_q3_coef + [q4[k]]
            A_q3_id1 = [int(x) for x in A_q3_id1]
            A_q3_id2 = [int(x) for x in A_q3_id2]
            q = cplex.SparseTriple(ind1=A_q3_id1, ind2=A_q3_id2, val=A_q3_coef)
            mdl.quadratic_constraints.add(quad_expr=q, rhs=0, sense="L")

    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            for k in range(lp.third[i][j]['numScenarios']):
                A_q4_id1 = [int(col_A3[i][j][-1]) + 2, int(col_A3[i][j][-1]) + 1, int(col_A3[i][j][-1]) + 2] + list(col_A4[i][j][k].astype(int))
                A_q4_id2 = [int(col_A3[i][j][-1]) + 2, int(col_A4[i][j][k][-1]) + 1, int(col_A4[i][j][k][-1]) + 1] + list((int(col_A4[i][j][k][-1]) + 1) * np.ones_like(col_A4[i][j][k]))
                A_q4_coef = [1, -1, -1] + list(philp3[i][j][k].lpModel['obj'])
                A_q4_id1 = [int(x) for x in A_q4_id1]
                A_q4_id2 = [int(x) for x in A_q4_id2]
                q = cplex.SparseTriple(ind1=A_q4_id1, ind2=A_q4_id2, val=A_q4_coef)
                mdl.quadratic_constraints.add(quad_expr=q, rhs=0, sense="L")
    print("test"*100)



    # sys.stdout is the default output stream for log and results
    # so these lines may be omitted
    mdl.set_log_stream(sys.stdout)
    mdl.set_results_stream(sys.stdout)


    # Apply parameter settings.
    mdl.parameters.barrier.qcpconvergetol.set(CONVTOL)

    # Solve the problem. If we cannot find an _optimal_ solution then
    # there is no point in checking the KKT conditions and we throw an
    # exception.
    timeRuns1 = time.clock() - start1

    start = time.clock()
    mdl.solve()
    timeRuns = time.clock() - start
    solution = mdl.solution
    if not mdl.solution.get_status() == mdl.solution.status.optimal:
        raise Exception("Failed to solve problem to optimality")




    fval = np.float64(solution.get_objective_value())
    X = solution.get_values()

    with open(savefile, "w") as att_file:
        att_file.write("Time make extensive form (seconds) = " + str(timeRuns1) + '\n\n')
        att_file.write("Time (seconds) = " + str(timeRuns) + '\n\n')
        att_file.write("fval = " + str(fval) + "\n\n")
        att_file.write("X = " + str(X[0:300]) + '\n\n')


if __name__ == "__main__":
    run('hellinger', 0.05, 'news0.mat', 'news1.mat', 'news2.mat', 'news3.mat', './result/newscqp.txt')
