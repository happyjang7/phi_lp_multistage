function make_matrix_for_water_qual(n,save0,save1,save2,save3)
load('NI_first_second_third.mat')
first.obs = ones(1,n);
first.numScenarios =n;

for i=1:n
    StagePeriods{i,1}=second.StagePeriods{i,1};
    obj{i,1}=second.obj{i,1};
    A{i,1}=second.A{i,1};
    B{i,1}=second.B{i,1};
    lb{i,1}=second.lb{i,1};
    ub{i,1}=second.ub{i,1};
    obs{i,1}=ones(1,n);
    numScenarios{i,1}=n;
    rhs{i,1}=second.rhs{i,1}; 
end
second.StagePeriods=StagePeriods;
second.obj = obj;
second.A = A;
second.B = B;
second.lb = lb;
second.ub = ub;
second.obs =obs;
second.numScenarios =numScenarios;
second.rhs = rhs;

clear StagePeriods obj A B lb ub obs numScenarios rhs tmp
for i=1:n
    for j=1:n
        StagePeriods{i,j}=third.StagePeriods{i,j};
        obj{i,j}=third.obj{i,j};
        A{i,j}=third.A{i,j};
        B{i,j}=third.B{i,j};
        lb{i,j}=third.lb{i,j};
        ub{i,j}=third.ub{i,j};
        obs{i,j}=ones(1,n);
        numScenarios{i,j}=n;
        rhs{i,j}=third.rhs{i,j};
    end
end
third.StagePeriods=StagePeriods;
third.obj = obj;
third.A = A;
third.B = B;
third.lb = lb;
third.ub = ub;
third.obs =obs;
third.numScenarios =numScenarios;
third.rhs = rhs;


save(save0,'first','numStages','second','third')

clear StagePeriods obj A B lb ub obs numScenarios rhs tmp

load('NI_fourth1.mat')
for i=1:n
    for j=1:n
        for k=1:n
            StagePeriods{i,j,k}=fourth.StagePeriods{i,j,k};
            obj{i,j,k}=fourth.obj{i,j,k};
        end
    end
end
fourth.StagePeriods=StagePeriods;
fourth.obj = obj;

save(save1,'fourth')


load('NI_fourth2.mat')
for i=1:n
    for j=1:n
        for k=1:n
            A{i,j,k}=fourth.A{i,j,k};
            B{i,j,k}=fourth.B{i,j,k};
        end
    end
end
fourth.A = A;
fourth.B = B;

save(save2,'fourth')

load('NI_fourth3.mat')
for i=1:n
    for j=1:n
        for k=1:n           
            lb{i,j,k}=fourth.lb{i,j,k};
            ub{i,j,k}=fourth.ub{i,j,k};
            rhs{i,j,k}=fourth.rhs{i,j,k};
        end
    end
end
fourth.lb = lb;
fourth.ub = ub;
fourth.rhs = rhs;

save(save3,'fourth')