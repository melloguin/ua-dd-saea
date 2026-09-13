classdef CLMEA < ALGORITHM
    % <multi/many> <real/integer> <expensive>
    % Classifier and Local Model-Based Evolutionary Algorithm
    % num_infill    ---    1 --- Number of infill samples for each strategy
    % epsilon       --- 1e-5 --- minimum distance with archive points
    % Gen_max1       --- 200   --- Maximum evolving generations for
    % Gen_max2       --- 50   --- Maximum evolving generations
    % k_local       --- 20  --- Number of solutions to build local model
    
    %------------------------------- Reference --------------------------------
    %
    %------------------------------- Copyright --------------------------------
    % Copyright (c) 2022 BIMK Group. You are free to use the PlatEMO for
    % research purposes. All publications which use this platform or any code
    % in the platform should acknowledge the use of "PlatEMO" and reference "Ye
    % Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
    % for evolutionary multi-objective optimization [educational forum], IEEE
    % Computational Intelligence Magazine, 2017, 12(4): 73-87".
    %--------------------------------------------------------------------------
    
    % This function is written by Guodong Chen, The University of Hong Kong
    
    methods
        function main(Algorithm,Problem)
            %% Parameter setting
            [num_infill, epsilon, Gen_max1, Gen_max2, k_local] = Algorithm.ParameterSet(1, 1e-5, 200, 50, 20);
            %% Initalize the population by Latin hypercube sampling
            if Problem.D < 100
                N      = 100;
            elseif Problem.D >=100
                N      = 200;
            end
            % [R1-e74] Init = DoE 11D-1 INJETADO do artefato (D63/D87/D88) — NUNCA
            % regenerar. X0 e NATIVO (load_doe): entra DIRETO na Evaluation — o par
            % gera-LHS([0,1])+re-escala do stock (:33-34) e substituido JUNTO (o
            % mesmo principio da D94; injetar so no RHS re-escalaria de novo).
            % Desvio DELIBERADO do paper (init nativo = N = 100/200) — registrado.
            % N (pop das estrategias) fica o stock 100/200; o teto min(N,|Arc|)
            % nas 3 chamadas abaixo e o patch L.8 de D-baixo. Guarda do hazard
            % L.8 "init em lote SEM check previo — se maxFE<=|init| estoura":
            assert(Problem.maxFE > size(Problem.data.X0,1), ...
                'e74: maxFE=%d <= |DoE|=%d — o init sozinho estoura o orcamento (L.8)', ...
                Problem.maxFE, size(Problem.data.X0,1));
            Arc        = Problem.Evaluation(Problem.data.X0);
            Problem.FE = Problem.data.bud.fe;   % [R1-e74] sync D89 (obj.FE nao governa o termino)
            Algorithm.NotTerminated(Arc);
            tGer_e74 = tic;                     % [DI09-R1c] §17.6 wall do bloco 'boot' (g=1 pos-bump)
            %% Find extreme points
            % Select training sample point
            x_train = Arc.decs;    y_train = Arc.objs;
            % Calculate the kernal width of RBF
            ghxd=real(sqrt(x_train.^2*ones(size(x_train'))+ones(size(x_train))*(x_train').^2-2*x_train*(x_train')));
            D = size(x_train,2);
            spr = max(max(ghxd))/(D*size(x_train,1))^(1/D);
            % [R1-e74] bootstrap de extremos = ATE M FEs reais (extremos ACEITOS no
            % dedup ε — e o metodo, Alg. 1 do paper; contam no orcamento). DE roda
            % 100% no surrogate (0 FE). Instrumentacao de leitura (D97) + §17.6.
            boot_e74 = struct('aceitos', 0, 'rejeitados', 0, 'x_ext', [], ...
                'f_ext', [], 'dist_ext', [], 'n_treino', size(x_train,1), ...
                'spr', spr, 'tempo_fit_s', 0, 'tempo_busca_s', 0);
            nets_e74 = {};     % [DI09-R1c] as M redes mono-saida acumuladas p/ a sonda 'boot'
            for i = 1:Problem.M
                % Construct a surrogate for the ith objective
                t0_e74 = tic;
                net = newrbe(x_train',y_train(:,i)',spr);    FUN = @(x) sim(net,x');
                boot_e74.tempo_fit_s = boot_e74.tempo_fit_s + toc(t0_e74);
                nets_e74{end+1} = net;   % [DI09-R1c] leitura pura, FORA do tic/toc do fit (§17.6)
                % Locate the optimum of the surrogate model
                max_gen = 20*D;
                t0_e74 = tic;
                [~,x_extreme,f_ext_e74] = DE(max_gen,FUN,D,Problem.upper,Problem.lower,epsilon);
                boot_e74.tempo_busca_s = boot_e74.tempo_busca_s + toc(t0_e74);
                dist_ext_e74 = min(pdist2(x_extreme,Arc.decs));
                boot_e74.x_ext(end+1,:) = x_extreme;
                boot_e74.f_ext(end+1) = f_ext_e74;
                boot_e74.dist_ext(end+1) = dist_ext_e74;
                if dist_ext_e74>epsilon
                    Arc = [Arc,Problem.Evaluation(x_extreme)];
                    boot_e74.aceitos = boot_e74.aceitos + 1;
                else
                    boot_e74.rejeitados = boot_e74.rejeitados + 1;  % rejeitado SEM FE (slot perdido)
                end
            end
            Problem.FE = Problem.data.bud.fe;   % [R1-e74] sync D89
            % [DI09-R1c] SONDA 'boot' (DI-09/§17.2.2): pos-fit das M redes, em
            % g=1 (a clausula da 1a dispara p/ qualquer k), ANTES do instrument.
            % UNICA excecao declarada a letra "pre-Evaluation" (os extremos de
            % :78 ja avaliados — inofensiva, ver e74_sonda.m). ftm sobre o
            % SNAPSHOT x_train do DoE (:50) — e o que as M redes viram; NAO
            % usar o atalho bud.fe-1 aqui (superestimaria o treino).
            boot_e74.ftm = e74_sonda(Problem, 'boot', nets_e74, x_train, ...
                'spr', spr, 'tempo_fit_s', boot_e74.tempo_fit_s);
            e74_instrument(Problem, 'boot', boot_e74, [], [], Arc.objs, [], toc(tGer_e74));
            %% Iterative sampling optimization
            % [R1-e74] L.8: Nw=min(N,length(Arc)) nas 3 chamadas (== min(100,|Arc|)
            % p/ D<100 — anti-crash de D-baixo, D20) + k_local=min(20,|Arc|).
            % Dedup ε=1e-5 STOCK: rejeita SEM gastar FE (slot perdido — logado).
            % Sync D89 apos cada Evaluation; e74_instrument = leitura pura (D97).
            % D60-c: ciclo sem consumir FE -> stall (SO loga saldo_congelado).
            fe_stall_e74 = 0;
            while Algorithm.NotTerminated(Arc)
                fe_ciclo0_e74 = Problem.data.bud.fe;
                tGer_e74 = tic;                     % [DI09-R1c] §17.6 wall do bloco s1 (pos-bump)
                % 1: Classifier assisted infilling strategy
                [x_candidates1, inst1_e74] = ClassifierSelect(Problem, Arc, min(N,length(Arc)), num_infill);
                ArcDecPre_e74 = Arc.decs;           % [DI09-R1c] DI-10/B3: arquivo PRE-infill (DECISAO nativa, DI-19.4)
                Choose_index = min(pdist2(x_candidates1,Arc.decs),[],2)>epsilon;
                if sum(Choose_index)>0
                    Arc = [Arc,Problem.Evaluation(x_candidates1(Choose_index,:))];
                end
                Problem.FE = Problem.data.bud.fe;   % [R1-e74] sync D89
                e74_instrument(Problem, 's1', inst1_e74, x_candidates1, Choose_index, ...
                    Arc.objs, ArcDecPre_e74, toc(tGer_e74));  % [DI-19.2] Arc.objs POS-Evaluation
                if ~Algorithm.NotTerminated(Arc)
                    break;
                end

                % 2: Hypervolume-based non-dominated pareto sort
                tGer_e74 = tic;                     % [DI09-R1c] §17.6 wall do bloco s2 (pos-bump)
                [x_candidates2, inst2_e74] = Hv_Select(Problem, Arc, min(N,length(Arc)), num_infill, Gen_max1);
                ArcDecPre_e74 = Arc.decs;           % [DI09-R1c] DI-10/B3: arquivo PRE-infill
                Choose_index = min(pdist2(x_candidates2,Arc.decs),[],2)>epsilon;
                if sum(Choose_index)>0
                    Arc = [Arc,Problem.Evaluation(x_candidates2(Choose_index,:))];
                end
                Problem.FE = Problem.data.bud.fe;   % [R1-e74] sync D89
                e74_instrument(Problem, 's2', inst2_e74, x_candidates2, Choose_index, ...
                    Arc.objs, ArcDecPre_e74, toc(tGer_e74));
                if ~Algorithm.NotTerminated(Arc)
                    break;
                end

                % 3: Local search in objective space
                tGer_e74 = tic;                     % [DI09-R1c] §17.6 wall do bloco s3 (pos-bump)
                [x_candidates3, inst3_e74] = Local_infill(Problem, Arc, num_infill, min(N,length(Arc)), min(k_local,length(Arc)), Gen_max2);
                ArcDecPre_e74 = Arc.decs;           % [DI09-R1c] DI-10/B3: arquivo PRE-infill
                Choose_index = min(pdist2(x_candidates3,Arc.decs),[],2)>epsilon;
                if sum(Choose_index)>0
                    Arc = [Arc,Problem.Evaluation(x_candidates3(Choose_index,:))];
                end
                Problem.FE = Problem.data.bud.fe;   % [R1-e74] sync D89
                e74_instrument(Problem, 's3', inst3_e74, x_candidates3, Choose_index, ...
                    Arc.objs, ArcDecPre_e74, toc(tGer_e74));
                % [R1-e74] D60-c (guarda de stall logico — SO LOGA; o watchdog
                % externo e quem age): ciclo inteiro sem FE = as 3 estrategias
                % rejeitadas no dedup ε (candidato ja no arquivo).
                if Problem.data.bud.fe == fe_ciclo0_e74
                    fe_stall_e74 = fe_stall_e74 + 1;
                else
                    fe_stall_e74 = 0;
                end
                if fe_stall_e74 >= 2
                    e74_instrument(Problem, 'stall', struct('ciclos', fe_stall_e74), [], [], [], [], []);
                end
                if ~Algorithm.NotTerminated(Arc)
                    break;
                end
            end
        end
    end
end