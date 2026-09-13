function b1_instrument(Problem, lamda, fmin, fmax, gainfo, PopDec, ...
                       n_arquivo, n_subset, n_treino, n_dedup, ...
                       nan_guard_fired, theta, tfit_s, tbusca_s, ...
                       tger_s, ftm, A_pre, ObjPos, dmodel)
% b1_instrument — instrumentacao POS-decisao do b1 ParEGO (chamada no fim de
% cada iteracao de BO pela ParEGO.main patchada). NAO altera nenhuma decisao da
% busca (D97): so LE o que a iteracao ja computou (a pop final scorada do GA
% interno via gainfo, o λ sorteado, o min/max da normalizacao, o Gbest, os
% contadores de guarda) e emite as camadas de auditoria/analise. O gate
% objetivo (FE/4-saidas/CP-init) NAO depende deste conteudo; ele existe p/ a
% validacao MANUAL do autor (D97).
%
% O que emite:
%   ③ (DEF-C2 §17.4 + D47/C3 — MONO-OUTPUT): a populacao FINAL do otimizador
%     de aquisicao (GA interno EvolALG) por iteracao de BO, 1 linha 'valor' por
%     candidato scorado: mu_0 = y (escalar PCheby PREDITO — lossy, D47) e
%     sigma_0 = s = sqrt(max(mse,0)) do GP mono-output; mu_1../sigma_1.. NULL
%     (o writer do R1-00 preenche NaN=NULL — caso mono-output do §17.2,
%     corrigido no F0-03). C3 (DEF-C3): espaco_modelo='transformado',
%     transf_tipo='escalar-tcheby', transf_params={lambda, min, max, gbest} da
%     iteracao — sem eles o escalar e ininterpretavel (o λ muda a cada
%     iteracao). real_solution_id nullable: quase todos os candidatos sao
%     offspring nunca avaliados (NULL); o Best (avaliado no fim da iteracao) e
%     membros re-copiados do arquivo apontam o id -> o write_surrogate cai p/
%     double+NaN (fallback do R1-00; consolidacao re-casta int32).
%   .jsonl §17.5/S.7 (linha 'b1_gen'): lambda, min/max da normalizacao, gbest,
%     theta resumo (min/max/media), n_arquivo/n_subset/n_treino/n_dedup,
%     ga (iters, |pop final|, trace do melhor EI), EI/mu/sigma do Best, lote
%     (=1), contadores de guarda; eventos 'guard': mse_neg (P2/L8), nan_guard
%     (P4/DEF-A8), dedup_treino (near-dups removidos no cap 1e-6).
%   timing §17.6: 1 evento de retreino por iteracao (n_acumulado = n_treino do
%     dacefit; tempo_fit_s + tempo_busca_s do EvolALG, medidos na ParEGO.main).
%
% Fontes (via Problem.data, empacotado pelo run_b1): .buf RunBuffer (o MESMO
% que o hook_output alimenta com ②) · .bud FEBudget (X -> solution_id, D57) ·
% .log fid do .jsonl. Alinhamento: g = buf.gen (o hook ja fez bumpGen no TOPO
% desta iteracao, via NotTerminated) -> ② (hook) e ③/timing (aqui) partilham o
% g. RNG: NENHUM consumo (solutionIdOf/min/max/jsonencode deterministicos).

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end

    % ── eventos de guarda (§17.5) ─────────────────────────────────────────────
    if gainfo.n_mse_neg > 0
        guard_line(fid, 'mse_neg', g, 'n', gainfo.n_mse_neg, 'motivo', ...
            'dacefit devolveu mse<0 — guard P2/L8 aplicou sqrt(max(mse,0))');
    end
    if nan_guard_fired
        guard_line(fid, 'nan_guard', g, 'motivo', ...
            'objetivo constante no arquivo (min==max) — den==0 -> eps (P4/DEF-A8)');
    end
    if n_dedup > 0
        guard_line(fid, 'dedup_treino', g, 'n', n_dedup, 'motivo', ...
            'near-duplicatas (cap 1e-6, ParEGO:51-55) removidas do subset de treino');
    end
    if gainfo.n_ei_nan > 0
        guard_line(fid, 'ei_nan', g, 'n', gainfo.n_ei_nan, 'motivo', ...
            'EI=NaN na pop final do GA (s=0 & y==Gbest) — hazard N.3, so contagem');
    end

    % ── ③ DEF-C2/D47: pop FINAL scorada do GA interno, mono-output + C3 ───────
    % transf_params identico p/ todas as linhas da iteracao (RLE comprime).
    tp = string(jsonencode(struct('lambda', lamda(:).', 'min', fmin(:).', ...
                                  'max', fmax(:).', 'gbest', gainfo.gbest)));
    srows = {};
    pop = gainfo.pop;
    for i = 1:size(pop.dec, 1)
        sid = bud.solutionIdOf(pop.dec(i, :));  % >=0 so se JA avaliado (arquivo/Best)
        rsi = int32([]);
        if sid >= 0, rsi = int32(sid); end
        srows{end+1} = RunBuffer.mkSurrogateRow(pop.dec(i, :), ...
            'real_solution_id', rsi, ...
            'mu', pop.y(i), 'sigma', pop.s(i), ...
            'pred_tipo', "valor", 'modelo_flag', "GP-DACE", ...
            'espaco_modelo', "transformado", 'transf_tipo', "escalar-tcheby", ...
            'transf_params', tp, ...
            'fe_treino_max', ftm); %#ok<AGROW>   % [DI-09/A1] tb nas linhas de busca
    end

    % ── §17.6 timing: 1 retreino (dacefit) + busca (EvolALG) por iteracao ─────
    % [DI-13.10] tempo_geracao_s DESCONTA a sonda: o relogio da iteracao mede o
    % custo do ALGORITMO, nao o do instrumento (molde c141_instrument.m:104).
    tps = sonda_tempo_b1(d);
    timing = struct('n_acumulado', n_treino, 'tempo_fit_s', tfit_s, ...
                    'tempo_busca_s', tbusca_s, ...
                    'tempo_geracao_s', max(tger_s - tps, 0), ...
                    'tempo_pred_sonda_s', tps);

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── .jsonl §17.5/S.7 — a linha 'b1_gen' por iteracao de BO ────────────────
    if ~isempty(fid) && fid > 2
        sid_best = bud.solutionIdOf(PopDec(1, :));
        rec = struct('ts', iso_now_b1(), 'rec', "b1_gen", ...
            'geracao', g, 'fe', bud.fe, ...
            'lambda', lamda(:).', ...
            'norm_min', fmin(:).', 'norm_max', fmax(:).', ...
            'gbest', gainfo.gbest, ...
            'theta_min', min(theta), 'theta_max', max(theta), ...
            'theta_media', mean(theta), ...
            'n_arquivo', n_arquivo, 'n_subset', n_subset, ...
            'n_treino', n_treino, 'n_dedup', n_dedup, ...
            'ga_iters', gainfo.n_iters, 'ga_pop', size(pop.dec, 1), ...
            'e0_trace', gainfo.e0_trace(:).', ...
            'ei_best', gainfo.e0, 'mu_best', gainfo.best_y, ...
            'sigma_best', gainfo.best_s, 'best_sid', sid_best, ...
            'lote', 1, ...
            'n_mse_neg', gainfo.n_mse_neg, 'n_ei_nan', gainfo.n_ei_nan, ...
            'nan_guard', nan_guard_fired, ...
            ... % ── DI-10: especificos do b1 (S.7.1/CONTRATO §6.1) ──
            ... % `lambda` (vetor completo de M valores) e `ei_best` ja saem acima,
            ... % nas chaves de mesmo nome. `n_pool_ga` e o NOME CONTRATADO da
            ... % grandeza que ja era escrita como `ga_pop`: emito as DUAS (aditivo
            ... % — renomear quebraria qualquer leitor escrito contra `ga_pop`).
            'n_pool_ga', size(pop.dec, 1), ...
            'modelo_hp', hp_gp_b1(dmodel, theta, tfit_s), ...
            ... % ── DI-10: minimo comum dos 21 (S.7.1) ──
            'f_best', min(ObjPos, [], 1), ...
            'n_front1', sum(NDSort(ObjPos, 1) == 1), ...
            'fe_treino_max', opt_null_b1(ftm), ...
            'tempo_busca_s', tbusca_s, 'tempo_geracao_s', tger_s, ...
            'tempo_pred_sonda_s', tps, ...
            'dist_min_arquivo', dist_min_b1(PopDec, A_pre), ...
            'tempo_fit_s', tfit_s);
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function t = sonda_tempo_b1(d)
    if isfield(d, 'snd') && ~isempty(d.snd), t = d.snd.takePendingTime(); else, t = 0; end
end

function hp = hp_gp_b1(dmodel, theta, tfit_s)
% [DI-10/B1] hp EFETIVOS do GP-DACE, read-only de dacefit.m:123-125.
% As chaves planas theta_min/max/media seguem sendo emitidas acima (nao remover:
% ha leitores escritos contra elas) — esta e a forma ESTRUTURADA que o S.7.1 pede.
    hp = struct('theta', theta(:).', 'n', NaN, 'sigma2', [], ...
                'regr', "regpoly1", 'corr', "corrgauss", 'tempo_fit_s', tfit_s);
    try
        if isstruct(dmodel)
            if isfield(dmodel, 'S'),      hp.n      = size(dmodel.S, 1); end
            if isfield(dmodel, 'sigma2'), hp.sigma2 = dmodel.sigma2(:).'; end
            if isfield(dmodel, 'theta'),  hp.theta  = dmodel.theta(:).';  end
        end
    catch
    end
end

function dmin = dist_min_b1(PopDec, A_pre)
% [DI-10/B3] Distancia de cada infill ao arquivo ANTERIOR (espaco de decisao).
% O b1 nao tem arquivo ND separado: o arquivo E a Population (snapshot pre-:88).
% Laco sem pdist2 (molde c141_instrument.m:171-183) — o b1 TEM a Statistics
% Toolbox, mas manter o mesmo helper mantem a coluna comparavel entre configs.
% O lote do b1 e sempre 1 (PopDec = Best, EvolALG.m:67) => escalar.
    dmin = [];
    if isempty(PopDec) || isempty(A_pre), return; end
    n = size(PopDec, 1);
    dmin = zeros(1, n);
    for i = 1:n
        dif = A_pre - PopDec(i, :);
        dmin(i) = sqrt(min(sum(dif .* dif, 2)));
    end
end

function v = opt_null_b1(x)
    if isempty(x), v = []; else, v = double(x); end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_b1(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function s = iso_now_b1()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
