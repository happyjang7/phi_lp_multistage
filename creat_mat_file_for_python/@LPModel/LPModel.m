% LPModel constructs and stores all the matrices and vectors needed to
% formulate a 1- or 2-stage LP.  It can construct the LP from either matrix
% data entered through MATLAB, or using Alicia Forrester's code to read
% water models from excel files.

classdef LPModel < handle
    
%     First stage/single stage LP matrices
    properties (GetAccess=public, SetAccess=private)
        c
        A
        b
        l
        u
        variableNames
        Final
    end
    
%     Second stage LP matrices
    properties (Access=private)
        q
        D
        d
        l2
        u2
        B
    end
    
%     Properties of the LP Water Model
    properties (GetAccess=public, SetAccess=immutable)
        numStages
        numScenarios
        timePeriods
        numYears
        timeLag
        firstStagePeriods
        folderCellArray
        numProfiles
        GPPD
        averagePerCapitaDemand
        gpd2afy
    end
    
%     Properties for expanding the scenario set
    properties (Access=public)
        zoneNames
        population
        demandMultiplier
        fractionDemandP
        profileNames
    end
    
%     Leftover properties
    properties %(Access=private)
        Abase
        A_st
        A_lag
        Nr
        Nc
        Zones
        fullCostVector
        y
        Fs
    end
    
%     Excel writing parameters
    properties (Access=private)
        writeToExcel = false;
        Question1 = 2;
        prompt = 2;
    end
    
    methods
%         The constructor determines what type of LP model to work with:
%           1. One-stage explicit model
%           2. Two-stage explicit model
%           3. One-stage excel water model
%           4. Two-stage excel water model
%         And sets the immutable data accordingly
        function obj = LPModel(varargin)
            if nargin == 0
                error('Must supply initialization arguments')
            end            
            if ischar(varargin{1})
                switch varargin{1}
                    case '1 stage'
                        obj.numStages = 1;
                        obj.numScenarios = 0;
                        obj.timePeriods = [];
                        obj.timeLag = [];
                        obj.firstStagePeriods = [];
                    case '2 stage'
                        obj.numStages = 2;
                        obj.numScenarios = varargin{2};
                        obj.timePeriods = [];
                        obj.timeLag = [];
                        obj.firstStagePeriods = [];
                        obj.SetBlankSecondStage;
                    otherwise
                        obj.folderCellArray = { varargin{1} };
                        obj.numStages = 1;
                        obj.numScenarios = 0;
                        obj.numYears = varargin{2};
                        obj.timeLag = varargin{3};
                        obj.timePeriods = obj.numYears * obj.timeLag;
                        obj.firstStagePeriods = obj.timePeriods;
                        [obj.y, obj.Fs] = wavread([obj.folderCellArray{1} 'bell']);
                        
                        % Average per capita demand is 135 gallons per day,
                        % converted to acre-feet per year
                        obj.gpd2afy = 0.00112;
                        obj.averagePerCapitaDemand = 135 * obj.gpd2afy;
                        
                        obj.GenerateDataFromExcel;
                end
            elseif iscellstr(varargin{1})
                obj.folderCellArray = varargin{1};
                obj.numStages = 2;
                obj.numYears = varargin{2};
                obj.timeLag = varargin{3};
                obj.timePeriods = obj.numYears * obj.timeLag;
                obj.firstStagePeriods = varargin{4} * obj.timeLag;
               [obj.y, obj.Fs] = audioread([obj.folderCellArray{1} 'bell.wav']);
                
                if length(varargin) > 4
                    if length(varargin) < 6
                        error('Need both number of profiles, and profile function')
                    end
                    obj.numProfiles = varargin{5};
                    %obj.GPPD = varargin{6};
                    obj.GPPD = varargin{1,6}(1:varargin{1,5},:);
                else
                    obj.numProfiles = 1;
                end
                obj.numScenarios = length(obj.folderCellArray) * obj.numProfiles;
                        
                % Average per capita demand is 135 gallons per day,
                % converted to acre-feet per year
                obj.gpd2afy = 0.00112;
                obj.averagePerCapitaDemand = 135 * obj.gpd2afy;
                
                obj.SetBlankSecondStage;
                obj.GenerateDataFromExcel;
            else
                error('Unrecognized initialization')
            end
        end
    end
    
    methods (Access=private)
        [A,A_st,A_lag,Nr,Nc,Zones] = BuildA(obj, ConnectionsFile, InputFile)
        [b1,UB1,LB1,Cost1,b2,UB2,LB2,Cost2,costOut] = BuildVectors(obj, cellInputFile)
        A_full = ExpandA(obj,A,A_st,A_lag)
        [iOut,jOut,sOut] = GenerateDiagonal( obj, matrixIn, subDiag )
        
%         SetBlankSecondStage sets all second stage data to blank arrays of
%         the correct size
        function SetBlankSecondStage( obj )
            if obj.numStages == 2
                obj.q = cell( 1, obj.numScenarios );
                obj.D = cell( 1, obj.numScenarios );
                obj.d = cell( 1, obj.numScenarios );
                obj.l2 = cell( 1, obj.numScenarios );
                obj.u2 = cell( 1, obj.numScenarios );
                obj.B = cell( 1, obj.numScenarios );
            else
                error( 'Must be a two stage problem' )
            end
        end
        
        function tf = IsValidScenario( obj, inScenario )
            if inScenario > 0 && inScenario <= obj.numScenarios
                tf = true;
            else
                error(['Input scenario number ' num2str(inScenario) ...
                    ' is wrong.  Scenarios must be numbered 1 to ' ...
                    num2str(obj.numScenarios)])
            end
        end
        
        function GenerateDataFromExcel( obj )
            cellConnectionsFile = strcat(obj.folderCellArray,'Connections.xlsx');
            cellInputFile = strcat(obj.folderCellArray,'Inputs.xlsx');
            [obj.Abase,obj.A_st,obj.A_lag,obj.Nr,obj.Nc,obj.Zones] ...
                = obj.BuildA(cellConnectionsFile{1}, cellInputFile{1});
            A_full_temp = obj.ExpandA(obj.Abase,obj.A_st,obj.A_lag);
            switch obj.numStages
                case 1
                    obj.SetA( A_full_temp );
                case 2
                    [rows,cols] = size(obj.Abase);
                    obj.SetA( A_full_temp(1:obj.firstStagePeriods*rows,1:obj.firstStagePeriods*cols) );
                    for omega = 1:obj.numScenarios
                        obj.SetD(A_full_temp(obj.firstStagePeriods*rows+1:end,obj.firstStagePeriods*cols+1:end),omega);
                        obj.SetB(-A_full_temp(obj.firstStagePeriods*rows+1:end,1:obj.firstStagePeriods*cols),omega);
                    end
            end
            [b1,UB1,LB1,Cost1,b2,UB2,LB2,Cost2,obj.fullCostVector] ...
                = obj.BuildVectors(cellInputFile);
            obj.Setb(b1);
            obj.Setl(LB1);
            obj.Setu(UB1);
            obj.Setc(Cost1');
            if obj.numStages == 2
                for omega = 1:obj.numScenarios
                    obj.Setq( Cost2(:,omega)', omega );
                    obj.Setd( b2(:,omega), omega );
                    obj.Setl2( LB2(:,omega), omega );
                    obj.Setu2( UB2(:,omega), omega );
                end
            end
        end
                
    end
    
%     Setting and Accessing Routines
    methods (Access=public)
        
        Q = ReadResults(obj,Q,InputFile,solutionFile)
        PrintConstraint(obj,inConstraint,varargin)
        
%         Read in data for the first stage
        function Setc( obj, inc )
            obj.c = inc;
        end
        function SetA( obj, inA )
            obj.A = inA;
        end
        function Setb( obj, inb )
            obj.b = inb;
        end
        function Setl( obj, inl )
            obj.l = inl;
        end
        function Setu( obj, inu )
            obj.u = inu;
        end
        
%         Read in data for the second stage
        function Setq( obj, inq, inScenario )
            if obj.IsValidScenario( inScenario )
                obj.q{inScenario} = inq;
            end
        end
        function SetD( obj, inD, inScenario )
            if obj.IsValidScenario( inScenario )
                obj.D{inScenario} = inD;
            end
        end
        function Setd( obj, ind, inScenario )
            if obj.IsValidScenario( inScenario )
                obj.d{inScenario} = ind;
            end
        end
        function Setl2( obj, inl2, inScenario )
            if obj.IsValidScenario( inScenario )
                obj.l2{inScenario} = inl2;
            end
        end
        function Setu2( obj, inu2, inScenario )
            if obj.IsValidScenario( inScenario )
                obj.u2{inScenario} = inu2;
            end
        end
        function SetB( obj, inB, inScenario )
            if obj.IsValidScenario( inScenario )
                obj.B{inScenario} = inB;
            end
        end
        
%         Accessor routines for second stage data
        function outq = Getq( obj, inScenario )
            if obj.IsValidScenario( inScenario )
                outq = obj.q{inScenario};
            end
        end
        function outD = GetD( obj, inScenario )
            if obj.IsValidScenario( inScenario )
                outD = obj.D{inScenario};
            end
        end
        function outd = Getd( obj, inScenario )
            if obj.IsValidScenario( inScenario )
                outd = obj.d{inScenario};
            end
        end
        function outl2 = Getl2( obj, inScenario )
            if obj.IsValidScenario( inScenario )
                outl2 = obj.l2{inScenario};
            end
        end
        function outu2 = Getu2( obj, inScenario )
            if obj.IsValidScenario( inScenario )
                outu2 = obj.u2{inScenario};
            end
        end
        function outB = GetB( obj, inScenario )
            if obj.IsValidScenario( inScenario )
                outB = obj.B{inScenario};
            end
        end
        
    end
end
        