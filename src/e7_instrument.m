function e7_instrument(Problem, snaps, PopNew, n_treino, ...
                       RatioVelho, RatioNew, delta, flag, ...
                       fe_ciclo, stall_ciclos, n_std_neg, ...
                       ymin_vig, espaco_vig, NW, tfit_s, tfit_init_s, ...
                       ftm, tger_s, A, Params, tbusca_s)
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
%     ciclo, +1 linha com o treino INICIAL (trainmodel 8e4 passos). [DI-13.10]
%     tempo_geracao_s da ④ = max(tger-tps,0) — DESCONTA a sonda (tps via
%     snd.takePendingTime); o BRUTO vai no .jsonl.
%   [DI09-R1c] minimo comum DI-10 (S.7.1) na linha 'e7_gen': f_best/n_front1
%     [DI-19.2: ARQUIVO REAL POS-ciclo — o A recebido ja inclui o New],
%     fe_treino_max=ftm (vindo do e7_sonda; o e7 SUBAMOSTRA o treino —
%     SelectTrainData capa em N1=11D-1 — logo NUNCA usar bud.fe-1),
%     dist_min_arquivo [DI-19.4: espaco de DECISAO NATIVO, vs arquivo
%     PRE-infill], tempo_geracao_s BRUTO, tempo_pred_sonda_s, modelo_hp (hp
%     EFETIVOS — mesmos que o e7_sonda documenta — + NW + loss_treino
%     INACESSIVEL, DI-12.1). O ftm tambem vai nas linhas ③ da busca (DI-09/A1).
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

    % [DI-19.2] arquivo REAL POS-ciclo: o A do call-site ja fez A=[A,New] (o e7
    % nao poda o A — so cresce). [DI-10/B3] snapshot PRE-infill p/ o dist_min:
    % [A,New] e append puro e |New|==lote SEMPRE aqui (duplicata vira cache-hit
    % 0 FE mas AINDA e uma SOLUTION; e no hard-stop NO MEIO do lote o instrument
    % nem roda — o ciclo morre na Evaluation), logo o fatiamento e EXATO e
    % dispensa captura extra na EDNARMOEA.main.
    AObj    = A.objs;
    ADec    = A.decs;
    ADecPre = ADec(1:end-lote, :);

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
                'transf_params', tp, ...
                'fe_treino_max', ftm); %#ok<AGROW>
                % ^ [DI-09/A1] ftm do e7_sonda (MESMO fit deste ciclo). O e7
                %   SUBAMOSTRA o treino (SelectTrainData capa em N1=11D-1):
                %   recalcular aqui daria o ftm do PROXIMO fit, e bud.fe-1 e
                %   atalho INVALIDO (cabecalho do e7_sonda).
        end
    end

    % ── §17.6 timing: retreino (8e3) por ciclo; 1o ciclo += treino inicial ────
    % [DI-13.10] tempo_geracao_s DESCONTA a sonda (tps); o BRUTO vai no .jsonl.
    % tempo_busca_s segue NaN: o e7 nao tem tic de busca sancionado (o wall do
    % ciclo e o tger; fit e sonda tem medidores proprios).
    tps = sonda_tempo_e7(d);
    view = struct('g', g, 'srows', {srows}, ...
                  'timing', struct('n_acumulado', n_treino, ...
                                   'tempo_fit_s', tfit_s, 'tempo_busca_s', tbusca_s, ...
                                   'tempo_geracao_s', max(tger_s - tps, 0), ...
                                   'tempo_pred_sonda_s', tps));
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
            ... % [DI-10 §6.1] n_clusters_efetivo SEM patch: IndividualSelect
            ... % monta xnew com UMA linha por cluster NAO-VAZIO do kmeans =>
            ... % |PopNew| E a contagem efetiva (Ke=3 e o teto, nao o efetivo).
            ... % O "cluster de CADA infill" e POSICIONAL: o infill i vem do
            ... % i-esimo cluster nao-vazio — os labels do kmeans sao arbitrarios
            ... % por ciclo, entao o indice e a unica leitura estavel (B18: nao
            ... % inventar grandeza; o ramo flag e POR CICLO, nao por infill).
            'n_clusters_efetivo', double(size(PopNew, 1)), ...
            'cluster_por_infill', "posicional: infill i = i-esimo cluster nao-vazio (labels kmeans arbitrarios)", ...
            'lote', double(lote), 'fe_ciclo', double(fe_ciclo), ...
            'tempo_busca_s', tbusca_s, ...
            'n_dup_infill', double(n_dup), 'stall_ciclos', double(stall_ciclos), ...
            'n_treino', double(n_treino), 'NW', double(NW), ...
            'ymin', ymin_vig(:).', 'espaco', string(espaco_vig), ...
            'pop_por_w', pop_por_w, 'n_std_neg', double(n_std_neg), ...
            'rss_mb', rss_mb, ...
            'tempo_fit_s', tfit_s, 'tempo_fit_inicial_s', tfit_init_s, ...
            ... % ── DI-10: minimo comum dos 21 (S.7.1) ──
            ... % [DI-19.2] f_best/n_front1 = ARQUIVO REAL POS-ciclo (o A aqui ja
            ... % inclui o New; o e7 nao poda o A). [DI-13.10] tempo_geracao_s
            ... % BRUTO aqui (o DESCONTADO vive na ④).
            'f_best', min(AObj, [], 1), ...
            'n_front1', n_front1_e7(AObj), ...
            'fe_treino_max', opt_null_e7(ftm), ...
            'tempo_geracao_s', tger_s, ...
            'tempo_pred_sonda_s', tps, ...
            'dist_min_arquivo', dist_min_e7(PopNew, ADecPre), ...
            'modelo_hp', hp_edn_e7(Params, n_treino, NW));
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end

function t = sonda_tempo_e7(d)
% [DI-13.10] tempo pendente da sonda (0 em run sem sonda — guard p/ snd vazio).
    if isfield(d, 'snd') && ~isempty(d.snd), t = d.snd.takePendingTime(); else, t = 0; end
end

function hp = hp_edn_e7(Params, n_treino, NW)
% [DI-10/B1] hp EFETIVOS da EDN — o MESMO conjunto que o e7_sonda documenta e
% emite nos blocos da sonda: Params.round=8e4 NAO governa o update
% (updatemodel.m:5 hardcoda run=8000) e Params.decay NAO e usado (trainNet.m:42
% hardcoda decay=1e-05); T=100 de Estimate.m:16; batchsize=V=D (trainmodel.m:11).
% + NW (nº de vetores de referencia do ARMOEA — denominador do Ratio).
% `loss_treino` NAO EXISTE: BARRADO pelo autor (DI-12.1) — a loss esta COMENTADA
% em trainNet.m:17 (re-habilita-la seria computacao nova no laco de 8e4/8e3
% passos, nao "+1 retorno a um numero ja calculado") e o proxy via testNet
% consome RNG (dropout.m:4). Registrado como INACESSIVEL, nao omitido.
    hp = struct('neuronN',        40, ...
                'dropP',          Params.dropP(:).', ...
                'learnR',         Params.learnR, ...
                'decay_efetivo',  1e-05, ...
                'batchsize',      Params.batchsize, ...
                'T',              100, ...
                'passos_init',    80000, ...
                'passos_update',  8000, ...
                'NW',             double(NW), ...
                'n_treino',       double(n_treino), ...
                'loss_treino',    "INACESSIVEL (DI-12.1)");
end

function n = n_front1_e7(PopObj)
% [DI-10] |ND| do arquivo real POS-ciclo (DI-19.2). NDSort e built-in PlatEMO,
% deterministico e zero-RNG; o `1` para no 1o front.
    n = NaN;
    try, n = sum(NDSort(PopObj, 1) == 1); catch, end
    n = double(n);
end

function dmin = dmin_loop_e7(PopNew, ADecPre)
    n = size(PopNew, 1);
    dmin = zeros(1, n);
    for i = 1:n
        dif = ADecPre - PopNew(i, :);
        dmin(i) = sqrt(min(sum(dif .* dif, 2)));
    end
end

function dmin = dist_min_e7(PopNew, ADecPre)
% [DI-10/B3] Distancia de cada infill ao arquivo PRE-infill — espaco de DECISAO,
% NATIVO (DI-19.4). `pdist2` e legitimo: o e7 ja depende da Statistics Toolbox
% (kmeans em IndividualSelect.m:13); fallback em loop puro por robustez.
    dmin = [];
    if isempty(PopNew) || isempty(ADecPre), return; end
    try
        dmin = min(pdist2(PopNew, ADecPre), [], 2).';
    catch
        dmin = dmin_loop_e7(PopNew, ADecPre);
    end
end

function v = opt_null_e7(x)
    if isempty(x), v = []; else, v = double(x); end
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
