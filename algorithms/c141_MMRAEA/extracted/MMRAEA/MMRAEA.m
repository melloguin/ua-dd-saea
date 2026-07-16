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
            % [R1-c141] Init = DoE 11D-1 INJETADO do artefato (D63/D87/D88) — NUNCA
            % regenerar. X0 e NATIVO (load_doe): entra DIRETO na Evaluation — o par
            % gera-LHS([0,1])+re-escala do stock (:19-21) e substituido JUNTO (mesma
            % classe da D94: injetar so no RHS re-escalaria de novo). Porte 4.15:
            % SOLUTION(dec) (API 3.x) -> Problem.Evaluation (L.7).
            A2    = Problem.Evaluation(Problem.data.X0);
            A1    = A2;
            RModel = cell(1,Problem.M);
            %% Optimization
            while Algorithm.NotTerminated(A2)
                A1Obj = A1.objs;
                A1Dec = A1.decs;
                n_treino_c141 = size(A1Dec,1);   % [R1-c141] n_acumulado do retreino (§17.6)
                tFit_c141 = tic;                 % [R1-c141] timing do fit dos M+2 RBFs (§17.6; nao altera decisao — D97)
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
                [Fitness, sde_fmodel_c141] = calFitness(A1Obj);   % [R1-c141] captura o flag do guard L4/D76 p/ log (decisao intacta)
                [FS, FY]   = dsmerge(A1Dec, Fitness);
                Fmodel = rbf_build(FS,FY);
                tfit_s_c141 = toc(tFit_c141);
                PopDec = A1Dec;
                PopObj = A1Obj;
                % Evolutionary Optimization
                [PopDec,PopObj,nsub_c141] = EAOptimization(PopDec,Problem,wmax,RModel,Fmodel,mS,FS);
                % Selection of new samples
                [PopNew, inf_c141] = InfillStrategy(PopDec,PopObj,Dmodel,DS,Fmodel,FS,A1);
                % re-evaluate infilled points and update A1 and A2
                % [R1-c141] guard batch-vazio [IMPL]: o batch e VARIAVEL e pode ser 0
                % (iteracao 0-FE — fiel ao paper); Evaluation([]) quebraria o CallFcn/
                % SOLUTION do 4.15. Porte 4.15: SOLUTION(PopNew) -> Problem.Evaluation.
                if ~isempty(PopNew)
                    New = Problem.Evaluation(PopNew);
                    A1  = UpdataArchive(A1,New);
                end
                % [R1-c141] D89 (fix herdado do c217/PCS:61): o obj.FE nativo NAO governa
                % o termino — infla com cache-hit (Evaluation soma length(Population)
                % incluindo duplicatas, que o c141 propoe rotineiramente: membros do
                % arquivo sobrevivem nas subpops e chegam ao infill). Re-sincroniza com o
                % saldo DISTINTO do wrapper -> NotTerminated para em bud.fe=31D-1; o
                % hard-stop real segue sendo o throw do FEBudget (D61).
                Problem.FE = Problem.data.bud.fe;
                A2 = A1;
                [FN,~] = NDSort(A2.objs,inf);
                A2 = A2(FN == 1);
                % [R1-c141] instrumentacao POS-decisao (NAO altera a busca — D97): ③ D45
                % (pool 2N: mu ARBFs + as 2 incertezas) + .jsonl §17.5/S.7 + timing §17.6.
                c141_instrument(Problem, A1, PopDec, PopObj, PopNew, Dmodel, DS, ...
                                Fmodel, FS, inf_c141, nsub_c141, n_treino_c141, ...
                                sde_fmodel_c141, tfit_s_c141);
            end
        end
    end
end
