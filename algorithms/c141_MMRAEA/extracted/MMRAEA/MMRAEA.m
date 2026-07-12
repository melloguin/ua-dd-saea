classdef MMRAEA < ALGORITHM
    % <multi/many> <real> <expensive>
    % Surrogate-assisted RVEA
    
    %------------------------------- Copyright --------------------------------
    % Copyright (c) 2021 BIMK Group. You are free to use the PlatEMO for
    % research purposes. All publications which use this platform or any code
    % in the platform should acknowledge the use of "PlatEMO" and reference "Ye
    % Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
    % for evolutionary multi-objective optimization [educational forum], IEEE
    % Computational Intelligence Magazine, 2017, 12(4): 73-87".
    %--------------------------------------------------------------------------
    % This function is written by Jiangtao Shen
    methods
        function main(Algorithm,Problem)
            %% Parameter
            wmax = 20;
            %% Generate the reference points and population
            NI    = 11*Problem.D-1;
            P     = UniformPoint(NI,Problem.D,'Latin');
            A2    = SOLUTION(repmat(Problem.upper-Problem.lower,NI,1).*P+repmat(Problem.lower,NI,1));
            A1    = A2;
            RModel = cell(1,Problem.M);
            %% Optimization
            while Algorithm.NotTerminated(A2)
                A1Obj = A1.objs;
                A1Dec = A1.decs;
                % Construct dominance prediction model
                DA1Obj = A1Obj;
                [FrontNo,~] = NDSort(DA1Obj,length(A1));
                [DS, DY]   = dsmerge(A1Dec, FrontNo');
                Dmodel = rbf_build(DS, DY);
                % Construct approximation models
                for i = 1 : Problem.M
                    [mS, mY]   = dsmerge(A1Dec, A1Obj(:,i));                  
                    rmodel = rbf_build(mS,mY);
                    RModel{i}   = rmodel;
                end
                % Construct fitness prediction model
                Fitness = calFitness(A1Obj);
                [FS, FY]   = dsmerge(A1Dec, Fitness);
                Fmodel = rbf_build(FS,FY);                
                PopDec = A1Dec;
                PopObj = A1Obj;
                % Evolutionary Optimization
                [PopDec,PopObj] = EAOptimization(PopDec,Problem,wmax,RModel,Fmodel,mS,FS); 
                % Selection of new samples
                PopNew = InfillStrategy(PopDec,PopObj,Dmodel,DS,Fmodel,FS,A1);
                % re-evaluate infilled points and update A1 and A2
                New     = SOLUTION(PopNew);
                A1 = UpdataArchive(A1,New);
                A2 = A1;
                [FN,~] = NDSort(A2.objs,inf);
                A2 = A2(FN == 1);
            end
        end
    end
end
