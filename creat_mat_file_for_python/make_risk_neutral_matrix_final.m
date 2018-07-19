function make_risk_neutral_matrix_final(production, inventory, num2, num3, num4,seed,saveFile);

% production = production cost = [100,100,100,100]
% inventory = selling cost = [80,80,80,80]
% num2, num3, num4 = number of scen
rng(seed, 'twister')
numStages = 4;
first.obj = [production(1), inventory(1)];
first.lb = [0, 0];
first.ub = [inf, inf];
first.A = sparse([1 -1]);
first.rhs = normrnd(100,5);
first.obs = ones(1,num2);
first.prob = ones(1,num2)/num2;
first.numScenarios = num2;

for i=1:num2
    second.rhs{i,1} = normrnd(100,5);
    second.obj{i,1} = [production(2), inventory(2)];
    second.lb{i,1} = [0, 0];
    second.ub{i,1} = [inf, inf];
    second.A{i,1} = sparse([1 -1]);
    second.B{i,1} = sparse([0 1]);
    
    second.obs{i,1} = ones(1,num3);
    second.prob{i,1} = ones(1,num3)/num3;
    second.numScenarios{i,1} = num3;
    for j=1:num3
        third.rhs{i,j} = normrnd(100,5);
        third.obj{i,j} = [production(3), inventory(3)];
        third.lb{i,j} = [0, 0];
        third.ub{i,j} = [inf, inf];
        third.A{i,j} = sparse([1 -1]);
        third.B{i,j}=  sparse([0 1]);
        
        third.obs{i,j} = ones(1,num4);
        third.prob{i,j} = ones(1,num4)/num4;
        third.numScenarios{i,j} = num4;
        for k=1:num4
            fourth.rhs{i,j,k} = normrnd(100,5);
            fourth.obj{i,j,k} = [production(4), inventory(4)];
            fourth.lb{i,j,k} = [0, 0];
            fourth.ub{i,j,k} = [inf, inf];
            fourth.A{i,j,k} = sparse([1 -1]);
            fourth.B{i,j,k}= sparse([0 1]);
        end
    end
end
save(saveFile,'numStages', 'first', 'second', 'third', 'fourth')