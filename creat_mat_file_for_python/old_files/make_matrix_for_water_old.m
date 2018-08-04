function [first, second,third,fourth]=make_matrix_for_water_old(lpfile,scenario, num2stage,num3stage,num4stage,seed, savefile)


rng(seed)
load(lpfile)
num_var = 100;num_row = 60;

% time_series_index = [17;18;22;23;27;28;32;33;37;38;42;43;45;46;50;51;55;56;58;59];
StagePeriods=[3,9,10,15];

tmp.c=lp.Getq(scenario);
tmp.A=lp.GetD(scenario);
tmp.B=lp.GetB(scenario);
tmp.b=lp.Getd(scenario);
tmp.l=lp.Getl2(scenario);
tmp.u=lp.Getu2(scenario);


%% First
first.StagePeriods=StagePeriods(1);
first.obj=lp.c;
first.A=lp.A;
first.rhs=lp.b;
first.lb=lp.l;
first.ub=lp.u;
first.obs = ones(1,num2stage);
first.numScenarios = num2stage;


%% Second_tmp
second_tmp.StagePeriods=StagePeriods(2);
second_tmp.obj=tmp.c(1:num_var*sum(StagePeriods(2:2)));
second_tmp.A=tmp.A(1:num_row*sum(StagePeriods(2:2)),1:num_var*sum(StagePeriods(2:2)));
second_tmp.B=tmp.B(1:num_row*sum(StagePeriods(2:2)),1:num_var*sum(StagePeriods(1:1)));
second_tmp.rhs=tmp.b(1:num_row*sum(StagePeriods(2:2)));
second_tmp.lb=tmp.l(1:num_var*sum(StagePeriods(2:2)));
second_tmp.ub=tmp.u(1:num_var*sum(StagePeriods(2:2)));
second_tmp.obs = ones(1,num3stage);
second_tmp.numScenarios = num3stage;

%% Third_tmp
third_tmp.StagePeriods=StagePeriods(3);
third_tmp.obj=tmp.c(num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.A=tmp.A(num_row*sum(StagePeriods(2:2))+1:num_row*sum(StagePeriods(2:3)),num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.B=-tmp.A(num_row*sum(StagePeriods(2:2))+1:num_row*sum(StagePeriods(2:3)),1:num_var*sum(StagePeriods(2:2)));
third_tmp.rhs=tmp.b(num_row*sum(StagePeriods(2:2))+1:num_row*sum(StagePeriods(2:3)));
third_tmp.lb=tmp.l(num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.ub=tmp.u(num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.obs = ones(1,num4stage);
third_tmp.numScenarios = num4stage;



%% Fourth_tmp
fourth_tmp.StagePeriods=StagePeriods(4);
fourth_tmp.obj=tmp.c(num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));
fourth_tmp.A=tmp.A(num_row*sum(StagePeriods(2:3))+1:num_row*sum(StagePeriods(2:4)),num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));
fourth_tmp.B=-tmp.A(num_row*sum(StagePeriods(2:3))+1:num_row*sum(StagePeriods(2:4)),num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
fourth_tmp.rhs=tmp.b(num_row*sum(StagePeriods(2:3))+1:num_row*sum(StagePeriods(2:4)));
fourth_tmp.lb=tmp.l(num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));
fourth_tmp.ub=tmp.u(num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));


%% convert to row vector
first.obj=first.obj(:)';second_tmp.obj=second_tmp.obj(:)';third_tmp.obj=third_tmp.obj(:)';fourth_tmp.obj=fourth_tmp.obj(:)';
first.rhs=first.rhs(:)';second_tmp.rhs=second_tmp.rhs(:)';third_tmp.rhs=third_tmp.rhs(:)';fourth_tmp.rhs=fourth_tmp.rhs(:)';
first.lb=first.lb(:)';second_tmp.lb=second_tmp.lb(:)';third_tmp.lb=third_tmp.lb(:)';fourth_tmp.lb=fourth_tmp.lb(:)';
first.ub=first.ub(:)';second_tmp.ub=second_tmp.ub(:)';third_tmp.ub=third_tmp.ub(:)';fourth_tmp.ub=fourth_tmp.ub(:)';


%% Generate Error
for i=1:num2stage
    secondStageError{i}=zeros(1,length(second_tmp.rhs));
    secondStageError{i}(second_tmp.rhs~=0)=normrnd(0,sqrt(55.27),1,sum(second_tmp.rhs~=0));
    for j=1:num3stage
        thirdStageError{i,j}=zeros(1,length(third_tmp.rhs));
        thirdStageError{i,j}(third_tmp.rhs~=0)=normrnd(0,sqrt(55.27),1,sum(third_tmp.rhs~=0));
        for k=1:num4stage
            fourthStageError{i,j,k}=zeros(1,length(fourth_tmp.rhs));
            fourthStageError{i,j,k}(fourth_tmp.rhs~=0)=normrnd(0,sqrt(55.27),1,sum(fourth_tmp.rhs~=0));
        end
    end
end


%% Scenario Tree
for i=1:num2stage
    second.StagePeriods{i,1}=second_tmp.StagePeriods;
    second.obj{i,1}=second_tmp.obj;
    second.A{i,1}=second_tmp.A;
    second.B{i,1}=second_tmp.B;
    second.rhs{i,1}=second_tmp.rhs+secondStageError{i};
    second.lb{i,1}=second_tmp.lb;
    second.ub{i,1}=second_tmp.ub;
    second.obs{i,1}=second_tmp.obs;
    second.numScenarios{i,1}=second_tmp.numScenarios;
    for j=1:num3stage
        third.StagePeriods{i,j}=third_tmp.StagePeriods;
        third.obj{i,j}=third_tmp.obj;
        third.A{i,j}=third_tmp.A;
        third.B{i,j}=third_tmp.B;
        third.rhs{i,j}=third_tmp.rhs+thirdStageError{i,j};
        third.lb{i,j}=third_tmp.lb;
        third.ub{i,j}=third_tmp.ub;
        third.obs{i,j}=third_tmp.obs;
        third.numScenarios{i,j}=third_tmp.numScenarios;
        for k=1:num4stage
            fourth.StagePeriods{i,j,k}=fourth_tmp.StagePeriods;
            fourth.obj{i,j,k}=fourth_tmp.obj;
            fourth.A{i,j,k}=fourth_tmp.A;
            fourth.B{i,j,k}=fourth_tmp.B;
            fourth.rhs{i,j,k}=fourth_tmp.rhs+fourthStageError{i,j,k};
            fourth.lb{i,j,k}=fourth_tmp.lb;
            fourth.ub{i,j,k}=fourth_tmp.ub;
        end
    end
end
numStages=4;
save(savefile, 'first', 'second','third','fourth','numStages')





