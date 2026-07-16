function c217_instrument(Problem, Arc, Next, delta, Error1, Error2, TestPre, tfit_s)
% c217_instrument — instrumentacao POS-decisao do c217 PC-SAEA (chamada no fim de
% cada geracao pela PCSAEA.main patchada). NAO altera nenhuma decisao da busca
% (D97): so LE o que a geracao ja computou (Error1/2, estado, lote, TestPre) e
% emite as camadas de auditoria/analise. O gate objetivo (FE/4-saidas/CP-init)
% NAO depende deste conteudo; ele existe para a validacao MANUAL de fidelidade do
% autor (D97) e materializa os requisitos §17.2.1 (log da regra tripla), ③ (score
% ternario da acao corrigida — D17) e a serie de tempo §17.6.
%
% Fontes (via Problem.data, empacotado pelo run_c217):
%   .buf  RunBuffer  — coletor ②③/timing (o MESMO que o hook_output alimenta com ②)
%   .bud  FEBudget   — mapeia X real -> solution_id (dedup bit-a-bit, D57)
%   .log  double     — fid do .jsonl aberto (§17.5); escreve a linha da regra tripla
% Alinhamento de geracao: `g = buf.gen` — o hook (outputFcn) ja fez bumpGen no TOPO
% desta iteracao (NotTerminated), entao ② (hook) e ③/timing (aqui) partilham o mesmo g.

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);                        % geracao corrente (bumpada pelo hook)
    if g < 1, g = 1; end

    % ── Estado da regra tripla CORRIGIDA (D17), reproduzindo as guardas do SAS ──
    % (so p/ LOG/score; a decisao real ja foi tomada pelo SAS com estas MESMAS
    %  condicoes. NaN>delta = false em ambas -> estado 3, o ramo aleatorio — L6.)
    if Error1 > delta
        estado = 1;  score = 1;  motivo = sprintf('Error1=%.4f > delta=%.2f -> estado 1 (maximiza)', Error1, delta);
    elseif Error2 > delta
        estado = 2;  score = -1; motivo = sprintf('Error2=%.4f > delta=%.2f -> estado 2 (minimiza/inverte)', Error2, delta);
    else
        estado = 3;  score = 0;
        if isnan(Error1) || isnan(Error2)
            motivo = 'regime-NaN (objetivo constante) -> estado 3 (aleatorio)';
        else
            motivo = sprintf('Error1=%.4f, Error2=%.4f <= delta=%.2f (contradicoes) -> estado 3 (aleatorio)', Error1, Error2, delta);
        end
    end
    n_empates = sum(TestPre(:) == 1.5);         % contradicoes/empates do PNN (S.3#4)
    lote      = size(Next, 1);
    arc_size  = numel(Arc);

    % ── ③ surrogate (schema C1): 1 linha 'score' por candidato SELECIONADO ──────
    % O candidato foi avaliado no ciclo (PCS:53) -> tem solution_id -> real_solution_id
    % SEMPRE presente (int32). pred_score = acao ternaria {-1,0,+1} da regra corrigida
    % (D17); pred_confianca = Error1 (confiabilidade da geracao); modelo = 'PNN-par'.
    srows = {};
    if lote > 0
        Dec = Next;                              % lote x D (nativo)
        for i = 1:lote
            sid = bud.solutionIdOf(Dec(i, :));   % >=0 pois o candidato foi avaliado
            rsi = int32([]);
            if sid >= 0, rsi = int32(sid); end
            srows{end+1} = RunBuffer.mkSurrogateRow(Dec(i, :), ...
                'real_solution_id', rsi, ...
                'pred_tipo', "score", 'pred_score', score, ...
                'pred_confianca', Error1, 'modelo_flag', "PNN-par"); %#ok<AGROW>
        end
    end

    % ── §17.6 timing: 1 evento de retreino do PNN por geracao ──────────────────
    timing = struct('n_acumulado', arc_size, 'tempo_fit_s', tfit_s, 'tempo_busca_s', NaN);

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ─────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── §17.2.1 — log legivel da regra tripla por geracao (.jsonl) ─────────────
    if ~isempty(fid) && fid > 2
        rec = struct('ts', iso_now_c217(), 'rec', "c217_gen", ...
            'geracao', g, 'arc_size', arc_size, 'delta', delta, ...
            'p_mais', num_or_null(Error1), 'p_menos', num_or_null(Error2), ...
            'n_contradicoes', double(n_empates), 'n_empates', double(n_empates), ...
            'estado', estado, 'motivo', string(motivo), ...
            'lote', double(lote), 'score', double(score), ...
            'tempo_fit_s', tfit_s);
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function v = num_or_null(x)
% NaN -> [] (=> null no jsonencode), mantendo o log parseavel (regime-NaN L6).
    if isnan(x), v = []; else, v = double(x); end
end

function s = iso_now_c217()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
