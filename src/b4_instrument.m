function b4_instrument(Problem, Arc, Ref, Next, sasinfo, p0, p1, rr, tr, ...
                       n_treino, tfit_s)
% b4_instrument — instrumentacao POS-decisao do b4 CSEA (chamada no fim de cada
% geracao pela CSEA.main patchada, DEPOIS da avaliacao real do lote). NAO altera
% nenhuma decisao da busca (D97): so LE o que a geracao ja computou (p0/p1/rr/
% tr, ramo do SAS, lote e seus L) e emite as camadas de auditoria/analise. O
% gate objetivo (FE/4-saidas/CP-init) NAO depende deste conteudo; ele existe p/
% a validacao MANUAL do autor (D97).
%
% O que emite:
%   ③ (DEF-C1, classificador): 1 linha 'classe' por candidato do lote
%     SELECIONADO p/ avaliacao real ("L dos selecionados" — cartao b4/§22):
%     pred_classe = "bom" (L>=0.5) / "ruim" (L<0.5) — a leitura binaria da
%     sigmoide; pred_confianca = L in (0,1) (saida da FNN); mu/sigma/score =
%     NULL; modelo_flag = FNN. real_solution_id SEMPRE presente (o instrument
%     roda POS-avaliacao -> int32, como no c217). A semantica da SELECAO (no
%     ramo 3 selecionam-se os L<0.1 — modelo invertido) esta no `ramo` do
%     .jsonl, nao na classe.
%   .jsonl §17.5/S.7 (linha 'b4_gen'): (p0,p1,rr,tr) da geracao, regime/ramo
%     do SAS (1 confiavel/2 anti-loop/3 invertido/4 inconclusivo) + motivo (a
%     desigualdade), |lote| (0 = geracao sem FE — stall, D60-c: monitorado),
%     L dos selecionados, |Arc|, ref_ids (as K=6 referencias da geracao —
%     contexto, §17.4); eventos de guarda: stall_0fe, randperm_dim.
%   timing §17.6: 1 evento de retreino por geracao (n_acumulado = |Arc| no fit
%     do trainNetwork — arquivo INTEIRO, B4.6; tempo_fit_s da CSEA.main).
%
% Fontes (via Problem.data, empacotado pelo run_b4): .buf RunBuffer (o MESMO
% que o hook_output alimenta com ②) · .bud FEBudget (X -> solution_id, D57) ·
% .log fid do .jsonl. Alinhamento: g = buf.gen (o hook ja fez bumpGen no TOPO
% desta geracao, via NotTerminated) -> ② (hook) e ③/timing (aqui) partilham g.
% RNG: NENHUM consumo (solutionIdOf deterministico).

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end
    lote = size(Next, 1);
    L = sasinfo.Lsel(:);

    % ── eventos de guarda (§17.5) ──────────────────────────────────────────────
    if lote == 0
        guard_line(fid, 'stall_0fe', g, 'ramo', sasinfo.ramo, 'motivo', ...
            'gate do ramo devolveu lote vazio — geracao sem FE real (design; D60-c monitora)');
    end
    if sasinfo.guard_randperm
        guard_line(fid, 'randperm_dim', g, 'motivo', ...
            'length(Next) ~= size(Next,1) — randperm teria excedido as linhas (bug latente SAS:30)');
    end

    % ── ③ DEF-C1: o lote SELECIONADO, 1 linha 'classe' por candidato ───────────
    srows = cell(1, lote);
    for i = 1:lote
        sid = bud.solutionIdOf(Next(i, :));   % POS-avaliacao -> sempre >= 0
        rsi = int32([]);
        if sid >= 0, rsi = int32(sid); end
        if L(i) >= 0.5, classe = "bom"; else, classe = "ruim"; end
        srows{i} = RunBuffer.mkSurrogateRow(Next(i, :), ...
            'real_solution_id', rsi, ...
            'pred_tipo', "classe", 'pred_classe', classe, ...
            'pred_confianca', L(i), 'modelo_flag', "FNN");
    end

    % ── §17.6 timing: 1 retreino (trainNetwork, arquivo inteiro) por geracao ───
    timing = struct('n_acumulado', n_treino, 'tempo_fit_s', tfit_s, ...
                    'tempo_busca_s', NaN);

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ─────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── .jsonl §17.5/S.7 — a linha 'b4_gen' por geracao ────────────────────────
    if ~isempty(fid) && fid > 2
        aa = tr; bb = 1 - tr;
        switch sasinfo.ramo
            case 1, motivo = sprintf('p0=%.3f<0.4 OU (p1=%.3f<a=%.3f E p0<b=%.3f) -> confiavel: maximiza L, gate L>0.9', p0, p1, aa, bb);
            case 2, motivo = sprintf('p0=%.3f>b=%.3f E p1=%.3f<a=%.3f -> anti-loop: 1 aleatorio', p0, bb, p1, aa);
            case 3, motivo = sprintf('p1=%.3f>b=%.3f -> invertido: minimiza L, gate L<0.1', p1, bb);
            otherwise, motivo = sprintf('inconclusivo (p0=%.3f, p1=%.3f, a=%.3f, b=%.3f) -> 1 aleatorio', p0, p1, aa, bb);
        end
        ref_ids = -ones(1, size(Ref.decs, 1));
        RD = Ref.decs;
        for i = 1:size(RD, 1)
            ref_ids(i) = bud.solutionIdOf(RD(i, :));
        end
        rec = struct('ts', iso_now_b4(), 'rec', "b4_gen", ...
            'geracao', g, 'fe', bud.fe, 'arquivo', numel(Arc), ...
            'p0', p0, 'p1', p1, 'rr', rr, 'tr', tr, ...
            'ramo', sasinfo.ramo, 'motivo', string(motivo), ...
            'lote', double(lote), 'L_sel', L.', ...
            'ref_ids', ref_ids, 'n_treino', n_treino, ...
            'guard_randperm', sasinfo.guard_randperm, 'tempo_fit_s', tfit_s);
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_b4(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function s = iso_now_b4()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
