classdef EIM < ALGORITHM
% <multi> <real> <expensive>
% EIM — Expected Improvement Matrix (Zhan, Cheng & Liu, IEEE TEVC 2017)
% [R1-c238] EMBRULHO classdef do contrato N.5 (SPEC v5.2): o repo oficial e um
% SCRIPT standalone (MultiObjective_EIM.m — roda clearvars/close all, avalia a
% funcao por feval proprio) e NAO e um Algorithm do PlatEMO. Este classdef
% re-expressa o loop do script chamando as FUNCOES INTACTAS do proprio repo
% (GP_Train / Infill_EIM / Optimizer_GA / Paretoset), com os 8 pontos do N.5:
%   (1) sem clearvars/close all/fprintf; sem as 2 linhas Hypervolume (mex
%       Windows-only — ancora c238-hypervolume-rm aplicada no script);
%   (2) orcamento = Problem.maxFE (31D-1), nunca o max_evaluation=200 fixo;
%       'N'=100 no UserProblem (N.5-2; INERTE aqui — o GA interno e 10D e o
%       init e o DoE do artefato);
%   (3) init: o lhsdesign nativo e SOBRESCRITO pelo global-override do cartao
%       (bundle alg_c238_eim: "Sobrescreve o init=100 e maxFE=200 fixos do
%       repo") — DoE 11D-1 do ARTEFATO via Problem.data.X0 (D63/D87/D88),
%       avaliado SOMENTE pela ponte/FEBudget (D89) — NUNCA avaliacao propria;
%   (4) while Algorithm.NotTerminated(Pop) — termino pela excecao
%       PlatEMO:Termination (D61); overshoot ZERO (1 infill/iteracao);
%   (5) re-scaling min-max de y POR ITERACAO (paper §V-B(5)a) + guard [IMPL]
%       max(range,eps); front nao-dominado via Paretoset sobre o y CRU
%       (script :37/:61 — o min-max e monotono, o ND e o mesmo);
%   (6) GP_Train por objetivo (kriging PROPRIO estilo Forrester: theta0=1,
%       bounds [1e-3,1e3] vetoriais ARD, MLE fmincon sqp em log10(theta),
%       single-start, MaxFunEvals=20D, nugget (10+n)*eps — CODIGO);
%   (7) infill = Optimizer_GA(@(x)-Infill_EIM(x,GP,ndf_scaled,criterion),
%       pop=10D, 200 ger) — GA do CODIGO (diverge do DE do paper, B10.2/D30;
%       anti-clustering AUSENTE no repo = CODIGO, B10.7 — so telemetria);
%       `criterion` e VARIAVEL (L.9; era literal hardcoded + var morta :51);
%   (8) Pop = [Pop, Problem.Evaluation(infill)] — lote=1/iteracao.
% Guards [IMPL] do cartao (instrumentados e LOGADOS, nunca silenciosos):
%   EIM(isnan(EIM))=0 (no Infill_EIM.m patchado); max(range,eps) no re-scaling;
%   chol desprotegido (GP_Train.m:22) -> DEDUP do dataset SO para o treino
%   (duplicata bit-exata de infill = cache-hit 0 FE — D89 — que o script
%   original nem produz: la nao ha cache; aqui ela entraria 2x no treino e
%   mataria o chol). Guarda (c) do D60: stall de iteracoes sem consumir FE
%   (dup em loop) — SO LOGA (saldo_congelado), nunca conserta.
% RNG: NENHUM rng interno — a semente e do harness (D59: rng(semente) DEPOIS
% do Problem, ANTES do Solve); consumidores: lhsdesign (init do GA), randi
% (torneio, sinal SBX), rand (SBX/mutacao). fmincon e deterministico.
% Sync D89 pos-infill: Problem.FE = Problem.data.bud.fe (o obj.FE nativo NAO
% governa o termino — receita do caso-modelo c217).

    methods
        function main(Algorithm,Problem)
            %% (N.5-7/L.9) criterion como VARIAVEL — default EIM-Euclidean
            % (EIMe = default do driver oficial; o paper nao elege — E.5).
            criterion = Algorithm.ParameterSet('Euclidean');
            D  = Problem.D;   M  = Problem.M;
            lb = Problem.lower;   ub = Problem.upper;
            bud = Problem.data.bud;

            %% (N.5-3) init = DoE 11D-1 do ARTEFATO (D63/D87/D88) pela ponte
            Population = Problem.Evaluation(Problem.data.X0);
            Problem.FE = bud.fe;                   % sync D89 (pos-init)

            iter  = 0;
            stall = 0;                             % guarda (c) D60 — so loga
            %% (N.5-4) loop de BO — 1 infill/iteracao, termino exato 31D-1
            while Algorithm.NotTerminated(Population)
                iter = iter + 1;
                sample_x = Population.decs;
                sample_y = Population.objs;

                % (N.5-5) re-scaling min-max POR ITERACAO (paper) + guard range
                ymin   = min(sample_y,[],1);
                ymax   = max(sample_y,[],1);
                yrange = ymax - ymin;
                n_range0 = nnz(yrange <= 0);       % objetivo constante -> 0/0
                if n_range0 > 0
                    % guard logado NA DETECCAO (achado da revisao adversarial
                    % R1-c238): se o fit subsequente morrer (sigma2=0 -> fmincon
                    % aborta), o evento ja esta no .jsonl — nunca silencioso.
                    Problem.data.logger.guard('guard_range', 'geracao', iter, ...
                        'n', n_range0, 'motivo', ...
                        'objetivo constante na amostra (max==min) — re-scaling usou max(range,eps)');
                end
                yrange = max(yrange, eps);         % guard [IMPL] max(range,eps)
                sample_y_scaled = (sample_y - ymin)./yrange;

                % front nao-dominado do y CRU (script :37/:61); EIM le o scaled
                idx_nd     = Paretoset(sample_y);
                ndf_scaled = sample_y_scaled(idx_nd,:);

                % guard [IMPL]: dedup do dataset SO p/ o treino (chol GP_Train:22)
                [~, ia]  = unique(sample_x, 'rows', 'stable');
                n_dedup  = size(sample_x,1) - numel(ia);
                train_x  = sample_x(ia,:);
                train_ys = sample_y_scaled(ia,:);

                % (N.5-6) kriging proprio por objetivo (ARD; §17.6 timing)
                t0 = tic;
                GP_obj = cell(1, M);
                for ii = 1 : M
                    GP_obj{ii} = GP_Train(train_x, train_ys(:,ii), lb, ub, ...
                        1*ones(1,D), 0.001*ones(1,D), 1000*ones(1,D));
                end
                tempo_fit = toc(t0);

                % (N.5-7) GA interno maximiza o EIM (pop final = ③, DEF-C2)
                t1 = tic;
                [infill_x, neg_best, ga_pop, ga_fit] = Optimizer_GA( ...
                    @(x)-Infill_EIM(x, GP_obj, ndf_scaled, criterion), ...
                    D, lb, ub, 10*D, 200);
                tempo_busca = toc(t1);

                % instrumentacao: 1 chamada extra pos-GA (0 FE — L.9): mu/sigma
                % da pop FINAL do GA no espaco do modelo + contagem do guard NaN.
                [y_pop, u_pop, s_pop, n_nan_pop] = ...
                    Infill_EIM(ga_pop, GP_obj, ndf_scaled, criterion);
                % telemetria B10.7 (anti-clustering AUSENTE — so observar):
                min_dist = min(sqrt(sum((sample_x - infill_x).^2, 2)));

                % (N.5-8) 1 FE pela ponte/FEBudget (D61/D89) — nunca propria
                fe_antes   = bud.fe;
                New        = Problem.Evaluation(infill_x);
                Population = [Population, New];
                Problem.FE = bud.fe;               % sync D89 (obrigatorio)
                if bud.fe == fe_antes, stall = stall + 1; else, stall = 0; end

                c238_instrument(Problem, iter, criterion, ymin, ymax, yrange, ...
                    n_range0, n_dedup, numel(ia), idx_nd, GP_obj, ...
                    ga_pop, ga_fit, y_pop, u_pop, s_pop, n_nan_pop, ...
                    infill_x, neg_best, min_dist, fe_antes, stall, ...
                    tempo_fit, tempo_busca);
            end
        end
    end
end
