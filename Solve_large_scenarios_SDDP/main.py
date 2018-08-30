import numpy as np
import lp_reader, PhiDivergence, PhiLP_root, PhiLP_child, PhiLP_leaf
import time, copy
import os
import scipy.io as sio
import pickle



def run(numScen, inputPHI, alpha, matlab_input_data,matlab_input_data1,matlab_input_data2,matlab_input_data3, saveFileName, saveFigureName):
    # read data from Matlab .mat file
    mat_data = sio.loadmat(os.getcwd() + "/mat_data/" + matlab_input_data)
    fourth1 = sio.loadmat(os.getcwd() + "/mat_data/"+ matlab_input_data1)
    fourth2 = sio.loadmat(os.getcwd() + "/mat_data/"+ matlab_input_data2)
    fourth3 = sio.loadmat(os.getcwd() + "/mat_data/"+ matlab_input_data3)
    # set lp data
    lp = lp_reader.set(mat_data,fourth1,fourth2,fourth3)
    start = time.clock()
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



    totalProblemsSolved = 0
    totalCutsMade = 0
    lower = np.array([])
    upper = np.array([])
    # while not (philp.currentObjectiveTolerance <= philp.objectiveTolerance
    #            and philp.currentProbabilityTolerance <= philp.probabilityTolerance):
    while not philp.currentObjectiveTolerance <= philp.objectiveTolerance:
        if totalProblemsSolved >= 1000:
            break
        # SubProblem: Forward


        SampleList = np.array([(i, j, k)
                               for i in range(lp.first['numScenarios'])
                               for j in range(lp.second[i]['numScenarios'])
                               for k in range(lp.third[i][j]['numScenarios'])])
        idx = np.sort(np.random.choice(SampleList.shape[0], numScen, replace=False))
        Samples = SampleList[idx]

        iId = np.unique(Samples[:, 0])
        jId = np.unique(Samples[:, 0:2], axis=0)
        kId = Samples

        # SubProblem: Forward
        philp.SubProblem()
        for i in range(np.size(iId, 0)):
            philp1[iId[i]].SubProblem(x_parent=philp.candidateSolution.X())
        for j in range(np.size(jId, 0)):
            philp2[jId[j][0]][jId[j][1]].SubProblem(x_parent=philp1[jId[j][0]].candidateSolution.X())
        for k in range(np.size(kId, 0)):
            philp3[kId[k][0]][kId[k][1]][kId[k][2]].SubProblem(x_parent=philp2[kId[k][0]][kId[k][1]].candidateSolution.X())

        secondStageValues_selected = [philp1[i].candidateSolution.Fval() for i in iId]
        philp.muFeasible_selected(secondStageValues_selected)

        # calculate true for upperbound
        for j in range(np.size(jId, 0)):
            secondStageValues_selected = np.array([np.asscalar(philp3[jId[j][0]][jId[j][1]][kId[k][2]].candidateSolution.Fval())
                                          for k in range(np.size(kId, 0)) if
                                          jId[j][0] == kId[k][0] and jId[j][1] == kId[k][1]])
            philp2[jId[j][0]][jId[j][1]].secondStageValues_selected = secondStageValues_selected
            philp2[jId[j][0]][jId[j][1]].muFeasible_selected_true(secondStageValues_selected)
            philp2[jId[j][0]][jId[j][1]].MuFeasible_for_upperbound(secondStageValues_selected)

        for i in range(np.size(iId, 0)):
            secondStageValues_selected = np.array([np.asscalar(philp2[iId[i]][jId[j][1]].Get_h_True())
                                          for j in range(np.size(jId, 0)) if
                                          iId[i] == jId[j][0]])
            philp1[iId[i]].secondStageValues_selected = secondStageValues_selected
            philp1[iId[i]].muFeasible_selected_true(secondStageValues_selected)
            philp1[iId[i]].MuFeasible_for_upperbound(secondStageValues_selected)


        secondStageValues_selected = np.array([np.asscalar(philp1[iId[i]].Get_h_True()) for i in range(np.size(iId, 0))])
        philp.secondStageValues_selected = secondStageValues_selected
        philp.muFeasible_selected_true(secondStageValues_selected)
        philp.MuFeasible_for_upperbound(secondStageValues_selected)

        philp.UpdateSolutions()
        philp.UpdateTolerances()
        totalProblemsSolved = totalProblemsSolved + 1
        totalCutsMade = totalCutsMade + 1
        philp.WriteProgress()

        print('Total cuts made: ' + str(totalCutsMade))
        print('Total problems solved: ' + str(totalProblemsSolved))
        print('=' * 100)
        upper = np.append(upper, philp.zUpper / philp.objectiveScale)
        lower = np.append(lower, philp.zLower / philp.objectiveScale)

        #: Backward
        for j in range(np.size(jId, 0)):
            for k in range(lp.third[jId[j][0]][jId[j][1]]['numScenarios']):
                philp3[jId[j][0]][jId[j][1]][k].SubProblem(x_parent=philp2[jId[j][0]][jId[j][1]].candidateSolution.X())
            philp2[jId[j][0]][jId[j][1]].SetChildrenStage(philp3[jId[j][0]][jId[j][1]])
            philp2[jId[j][0]][jId[j][1]].GenerateCuts()

        for i in range(np.size(iId, 0)):
            for j in range(lp.second[iId[i]]['numScenarios']):
                philp2[iId[i]][j].SubProblem(x_parent=philp1[iId[i]].candidateSolution.X())
            philp1[iId[i]].SetChildrenStage(philp2[iId[i]])
            philp1[iId[i]].GenerateCuts()

        for i in range(lp.first['numScenarios']):
            philp1[i].SubProblem(x_parent=philp.candidateSolution.X())
        philp.SetChildrenStage(philp1)
        philp.GenerateCuts()
    timeRuns = time.clock() - start
    # output one item
    with open('results.pkl', 'wb') as f:
        pickle.dump([philp, philp1, philp2, philp3], f)
    import matplotlib.pyplot as plt

    x = np.arange(1, np.size(upper) + 1, dtype=int)
    plt.plot(x, upper, 'r')  # plotting t, a separately
    plt.plot(x, lower, 'b')  # plotting t, a separately
    plt.xlabel('iteration')
    plt.ylabel('fval')
    plt.title('Lower and Upper Bound: ' + inputPHI + " with alpha=" + str(alpha))
    plt.legend(['Upper', 'Lower'])
    # plt.show()

    plt.savefig(saveFigureName, bbox_inches='tight')
    plt.close()

    with open(saveFileName, "w") as att_file:
        att_file.write("Phi = " + inputPHI + "\n")
        att_file.write("alpha = " + str(alpha) + '\n\n')
        att_file.write("Current Objective Tolerance = " + str(philp.currentObjectiveTolerance) + '\n')
        att_file.write("Current Probability Tolerance = " + str(philp.currentProbabilityTolerance) + '\n')
        att_file.write("Iteratoins = " + str(totalProblemsSolved) + '\n')
        att_file.write("Time (seconds) = " + str(timeRuns) + '\n\n')

        att_file.write("ObjectiveValue = " + str(philp.ObjectiveValue()) + '\n')
        att_file.write("Lower Bound = " + str(philp.zLower / philp.objectiveScale) + '\n')
        att_file.write("Upper Bound = " + str(philp.zUpper / philp.objectiveScale) + '\n\n')

        att_file.write("X = " + str(philp.bestSolution.X()) + '\n')
        att_file.write("Mu = " + str(philp.bestSolution.Mu()) + '\n')
        att_file.write("Lambda = " + str(philp.bestSolution.Lambda()) + '\n')
        att_file.write("pWorst = " + str(philp.pWorst) + '\n')


if __name__ == "__main__":
    run('burg', 0.1, "new10.mat", './result/test1.txt', './result/test1.png')
