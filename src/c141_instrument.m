function c141_instrument(Problem, A1, PoolDec, PoolObj, PopNew, Dmodel, DS, ...
                         Fmodel, FS, info, nsub, n_treino, sde_fmodel, tfit_s, ...
                         tbusca_s, tger_s, RModel, mS, A1DecPre)
% c141_instrument — instrumentacao POS-decisao do c141 MMRAEA (chamada no fim de
% cada ciclo pela MMRAEA.main patchada). NAO altera nenhuma decisao da busca
% (D97): so LE o que o ciclo ja computou (pool pos-ES_PDR, cascata, batch) e
% emite as camadas de auditoria/analise. O gate objetivo (FE/4-saidas/CP-init)
% NAO depende deste conteudo; ele existe p/ a validacao MANUAL do autor (D97).
%
% O que emite:
%   ③ (D45/DEF-C2): 1 linha 'valor' por candidato do POOL 2N pos-ES_PDR (a
%     populacao que sobrevive a selecao do ciclo), com mu_0..mu_{M-1} = objetivos
%     PREDITOS pelos ARBFs e as DUAS incertezas do c141 em colunas separadas:
%       sigma_0 = U de ranks NATIVA (discordancia |Q1-Q2|+|Q1-Q3|+|Q2-Q3| entre os
%                 3 modos), calculada na POPULACAO COMPLETA — a "extensao leve"
%                 da D45 (o algoritmo so a computa p/ o subconjunto do nivel 3);
%       sigma_1 = desvio BRUTO entre os 3 modos (std de [Fit1,Fit2,Fit3] por
%                 candidato) — proxy de ensemble comparavel ao c149 (D45; escalas
%                 incomensuraveis: registrado no dicionario de sigma, DEF-C4).
%     real_solution_id nullable: presente so p/ candidatos JA avaliados (membros
%     do arquivo que sobreviveram / infills do ciclo) -> o write_surrogate cai p/
%     double+NaN (fallback do R1-00; a consolidacao re-casta int32 nullable).
%   .jsonl §17.5/S.7 (linha 'c141_gen'): Fit1/2/3 resumo, ranks/Q/U, NIVEL da
%     cascata (1/2/3) + telemetria do ramo (Q,U), |subpops| pos-ES_PDR, |lote|,
%     eventos de guarda (batch-vazio; +eps L4 por sitio).
%   timing §17.6: 1 evento de retreino por ciclo (n_acumulado = |A1| no fit dos
%     M+2 RBFs; tempo_fit_s medido na MMRAEA.main).
%
% Fontes (via Problem.data, empacotado pelo run_c141): .buf RunBuffer (o MESMO
% que o hook_output alimenta com ②) · .bud FEBudget (X -> solution_id, D57) ·
% .log fid do .jsonl. Alinhamento: g = buf.gen (o hook ja fez bumpGen no TOPO
% deste ciclo, via NotTerminated) -> ② (hook) e ③/timing (aqui) partilham o g.
% RNG: NENHUM consumo (calFitness/rbf_predict/sort/NDSort deterministicos).

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end
    lote = size(PopNew, 1);
    npool = size(PoolDec, 1);
    snd = [];
    if isfield(d, 'snd'), snd = d.snd; end      % [DI-09]
    % [DI-09/A1] fe_treino_max: o treino e A1 INTEIRO (UpdataArchive so faz
    % unique/dedup, nunca poda) e solution_id == fe_index => bud.fe-1. Aqui o
    % ciclo JA avaliou o infill (MMRAEA.m:60), entao subtrai-se o lote para
    % recuperar o estado do fit — que e o que a coluna significa.
    ftm = bud.fe - 1 - lote;
    if ftm < 0, ftm = []; end

    % ── eventos de guarda (§17.5): batch-vazio [IMPL] e +eps L4/D76 por sitio ──
    if lote == 0
        guard_line(fid, 'batch_vazio', g, 'motivo', ...
            sprintf('cascata nivel %d devolveu 0 candidatos (iteracao 0-FE — paper)', info.nivel));
    end
    if sde_fmodel
        guard_line(fid, 'sde_eps', g, 'site', "fmodel_train");
    end
    if isfield(info, 'sde_guard') && info.sde_guard
        guard_line(fid, 'sde_eps', g, 'site', "infill_fit1");
    end

    % ── ③ D45: Fit1/2/3 + ranks/U na POPULACAO COMPLETA (extensao leve) ────────
    % Espelha InfillStrategy:11-17/:25-35 sobre o pool inteiro (mesmos modelos,
    % mesmas convencoes de ordenacao); custo O(2N * |treino|), sem RNG.
    [Fit1p, sde_pool] = calFitness(PoolObj);
    if sde_pool
        guard_line(fid, 'sde_eps', g, 'site', "instrument_pool");
    end
    Fit2p = zeros(npool, 1);
    Fit3p = zeros(npool, 1);
    for i = 1:npool
        Fit2p(i) = rbf_predict(Dmodel, DS, PoolDec(i, :));
        Fit3p(i) = rbf_predict(Fmodel, FS, PoolDec(i, :));
    end
    [~, s1] = sort(Fit1p, 'descend');            % SDE-calc: maior = melhor
    [~, s2] = sort(Fit2p);                       % front-number pred: menor = melhor
    [~, s3] = sort(Fit3p, 'descend');            % SDE-pred: maior = melhor
    Q1 = zeros(npool, 1); Q2 = zeros(npool, 1); Q3 = zeros(npool, 1);
    for i = 1:npool
        Q1(s1(i)) = i;  Q2(s2(i)) = i;  Q3(s3(i)) = i;
    end
    Upool = abs(Q1 - Q2) + abs(Q1 - Q3) + abs(Q2 - Q3);      % sigma_0 (nativa)
    Ens   = std([Fit1p, Fit2p, Fit3p], 0, 2);                % sigma_1 (desvio bruto)

    srows = cell(1, npool);
    for i = 1:npool
        sid = bud.solutionIdOf(PoolDec(i, :));   % >=0 so se JA avaliado (arquivo)
        rsi = int32([]);
        if sid >= 0, rsi = int32(sid); end
        srows{i} = RunBuffer.mkSurrogateRow(PoolDec(i, :), ...
            'real_solution_id', rsi, ...
            'mu', PoolObj(i, :), 'sigma', [Upool(i), Ens(i)], ...
            'pred_tipo', "valor", 'modelo_flag', "RBF-MQ3", ...
            'fe_treino_max', ftm);
    end

    % ── §17.6 timing: 1 evento de retreino (M+2 RBFs) por ciclo ────────────────
    timing = struct('n_acumulado', n_treino, 'tempo_fit_s', tfit_s, ...
                    'tempo_busca_s', tbusca_s, ...
                    'tempo_geracao_s', tger_s, ...
                    'tempo_pred_sonda_s', sonda_tempo_c141(snd));

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ─────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── .jsonl §17.5/S.7 — a linha 'c141_gen' por ciclo ────────────────────────
    if ~isempty(fid) && fid > 2
        switch info.nivel
            case 1, motivo = sprintf('|front1 ∩ pop| = %d <= 1 -> lote = front1 (nivel 1)', info.n_front1);
            case 2, motivo = sprintf('|front2([-Fit1,Fit2,-Fit3])| = %d <= 1 -> lote = front2 (nivel 2)', info.n_front2);
            otherwise, motivo = sprintf('front2 = %d > 1 -> front ND de (Q,U) ∪ argmax U (nivel 3)', info.n_front2);
        end
        rec = struct('ts', iso_now_c141(), 'rec', "c141_gen", ...
            'geracao', g, 'fe', bud.fe, 'arquivo', numel(A1), ...
            'nivel', info.nivel, 'ramo_QU', info.nivel == 3, 'motivo', string(motivo), ...
            'n_front1', info.n_front1, 'n_front2', info.n_front2, ...
            'lote', double(lote), 'n_pool', npool, ...
            'n_sub1', nsub(1), 'n_sub2', nsub(2), ...
            'fit1', resumo(info.Fit1), 'fit2', resumo(info.Fit2), ...
            'fit3', resumo(info.Fit3), ...
            'Q', resumo(info.Q), 'U', resumo(info.U), ...
            'U_pool_max', max(Upool), 'tempo_fit_s', tfit_s, ...
            ... % ── DI-10: especificos do c141 (S.7.1) ──
            'n_por_nivel', struct('entrada', npool, ...
                                  'nivel1', double(info.n_front1), ...
                                  'nivel2', double(info.n_front2), ...
                                  'selecionados', double(n_sel_c141(info)), ...
                                  'lote', double(lote)), ...
            'modelo_hp', hp_rbf_c141(RModel, mS), ...
            ... % ── DI-10: minimo comum dos 21 (S.7.1) ──
            'f_best', min(A1.objs, [], 1), ...
            'fe_treino_max', opt_null_c141(ftm), ...
            'tempo_busca_s', tbusca_s, 'tempo_geracao_s', tger_s, ...
            'dist_min_arquivo', dist_min_c141(PopNew, A1DecPre));
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end


function t = sonda_tempo_c141(snd)
    if isempty(snd), t = 0; else, t = snd.takePendingTime(); end
end

function n = n_sel_c141(info)
% [DI-10] nivel 3 da cascata = |unique([index1,index2])| — ja capturado no
% struct `info` (idx_sel, InfillStrategy.m:54-55), so nao era escrito.
    if isfield(info, 'idx_sel'), n = numel(info.idx_sel); else, n = NaN; end
end

function hp = hp_rbf_c141(RModel, mS)
% [DI-10/B1] hp EFETIVOS do RBF: MMRAEA chama rbf_build com 2 args, entao valem
% os defaults (MQ, c=1, poly=0). n = size(mS,1) pos-dsmerge (ds=1e-14).
    hp = struct('bf_type', "MQ", 'bf_c', 1, 'poly', 0, 'n', size(mS, 1));
    try
        if ~isempty(RModel) && isstruct(RModel{1})
            m = RModel{1};
            if isfield(m,'bf_type'), hp.bf_type = string(m.bf_type); end
            if isfield(m,'bf_c'),    hp.bf_c    = double(m.bf_c);    end
            if isfield(m,'poly'),    hp.poly    = double(m.poly);    end
            if isfield(m,'n'),       hp.n       = double(m.n);       end
        end
    catch
    end
end

function dmin = dist_min_c141(PopNew, A1DecPre)
% [DI-10/B3] Distancia de cada infill ao arquivo ANTERIOR (espaco de decisao).
% ⚠ SEM pdist2: o c141 e "zero toolbox confirmado" (handoff R1-c141) — usar a
% Statistics Toolbox aqui criaria uma dependencia que o config nao tem.
    dmin = [];
    if isempty(PopNew) || isempty(A1DecPre), return; end
    n = size(PopNew, 1);
    dmin = zeros(1, n);
    for i = 1:n
        dif = A1DecPre - PopNew(i, :);          % broadcast implicito
        dmin(i) = sqrt(min(sum(dif .* dif, 2)));
    end
end

function v = opt_null_c141(x)
    if isempty(x), v = []; else, v = double(x); end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_c141(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function r = resumo(v)
% min/mediana/max de um vetor da cascata ([] quando o nivel nao o computou).
    if isempty(v)
        r = [];
    else
        r = struct('min', min(v), 'med', median(v), 'max', max(v));
    end
end

function s = iso_now_c141()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
