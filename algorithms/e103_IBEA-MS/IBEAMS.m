function [FinalDec, FinalObj] = IBEAMS(Global)
    %------------------------------- Reference --------------------------------
    % Z. Liu, H. Wang, and Y. Jin, Performance Indicator based 
    % Adaptive Model Selection for Offline Data-Driven Multi-Objective 
    % Evolutionary Optimization in IEEE Transactions on Cybernetics.
    %------------------------------- Copyright --------------------------------
    % Copyright (c) 2022 HandingWangXD Group. Permission is granted to copy and
    % use this code for research, noncommercial purposes, provided this
    % copyright notice is retained and the origin of the code is cited. The
    % code is provided "as is" and without any warranties, express or implied.
    %---------------------------- Parameter setting ---------------------------
    
    % IniN = 11*D-1-----The number of initial offline data
    % N    = 100--------The size of population
    % kappa= 0.05-------The parameter of IBEA parameter 
    % epsilon = 10^-5---The defined minimal distance difference and the sum
    % of RMSE
    % Objective relaxation: M-1
    % This code is written by Zhening Liu.
    % Email: zheningliu2@gmail.com
    
    %% Parameter setting
    % [R1-e103 · L.15(a)] :23-31 parametrizados: D/M/N/lower/upper vem do
    % CHAMADOR (run_e103 monta o Global; N=100 mantido — Balde B). Os
    % hardcodes stock (D=20, M=3, problem='DTLZ1', bounds [0,1]) sairam;
    % Global.problem nao existe mais (o unico consumidor era o Fitness, que a
    % injecao L.15(c) elimina). kappa/Generations/CurGen ficam STOCK.
    kappa    = 0.05;                    %The parameter of IBEA
    Generations    = 100;
    CurGen         = 1;
    % [R1-e103 · L.15(b)] cd(fileparts(...))+addpath(genpath(cd)) -> addpath
    % PURO da propria arvore (o CWD do processo NAO muda — hazard N.3; o
    % ensure_paths_e103 do harness ja monta/restaura o path por fora).
    addpath(genpath(fileparts(mfilename('fullpath'))));
    %% Construct the kriging and RBFN models
    % [R1-e103 · L.15(c)] :35-36 -> INJETAR Population = o DATASET (X,F do
    % artefato D90; zero avaliacao real — o LHS_sam/Fitness stock saem do
    % caminho). MSE=zeros (:abaixo, stock) marca os membros como "reais":
    % AmendKriCal/AmendRBFCal preservam o Obj de quem tem SumMSE==0.
    PopDec      = Global.data.X0;
    Population  = PopStruct(PopDec, Global.data.F0);
    t0_fit      = tic;
    KModel      = construct_kriging(Population, Global);
    tempo_krig  = toc(t0_fit);
    t0_fit      = tic;
    Rnets       = construct_Rnets(Population, Global);
    tempo_rbfn  = toc(t0_fit);
    MSE         = zeros(length(Population),Global.M);
    % [R1-e103 · inst] setup read-only (timing §17.6 + e103_setup no .jsonl).
    if isfield(Global, 'inst') && ~isempty(Global.inst)
        e103_instrument('setup', Global, KModel, Rnets, tempo_krig, tempo_rbfn);
    end
    t0_busca = tic;
    %% Optimization
    while CurGen < Generations
        MatingPool         = TournamentSelection(2,Global.N,-CalFitness(Population,kappa));
        % [R1-e103 · ancora e103-pm-D93a 🔴 D30/ARTIGO] proM (3o parametro do
        % GA) stock era (1/D), mas o GA.m:69 divide proM por D DE NOVO
        % (convencao PlatEMO: proM = nº esperado de variaveis mutadas) -> pm
        % efetiva stock = 1/D^2. Com proM=1, pm efetiva = 1/D (paper). GA.m intacto.
        OffDec             = GA(Global, decs(Population(MatingPool)), {1,20,1,20});
        [Population, MSE]  = AmendKriCal(Population, KModel, Global, MSE);                                  %Re-evaluate the parent population by the Kriging models
        [Offspring,OffMSE] = kriging_cal(OffDec, KModel, Global);                                           %Evaluate the Offspring by the Kriging models
        KFlag              = JudgeModel([Population,Offspring],[MSE;OffMSE]);                              %Select the Models to lead the optimization
        % [R1-e103 · inst] captura read-only do conjunto JULGADO (o que o
        % JudgeModel viu) ANTES do ramo KFlag=0 sobrescrever OffMSE com ones.
        MSE_julgada_e103 = [MSE;OffMSE];
        % [R1-e103 · inst / DI-13.4] +1 captura read-only: os OBJETIVOS do
        % conjunto JULGADO — o OUTRO input do JudgeModel — p/ o instrument
        % recomputar site/Msite (margem_3sigma_stats) SEM tocar o mecanismo.
        % Aqui Population/Offspring ainda sao EXATAMENTE o que o JudgeModel
        % recebeu (:64); o ramo abaixo os sobrescreve.
        PopObj_julgada_e103 = objs([Population,Offspring]);
        if KFlag
            [Population,MSE] = EnvironmentalSelection([Population,Offspring],Global.N,kappa,[MSE;OffMSE]);  %Environmental selection assisted by the Kriging models
        else
            Population = AmendRBFCal(Population, Rnets, Global, MSE);                                       %Re-evaluate the parent population by the RBFN models
            Offspring  = RBFN_cal(OffDec, Rnets, Global);                                                %Re-evaluate the offspring by the RBFN models
            OffMSE     = ones(size(OffDec,1),Global.M);                                                     
            [Population,MSE] = EnvironmentalSelection([Population,Offspring],Global.N,kappa,[MSE;OffMSE]);  %Environmental selection assisted by the RBFN models
        end
        % [R1-e103 · inst] fim do ciclo (pos-selecao, "pos :46" da L.15):
        % ②③ + linha e103_gen (CurGen/KFlag/√MSE + μ dos DOIS modelos) —
        % read-only, ZERO decisao alterada (D97).
        if isfield(Global, 'inst') && ~isempty(Global.inst)
            e103_instrument('gen', Global, KModel, Rnets, CurGen, KFlag, ...
                            Population, MSE, MSE_julgada_e103, PopObj_julgada_e103);
        end
        CurGen = CurGen+1;
    end
    % [R1-e103 · inst] fecha a serie §17.6 (offline treino-unico = UMA linha:
    % n_acumulado = n_dataset, tempo_fit_s = kriging+RBFN, tempo_busca_s = o
    % laco IBEA inteiro — 99 geracoes).
    if isfield(Global, 'inst') && ~isempty(Global.inst)
        e103_instrument('busca_fim', Global, toc(t0_busca), tempo_krig, tempo_rbfn);
    end
    % [R1-e103 · L.15(d)] retorno: a funcao stock nao devolvia nada
    % (OutPopulation era descartado) -> [FinalDec, FinalObj] = a populacao
    % final (N=100; objs = valores do MODELO da ultima selecao; membros do
    % dataset preservam o F real — marcador MSE=0).
    FinalDec = decs(Population);
    FinalObj = objs(Population);
end
