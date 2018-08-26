import numpy as np
import lp_reader, PhiDivergence, PhiLP
import time
import os
import scipy.io as sio


def run(inputPHI, alpha, matlab_input_data,matlab_input_data1,matlab_input_data2,matlab_input_data3, saveFileName, saveFigureName):
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
    philp = PhiLP.set([lp.first, lp.second], inPhi, lp.first['obs'], inPhi.Rho(alpha, lp.first['obs']))
    philp1 = [PhiLP.set([lp.second[i], lp.third[i]],
                        inPhi, lp.second[i]['obs'], inPhi.Rho(alpha, lp.second[i]['obs']))
              for i in range(lp.first['numScenarios'])]
    philp2 = [[PhiLP.set([lp.third[i][j], lp.fourth[i][j]],
                         inPhi, lp.third[i][j]['obs'], inPhi.Rho(alpha, lp.third[i][j]['obs']))
               for j in range(lp.second[i]['numScenarios'])]
              for i in range(lp.first['numScenarios'])]

    # InitializeBenders: Forward
    philp.InitializeBenders(type='1-2stage', type1='Initial',x_parent=0)
    for i in range(lp.first['numScenarios']):
        philp1[i].InitializeBenders(type1='Initial',x_parent=philp.candidateSolution.X())
        for j in range(lp.second[i]['numScenarios']):
            philp2[i][j].InitializeBenders(type1='Initial',x_parent=philp1[i].candidateSolution.X())
            philp2[i][j].SolveSubProblems()

    philp.SetChildrenStage(philp1)
    # calculate true for upperbound
    for i in range(philp.lpModel_parent['numScenarios']):
        for j in range(philp1[i].lpModel_parent['numScenarios']):
            for k in range(philp2[i][j].lpModel_parent['numScenarios']):
                fval_true = philp2[i][j].candidateSolution.secondStageValues[k]
                philp2[i][j].candidateSolution.SetSecondStageValue_true(k, fval_true)
            philp2[i][j].MuFeasible_for_upperbound()
            philp1[i].candidateSolution.SetSecondStageValue_true(j, philp2[i][j].Get_h_True())
        philp1[i].MuFeasible_for_upperbound()
        philp.candidateSolution.SetSecondStageValue_true(i, philp1[i].Get_h_True())
    philp.MuFeasible_for_upperbound()

    philp.UpdateSolutions()
    philp.UpdateTolerances()
    totalProblemsSolved = 1
    totalCutsMade = 1
    philp.WriteProgress()
    print('Total cuts made: ' + str(totalCutsMade))
    print('Total problems solved: ' + str(totalProblemsSolved))
    print('=' * 100)

    #: Backward
    for i in range(lp.first['numScenarios']):
        for j in range(lp.second[i]['numScenarios']):
            philp2[i][j].GenerateCuts()
            philp2[i][j].SolveMasterProblem(x_parent=philp1[i].candidateSolution.X())
        philp1[i].SetChildrenStage(philp2[i])
        philp1[i].GenerateCuts()
        philp1[i].SolveMasterProblem(x_parent=philp.candidateSolution.X())

    philp.SetChildrenStage(philp1)
    philp.GenerateCuts()

    lower = np.array([])
    upper = np.array([])
    while not (philp.currentObjectiveTolerance <= philp.objectiveTolerance
               and philp.currentProbabilityTolerance <= philp.probabilityTolerance):
        if totalProblemsSolved >= 1000:
            break
        # SolveMasterProblem: Forward
        philp.SolveMasterProblem(type='1-2stage', x_parent=0)
        for i in range(lp.first['numScenarios']):
            philp1[i].SolveMasterProblem(x_parent=philp.candidateSolution.X())
            for j in range(lp.second[i]['numScenarios']):
                philp2[i][j].SolveMasterProblem(x_parent=philp1[i].candidateSolution.X())
                philp2[i][j].SolveSubProblems()

        philp.SetChildrenStage(philp1)
        # calculate true for upperbound
        for i in range(philp.lpModel_parent['numScenarios']):
            for j in range(philp1[i].lpModel_parent['numScenarios']):
                for k in range(philp2[i][j].lpModel_parent['numScenarios']):
                    fval_true = philp2[i][j].candidateSolution.secondStageValues[k]
                    philp2[i][j].candidateSolution.SetSecondStageValue_true(k, fval_true)
                philp2[i][j].MuFeasible_for_upperbound()
                philp1[i].candidateSolution.SetSecondStageValue_true(j, philp2[i][j].Get_h_True())
            philp1[i].MuFeasible_for_upperbound()
            philp.candidateSolution.SetSecondStageValue_true(i, philp1[i].Get_h_True())
        philp.MuFeasible_for_upperbound()

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
        for i in range(lp.first['numScenarios']):
            for j in range(lp.second[i]['numScenarios']):
                philp2[i][j].GenerateCuts()
                philp2[i][j].SolveMasterProblem(x_parent=philp1[i].candidateSolution.X())
            philp1[i].SetChildrenStage(philp2[i])
            philp1[i].GenerateCuts()
            philp1[i].SolveMasterProblem(x_parent=philp.candidateSolution.X())

        philp.SetChildrenStage(philp1)
        philp.GenerateCuts()



    timeRuns = time.clock() - start

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
