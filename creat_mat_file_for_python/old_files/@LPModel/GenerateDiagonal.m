function [iOut,jOut,sOut] = GenerateDiagonal( obj, matrixIn, subDiag )

% GenerateDiagonal generates the sparse matrix coordinates of the block
% diagonals and sub-diagonals of the constraint matrix A_full. It generates
% copies of matrixIn on the subDiag'th sub-diagonal of a matrix with obj.timePeriods
% periods.
% 
% Note: subDiag = 0 is the main block diagonal.
%       subDiag = 1 is the first block sub-diagonal, etc.

assert(subDiag >= 0)
assert(subDiag < obj.timePeriods)

[rowsM,colsM] = size(matrixIn);

[iIn, jIn, sIn]  = find(matrixIn);
nzM = length(sIn);

iOut = zeros( (obj.timePeriods-subDiag)*length(sIn), 1 );
jOut = iOut;
sOut = iOut;

for pp=subDiag+1:obj.timePeriods
    iOut( (pp-subDiag-1)*nzM + (1:nzM) ) = iIn + (pp-1)*rowsM;
    jOut( (pp-subDiag-1)*nzM + (1:nzM) ) = jIn + (pp-subDiag-1)*colsM;
    sOut( (pp-subDiag-1)*nzM + (1:nzM) ) = sIn;
end