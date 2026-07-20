classdef ParEGO < ALGORITHM
% <2006> <multi> <real/integer> <expensive>
% Efficient global optimization for Pareto optimization
% IFEs --- 10000 --- Internal GA evals per iteration

%------------------------------- Reference --------------------------------
% J. Knowles. ParEGO: A hybrid algorithm with on-line landscape
% approximation for expensive multiobjective optimization problems. IEEE
% Transactions on Evolutionary Computation, 2006, 10(1): 50-66.
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
            IFEs = Algorithm.ParameterSet(10000);

            %% Generate the weight vectors and random population
            [W,Problem.N] = UniformPoint(Problem.N,Problem.M);
            N             = 11*Problem.D-1;
            % [R1-b1] injecao do DoE (D63/D87/D88): substitui o PAR gera+re-escala
            % das :29-:30 JUNTAS (classe D94 — X0 NATIVO direto na Evaluation, a
            % re-escala nunca roda; injetar so na :29 causaria dupla-escala em
            % WFG/BBOB). Init STOCK N=11D-1 mantido; X0 vem do artefato via
            % Problem.data (run_b1).
            Population    = Problem.Evaluation(Problem.data.X0);
            theta         = 10.*ones(1,Problem.D);

            %% Optimization
            while Algorithm.NotTerminated(Population)
                tGer_b1 = tic;                       % [DI09-R1c] §17.6 wall da iteracao
                % Randomly select a weight vector and preprocess the data
                lamda  = W(randi(size(W,1)),:);
                PopObj = Population.objs;
                [N,D]  = size(Population.decs);
                n_arquivo = N;                       % [R1-b1] .jsonl S.7
                % [R1-b1] P4 NaN-guard (DEF-A8; idioma L4 do c141): objetivo
                % constante no arquivo (min==max) faria 0/0=NaN aqui e propagaria
                % ao PCheby/EI. den==0 -> eps: o numerador (f-min) e 0 nessas
                % colunas => normalizado 0, identico p/ qualquer den>0. So
                % captura + guarda (D97); fmin/fmax alimentam o C3 (D47).
                fmin = min(PopObj,[],1);
                fmax = max(PopObj,[],1);
                den  = fmax - fmin;
                nan_guard_fired = any(den == 0);     % [R1-b1] evento no .jsonl
                den(den == 0) = eps;
                PopObj = (PopObj-repmat(fmin,N,1))./repmat(den,N,1);
                PCheby = max(PopObj.*repmat(lamda,N,1),[],2)+0.05.*sum(PopObj.*repmat(lamda,N,1),2);
                if N > 11*D-1+25
                    [~,index] = sort(PCheby);
                    Next      = index(1:11*D-1+25);
                else
                    Next = true(N,1);
                end
                PDec   = Population(Next).decs;
                PCheby = PCheby(Next);

                n_subset = size(PDec,1);             % [R1-b1] pos-cap top-(11D-1+25)
                % Eliminate the solutions having duplicated inputs or outputs
                [~,distinct1] = unique(round(PDec*1e6)/1e6,'rows');
                [~,distinct2] = unique(round(PCheby*1e6)/1e6);
                distinct = intersect(distinct1,distinct2);
                PDec     = PDec(distinct,:);
                PCheby   = PCheby(distinct);
                n_dedup  = n_subset - size(PDec,1);  % [R1-b1] near-dups removidos (S.7)

                % Surrogate-assisted prediction
                n_treino   = size(PDec,1);           % [R1-b1] §17.6: pontos no fit
                t0_fit     = tic;                    % [R1-b1] §17.6: tempo do fit
                dmodel     = dacefit(PDec,PCheby,'regpoly1','corrgauss',theta,1e-5.*ones(1,D),20.*ones(1,D));
                tfit_s     = toc(t0_fit);            % [R1-b1] §17.6
                theta      = dmodel.theta;
                % [DI09-R1c] SONDA (DI-09/§17.2.2): pos-fit, ANTES do EvolALG (o
                % 1o consumidor de RNG do ciclo), ANTES da Evaluation (:88, onde o
                % hard-stop aborta o corpo) e ANTES do t0_busca (senao contaminaria
                % tempo_busca_s). Devolve o fe_treino_max, que so e calculavel aqui
                % (o treino e o PDec pos-cap/dedup, nao o arquivo) e que o
                % b1_instrument — que roda POS-Evaluation — nao consegue reconstruir.
                ftm_b1 = b1_sonda(Problem, dmodel, PDec, PCheby, lamda, fmin, fmax, tfit_s);
                % [R1-b1] EvolALG com output de instrumentacao (gainfo): pop FINAL
                % scorada do GA interno + y/s/EI + Gbest/E0 + contadores dos guards
                % (mse<0, EI-NaN). Decisoes intactas (D97).
                t0_busca   = tic;                    % [R1-b1] §17.6 (opcional)
                [PopDec,gainfo] = EvolALG(Problem,PCheby,Population.decs,dmodel,IFEs);
                tbusca_s   = toc(t0_busca);          % [R1-b1]
                A_pre_b1   = Population.decs;        % [DI09-R1c] DI-10/B3: arquivo PRE-infill
                ObjPre_b1  = Population.objs;        % [DI09-R1c] DI-10: f_best/n_front1 do ciclo
                Population = [Population,Problem.Evaluation(PopDec)];
                % [R1-b1] sync D89 (herdado do c217, PCS:56): o obj.FE nativo NAO
                % governa; re-sincroniza com o saldo DISTINTO do wrapper apos o
                % infill (b1 PODE propor duplicata: mutacao-only copia o pai).
                Problem.FE = Problem.data.bud.fe;
                % [R1-b1] instrumentacao POS-decisao (D97): ③ mono-output D47/C3
                % + linha b1_gen no .jsonl (S.7) + timing §17.6.
                b1_instrument(Problem, lamda, fmin, fmax, gainfo, PopDec, ...
                              n_arquivo, n_subset, n_treino, n_dedup, ...
                              nan_guard_fired, theta, tfit_s, tbusca_s, ...
                              toc(tGer_b1), ftm_b1, A_pre_b1, ObjPre_b1, dmodel);
            end
        end
    end
end