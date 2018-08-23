function make_newsvendor(production, inventory, num2, num3, num4,seed,saveFile,saveFile1,saveFile2,saveFile3)

rng(seed, 'twister')
numStages = 4;
first.obj = [production(1), inventory(1)];
first.lb = [0, 0];
first.ub = [inf, inf];
first.A = sparse([1 -1]);
first.rhs = normrnd(100,5);
first.obs = ones(1,num2);
first.numScenarios = num2;
first.StagePeriods = 1;


for i=1:num2
    second.rhs{i,1} = normrnd(100,5);
    second.obj{i,1} = [production(2), inventory(2)];
    second.lb{i,1} = [0, 0];
    second.ub{i,1} = [inf, inf];
    second.A{i,1} = sparse([1 -1]);
    second.B{i,1} = sparse([0 1]);
    second.obs{i,1} = ones(1,num3);
    second.numScenarios{i,1} = num3;
    second.StagePeriods{i,1} = 1;
    for j=1:num3
        third.rhs{i,j} = normrnd(100,5);
        third.obj{i,j} = [production(3), inventory(3)];
        third.lb{i,j} = [0, 0];
        third.ub{i,j} = [inf, inf];
        third.A{i,j} = sparse([1 -1]);
        third.B{i,j}=  sparse([0 1]);
        third.obs{i,j} = ones(1,num4);
        third.numScenarios{i,j} = num4;
        third.StagePeriods{i,j} = 1;
        for k=1:num4
            fourth.rhs{i,j,k} = normrnd(100,5);
            fourth.obj{i,j,k} = [production(4), inventory(4)];
            fourth.lb{i,j,k} = [0, 0];
            fourth.ub{i,j,k} = [inf, inf];
            fourth.A{i,j,k} = sparse([1 -1]);
            fourth.B{i,j,k}= sparse([0 1]);
            fourth.StagePeriods{i,j,k} = 1;
        end
    end
end
save(saveFile,'numStages', 'first', 'second', 'third')

tmp1 = fourth;
clear fourth 
fourth.StagePeriods=tmp1.StagePeriods;
fourth.obj=tmp1.obj;
save(saveFile1, 'fourth');

clear fourth
fourth.A=tmp1.A;
fourth.B=tmp1.B;
save(saveFile2, 'fourth');

clear fourth
fourth.rhs=tmp1.rhs;
fourth.lb=tmp1.lb;
fourth.ub=tmp1.ub;
save(saveFile3, 'fourth');

