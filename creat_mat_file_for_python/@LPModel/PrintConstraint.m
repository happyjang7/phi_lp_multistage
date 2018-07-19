function PrintConstraint(obj, inConstraint, varargin)

% PrintConstraint prints the requested constraint(s) in a human readable
% format.
%
% PrintConstraint can be called in several ways:
% 1. obj.PrintConstraint( row ) prints the constraint by the specified row
%    number
% 2. obj.PrintConstraint( vector ) prints the constraints specified by each
%    row number in the vector.
% 3. obj.PrintConstraint( string ) prints the constraint for the node named
%    in the input string
% 4. obj.PrintConstraint( cellArray ) prints the constraints for each node
%    named in the cell array of strings.
%
% An optional numeric argument specifies the time period to print the
% constraint.  If omitted, the earliest time period for which all lag and
% storage variables appear is chosen.
%
% An optional string argument 'loss' may be given, which will show the loss
% variables explicitely, rather than expanding the loss variable.

inPeriod = obj.timeLag + 1;
expandLoss = true;

for ii = 1:length(varargin)
    if isnumeric(varargin{ii})
        inPeriod = varargin{ii};
    elseif ischar(varargin{ii}) && strcmpi(varargin{ii}, 'loss')
        expandLoss = ~expandLoss;
    end
end

if ischar(inConstraint)
    inConstraint = {inConstraint};
end

numUsers = length(find(not(cellfun('isempty', strfind(obj.Nr, 'oss')))));
rhs = reshape(obj.b,length(obj.Nr),obj.timePeriods);

% Method only works if identity matrices of opposite signs are at the end
% of Abase, but zeros are at the end of A_st and A_lag
assert( isequal(abs(obj.Abase(1:numUsers,end-numUsers+1:end)), eye(numUsers)) )
assert( isequal(obj.Abase(1:numUsers,end-numUsers+1:end), ...
               -obj.Abase(end-numUsers+1:end,end-numUsers+1:end)) )
assert( isequal(obj.A_st(1:numUsers,end-numUsers+1:end),zeros(numUsers)) )
assert( isequal(obj.A_st(end-numUsers+1:end,end-numUsers+1:end),zeros(numUsers)) )
assert( isequal(obj.A_lag(1:numUsers,end-numUsers+1:end),zeros(numUsers)) )
assert( isequal(obj.A_lag(end-numUsers+1:end,end-numUsers+1:end),zeros(numUsers)) )

for ic = inConstraint
    if iscell(ic)
        constraintName = ic{1};
        constraintRow = find(strcmp(constraintName,obj.Nr));
        if isempty(constraintRow)
            error(['No constraint named "' constraintName '"'])
        end
    elseif isnumeric(ic)
        constraintRow = ic;
        constraintName = obj.Nr{constraintRow};
    else
        error('inConstraint must be constraint name or index')
    end
    
    if expandLoss && constraintRow <= numUsers
        [lossRow,~] = find(obj.Abase(:,end-numUsers+constraintRow));
        assert( lossRow(1) == constraintRow )
        assert( length(lossRow) == 2 )
        constraintRow = lossRow;
    end
    
    disp(' ')
    disp(['Constraint for ' constraintName ' in time period t = ' num2str(inPeriod) ':'])
    
    constraint = strcat( ...
        WriteConstraint( obj, obj.A_lag, constraintRow, inPeriod, obj.timeLag ), ...
        WriteConstraint( obj, obj.A_st,  constraintRow, inPeriod, 1 ), ...
        WriteConstraint( obj, obj.Abase, constraintRow, inPeriod, 0 ) ...
        );
    
    constraint = sprintf( '%s = %f', constraint, ...
        sum(rhs(constraintRow,inPeriod)) );
    
    disp(constraint)
end
disp(' ')

function outString = WriteConstraint( obj, inMatrix, inRow, inPeriod, inDelay )
outString = '';
if inPeriod >= inDelay + 1 % Tests whether delay is great enough
    [~,c] = find(inMatrix(inRow,:));
    c = unique(c);
    for ii=1:length(c)
        % Get variable name, remove spaces for readability
        varName = obj.variableNames{c(ii)};
        varName(ismember(varName,' ')) = [];

        % Get value from row and loss row, if applicable
        v = full(inMatrix(inRow(1),c(ii)));
        if length(inRow) == 2
            loss = full(inMatrix(inRow(2),c(ii)));
        else
            loss = 0;
        end

        % Set delay string
        if inDelay == 0
            delayString = 't';
        else
            delayString = strcat( 't-', num2str(inDelay) );
        end

        % Concatenate variable output
        if loss ~= 0
            if v + loss ~= 0
                outString = strcat( outString, sprintf( ' %s (%0.2f %s %0.2f)[%s](%s)', ...
                    strsign(v), abs(v), ...
                    strsign(v*loss), abs(loss), ...
                    varName, delayString ) );
            end
        else
            outString = strcat( outString, sprintf( ' %s %0.2f[%s](%s)', ...
                strsign(v), abs(v), varName, delayString ) );
        end
    end
end


function outSign = strsign(inNum)

switch sign(inNum)
    case {1,0}
        outSign = '+';
    case -1
        outSign = '-';
end