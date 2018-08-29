function [first, second, third, fourth]=make_matrix_for_water_large_FULL_on(type,lpfile,savefile1,savefile2,savefile3,savefile4)
% matlab "save" needs "-V7.3" to save large variables
% instead of "-V7.3", fourth stage variables are divided in to three
% fourth1.mat = fourth.StagePeriods,fourth.obj
% fourth2.mat = fourth.A, fourth.B
% fourth3.mat = fourth.rhs, fourth.lb, fourth.ub







load(lpfile)

num2stage = 4*2*48;
num3stage = 4*2;
num4stage = 4*2;
StagePeriods=[3,9,10,15];
num_var = length(lp.c)/StagePeriods(1);num_row = length(lp.b)/StagePeriods(1);

%% data lp
tmp.c=lp.Getq(1);
tmp.A=lp.GetD(1);
tmp.B=lp.GetB(1);
% tmp.b=lp.Getd(1);
tmp.l=lp.Getl2(1);
tmp.u=lp.Getu2(1);


%% First
first.StagePeriods=StagePeriods(1);
first.obj=lp.c;
first.A=lp.A;
first.rhs=lp.b;
first.lb=lp.l; 
first.ub=lp.u;
first.obs = repmat(repmat(4*[0.6232 0.0891 0.0749 0.2128],1,2),1,48);
first.numScenarios = num2stage;


%% Second_tmp
second_tmp.StagePeriods=StagePeriods(2);
second_tmp.obj=tmp.c(1:num_var*sum(StagePeriods(2:2)));
second_tmp.A=tmp.A(1:num_row*sum(StagePeriods(2:2)),1:num_var*sum(StagePeriods(2:2)));
second_tmp.B=tmp.B(1:num_row*sum(StagePeriods(2:2)),1:num_var*sum(StagePeriods(1:1)));
% second_tmp.rhs=tmp.b(1:num_row*sum(StagePeriods(2:2)));
second_tmp.lb=tmp.l(1:num_var*sum(StagePeriods(2:2)));
second_tmp.ub=tmp.u(1:num_var*sum(StagePeriods(2:2)));
second_tmp.obs = repmat(4*[0.4757 0.0960 0.0777 0.3506],1,2);
second_tmp.numScenarios = num3stage;

%% Third_tmp
third_tmp.StagePeriods=StagePeriods(3);
third_tmp.obj=tmp.c(num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.A=tmp.A(num_row*sum(StagePeriods(2:2))+1:num_row*sum(StagePeriods(2:3)),num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.B=-tmp.A(num_row*sum(StagePeriods(2:2))+1:num_row*sum(StagePeriods(2:3)),1:num_var*sum(StagePeriods(2:2)));
% third_tmp.rhs=tmp.b(num_row*sum(StagePeriods(2:2))+1:num_row*sum(StagePeriods(2:3)));
third_tmp.lb=tmp.l(num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.ub=tmp.u(num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
third_tmp.obs = repmat(4*[0.3787 0.0831 0.0601 0.4781],1,2);
third_tmp.numScenarios = num4stage;



%% Fourth_tmp
fourth_tmp.StagePeriods=StagePeriods(4);
fourth_tmp.obj=tmp.c(num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));
fourth_tmp.A=tmp.A(num_row*sum(StagePeriods(2:3))+1:num_row*sum(StagePeriods(2:4)),num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));
fourth_tmp.B=-tmp.A(num_row*sum(StagePeriods(2:3))+1:num_row*sum(StagePeriods(2:4)),num_var*sum(StagePeriods(2:2))+1:num_var*sum(StagePeriods(2:3)));
% fourth_tmp.rhs=tmp.b(num_row*sum(StagePeriods(2:3))+1:num_row*sum(StagePeriods(2:4)));
fourth_tmp.lb=tmp.l(num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));
fourth_tmp.ub=tmp.u(num_var*sum(StagePeriods(2:3))+1:num_var*sum(StagePeriods(2:4)));


%% convert to row vector
first.obj=first.obj(:)';second_tmp.obj=second_tmp.obj(:)';third_tmp.obj=third_tmp.obj(:)';fourth_tmp.obj=fourth_tmp.obj(:)';
first.rhs=first.rhs(:)';%second_tmp.rhs=second_tmp.rhs(:)';third_tmp.rhs=third_tmp.rhs(:)';fourth_tmp.rhs=fourth_tmp.rhs(:)';
first.lb=first.lb(:)';second_tmp.lb=second_tmp.lb(:)';third_tmp.lb=third_tmp.lb(:)';fourth_tmp.lb=fourth_tmp.lb(:)';
first.ub=first.ub(:)';second_tmp.ub=second_tmp.ub(:)';third_tmp.ub=third_tmp.ub(:)';fourth_tmp.ub=fourth_tmp.ub(:)';





%% Scenario Tree
for i=1:num2stage
    second.StagePeriods{i,1}=second_tmp.StagePeriods;
    second.obj{i,1}=second_tmp.obj;
    second.A{i,1}=second_tmp.A;
    second.B{i,1}=second_tmp.B;
    second.lb{i,1}=second_tmp.lb;
    second.ub{i,1}=second_tmp.ub;
    second.obs{i,1}=second_tmp.obs;
    second.numScenarios{i,1}=second_tmp.numScenarios;
    for j=1:num3stage
        third.StagePeriods{i,j}=third_tmp.StagePeriods;
        third.obj{i,j}=third_tmp.obj;
        third.A{i,j}=third_tmp.A;
        third.B{i,j}=third_tmp.B;
        third.lb{i,j}=third_tmp.lb;
        third.ub{i,j}=third_tmp.ub;
        third.obs{i,j}=third_tmp.obs;
        third.numScenarios{i,j}=third_tmp.numScenarios;
        for k=1:num4stage
            fourth.StagePeriods{i,j,k}=fourth_tmp.StagePeriods;
            fourth.obj{i,j,k}=fourth_tmp.obj;
            fourth.A{i,j,k}=fourth_tmp.A;
            fourth.B{i,j,k}=fourth_tmp.B;
            fourth.lb{i,j,k}=fourth_tmp.lb;
            fourth.ub{i,j,k}=fourth_tmp.ub;
        end
    end
end


switch lower(type)
    case 'ni'
        for i=1:num2stage
            second.ub{i,1}(end-4)=0;
            for j=1:num3stage
                third.ub{i,j}(end-4)=0;
            end
        end
    case 'wwtp'
        for i=1:num2stage
            second.ub{i,1}(end-6)=0;
            for j=1:num3stage
                third.ub{i,j}(end-6)=0;
            end
        end
    case 'ipr'
        for i=1:num2stage
            second.ub{i,1}(end-6)=0;
            for j=1:num3stage
                third.ub{i,j}(end-6)=0;
            end
        end
    otherwise
        error('Type,Unknown')
end





%% Generate rhs
[second_rhs, third_rhs, fourth_rhs] = make_full_rhs(type);
second.rhs = second_rhs;
third.rhs = third_rhs;
fourth.rhs = fourth_rhs;

numStages=4;
save(savefile1, 'first', 'second','third','numStages')

tmp1 = fourth;
clear fourth 
fourth.StagePeriods=tmp1.StagePeriods;
fourth.obj=tmp1.obj;
save(savefile2, 'fourth');

clear fourth
fourth.A=tmp1.A;
fourth.B=tmp1.B;
save(savefile3, 'fourth');

clear fourth
fourth.rhs=tmp1.rhs;
fourth.lb=tmp1.lb;
fourth.ub=tmp1.ub;
save(savefile4, 'fourth');






