function Q = ReadResults(obj,Q,inputLocation)

% ReadResults runs Alicia's code to understand the details of the solutions
% provided by the linear program

%% Get needed informationn

Var_name = obj.variableNames;
cost = obj.fullCostVector;

inputFile = [inputLocation,'Inputs.xlsx'];
solutionFile = [inputLocation,'Solution.xlsx'];

%% Write Variable Names to Input file

if obj.writeToExcel && obj.Question1 == 1
    disp('Updating Input file variables...');
    
    xlswrite(inputFile,Var_name,'Costs','B2');
    xlswrite(inputFile,Var_name,'Upper Bounds','B2');
    xlswrite(inputFile,Var_name,'Lower Bounds','B2');
    xlswrite(inputFile,Var_name,'kWh','B2');
    sound(obj.y, obj.Fs);
    
    Question2 = input('Enter 1 after "Inputs" file has been updated:  ');
    clc;
end

%% User Constraint Check

Residuals = round(obj.b - obj.A*Q);
check = any(Residuals);

Q = Q';
clc;

%% Sort solution by year

Q = roundn(Q,-2);
Flow = zeros(length(obj.A)/obj.timePeriods,obj.timePeriods);
Flow(1:length(obj.A)/obj.timePeriods,1)= Q(1:length(obj.A)/obj.timePeriods);

for xa = 1:obj.timePeriods-1
    xb = length(obj.A)/obj.timePeriods*xa;
    Flow(1:length(obj.A)/obj.timePeriods,xa+1) = Q(xb+1:xb+length(obj.A)/obj.timePeriods);
end

cost = reshape(cost,size(Flow));


%% Compute additional results

disp('Computing additional outputs...')

% Individual arc costs (dummy flow set to 0)
blank = cell(250,250);
xa = find(cost(:,1) == 1e10);
cost(xa,:) = 150;
Var_cost = Flow.*cost;

% Total system Losses (includes leakage, evap, and treatment)
xa = strfind(Var_name,'loss');
xa = find(~cellfun(@isempty,xa));
Treat_Evap_Loss = sum(sum(Flow(xa,:))); % loss to recharge evap and WWTP solids
xb = strfind(Var_name,'Loss');
xb = find(~cellfun(@isempty,xb));
Dist_Loss = sum(sum(Flow(xb,:))); % distribution losses (leakage)
Total_Loss = Treat_Evap_Loss +Dist_Loss;
xa = find(strncmpi(Var_name,'DemP',4));
Dist_PLoss = sum(sum(Flow(xa,:))); % potable user distribution losses
xa = find(strncmpi(Var_name,'DemNP',5));
Dist_NPLoss = sum(sum(Flow(xa,:))); % non-potable user distribution losses


% Total potable and Non-Potable Demand
xa = strfind(Var_name,'Dem');
xa = find(~cellfun(@isempty,xa));
xb = strfind(Var_name,'Dum');
xb = find(~cellfun(@isempty,xb));
xa=setdiff(xa,xb);
xb = strfind(Var_name,'Loss');
xb = find(~cellfun(@isempty,xb));
xc=setdiff(xa,xb);
xa = strfind(Var_name,'DemP');
xa = find(~cellfun(@isempty,xa));
xb = setdiff(xc,xa);
NP_Demand = sum(sum(Flow(xb,:))); % Total Non-potable Demand

xa = strfind(Var_name,'DemNP');
xa = find(~cellfun(@isempty,xa));
xd = setdiff(xc,xa); % potable demand
P_Demand = sum(sum(Flow(xd,:))); % Total Potable Demand

% Total WWTP release
xa = strfind(Var_name,'release');
xa = find(~cellfun(@isempty,xa));
Total_Release = sum(sum(Flow(xa,:)));

% Demands and Loss Percentage
xa = strfind(Var_name,'Dem');
xa = find(~cellfun(@isempty,xa));
xb = strfind(Var_name,'Dum');
xb = find(~cellfun(@isempty,xb));
xa=setdiff(xa,xb);
xb = strfind(Var_name,'Loss');
xb = find(~cellfun(@isempty,xb));
xc=setdiff(xa,xb);
xa = strfind(Var_name,'Dem');
xa = find(~cellfun(@isempty,xa));
xb = strfind(Var_name,'Dum');
xb = find(~cellfun(@isempty,xb));
xa=setdiff(xa,xb);
xd = setdiff(xa,xc);
User_Losses = sum(sum(Flow(xd,:))); % End user losses
User_Demand = P_Demand + NP_Demand;
Initial_Demand = User_Demand-User_Losses; % This is a mass balance check
System_Demand = User_Demand + Total_Loss; % Real demand is initial demand plus system losses
Percent_Loss = Dist_Loss/User_Demand;

% Total Demand Shortages
xa = strfind(Var_name,'Dum');
xa = find(~cellfun(@isempty,xa));
Total_Shortages = sum(sum(Flow(xa,:)));

% Total Potable Storage (including any IPR facilities)
xa = strfind(Var_name,'strg');
xa = find(~cellfun(@isempty,xa));
xb = strfind(Var_name,'NPstrg');
xb = find(~cellfun(@isempty,xb));
xa = setdiff(xa,xb);
Potable_Storage = sum(sum(Flow(xa,end)));



% Energy Consumption

kWh = xlsread(inputFile,'kWh');

kWh = kWh(2:end,:);
Energy = zeros(size(Flow));
for xa = 1:length(kWh)
    for xb = 1:size(Flow,2)
        Energy(xa,xb) = kWh(xa)*Flow(xa,xb);
    end
end
Total_Energy = sum(sum(Energy));

% GHG Emissions
GHG = 0.000623854*Total_Energy;

% Total IPR used for potable demand
xa = find(strncmpi(Var_name,'IPR',3));
xb = find(strncmpi(Var_name,'RO',2));
xc = union(xa,xb);
xb = strfind(Var_name,'DemP');
xb = find(~cellfun(@isempty,xb));
xa=intersect(xc,xb);
Total_IPR_P_Use = sum(sum(Flow(xa,:)));

% Total IPR used for non-potable demand
xa = find(strncmpi(Var_name,'IPR',3));
xb = find(strncmpi(Var_name,'RO',2));
xc = union(xa,xb);
xb = strfind(Var_name,'DemNP');
xb = find(~cellfun(@isempty,xb));
xa=intersect(xc,xb);
Total_IPR_NP_Use = sum(sum(Flow(xa,:)));

% Total Reclaimed Water used for non-potable demand (not including IPR)
xd = strfind(Var_name,'DemNP');
xd = find(~cellfun(@isempty,xd));
xb = strfind(Var_name,'Dum');
xb = find(~cellfun(@isempty,xb));
xd=setdiff(xd,xb);
xb = strfind(Var_name,'loss');
xb = find(~cellfun(@isempty,xb));
xc=setdiff(xd,xb);
xb = strfind(Var_name,'Loss');
xb = find(~cellfun(@isempty,xb));
xc=setdiff(xd,xb);
xd = strmatch('P',Var_name);
xb = setdiff(xc,xd);
xb = setdiff(xb,xa);
Total_NP_Reuse = sum(sum(Flow(xb,:)));


% Total Demand met by reclaimed water
Total_Reuse = Total_NP_Reuse + Total_IPR_P_Use + Total_IPR_NP_Use;
Percent_Reuse = Total_Reuse/User_Demand;





%% Write to excel solution file

disp('Writing to excel...')

%     Flow = roundn(Flow,0);
Flow = num2cell(Flow);
Flow = horzcat(Var_name,Flow);
cost = num2cell(cost);
cost = horzcat(Var_name,cost);
%     cost = cost(:,1:obj.timePeriods);
Total_cost = sum(sum(Var_cost));
obj.Final = [Initial_Demand,Total_Release,Total_Loss,Dist_PLoss,Dist_NPLoss,Dist_Loss,Percent_Loss,Total_Shortages,Potable_Storage,...
    Total_cost/1e6, GHG/1e3,P_Demand, NP_Demand, User_Demand,...
    Total_NP_Reuse,Total_IPR_NP_Use,Total_IPR_P_Use, Total_Reuse, Percent_Reuse];
Var_cost = num2cell(Var_cost);
Var_cost = horzcat(Var_name,Var_cost);
if obj.writeToExcel
    if obj.Question1 == 1
        xlswrite(solutionFile,blank,'Solution','A2');
        xlswrite(solutionFile,Flow,'Solution','A2');
        xlswrite(solutionFile,blank,'Costs','A2');
        xlswrite(solutionFile,cost,'Costs','A2');
        xlswrite(solutionFile,blank,'Price','A2');
        xlswrite(solutionFile,Var_cost,'Price','A2');
        xlswrite(solutionFile,obj.Final,'Final Stats','B5');
    else
        xlswrite(solutionFile,Flow,'Solution','A2');
        xlswrite(solutionFile,cost,'Costs','A2');
        xlswrite(solutionFile,Var_cost,'Price','A2');
        xlswrite(solutionFile,obj.Final,'Final Stats','B5');
    end
end
% sound(obj.y, obj.Fs);
% toc;
% xf = toc;
Flow = Flow(:,2:end);
Flow = cell2mat(Flow);
clc;


%% System details

disp(' ');
disp(' =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  = ');
disp('                                      Sytem Outline');
disp(' =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  = ');

% disp(['Time to load data/construct matrix(min)  =  ',num2str(xf/60)]);
disp(' ');
disp(['Number of zones  =  ',num2str(floor(max(obj.Zones)))]);
disp(' ');
disp(['Number of arcs  =  ',num2str(length(obj.A)/obj.timePeriods)]);
disp(' ');
disp(['Number of years (yr)  =  ',num2str(obj.numYears)]);
disp(' ');
disp(['Time Periods = ',num2str(obj.timePeriods)]);
