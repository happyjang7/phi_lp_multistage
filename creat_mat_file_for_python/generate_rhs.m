function [second_rhs, third_rhs, fourth_rhs] = generate_rhs(GPCD_scen_num)
% GPCD_scen_num = 1:48

StagePeriods=[3,9,10,15];

load('empty_rhs.mat')
load('projected_Population.mat')
load('projected_GPCD.mat')
load('water_allocation.mat')
Population_all = fieldnames(Population);

GPCD_scen = GPCD_header{GPCD_scen_num+1}; %1,....,48


Current_stage = 2;
rhs = repmat(rhs,StagePeriods(Current_stage),1);
for PopNum = 1:2
    Population_scen = Population_all{PopNum}; % 1,2
    for AllotNum = 1:4
        Water_allocation_scen = water_allocation_header{AllotNum}; % 1,2,3
        
        
        RESIN_total_idx  = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),'Total'));
        RESIN_total      = eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(RESIN_total_idx),')'  ));
        Tucson = Population.Tucson.Tucson(sum(StagePeriods(1:Current_stage-1))+1:sum(StagePeriods(1:Current_stage)),2);        
        CAP = repmat(water_allocation(contains(water_allocation_header, Water_allocation_scen)),StagePeriods(Current_stage),1);
        rhs(:,contains(rhs_header,'CAP')) = -CAP.*(RESIN_total./Tucson);
        
        GPCD_idx = find(contains(GPCD_header,GPCD_scen));
        GPCD_pred = 0.00112*GPCD(sum(StagePeriods(1:Current_stage-1))+1:sum(StagePeriods(1:Current_stage)),GPCD_idx);
        
        Potable= 0.8;
        NonPotable = 1-Potable;
        switch Population_scen
            case  'TAZ_low'
                adjust_pop = 0.9;
            case  'WISP_high'
                adjust_pop = 1.1;
            otherwise
                msg = "Population_scen should be either 'WISP_high' or 'TAZ_low'";
                error(msg)
        end
        
        Zone_name ='C';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_C  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_C = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_C')) = Demand.DemP_C;
        rhs(:,contains(rhs_header,'DemNP_C')) = Demand.DemNP_C;
        
        
        Zone_name ='D';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_D  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_D = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_D')) = Demand.DemP_D;
        rhs(:,contains(rhs_header,'DemNP_D')) = Demand.DemNP_D;
        
        
        Zone_name ='E';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_E  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_E = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_E')) = Demand.DemP_E;
        rhs(:,contains(rhs_header,'DemNP_E')) = Demand.DemNP_E;
        
        
        
        
        Zone_name ='F';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_FS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_FS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_FN  = Demand.DemP_FS;
        Demand.DemNP_FN = Demand.DemNP_FS;
        rhs(:,contains(rhs_header,'DemP_FS')) = Demand.DemP_FS;
        rhs(:,contains(rhs_header,'DemNP_FS')) = Demand.DemNP_FS;
        rhs(:,contains(rhs_header,'DemP_FN')) = Demand.DemP_FN;
        rhs(:,contains(rhs_header,'DemNP_FN')) = Demand.DemNP_FN;
        
        
        
        Zone_name ='G';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_GS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_GS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_GN  = Demand.DemP_GS;
        Demand.DemNP_GN = Demand.DemNP_GS;
        rhs(:,contains(rhs_header,'DemP_GS')) = Demand.DemP_GS;
        rhs(:,contains(rhs_header,'DemNP_GS')) = Demand.DemNP_GS;
        rhs(:,contains(rhs_header,'DemP_GN')) = Demand.DemP_GN;
        rhs(:,contains(rhs_header,'DemNP_GN')) = Demand.DemNP_GN;
        
        
        
        Zone_name ='H';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_HS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_HS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_HN  = Demand.DemP_HS;
        Demand.DemNP_HN = Demand.DemNP_HS;
        rhs(:,contains(rhs_header,'DemP_HS')) = Demand.DemP_HS;
        rhs(:,contains(rhs_header,'DemNP_HS')) = Demand.DemNP_HS;
        rhs(:,contains(rhs_header,'DemP_HN')) = Demand.DemP_HN;
        rhs(:,contains(rhs_header,'DemNP_HN')) = Demand.DemNP_HN;
        
        
        Zone_name ='I';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_I  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_I = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_I')) = Demand.DemP_I;
        rhs(:,contains(rhs_header,'DemNP_I')) = Demand.DemNP_I;
        
        tmp = rhs';
        if PopNum == 1
            second_rhs{AllotNum,1} = tmp(:)';
        elseif PopNum == 2
            second_rhs{4+AllotNum,1} = tmp(:)';
        end
    end
end

load('empty_rhs.mat')
Current_stage = 3;
rhs = repmat(rhs,StagePeriods(Current_stage),1);
for PopNum = 1:2
    Population_scen = Population_all{PopNum}; % 1,2
    for AllotNum = 1:4
        Water_allocation_scen = water_allocation_header{AllotNum}; % 1,2,3
        
        Supply = repmat(water_allocation(contains(water_allocation_header, Water_allocation_scen)),StagePeriods(Current_stage),1);
        rhs(:,contains(rhs_header,'CAP')) = -Supply;
        
        GPCD_idx = find(contains(GPCD_header,GPCD_scen));
        GPCD_pred = 0.00112*GPCD(sum(StagePeriods(1:Current_stage-1))+1:sum(StagePeriods(1:Current_stage)),GPCD_idx);
        
        Potable= 0.8;
        NonPotable = 1-Potable;
        switch Population_scen
            case  'TAZ_low'
                adjust_pop = 0.9;
            case  'WISP_high'
                adjust_pop = 1.1;
            otherwise
                msg = "Population_scen should be either 'WISP_high' or 'TAZ_low'";
                error(msg)
        end
        
        Zone_name ='C';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_C  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_C = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_C')) = Demand.DemP_C;
        rhs(:,contains(rhs_header,'DemNP_C')) = Demand.DemNP_C;
        
        
        Zone_name ='D';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_D  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_D = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_D')) = Demand.DemP_D;
        rhs(:,contains(rhs_header,'DemNP_D')) = Demand.DemNP_D;
        
        
        Zone_name ='E';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_E  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_E = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_E')) = Demand.DemP_E;
        rhs(:,contains(rhs_header,'DemNP_E')) = Demand.DemNP_E;
        
        
        
        
        Zone_name ='F';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_FS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_FS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_FN  = Demand.DemP_FS;
        Demand.DemNP_FN = Demand.DemNP_FS;
        rhs(:,contains(rhs_header,'DemP_FS')) = Demand.DemP_FS;
        rhs(:,contains(rhs_header,'DemNP_FS')) = Demand.DemNP_FS;
        rhs(:,contains(rhs_header,'DemP_FN')) = Demand.DemP_FN;
        rhs(:,contains(rhs_header,'DemNP_FN')) = Demand.DemNP_FN;
        
        
        
        Zone_name ='G';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_GS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_GS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_GN  = Demand.DemP_GS;
        Demand.DemNP_GN = Demand.DemNP_GS;
        rhs(:,contains(rhs_header,'DemP_GS')) = Demand.DemP_GS;
        rhs(:,contains(rhs_header,'DemNP_GS')) = Demand.DemNP_GS;
        rhs(:,contains(rhs_header,'DemP_GN')) = Demand.DemP_GN;
        rhs(:,contains(rhs_header,'DemNP_GN')) = Demand.DemNP_GN;
        
        
        
        Zone_name ='H';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_HS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_HS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_HN  = Demand.DemP_HS;
        Demand.DemNP_HN = Demand.DemNP_HS;
        rhs(:,contains(rhs_header,'DemP_HS')) = Demand.DemP_HS;
        rhs(:,contains(rhs_header,'DemNP_HS')) = Demand.DemNP_HS;
        rhs(:,contains(rhs_header,'DemP_HN')) = Demand.DemP_HN;
        rhs(:,contains(rhs_header,'DemNP_HN')) = Demand.DemNP_HN;
        
        
        Zone_name ='I';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_I  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_I = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_I')) = Demand.DemP_I;
        rhs(:,contains(rhs_header,'DemNP_I')) = Demand.DemNP_I;
        
        tmp = rhs';
        if PopNum == 1
            third_tmp{1,AllotNum} = tmp(:)';
        elseif PopNum == 2
            third_tmp{1,4+AllotNum} = tmp(:)';
        end
    end
end

for i= 1:8
    for j=1:8
        third_rhs{i,j} = third_tmp{1,j};
    end
end





load('empty_rhs.mat')
Current_stage = 4;
rhs = repmat(rhs,StagePeriods(Current_stage),1);
for PopNum = 1:2
    Population_scen = Population_all{PopNum}; % 1,2
    for AllotNum = 1:4
        Water_allocation_scen = water_allocation_header{AllotNum}; % 1,2,3
        
        Supply = repmat(water_allocation(contains(water_allocation_header, Water_allocation_scen)),StagePeriods(Current_stage),1);
        rhs(:,contains(rhs_header,'CAP')) = -Supply;
        
        GPCD_idx = find(contains(GPCD_header,GPCD_scen));
        GPCD_pred = 0.00112*GPCD(sum(StagePeriods(1:Current_stage-1))+1:sum(StagePeriods(1:Current_stage)),GPCD_idx);
        
        Potable= 0.8;
        NonPotable = 1-Potable;
        switch Population_scen
            case  'TAZ_low'
                adjust_pop = 0.9;
            case  'WISP_high'
                adjust_pop = 1.1;
            otherwise
                msg = "Population_scen should be either 'WISP_high' or 'TAZ_low'";
                error(msg)
        end
        
        Zone_name ='C';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_C  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_C = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_C')) = Demand.DemP_C;
        rhs(:,contains(rhs_header,'DemNP_C')) = Demand.DemNP_C;
        
        
        Zone_name ='D';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_D  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_D = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_D')) = Demand.DemP_D;
        rhs(:,contains(rhs_header,'DemNP_D')) = Demand.DemNP_D;
        
        
        Zone_name ='E';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_E  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_E = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_E')) = Demand.DemP_E;
        rhs(:,contains(rhs_header,'DemNP_E')) = Demand.DemNP_E;
        
        
        
        
        Zone_name ='F';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_FS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_FS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_FN  = Demand.DemP_FS;
        Demand.DemNP_FN = Demand.DemNP_FS;
        rhs(:,contains(rhs_header,'DemP_FS')) = Demand.DemP_FS;
        rhs(:,contains(rhs_header,'DemNP_FS')) = Demand.DemNP_FS;
        rhs(:,contains(rhs_header,'DemP_FN')) = Demand.DemP_FN;
        rhs(:,contains(rhs_header,'DemNP_FN')) = Demand.DemNP_FN;
        
        
        
        Zone_name ='G';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_GS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_GS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_GN  = Demand.DemP_GS;
        Demand.DemNP_GN = Demand.DemNP_GS;
        rhs(:,contains(rhs_header,'DemP_GS')) = Demand.DemP_GS;
        rhs(:,contains(rhs_header,'DemNP_GS')) = Demand.DemNP_GS;
        rhs(:,contains(rhs_header,'DemP_GN')) = Demand.DemP_GN;
        rhs(:,contains(rhs_header,'DemNP_GN')) = Demand.DemNP_GN;
        
        
        
        Zone_name ='H';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_HS  = Potable   *Zone_Population.*GPCD_pred*0.5;
        Demand.DemNP_HS = NonPotable*Zone_Population.*GPCD_pred*0.5;
        Demand.DemP_HN  = Demand.DemP_HS;
        Demand.DemNP_HN = Demand.DemNP_HS;
        rhs(:,contains(rhs_header,'DemP_HS')) = Demand.DemP_HS;
        rhs(:,contains(rhs_header,'DemNP_HS')) = Demand.DemNP_HS;
        rhs(:,contains(rhs_header,'DemP_HN')) = Demand.DemP_HN;
        rhs(:,contains(rhs_header,'DemNP_HN')) = Demand.DemNP_HN;
        
        
        Zone_name ='I';
        Zone_idx = find(contains(eval(strcat('Population.',Population_scen,'.',Population_scen,'_header')),Zone_name));
        Zone_Population = adjust_pop * eval(strcat(     'Population.',Population_scen,'.', Population_scen,'(sum(StagePeriods(1:',num2str(Current_stage),'-1))+1:sum(StagePeriods(1:',num2str(Current_stage),')),',num2str(Zone_idx),')'  ));
        Demand.DemP_I  = Potable   *Zone_Population.*GPCD_pred;
        Demand.DemNP_I = NonPotable*Zone_Population.*GPCD_pred;
        rhs(:,contains(rhs_header,'DemP_I')) = Demand.DemP_I;
        rhs(:,contains(rhs_header,'DemNP_I')) = Demand.DemNP_I;
        
        tmp = rhs';
        if PopNum == 1
            fourth_tmp{1,AllotNum} = tmp(:)';
        elseif PopNum == 2
            fourth_tmp{1,4+AllotNum} = tmp(:)';
        end
    end
end


for i= 1:8
    for j=1:8
        for k=1:8
            fourth_rhs{i,j,k} = third_tmp{1,k};
        end
    end
end





