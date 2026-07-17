function b3_instrument(Problem, A1, snaps, PopNew, sel, NumV1, NumV2, Flag, ...
                       delta, mu_alvo, nzero, n_treino, tfit_s)
% b3_instrument — instrumentacao POS-decisao do b3 K-RVEA (chamada no fim de
% cada ciclo pela KRVEA.main patchada). NAO altera nenhuma decisao da busca
% (D97): so LE o que o ciclo ja computou (snapshots do RVEA-surrogate, switch
% APD x incerteza, lote de infill) e emite as camadas de auditoria/analise. O
% gate objetivo (FE/4-saidas/CP-init) NAO depende deste conteudo; ele existe
% p/ a validacao MANUAL do autor (D97).
%
% O que emite:
%   ③ (DEF-C2/B3.2): a populacao SELECIONADA de CADA geracao interna do RVEA
%     sobre o surrogate (wmax=20 por ciclo — TODAS, nada amostrado), 1 linha
%     'valor' por candidato: mu_0..mu_{M-1} = objetivos PREDITOS pelos DACEs e
%     sigma_j = sqrt(max(MSE_j,0)) por objetivo (B3.2 — o CRITERIO interno do
%     switch usa a MEDIA das MSEs SEM raiz; a raiz aqui e so unidade de export).
%     TODAS as linhas do ciclo levam geracao = CICLO (a predicao e datada pelo
%     RETREINO — §17.1; join direto com a ② por geracao, D31); os blocos por
%     geracao interna ficam na ORDEM das linhas, com as contagens por-w na
%     linha 'b3_gen' do .jsonl (pop_por_w) -> o filme e reconstruivel.
%     real_solution_id nullable: presente so p/ candidatos JA avaliados
%     (membros do arquivo que sobrevivem na pop interna) -> o write_surrogate
%     cai p/ double+NaN (fallback do R1-00; consolidacao re-casta int32).
%   .jsonl §17.5/S.7 (linha 'b3_gen'): |A1| (n_treino no fit e |A1| pos-update,
%     que encolhe p/ NI-5+u quando u<5 — L.2), u efetivo, NumV1/NumV2/Flag/
%     ramo (APD x incerteza) + motivo, index exportado (KrigingSelect:64),
%     lote, pop_por_w; eventos de guarda: updata_next0 (zeros filtrados).
%   timing §17.6: 1 evento de retreino por ciclo (n_acumulado = |A1| no fit
%     dos M DACEs; tempo_fit_s medido na KRVEA.main).
%
% Fontes (via Problem.data, empacotado pelo run_b3): .buf RunBuffer (o MESMO
% que o hook_output alimenta com ②) · .bud FEBudget (X -> solution_id, D57) ·
% .log fid do .jsonl. Alinhamento: g = buf.gen (o hook ja fez bumpGen no TOPO
% deste ciclo, via NotTerminated) -> ② (hook) e ③/timing (aqui) partilham o g.
% RNG: NENHUM consumo (solutionIdOf/sqrt/max deterministicos).

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end
    lote = size(PopNew, 1);

    % ── evento de guarda (§17.5): zeros de Next filtrados no UpdataArchive ────
    if nzero > 0
        guard_line(fid, 'updata_next0', g, 'nzero', nzero, 'motivo', ...
            'kmeans devolveu clusters vazios — indices 0 filtrados antes de indexar');
    end

    % ── ③ DEF-C2: pop selecionada de CADA geracao interna (blocos em ordem) ───
    srows = {};
    pop_por_w = zeros(1, numel(snaps));
    for w = 1:numel(snaps)
        s = snaps{w};
        if isempty(s), continue; end
        nw = size(s.dec, 1);
        pop_por_w(w) = nw;
        for i = 1:nw
            sid = bud.solutionIdOf(s.dec(i, :));  % >=0 so se JA avaliado (arquivo)
            rsi = int32([]);
            if sid >= 0, rsi = int32(sid); end
            srows{end+1} = RunBuffer.mkSurrogateRow(s.dec(i, :), ...
                'real_solution_id', rsi, ...
                'mu', s.obj(i, :), 'sigma', sqrt(max(s.mse(i, :), 0)), ...
                'pred_tipo', "valor", 'modelo_flag', "GP-DACE"); %#ok<AGROW>
        end
    end

    % ── §17.6 timing: 1 evento de retreino (M DACEs) por ciclo ────────────────
    timing = struct('n_acumulado', n_treino, 'tempo_fit_s', tfit_s, ...
                    'tempo_busca_s', NaN);

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── .jsonl §17.5/S.7 — a linha 'b3_gen' por ciclo ─────────────────────────
    if ~isempty(fid) && fid > 2
        if Flag <= delta
            ramo = "APD";
            motivo = sprintf('Flag = NumV2-NumV1 = %d-%d = %d <= delta=%.2f -> APD (convergencia)', ...
                             NumV2, NumV1, Flag, delta);
        else
            ramo = "incerteza";
            motivo = sprintf('Flag = NumV2-NumV1 = %d-%d = %d > delta=%.2f -> max incerteza media (diversidade)', ...
                             NumV2, NumV1, Flag, delta);
        end
        rec = struct('ts', iso_now_b3(), 'rec', "b3_gen", ...
            'geracao', g, 'fe', bud.fe, ...
            'n_treino', n_treino, 'arquivo', numel(A1), ...
            'u_alvo', mu_alvo, 'u_efetivo', numel(sel), ...
            'NumV1', NumV1, 'NumV2', NumV2, 'Flag', Flag, 'delta', delta, ...
            'ramo', ramo, 'motivo', string(motivo), ...
            'lote', double(lote), 'index', double(sel(:).'), ...
            'pop_por_w', pop_por_w, 'nzero_updata', nzero, ...
            'tempo_fit_s', tfit_s);
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_b3(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function s = iso_now_b3()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
