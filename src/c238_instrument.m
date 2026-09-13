function c238_instrument(Problem, iter, criterion, ymin, ymax, yrange, ...
                         n_range0, n_dedup, n_treino, idx_nd, GP_obj, ...
                         ga_pop, ga_fit, y_pop, u_pop, s_pop, n_nan_pop, ...
                         infill_x, neg_best, min_dist, fe_antes, stall, ...
                         tfit_s, tbusca_s, tger_s, A_pre, ObjPos)
% c238_instrument — instrumentacao POS-decisao do c238 EIM (chamada no fim de
% cada iteracao de BO pela EIM.main, o embrulho N.5). NAO altera nenhuma
% decisao da busca (D97): so LE o que a iteracao ja computou (a pop FINAL do
% GA de aquisicao re-scorada por 1 chamada extra do Infill_EIM — 0 FE, L.9 —
% o min/max do y-scaling, os thetas dos M GPs, os contadores de guarda) e
% emite as camadas de auditoria/analise. O gate objetivo (FE/4-saidas/CP-init)
% NAO depende deste conteudo; ele existe p/ a validacao MANUAL do autor (D97).
%
% O que emite:
%   ③ (DEF-C2 §17.4 — BO com EA interno): a populacao FINAL do Optimizer_GA
%     por iteracao de BO (10D linhas 'valor'), com mu_j = u e sigma_j = s POR
%     OBJETIVO do kriging proprio (GP_Predict, s = sqrt(max(mse,0)) STOCK), no
%     ESPACO DO MODELO (y re-escalado min-max por iteracao — paper). C3
%     (DEF-C3, leitura D47 — precedente e7): UMA linha por candidato em
%     espaco_modelo='transformado', transf_tipo='minmax', transf_params =
%     {min: ymin, range: yrange} da iteracao -> cru = mu.*range + min
%     (invertivel; yrange e o POS-guard max(range,eps)). real_solution_id
%     nullable: quase todos os candidatos sao pontos nunca avaliados (NULL); o
%     infill escolhido (avaliado nesta iteracao) aponta o id -> o
%     write_surrogate cai p/ double+NaN (fallback do R1-00).
%   .jsonl §17.5/S.7 (linha 'c238_gen'): min/max do y-scaling (C3), [y,u,s] do
%     escolhido, theta/lnL resumo por objetivo, n_treino/n_dedup/n_front,
%     ga (|pop|, 200 ger), lote=1, fe_iter, min_dist do infill (telemetria
%     B10.7 — anti-clustering ausente), stall (D60-c); eventos 'guard':
%     eim_nan (EIM NaN->0), guard_range (max(range,eps)), dedup_treino (chol),
%     dup_infill (cache-hit D89 — slot perdido), saldo_congelado (stall>=2).
%   timing §17.6: 1 evento de retreino por iteracao (n_acumulado = n_treino
%     DEDUPLICADO dos M GP_Train; tempo_fit_s = soma dos M fits; tempo_busca_s
%     = GA), medidos na EIM.main. [DI09-R1c] + tempo_geracao_s = wall da
%     iteracao (tGer da EIM.main) DESCONTANDO a sonda (DI-13.10) e
%     tempo_pred_sonda_s = snd.takePendingTime(); no .jsonl o tempo_geracao_s
%     vai BRUTO (sem desconto — o desconto e so na ④).
%   [DI09-R1c] DI-10 minimo comum (S.7.1) na linha c238_gen: f_best/n_front1
%     do ARQUIVO REAL POS-ciclo (ObjPos = Population.objs JA com o infill —
%     DI-19.2), fe_treino_max = fe_antes-1 (treino = Population inteira
%     pre-infill; tambem nas linhas ③ de busca), dist_min_arquivo em espaco
%     de DECISAO NATIVO (DI-19.4; A_pre = snapshot pre-infill = sample_x),
%     modelo_hp (theta/lnL DUPLICADOS dos campos soltos — originais mantidos:
%     ha leitores).
%
% Fontes (via Problem.data, empacotado pelo run_c238): .buf RunBuffer (o MESMO
% que o hook_output alimenta com ②) · .bud FEBudget (X -> solution_id, D57) ·
% .log fid do .jsonl. Alinhamento: g = buf.gen (o hook ja fez bumpGen no TOPO
% desta iteracao, via NotTerminated) -> ② (hook) e ③/timing (aqui) partilham o
% g. RNG: NENHUM consumo (solutionIdOf/min/max/jsonencode deterministicos).

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end
    dup_infill = (bud.fe == fe_antes);

    % [DI-09/A1] fe_treino_max: o treino do fit desta iteracao e a Population
    % INTEIRA pre-infill (o dedup 'stable' do chol nao altera o MAXIMO — prova
    % no cabecalho do c238_sonda.m). fe_antes = bud.fe PRE-Evaluation, ids
    % 0-based presentes = 0..fe_antes-1 (solution_id == fe_index, FEBudget).
    % MESMO valor que a sonda gravou no bloco ③ dela (bud.fe-1 pre-eval).
    ftm = fe_antes - 1;
    if ftm < 0, ftm = []; end

    % ── eventos de guarda (§17.5) ─────────────────────────────────────────────
    if n_nan_pop > 0
        guard_line(fid, 'eim_nan', g, 'n', n_nan_pop, 'motivo', ...
            'NaN na matriz EIM (s=0 & f=u) zerado — guard [IMPL] Infill_EIM (pop final do GA)');
    end
    % (guard_range e emitido NA DETECCAO pela EIM.main — revisao adversarial
    %  R1-c238: se o GP_Train morrer antes desta chamada, o evento ja saiu;
    %  aqui fica so o campo n_range0 na linha c238_gen.)
    if n_dedup > 0
        guard_line(fid, 'dedup_treino', g, 'n', n_dedup, 'motivo', ...
            'duplicata bit-exata na amostra removida SO do treino (chol GP_Train:22 desprotegido)');
    end
    if dup_infill
        guard_line(fid, 'dup_infill', g, 'motivo', ...
            'infill duplicata bit-exata -> cache-hit 0 FE (D89); slot do infill perdido');
    end
    if stall >= 2
        guard_line(fid, 'saldo_congelado', g, 'n', stall, 'motivo', ...
            'iteracoes consecutivas sem consumir FE (D60-c) — so LOGA; rede = watchdog D60-b');
    end

    % ── ③ DEF-C2: pop FINAL do GA de aquisicao, mu/sigma POR OBJETIVO + C3 ────
    % transf_params identico p/ todas as linhas da iteracao (RLE comprime).
    tp = string(jsonencode(struct('min', ymin(:).', 'range', yrange(:).')));
    srows = {};
    for i = 1:size(ga_pop, 1)
        sid = bud.solutionIdOf(ga_pop(i, :));   % >=0 so se JA avaliado (infill)
        rsi = int32([]);
        if sid >= 0, rsi = int32(sid); end
        srows{end+1} = RunBuffer.mkSurrogateRow(ga_pop(i, :), ...
            'real_solution_id', rsi, ...
            'mu', u_pop(i, :), 'sigma', s_pop(i, :), ...
            'pred_tipo', "valor", 'modelo_flag', "OK-Forrester", ...
            'espaco_modelo', "transformado", 'transf_tipo', "minmax", ...
            'transf_params', tp, ...
            'fe_treino_max', ftm); %#ok<AGROW> % [DI-09/A1] tb nas linhas de busca
    end

    % ── §17.6 timing: 1 retreino (M GP_Train) + busca (GA) por iteracao ───────
    % [DI-13.10] tempo_geracao_s DESCONTA a sonda.
    tps = sonda_tempo_c238(d);
    timing = struct('n_acumulado', n_treino, 'tempo_fit_s', tfit_s, ...
                    'tempo_busca_s', tbusca_s, ...
                    'tempo_geracao_s', max(tger_s - tps, 0), ...
                    'tempo_pred_sonda_s', tps);

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── .jsonl §17.5/S.7 — a linha 'c238_gen' por iteracao de BO ──────────────
    if ~isempty(fid) && fid > 2
        sid_inf = bud.solutionIdOf(infill_x(1, :));
        % [y,u,s] do ESCOLHIDO: o best do GA = argmin de ga_fit (mesmo argmin
        % do Optimizer_GA:60 — deterministico); u/s vem da chamada extra.
        [~, ibest] = min(ga_fit);
        th_min = zeros(1, Problem.M); th_max = zeros(1, Problem.M);
        th_med = zeros(1, Problem.M); lnl = zeros(1, Problem.M);
        for j = 1:Problem.M
            th = GP_obj{j}.theta;
            th_min(j) = min(th); th_max(j) = max(th); th_med(j) = mean(th);
            lnl(j) = GP_obj{j}.lnL;
        end
        rec = struct('ts', iso_now_c238(), 'rec', "c238_gen", ...
            'geracao', g, 'iter', iter, 'fe', bud.fe, ...
            'criterion', string(criterion), ...
            'norm_min', ymin(:).', 'norm_max', ymax(:).', ...
            'norm_range_efetivo', yrange(:).', ...
            'n_amostra', n_treino + n_dedup, 'n_treino', n_treino, ...
            'n_dedup', n_dedup, 'n_front', nnz(idx_nd), ...
            'theta_min', th_min, 'theta_max', th_max, 'theta_media', th_med, ...
            'lnL', lnl, ...
            'ga_pop', size(ga_pop, 1), 'ga_gens', 200, ...
            'eim_best', -neg_best, ...
            ... % [DI-10 §6.1] eim_mediana_pool: o decaimento do POOL inteiro do
            ... % GA de aquisicao, nao so do best. ga_fit = -EIM (o GA minimiza
            ... % -Infill_EIM), entao o EIM do pool e -ga_fit; a mediana e sobre
            ... % o pool FINAL scorado — mesma fonte do eim_best (read-only).
            'eim_mediana_pool', median(-double(ga_fit(:))), ...
            'y_best', y_pop(ibest), 'u_best', u_pop(ibest, :), ...
            's_best', s_pop(ibest, :), 'infill_sid', sid_inf, ...
            'lote', 1, 'fe_iter', double(~dup_infill), ...
            'min_dist_infill', min_dist, 'stall_iters', stall, ...
            'n_eim_nan', n_nan_pop, 'n_range0', n_range0, ...
            'tempo_fit_s', tfit_s, ...
            ... % ── DI-10: minimo comum dos 21 (S.7.1) ──
            ... % [DI-19.2] f_best/n_front1 = ARQUIVO REAL POS-ciclo (ObjPos =
            ... % Population.objs do call-site, JA com o infill da iteracao).
            'f_best', min(ObjPos, [], 1), ...
            'n_front1', n_front1_c238(ObjPos), ...
            'fe_treino_max', opt_null_c238(ftm), ...
            'tempo_busca_s', tbusca_s, 'tempo_geracao_s', tger_s, ...
            'tempo_pred_sonda_s', tps, ...
            ... % dist_min_arquivo: DECISAO, NATIVO (DI-19.4); A_pre = sample_x
            ... % pre-infill. Coincide com min_dist_infill (B10.7, escalar) —
            ... % que fica como esta: ha leitores.
            'dist_min_arquivo', dist_min_c238(infill_x, A_pre), ...
            'modelo_hp', hp_gp_c238(th_min, th_max, th_med, lnl, n_treino, tfit_s));
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function t = sonda_tempo_c238(d)
    if isfield(d, 'snd') && ~isempty(d.snd), t = d.snd.takePendingTime(); else, t = 0; end
end

function hp = hp_gp_c238(th_min, th_max, th_med, lnl, n_treino, tfit_s)
% [DI-10/B1] hp EFETIVOS dos M krigings proprios (GP_Train estilo Forrester,
% N.5-6): theta0=1 ARD, bounds [1e-3,1e3], MLE fmincon sqp em log10(theta),
% single-start, MaxFunEvals 20D, nugget (10+n)*eps. theta/lnL sao DUPLICADOS
% dos campos soltos da linha c238_gen (theta_min/max/media, lnL) — os
% originais ficam onde estao: ha leitores.
    hp = struct('modelo', "OK-Forrester", 'theta0', 1, ...
                'theta_bounds', "[1e-3,1e3]", ...
                'theta_min', th_min, 'theta_max', th_max, ...
                'theta_media', th_med, 'lnL', lnl, ...
                'n', double(n_treino), 'tempo_fit_s', tfit_s);
end

function n = n_front1_c238(PopObj)
    n = NaN;
    try, n = sum(NDSort(PopObj, 1) == 1); catch, end
    n = double(n);
end

function dmin = dist_min_c238(PopNew, APre)
% [DI-10/B3] espaco de DECISAO, NATIVO (DI-19.4). Vetor, 1 por infill (lote=1
% no c238 => 1x1).
    dmin = [];
    if isempty(PopNew) || isempty(APre), return; end
    n = size(PopNew, 1);
    dmin = zeros(1, n);
    for i = 1:n
        dif = APre - PopNew(i, :);
        dmin(i) = sqrt(min(sum(dif .* dif, 2)));
    end
end

function v = opt_null_c238(x)
    if isempty(x), v = []; else, v = double(x); end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_c238(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function s = iso_now_c238()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
