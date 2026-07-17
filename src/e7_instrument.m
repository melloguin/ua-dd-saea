function e7_instrument(Problem, snaps, PopNew, n_treino, ...
                       RatioVelho, RatioNew, delta, flag, ...
                       fe_ciclo, stall_ciclos, n_std_neg, ...
                       ymin_vig, espaco_vig, NW, tfit_s, tfit_init_s)
% e7_instrument — instrumentacao POS-decisao do e7 EDN-ARMOEA (chamada no fim
% de cada ciclo pela EDNARMOEA.main patchada). NAO altera nenhuma decisao da
% busca (D97): so LE o que o ciclo ja computou (snapshots do ARMOEA-sobre-o-
% surrogate, gatilho Ratio/flag, lote de infill, contadores de guarda) e emite
% as camadas de auditoria/analise. O gate objetivo (FE/4-saidas/CP-init) NAO
% depende deste conteudo; ele existe p/ a validacao MANUAL do autor (D97).
%
% O que emite:
%   ③ (DEF-C2 — EA): a populacao SELECIONADA de CADA geracao interna do ARMOEA
%     sobre o surrogate (wmax-1=19 por ciclo — TODAS), 1 linha 'valor' por
%     candidato: mu_j = objetivos PREDITOS pelo MC-dropout (T=100 passagens,
%     media) e sigma_j = desvio POPULACIONAL das T passagens (Estimate.m:29-30,
%     guard sqrt(max(var,0))), POR OBJETIVO. Os valores estao no ESPACO DO
%     MODELO: cru no 1o ciclo (treino inicial em y cru); TRANSLADADO por
%     ymin=min(A.objs) do fim do ciclo anterior nos seguintes (SelectTrainData
%     — C3): C3: espaco_modelo=cru|transformado, transf_tipo=translacao,
%     transf_params={ymin} -> cru = mu + ymin (invertivel; a ① da o cru real
%     dos avaliados — leitura D47 da DEF-C3; ⚠ sinalizado p/ veto do autor).
%     TODAS as linhas do ciclo levam geracao=CICLO (datada pelo retreino —
%     §17.1; precedente b3, tambem sinalizado); blocos por geracao interna em
%     ORDEM de linha, contagens em pop_por_w na linha e7_gen do .jsonl.
%     real_solution_id nullable (pop aleatoria/offspring nunca avaliados ->
%     NULL; infills e coincidencias -> id; coluna double+NaN, fallback R1-00).
%   .jsonl §17.5/S.7 (linha 'e7_gen'): Ratio/RatioOld/delta, flag + ramo
%     (incerteza|convergencia) + motivo, lote, fe_ciclo (consumido), n_dup_
%     infill (slots perdidos — D89: duplicata=0 FE), stall_ciclos (guarda (c)
%     D60), n_treino (cap 11D-1), NW, ymin/espaco (C3), pop_por_w, n_std_neg,
%     rss_mb (pico observavel — D86), tempos; eventos 'guard': std_neg,
%     dup_infill, saldo_congelado.
%   timing §17.6: 1 retreino (updatemodel 8e3 passos SGD) por ciclo; no 1o
%     ciclo, +1 linha com o treino INICIAL (trainmodel 8e4 passos).
%
% Fontes (via Problem.data, empacotado pelo run_e7): .buf RunBuffer (o MESMO
% que o hook_output alimenta com ②) · .bud FEBudget (X -> solution_id, D57) ·
% .log fid do .jsonl. Alinhamento: g = buf.gen (o hook ja fez bumpGen no TOPO
% deste ciclo, via NotTerminated). RNG: NENHUM consumo (solutionIdOf/min/max/
% jsonencode/unix-ps deterministicos p/ o stream do MATLAB).

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end
    lote = size(PopNew, 1);
    n_dup = lote - fe_ciclo;

    % ── eventos de guarda (§17.5) ─────────────────────────────────────────────
    if n_std_neg > 0
        guard_line(fid, 'std_neg', g, 'n', n_std_neg, 'motivo', ...
            'var populacional <0 (erro float das T passagens) — guard sqrt(max(var,0)) no Estimate');
    end
    if n_dup > 0
        guard_line(fid, 'dup_infill', g, 'n', n_dup, 'motivo', ...
            'infill duplicado (e7 nao deduplica) — cache-hit 0 FE (D89), slot do infill perdido');
    end
    if stall_ciclos > 0
        guard_line(fid, 'saldo_congelado', g, 'ciclos_consecutivos', stall_ciclos, 'motivo', ...
            'ciclo consumiu 0 FE (3 infills duplicados) — guarda (c) do D60: detectado e LOGADO, nao consertado');
    end

    % ── ③ DEF-C2: pop selecionada de CADA geracao interna (blocos em ordem) ───
    tp = string(jsonencode(struct('ymin', ymin_vig(:).')));
    srows = {};
    pop_por_w = zeros(1, numel(snaps));
    for w = 1:numel(snaps)
        s = snaps{w};
        if isempty(s), continue; end
        nw = size(s.dec, 1);
        pop_por_w(w) = nw;
        for i = 1:nw
            sid = bud.solutionIdOf(s.dec(i, :));  % >=0 so se JA avaliado
            rsi = int32([]);
            if sid >= 0, rsi = int32(sid); end
            srows{end+1} = RunBuffer.mkSurrogateRow(s.dec(i, :), ...
                'real_solution_id', rsi, ...
                'mu', s.obj(i, :), 'sigma', s.std(i, :), ...
                'pred_tipo', "valor", 'modelo_flag', "EDN-MCdropout", ...
                'espaco_modelo', string(espaco_vig), ...
                'transf_tipo', "translacao", ...
                'transf_params', tp); %#ok<AGROW>
        end
    end

    % ── §17.6 timing: retreino (8e3) por ciclo; 1o ciclo += treino inicial ────
    view = struct('g', g, 'srows', {srows}, ...
                  'timing', struct('n_acumulado', n_treino, ...
                                   'tempo_fit_s', tfit_s, 'tempo_busca_s', NaN));
    if ~isnan(tfit_init_s)
        % linha extra do treino INICIAL (8e4 passos) — mesmo g do 1o ciclo.
        buf.addGeneration(struct('g', g, ...
            'timing', struct('n_acumulado', n_treino, ...
                             'tempo_fit_s', tfit_init_s, 'tempo_busca_s', NaN)));
    end
    buf.addGeneration(view);

    % ── RAM observavel (D86): RSS do processo via ps (1x por ciclo, barato) ───
    rss_mb = NaN;
    try
        [st, out] = unix(sprintf('ps -o rss= -p %d', feature('getpid')));
        if st == 0, rss_mb = str2double(strtrim(out)) / 1024; end
    catch
    end

    % ── .jsonl §17.5/S.7 — a linha 'e7_gen' por ciclo ─────────────────────────
    if ~isempty(fid) && fid > 2
        if flag
            ramo = "convergencia";
            motivo = sprintf('RatioOld-Ratio = %.4f-%.4f = %.4f < delta=%.2f -> min ||obj_transladado|| por cluster', ...
                             RatioVelho, RatioNew, RatioVelho - RatioNew, delta);
        else
            ramo = "incerteza";
            motivo = sprintf('RatioOld-Ratio = %.4f-%.4f = %.4f >= delta=%.2f -> max sigma medio por cluster', ...
                             RatioVelho, RatioNew, RatioVelho - RatioNew, delta);
        end
        rec = struct('ts', iso_now_e7(), 'rec', "e7_gen", ...
            'geracao', g, 'fe', bud.fe, ...
            'RatioOld', RatioVelho, 'Ratio', RatioNew, 'delta', delta, ...
            'flag', logical(flag), 'ramo', ramo, 'motivo', string(motivo), ...
            'lote', double(lote), 'fe_ciclo', double(fe_ciclo), ...
            'n_dup_infill', double(n_dup), 'stall_ciclos', double(stall_ciclos), ...
            'n_treino', double(n_treino), 'NW', double(NW), ...
            'ymin', ymin_vig(:).', 'espaco', string(espaco_vig), ...
            'pop_por_w', pop_por_w, 'n_std_neg', double(n_std_neg), ...
            'rss_mb', rss_mb, ...
            'tempo_fit_s', tfit_s, 'tempo_fit_inicial_s', tfit_init_s);
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_e7(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function s = iso_now_e7()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
