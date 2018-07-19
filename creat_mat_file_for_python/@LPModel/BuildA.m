function [A,A_st,A_lag,rowNames,colNames,userZone] = BuildA(obj, connectionsFile, inputFile)

% BuildA constructs the submatrices A, A_st and A_lag, as well as counts
% the number of Zones, and builds cell arrays of names Nr (names of
% constraint rows), Nc (shortened names of variables) and obj.variableNames
% (names of variables)

%% Load Data
disp('Loading Data...');

[Con, text] = xlsread(connectionsFile,'Connections'); % System Connection Matrix
userID = text(3:end,1);
sourceID = text(1,4:end);
userZone = Con(2:end,1);
userType = Con(2:end,2);
Con = Con(:,3:end);
numUsers = size(Con,1)-1;
numArcs = sum(sum(Con(2:end,:)));

% Enumerate user and source types
GW   =  1; WWTP =  2; SW    =  3;
WTP  =  4; DMY  =  5; RCHRG =  6;
P    =  7; NP   =  8; RTRN  =  9;
PMU  = 10; NPMU = 11; PIN   = 12;
NPIN = 13; PAG  = 14; NPAG  = 15;
MAX = max([GW,WWTP,SW,WTP,DMY,RCHRG,P,NP,RTRN,PMU,NPMU,PIN,NPIN,PAG,NPAG]);

%% Clear inputs file if connections have been altared

if obj.writeToExcel
    obj.Question1 = input('Has the connection matrix changed?  Yes=1  No=2 :');
    if obj.Question1 == 1
        blank = cell(1000,1);
        
        % Document old variable names in excel for comparison to new
        [~,str] = xlsread(inputFile,'b_vec','B:B');
        str(1) = {'Old'};
        xlswrite(inputFile,blank,'b_vec','A');
        xlswrite(inputFile,str,'b_vec','A');
        xlswrite(inputFile,blank,'b_vec','B2');
        
        [~,str] = xlsread(inputFile,'Upper Bounds','B:B');
        str(1) = {'Old'};
        xlswrite(inputFile,blank,'Upper Bounds','A');
        xlswrite(inputFile,str,'Upper Bounds','A');
        xlswrite(inputFile,blank,'Upper Bounds','B2');
        
        xlswrite(inputFile,blank,'Lower Bounds','A');
        xlswrite(inputFile,str,'Lower Bounds','A');
        xlswrite(inputFile,blank,'Lower Bounds','B2');
        
        xlswrite(inputFile,blank,'Costs','A');
        xlswrite(inputFile,str,'Costs','A');
        xlswrite(inputFile,blank,'Costs','B2');
        
        xlswrite(inputFile,blank,'kWh','A');
        xlswrite(inputFile,str,'kWh','A');
        xlswrite(inputFile,blank,'kWh','B2');
        sound(obj.y, obj.Fs);
    end
end

%% Arrange Connection Matrix by type and zone

disp('Arranging Connection Matrix...');

sortIndex = [find(Con(1,:) == GW), find(Con(1,:) == WWTP), ...
    find(Con(1,:) == SW), find(Con(1,:) == WTP), ...
    find(Con(1,:) == DMY), find(Con(1,:) == RCHRG), ...
    find(Con(1,:) == P), find(Con(1,:) == NP), ...
    find(Con(1,:) == RTRN)];
assert( length(sortIndex) == size(Con,2), 'Source list contains demand nodes' )
sourceType = Con(1,sortIndex);
Con = Con(2:end,sortIndex);
sourceID = sourceID(sortIndex);

waterSources = find(sourceType == GW | sourceType == SW);
storageSources = find(sourceType == GW | sourceType == RCHRG);
releaseSources = find(sourceType == SW | sourceType == WWTP);
ST = length(waterSources);

% Check that the number of arcs hasn't changed
assert(numArcs + sum(sum(Con==0)) - numel(Con) == 0);
assert(numArcs == sum(sum(Con==1)));


% Arrange pressure zones

sortIndex = [];
for ii=min(userZone):max(userZone)
    sortIndex = [sortIndex; find(userZone==ii)];
end
Con = Con(sortIndex,:);
userID = userID(sortIndex);
userType = userType(sortIndex);
userZone = userZone(sortIndex);


%% Check Return Matrix

if obj.writeToExcel && ...
        input('Does Return Matrix need to be updated? Yes=1  No=2:  ') == 1;
    % if prompt == 1 % input default values
    blank = cell(100,100);
    xlswrite(inputFile,blank,'Returns','A1');
    Return_Matrix = ret;
    ret = num2cell(ret);
    ret = vertcat(rtrnID,ret);
    b = {[]};
    retsourceID = vertcat(b,retsourceID);
    Return_Write = horzcat(retsourceID,ret);
    xlswrite(inputFile,Return_Write,'Returns')
    disp('Are any returns other than default values?');
    disp('');
    question = input('Yes=1  No=2  : ');
    if question == 1 % modify defaults
        disp('Revise LP_Order excel file then save and close.');
        question = input('Enter 1 when complete: ');
        if question == 1
            Return_Matrix = xlsread(inputFile,'Returns');
        end
    else
        Return_Matrix = xlsread(inputFile,'Returns');% Use defaults
    end
else
    Return_Matrix = xlsread(inputFile,'Returns'); % Use previous values
end
% preallocate
disp('preallocating...');

numConstraints = numUsers*2 + ST;
numVars = numArcs + length(storageSources) + length(releaseSources) + numUsers;

A = zeros(numConstraints,numVars);
A_st = zeros(numConstraints,numVars);
A_lag = zeros(numConstraints,numVars);

rowNames = cell(numConstraints,1);
rowNames(1:numUsers) = userID;
colNames = cell(1,numVars);
obj.variableNames = cell(numVars,1);

A( 1:numUsers             ,end-numUsers+1:end) = -eye(numUsers);
A((1:numUsers)+numUsers+ST,end-numUsers+1:end) = eye(numUsers);

% clc;

%% Build Equality Matrix A
disp('Building Matrix...');

lossWWTPSolid = 0.05;
lossEvaporation = 0.03;
lossRO = 0.25;
lossPercent = 0.01;
lossArray = -ones(MAX,MAX);
lossArray(WWTP,[WWTP,WTP]) = lossWWTPSolid;
lossArray(RCHRG,[WWTP,SW]) = 0;
lossArray(:,DMY) = 0;
lossArray(lossArray == -1) = lossPercent;

[users, sources] = find(Con);
for arc = 1:length(users)
    u = users(arc);
    s = sources(arc);
    
    % Find the row of the source node
    s_on_u = find(strcmp(sourceID{s},userID));
    if length(s_on_u) < 1
        if ismember(s, waterSources)
            s_on_u = numUsers + find(waterSources == s);
            rowNames{s_on_u} = sourceID{s};
        elseif sourceType(s) == DMY
            % Do nothing, no source for dummy nodes
        end
    elseif length(s_on_u) > 1
        error(['Too many copies of ' userID{s}])
    end
    
    colNames{arc} = sourceID{s};
    obj.variableNames{arc} = [sourceID{s} ' -->> ' userID{u}];
    
    % Inflow to user node
    if userType(u) ~= RCHRG
        A(u,arc) = 1;
    else
        A_lag(u,arc) = 1;
        A_lag(numUsers+ST+u,arc) = -lossEvaporation;
    end
    
    % Outflow from source node
    if ~isempty(s_on_u)
        A(s_on_u,arc) = -1;
    end
    
    % Loss along flows
    A(numUsers+ST+u,arc) = -lossArray(userType(u),sourceType(s));
    if strncmpi(sourceID(s),'RO',2) == 1 && ~ismember(userType(u), [NPMU, NPIN, NPAG])
        A(numUsers+ST+u,arc) = -lossRO;
    end
    if A(numUsers+ST+u,arc) == -lossPercent
        rowNames{numUsers+ST+u} = [userID{u} '-Loss'];
    else
        rowNames{numUsers+ST+u} = [userID{u} '-loss'];
    end
    
    % Return flow through potable demand sources
    if ismember( userType(u), [PMU, PIN, PAG] )
        uz = userZone(u);
        returnNode = find(userZone == uz & userType == RTRN);
        rowNames{numUsers+ST+returnNode} = [userID{returnNode} '-Loss'];
        if sourceType(s) == P
            A(returnNode,arc) = Return_Matrix(uz-1,uz-1);
            A(numUsers+ST+returnNode,arc) = -lossArray(userType(u),sourceType(s));
        elseif sourceType(s) == WTP
            A(returnNode,arc) = 0.98;
        end
    end
    
    % Storage variables
    if ismember(s, storageSources)
        stvar = numArcs + find(storageSources == s);
        A(s_on_u,stvar) = -1;
        A_st(s_on_u,stvar) = 1;
        colNames{stvar} = [sourceID{s} '-strg'];
    end
    
    % Release variables
    if ismember(s, releaseSources)
        relvar = numArcs + length(storageSources) + find(releaseSources == s);
        A(s_on_u,relvar) = -1;
        if sourceType(s) == SW
            colNames{relvar} = [sourceID{s} '-DSflow'];
        else
            colNames{relvar} = [sourceID{s} '-release'];
        end
    end
end
colNames(end-numUsers+1:end) = rowNames(end-numUsers+1:end);
obj.variableNames(numArcs+1:end) = colNames(numArcs+1:end)';

% Remove the loss variables, hopefully making the problem numerically
% easier
if obj.numStages > 1
    A(1:numUsers,:) = A(1:numUsers,:) + A((1:numUsers)+numUsers+ST,:);
    A_st(1:numUsers,:) = A_st(1:numUsers,:) + A_st((1:numUsers)+numUsers+ST,:);
    A_lag(1:numUsers,:) = A_lag(1:numUsers,:) + A_lag((1:numUsers)+numUsers+ST,:);
    assert(isequal( A(1:numUsers,end-numUsers+1:end), zeros(numUsers) ));
    A = A(1:numUsers+ST,1:numVars-numUsers);
    A_st = A_st(1:numUsers+ST,1:numVars-numUsers);
    A_lag = A_lag(1:numUsers+ST,1:numVars-numUsers);
end

A = sparse(A);
A_st = sparse(A_st);
A_lag = sparse(A_lag);
