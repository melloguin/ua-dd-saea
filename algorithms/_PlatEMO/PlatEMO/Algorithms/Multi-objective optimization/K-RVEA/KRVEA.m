classdef KRVEA < ALGORITHM
% <2018> <multi/many> <real/integer> <expensive>
% Surrogate-assisted RVEA
% alpha ---  2 --- The parameter controlling the rate of change of penalty
% wmax  --- 20 --- Number of generations before updating Kriging models
% mu    ---  5 --- Number of re-evaluated solutions at each generation

%------------------------------- Reference --------------------------------
% T. Chugh, Y. Jin, K. Miettinen, J. Hakanen, and K. Sindhya. A surrogate-
% assisted reference vector guided evolutionary algorithm for
% computationally expensive many-objective optimization. IEEE Transactions
% on Evolutionary Computation, 2018, 22(1): 129-142.
%------------------------------- Copyright --------------------------------
% Copyright (c) 2026 BIMK Group. You are free to use the PlatEMO for
% research purposes. All publications which use this platform or any code
% in the platform should acknowledge the use of "PlatEMO" and reference "Ye
% Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
% for evolutionary multi-objective optimization [educational forum], IEEE
% Computational Intelligence Magazine, 2017, 12(4): 73-87".
%--------------------------------------------------------------------------

% This function is written by Cheng He

    methods
        function main(Algorithm,Problem)
            %% Parameter setting
            [alpha,wmax,mu] = Algorithm.ParameterSet(2,20,5);

            %% Generate the reference points and population
            [V0,Problem.N] = UniformPoint(Problem.N,Problem.M);
            V     = V0;
            NI    = 11*Problem.D-1;
            % [R1-b3] injecao do DoE (D63/D87/D88): substitui o PAR gera+re-escala
            % (classe D94 — X0 NATIVO direto, a re-escala nunca roda). Init STOCK
            % NI=11D-1 mantido; X0 vem do artefato via Problem.data (run_b3).
            A2    = Problem.Evaluation(Problem.data.X0);
            A1    = A2;
            THETA = 5.*ones(Problem.M,Problem.D);
            Model = cell(1,Problem.M);

            %% Optimization
            while Algorithm.NotTerminated(A2)
                % Refresh the model and generate promising solutions
                A1Dec = A1.decs;
                A1Obj = A1.objs;
                n_treino = size(A1Dec,1);            % [R1-b3] §17.6: |A1| no fit
                t0_fit   = tic;                      % [R1-b3] §17.6: tempo do fit
                for i = 1 : Problem.M
                    % The parameter 'regpoly1' refers to one-order polynomial
                    % function, and 'regpoly0' refers to constant function. The
                    % former function has better fitting performance but lower
                    % efficiency than the latter one
                    dmodel     = dacefit(A1Dec,A1Obj(:,i),'regpoly1','corrgauss',THETA(i,:),1e-5.*ones(1,Problem.D),100.*ones(1,Problem.D));
                    Model{i}   = dmodel;
                    THETA(i,:) = dmodel.theta;
                end
                tfit_s = toc(t0_fit);                % [R1-b3] §17.6
                PopDec = A1Dec;
                snaps  = cell(1,wmax);               % [R1-b3] ③ DEF-C2: pop selecionada por ger. interna
                w      = 1;
                while w <= wmax
                    drawnow('limitrate');
                    OffDec = OperatorGA(Problem,PopDec);
                    PopDec = [PopDec;OffDec];
                    [N,~]  = size(PopDec);
                    PopObj = zeros(N,Problem.M);
                    MSE    = zeros(N,Problem.M);
                    for i = 1: N
                        for j = 1 : Problem.M
                            [PopObj(i,j),~,MSE(i,j)] = predictor(PopDec(i,:),Model{j});
                        end
                    end
                    index  = KEnvironmentalSelection(PopObj,V,(w/wmax)^alpha);
                    PopDec = PopDec(index,:);
                    PopObj = PopObj(index,:);
                    % [R1-b3] ③ snapshot da pop SELECIONADA desta geracao interna
                    % (DEF-C2; so LEITURA — nenhuma decisao alterada, D97).
                    snaps{w} = struct('dec',PopDec,'obj',PopObj,'mse',MSE(index,:));
                    % Adapt referece vectors
                    if ~mod(w,ceil(wmax*0.1))
                        V(1:Problem.N,:) = V0.*repmat(max(PopObj,[],1)-min(PopObj,[],1),size(V0,1),1);
                    end
                    w = w + 1; 
                end

                % Select mu solutions for re-evaluation
                [NumVf,~] = NoActive(A1Obj,V0);
                % [R1-b3] KrigingSelect com outputs de instrumentacao (L.2):
                % sel=index (:64), NumV2 (:15), Flag (:42). Decisoes intactas.
                [PopNew,sel,NumV2,Flag] = KrigingSelect(PopDec,PopObj,MSE(index,:),V,V0,NumVf,0.05*Problem.N,mu,(w/wmax)^alpha);
                New       = Problem.Evaluation(PopNew);
                A2        = [A2,New];
                % [R1-b3] guarda do crash latente (anchors b3-updataarchive-guard):
                % nzero = clusters vazios do kmeans (zeros de Next filtrados).
                [A1,nzero] = UpdataArchive(A1,New,V,mu,NI);
                % [R1-b3] sync D89 (herdado do c217, PCS:56): o obj.FE nativo NAO
                % governa; re-sincroniza com o saldo DISTINTO do wrapper apos o
                % infill (b3 PODE propor duplicata: PopDec parte de A1Dec).
                Problem.FE = Problem.data.bud.fe;
                % [R1-b3] instrumentacao POS-decisao (D97): ③ + .jsonl + timing.
                b3_instrument(Problem, A1, snaps, PopNew, sel, NumVf, NumV2, ...
                              Flag, 0.05*Problem.N, mu, nzero, n_treino, tfit_s);
            end
        end
    end
end