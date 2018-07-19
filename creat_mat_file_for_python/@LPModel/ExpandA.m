function A_full = ExpandA(obj,A,A_st,A_lag)

% ExpandA creates the complete constraint matrix for all time periods out
% of the submatrices A, A_st and A_lag.  These submatrices are copied along
% the diagonals of A_full

[rowsA,colsA] = size(A);

if obj.timeLag == 1
    A_st = A_st + A_lag;
    assert(issparse(A_st));
else
    [iA_lag_full,jA_lag_full,sA_lag_full] = obj.GenerateDiagonal( A_lag, obj.timeLag );
end

[iA_full,jA_full,sA_full] = obj.GenerateDiagonal( A, 0  );
[iA_st_full,jA_st_full,sA_st_full] = obj.GenerateDiagonal( A_st, 1 );

if obj.timeLag == 1
    i = [iA_full; iA_st_full];
    j = [jA_full; jA_st_full];
    s = [sA_full; sA_st_full];
else
    i = [iA_full; iA_st_full; iA_lag_full];
    j = [jA_full; jA_st_full; jA_lag_full];
    s = [sA_full; sA_st_full; sA_lag_full];
end

A_full = sparse(i,j,s,obj.timePeriods*rowsA,obj.timePeriods*colsA,length(i));
% assert(sum(sum(A_full~=A_full_old))==0);