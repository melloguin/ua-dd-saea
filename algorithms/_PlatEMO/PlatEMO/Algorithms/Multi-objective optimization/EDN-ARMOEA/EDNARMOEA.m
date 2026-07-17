classdef EDNARMOEA < ALGORITHM
% <2022> <multi/many> <real/integer> <expensive>
% Efficient dropout neural network based AR-MOEA
% delta --- 0.05 --- Threshold of judging the diversity
% wmax  ---   20 --- Number of generations before updating Kriging models
% Ke    ---    3 --- Number of the solutions to be revaluated in each iteration

%------------------------------- Reference --------------------------------
% D. Guo, X. Wang, K. Gao, Y. Jin, J. Ding, and T. Chai. Evolutionary
% optimization of high-dimensional multiobjective and many-objective
% expensive problems assisted by a dropout neural network. IEEE
% Transactions on Systems, Man, and Cybernetics: Systems, 2022, 52(4):
% 2084-2097.
%------------------------------- Copyright --------------------------------
% Copyright (c) 2026 BIMK Group. You are free to use the PlatEMO for
% research purposes. All publications which use this platform or any code
% in the platform should acknowledge the use of "PlatEMO" and reference "Ye
% Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
% for evolutionary multi-objective optimization [educational forum], IEEE
% Computational Intelligence Magazine, 2017, 12(4): 73-87".
%--------------------------------------------------------------------------

    methods
        function main(Algorithm,Problem)
            assert(~isempty(ver('nnet')),'The execution of EDN-ARMOEA requires the Deep Learning Toolbox.');
            
            %% Parameter setting
            [delta,wmax,Ke] = Algorithm.ParameterSet(0.05,20,3);            
            W     = UniformPoint(Problem.N,Problem.M);
            NI    = 11*Problem.D-1;
            % [R1-e7] injecao do DoE (D63/D87/D88): substitui o PAR gera+re-escala
            % das :31-:32 JUNTAS (classe D94 — X0 NATIVO direto na Evaluation, a
            % re-escala nunca roda; injetar so na :31 causaria dupla-escala em
            % WFG/BBOB). Init STOCK NI=11D-1 mantido; X0 vem do artefato (run_e7).
            A     = Problem.Evaluation(Problem.data.X0);
            tr_x  = A.decs;
            tr_y  = A.objs;
            [tr_xx,ps] = mapminmax(tr_x');tr_xx=tr_xx';
            [tr_yy,qs] = mapminmax(tr_y');tr_yy=tr_yy';
            Params.ps  = ps;Params.qs=qs;
            RatioOld   = [];

            %% Train the model
            % [R1-e7] §17.6: tempo do treino INICIAL (8e4 passos SGD) — emitido
            % como retreino extra do 1o ciclo pelo e7_instrument.
            t0_init    = tic;
            [net, Params] = trainmodel(tr_xx, tr_yy, Params);
            tfit_init_s = toc(t0_init);
            % [R1-e7] estado da instrumentacao (so leitura, D97): ymin em vigor
            % nas predicoes do ciclo corrente (C3 — SelectTrainData translada o y
            % por min(A.objs) a partir do 1o retreino; o treino inicial e CRU),
            % e contador de ciclos consecutivos SEM consumo de FE (guarda (c) do
            % D60 — saldo congelado por infill 100% duplicado; so LOGA).
            ymin_vig    = zeros(1,Problem.M);      % ciclo 1: espaco CRU
            espaco_vig  = "cru";
            stall_ciclos = 0;

            while Algorithm.NotTerminated(A)
                %% Update the model
                fe_ciclo0 = Problem.data.bud.fe;   % [R1-e7] p/ FE consumido no ciclo
                t0_fit  = tic;                     % [R1-e7] §17.6
                net=updatemodel(tr_xx, tr_yy, Params, net);
                tfit_s  = toc(t0_fit);             % [R1-e7] §17.6

                %% Generate the sampling points and random population
                popsize=Problem.N;
                PopDec=repmat(Problem.upper-Problem.lower,popsize,1).*rand(popsize,Problem.D)+repmat(Problem.lower,popsize,1);
                [PopObj, PopMSE, nneg]=Estimate(PopDec, net, Params, Problem.M);
                n_std_neg = nneg;                  % [R1-e7] guard sqrt (Estimate)
                [Archive,RefPoint,Range, Ratio] = UpdateRefPoint(PopObj,W,[]);
                if isempty(RatioOld)
                    RatioOld=Ratio;
                end

                %% Start the interations
                w=1;
                snaps = cell(1,wmax-1);            % [R1-e7] ③ DEF-C2: pop selecionada/ger. interna
                while w < wmax
                    MatingPool = MatingSelection(PopObj,RefPoint,Range);
                    OffspringDec  = OperatorGA(Problem,PopDec(MatingPool,:),{1,20,1,20});
                    [OffspringObj, OffspringMSE, nneg] = Estimate(OffspringDec, net, Params, Problem.M);
                    n_std_neg = n_std_neg + nneg;  % [R1-e7]
                    [Archive,RefPoint,Range, Ratio] = UpdateRefPoint([Archive;OffspringObj],W,Range);
                    MediatePopDec=[PopDec;OffspringDec];
                    MediatePopObj=[PopObj;OffspringObj];
                    MediatePopMSE=[PopMSE;OffspringMSE];
                    [Index,Range]       = EnvironmentalSelection(MediatePopObj,RefPoint,Range,popsize);
                    PopDec=MediatePopDec(Index,:);
                    PopObj=MediatePopObj(Index,:);
                    PopMSE=MediatePopMSE(Index,:);
                    % [R1-e7] ③ snapshot da pop SELECIONADA desta geracao interna
                    % (DEF-C2; so LEITURA — nenhuma decisao alterada, D97).
                    snaps{w} = struct('dec',PopDec,'obj',PopObj,'std',PopMSE);
                    w=w+1;
                end
                flag=RatioOld-Ratio<delta;
                PopNew=IndividualSelect(PopDec, PopObj, PopMSE, Ke, flag);
                RatioNew=Ratio;                    % [R1-e7] p/ o .jsonl (motivo)
                RatioVelho=RatioOld;               % [R1-e7]
                RatioOld=Ratio;
                New = Problem.Evaluation(PopNew);
                A   = [A,New];
                [tr_x, tr_y]=SelectTrainData(A, 11*Problem.D-1, length(New));
                [tr_xx,ps]=mapminmax(tr_x');tr_xx=tr_xx';
                [tr_yy,qs]=mapminmax(tr_y');tr_yy=tr_yy';
                Params.ps=ps;Params.qs=qs;
                % [R1-e7] sync D89 (herdado do c217, PCS:56): o obj.FE nativo NAO
                % governa; re-sincroniza com o saldo DISTINTO do wrapper (o e7 NAO
                % deduplica o infill — duplicata = cache-hit 0 FE, slot perdido).
                Problem.FE = Problem.data.bud.fe;
                % [R1-e7] guarda (c) do D60: ciclo sem consumir NENHUM FE (3
                % infills 100% duplicados) — detectado e LOGADO, nunca consertado.
                fe_ciclo = Problem.data.bud.fe - fe_ciclo0;
                if fe_ciclo == 0
                    stall_ciclos = stall_ciclos + 1;
                else
                    stall_ciclos = 0;
                end
                % [R1-e7] instrumentacao POS-decisao (D97): ③ + .jsonl + timing.
                e7_instrument(Problem, snaps, PopNew, size(tr_xx,1), ...
                              RatioVelho, RatioNew, delta, flag, ...
                              fe_ciclo, stall_ciclos, n_std_neg, ...
                              ymin_vig, espaco_vig, size(W,1), ...
                              tfit_s, tfit_init_s);
                tfit_init_s = NaN;                 % so o 1o ciclo emite o treino inicial
                % [R1-e7] ymin p/ o PROXIMO ciclo (C3): o SelectTrainData acima
                % transladou o y por min(A.objs) — as predicoes do proximo ciclo
                % saem nesse espaco (mapminmax qs e interno/reversado no Estimate).
                ymin_vig   = min(A.objs,[],1);
                espaco_vig = "transformado";
            end
        end
    end
end