classdef CSEA < ALGORITHM
% <2019> <multi/many> <real/integer> <expensive>
% Classification based surrogate-assisted evolutionary algorithm
% k    ---    6 --- Number of reference solutions
% gmax --- 3000 --- Number of solutions evaluated by surrogate model

%------------------------------- Reference --------------------------------
% L. Pan, C. He, Y. Tian, H. Wang, X. Zhang, and Y. Jin. A classification
% based surrogate-assisted evolutionary algorithm for expensive
% many-objective optimization. IEEE Transactions on Evolutionary
% Computation, 2019, 23(1): 74-88.
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
            [k,gmax] = Algorithm.ParameterSet(6,3000);

            %% Initalize the population by Latin hypercube sampling
            % [R1-b4] init fiel ao paper: 11*Problem.D-1; % remover cap 109 (S.2#2)
            % (o 109 era a regra congelada em d=10; p/ D>=10 o cap reduziria o DoE)
            N          = 11*Problem.D-1;
            % [R1-b4] injecao do DoE (D63/D87/D88): substitui o PAR gera+re-escala
            % (classe D94 — X0 NATIVO direto; initFcn NAO alcanca o CSEA, L.3).
            Population = Problem.Evaluation(Problem.data.X0);
            Arc        = Population;
            
            %% Initialize the network
            hiddenLayerSize = ceil(Problem.D*2);
            layers = [featureInputLayer(Problem.D,'Normalization', 'zscore')
                    fullyConnectedLayer(hiddenLayerSize)
                    batchNormalizationLayer
                    reluLayer
                    fullyConnectedLayer(1)
                    sigmoidLayer
                    regressionLayer];

            maxEpochs = 100;
            miniBatchSize = 32;
            options = trainingOptions('adam', ...
                        'ExecutionEnvironment','cpu', ...
                        'MaxEpochs',maxEpochs, ...
                        'MiniBatchSize',miniBatchSize, ...
                        'Shuffle','every-epoch', ...
                        'Plots','none', ...
                        'Verbose',false);

            %% Optimization
            while Algorithm.NotTerminated(Arc)
                t0_ger_b4 = tic;                     % [DI09-R1c] §17.6 wall da geracao
                % Select reference solutions and preprocess the data
                Ref    = RefSelect(Population,k);
                % [R1-b4] treino no ARQUIVO INTEIRO (ARTIGO — B4.6/D30): o cap
                % nativo (= a Population de tamanho Problem.N) handicaparia o
                % classificador; rotula-se e treina-se sobre TODO o Arc.
                Input  = Arc.decs;
                Output = GetOutput(Arc.objs,Ref.objs);
                rr     = sum(Output)/length(Output);
                tr     = min(rr,1-rr)*0.5;
                [TrainIn,TrainOut,TestIn,TestOut] = DataProcess(Input,Output);
                n_treino = size(Input,1);            % [R1-b4] §17.6: |Arc| no fit
                t0_fit   = tic;                      % [R1-b4] §17.6
                net = trainNetwork(TrainIn,TrainOut-0,layers,options);
                tfit_s = toc(t0_fit);                % [R1-b4] §17.6

                % Error rates calculation
                TestPre = predict(net,TestIn);
                IndexGood = TestOut==1;
                p0 = sum(abs((TestOut(IndexGood)-TestPre(IndexGood))))/sum(IndexGood);
                p1 = sum(abs((TestOut(~IndexGood)-TestPre(~IndexGood))))/sum(~IndexGood);

                % [DI09-R1c] SONDA (DI-09/§17.2.2): pos-fit (:71), ANTES da unica
                % decisao do ciclo (:85 SAS), ANTES do 1o consumo de RNG pos-fit
                % (OperatorGA/randperm/randi vivem dentro do SAS) e ANTES da
                % Evaluation (:87), onde o hard-stop aborta o corpo. Devolve o
                % fe_treino_max sobre o TrainIn (subamostra 3/4 estratificada),
                % calculado UMA vez por geracao e repassado ao instrument.
                ftm_b4 = b4_sonda(Problem, net, TrainIn);

                % Surrogate-assisted selection and update the population
                % [R1-b4] SAS com 2o output de instrumentacao (ramo/L/guard) —
                % decisoes intactas (D97).
                t0_busca_b4 = tic;                   % [DI09-R1c] §17.6
                [Next,sasinfo] = SurrogateAssistedSelection(Problem,net,p0,p1,Ref,Population.decs,gmax,tr);
                tbusca_s_b4 = toc(t0_busca_b4);      % [DI09-R1c] §17.6
                if ~isempty(Next)
                    Arc = [Arc,Problem.Evaluation(Next)];
                end
                % [R1-b4] sync D89 (herdado do c217, PCS:56): o obj.FE nativo NAO
                % governa; re-sincroniza com o saldo DISTINTO do wrapper.
                Problem.FE = Problem.data.bud.fe;
                Population = RefSelect(Arc,Problem.N);
                % [R1-b4] instrumentacao POS-decisao (D97): ③ + .jsonl + timing.
                % [DI09-R1c] MOVIDA para DEPOIS do RefSelect: o `tempo_geracao_s`
                % do §17.6 e o wall TOTAL da geracao, e o RefSelect final nao e
                % barato (NDSort + pdist2 |Arc|x|Arc| no ZDT1). Deixa-lo fora do
                % relogio tornaria a curva de custo do b4 nao-comparavel com a do
                % c217, onde o EnvironmentalSelection analogo esta DENTRO
                % (PCSAEA.m:72 antes do instrument de :75). O b4_instrument nao le
                % nada mutado pelo RefSelect (nao recebe Population) e o RefSelect
                % nao consome RNG — o movimento e read-only.
                b4_instrument(Problem, Arc, Ref, Next, sasinfo, p0, p1, rr, tr, ...
                              n_treino, tfit_s, tbusca_s_b4, toc(t0_ger_b4), ...
                              ftm_b4, Input, size(TrainIn,1));
            end
        end
    end
end