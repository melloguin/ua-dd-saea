function e74_instrument(Problem, tag, inst, x_cand, aceito_mask, ObjPos, ArcDecPre, tger_s)
% e74_instrument — instrumentacao POS-decisao do e74 CLMEA (chamada pela
% CLMEA.main patchada, na ARVORE 4.1 propria — D95/N.0-4.1). NAO altera decisao
% nenhuma da busca (D97): so LE o que cada bloco ja computou (structs inst_e74
% de leitura pura) e emite ③ + .jsonl §17.5/S.7 + timing §17.6. O gate objetivo
% (FE/4-saidas/CP-init) NAO depende deste conteudo; ele existe p/ a validacao
% MANUAL do autor (D97).
%
% tags (1 chamada por bloco, na ordem do ciclo):
%   'boot' — bootstrap de extremos (M fits RBF + DE no surrogate; ate M FEs).
%   's1'   — ClassifierSelect: pop final do rank-learning + classe PNN por
%            membro; pseudo-σ = dist minima em DECISAO ao arquivo (dist_dec).
%   's2'   — Hv_Select: pop final da DE interna + μ_RBF (rede global no arquivo
%            inteiro); pseudo-σ = HV_gain D74-normalizado (so pseudo-front).
%   's3'   — Local_infill: pop final da busca local + ŷ (RBF local); pseudo-σ =
%            dist minima em OBJETIVOS ao arquivo (Eucli — "incerteza geometrica").
%   'stall'— D60-c: ciclo(s) sem consumir FE (saldo congelado) — SO loga.
%
% ③ (C1/B16.4 — hibrido do e74, 1 tabela): pred_tipo HONESTO por linha ("classe"
% p/ s1/PNN, "valor" p/ boot/s2/s3/RBF — nenhuma linha tem as duas cabecas ao
% mesmo tempo; a estrategia vai no modelo_flag). sigma_0 = o pseudo-σ da
% estrategia da linha (semantica por estrategia — dicionario DEF-C4 no
% manifesto). real_solution_id nullable (double+NaN — fallback R1-00): presente
% p/ membros ja avaliados (pops contem pontos do arquivo) e p/ o candidato
% ACEITO do bloco (instrument roda APOS a Evaluation).
%
% Alinhamento de geracao: g = buf.gen — o hook_output (outputFcn) ja fez o
% bumpGen no NotTerminated que PRECEDE o bloco (padrao c141): ② (hook) e
% ③/timing (aqui) partilham o g.
%
% [DI09-R1c] Argumentos ADITIVOS (renomear NADA — molde b3/b4_instrument):
%   ObjPos    — Arc.objs POS-Evaluation do bloco (DI-19.2: f_best/n_front1 =
%               ARQUIVO REAL pos-ciclo); [] no 'stall'.
%   ArcDecPre — Arc.decs PRE-Evaluation do bloco (DI-10/B3 dist_min_arquivo,
%               espaco de DECISAO NATIVO — DI-19.4); [] em 'boot' (la vale o
%               dist_ext ja medido por extremo) e 'stall'.
%   tger_s    — wall do bloco (tic pos-bump na CLMEA.main). Na ④ o
%               tempo_geracao_s DESCONTA a sonda (DI-13.10: max(tger_s-tps,0));
%               no .jsonl vai CRU ao lado de tempo_pred_sonda_s (reconstrutivel).
%   O fe_treino_max NAO vem por argumento: viaja em inst.ftm (calculado no
%   ponto do fit pelo e74_sonda — so la o treino subamostrado e conhecido;
%   handoff/DI09-retrofit-R1.md). tempo_pred_sonda_s = SOMA dos
%   takePendingTime dos handles de data.snd (struct POR CABECA, DI-19.1).

    d = Problem.data;
    buf = d.buf;  bud = d.bud;  fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end

    switch tag
        case 'stall'
            guard_line(fid, 'saldo_congelado', g, 'ciclos_sem_fe', inst.ciclos, ...
                'fe', bud.fe);
            return;

        case 'boot'
            srows = {};
            M = double(Problem.M);
            ftm = ftm_of(inst);                    % [DI-09/A1] via inst.ftm (e74_sonda)
            for i = 1:size(inst.x_ext, 1)
                mu_v = NaN(1, M);  mu_v(i) = inst.f_ext(i);   % DE minimizou SO o obj i
                srows{end+1} = srow(bud, inst.x_ext(i,:), ...
                    'mu', mu_v, 'pred_tipo', "valor", ...
                    'modelo_flag', "RBF-global(boot)", ...
                    'fe_treino_max', ftm); %#ok<AGROW>       % [DI-09/A1] tb nas linhas de busca
            end
            % [DI-13.10] tempo_geracao_s da ④ DESCONTA a sonda.
            tps = sonda_tempo_e74(d);
            view = struct('g', g, 'srows', {srows}, 'timing', struct( ...
                'n_acumulado', inst.n_treino, 'tempo_fit_s', inst.tempo_fit_s, ...
                'tempo_busca_s', inst.tempo_busca_s, ...
                'tempo_geracao_s', max(tger_s - tps, 0), ...
                'tempo_pred_sonda_s', tps));
            buf.addGeneration(view);
            if inst.rejeitados > 0
                guard_line(fid, 'extremo_rejeitado', g, 'n', inst.rejeitados, ...
                    'motivo', "dedup eps STOCK: extremo a <1e-5 do arquivo — slot perdido, 0 FE");
            end
            jline(fid, struct('ts', tnow(), 'rec', "e74_boot", 'geracao', g, ...
                'fe', bud.fe, 'aceitos', inst.aceitos, 'rejeitados', inst.rejeitados, ...
                'dist_ext', inst.dist_ext, 'f_ext', inst.f_ext, 'spr', inst.spr, ...
                'n_treino', inst.n_treino, 'tempo_fit_s', inst.tempo_fit_s, ...
                'tempo_busca_s', inst.tempo_busca_s, ...
                ... % ── DI-10: minimo comum dos 21 (S.7.1) — molde b3/b4 ──
                ... % [DI-19.2] f_best/n_front1 = ARQUIVO REAL POS-ciclo (o Arc
                ... % aqui ja inclui os extremos aceitos). dist_min_arquivo =
                ... % dist_ext (mesma medida: dist de cada extremo ao arquivo no
                ... % momento da proposta, DECISAO NATIVA — DI-19.4; sem rename).
                'f_best', min(ObjPos, [], 1), ...
                'n_front1', n_front1_e74(ObjPos), ...
                'fe_treino_max', opt_null_e74(ftm), ...
                'tempo_geracao_s', tger_s, 'tempo_pred_sonda_s', tps, ...
                'dist_min_arquivo', inst.dist_ext, ...
                'modelo_hp', hp_e74('boot', inst, M)));
            return;
    end

    % ── blocos s1/s2/s3 ──────────────────────────────────────────────────────
    n_cand = size(x_cand, 1);
    n_ok   = sum(aceito_mask);
    slot_perdido = n_cand - n_ok;
    ftm    = ftm_of(inst);                     % [DI-09/A1] via inst.ftm (e74_sonda)

    srows = {};
    switch tag
        case 's1'
            for k = 1:size(inst.x_pop, 1)
                srows{end+1} = srow(bud, inst.x_pop(k,:), ...
                    'sigma', inst.dist_dec(k), 'pred_tipo', "classe", ...
                    'pred_classe', "nivel_" + string(inst.classe_pop(k)), ...
                    'modelo_flag', "PNN(s1)", ...
                    'fe_treino_max', ftm); %#ok<AGROW>   % [DI-09/A1] tb nas linhas de busca
            end
        case 's2'
            % HV_gain so existe p/ os membros do pseudo-front (score CalHV D74).
            gain = NaN(size(inst.x_pop, 1), 1);
            sc   = NaN(size(inst.x_pop, 1), 1);
            if ~isempty(inst.score)
                fidx = find(inst.front_mask);
                m = min(numel(fidx), numel(inst.score));
                sc(fidx(1:m))   = inst.score(1:m);
                gain(fidx(1:m)) = inst.score(1:m) - inst.hv_base;
            end
            for k = 1:size(inst.x_pop, 1)
                srows{end+1} = srow(bud, inst.x_pop(k,:), ...
                    'mu', inst.y_pop(k,:), 'sigma', gain(k), ...
                    'pred_score', sc(k), 'pred_tipo', "valor", ...
                    'modelo_flag', "RBF-global(s2)", ...
                    'fe_treino_max', ftm); %#ok<AGROW>   % [DI-09/A1]
            end
        case 's3'
            for k = 1:size(inst.x_pop, 1)
                srows{end+1} = srow(bud, inst.x_pop(k,:), ...
                    'mu', inst.y_pop(k,:), 'sigma', inst.eucli(k), ...
                    'pred_tipo', "valor", 'modelo_flag', "RBF-local(s3)", ...
                    'fe_treino_max', ftm); %#ok<AGROW>   % [DI-09/A1]
            end
    end
    % [DI-13.10] tempo_geracao_s da ④ DESCONTA a sonda (soma dos 4 handles).
    tps = sonda_tempo_e74(d);
    view = struct('g', g, 'srows', {srows}, 'timing', struct( ...
        'n_acumulado', inst.n_treino, 'tempo_fit_s', inst.tempo_fit_s, ...
        'tempo_busca_s', inst.tempo_busca_s, ...
        'tempo_geracao_s', max(tger_s - tps, 0), ...
        'tempo_pred_sonda_s', tps));
    buf.addGeneration(view);

    % ── guardas §17.5 ────────────────────────────────────────────────────────
    if slot_perdido > 0
        guard_line(fid, 'dedup_slot_perdido', g, 'estrategia', string(tag), ...
            'n', slot_perdido, ...
            'motivo', "dedup eps=1e-5 STOCK rejeitou o candidato SEM gastar FE (slot perdido, nao o orcamento)");
    end
    if n_cand == 0
        guard_line(fid, 'cand_vazio', g, 'estrategia', string(tag), ...
            'motivo', "estrategia nao produziu candidato (edge stock — ex.: rank-learning sem nivel-1)");
    end
    if strcmp(tag, 's2') && inst.range0
        guard_line(fid, 'hv_range0', g, ...
            'motivo', "front-1 do arquivo degenerado em >=1 coordenada (Ymax-Ymin<=0) — norm D74 vira NaN; edge fora do paper, NAO consertado (so logado)");
    end

    % ── linha 'e74_gen' (S.7) por bloco ──────────────────────────────────────
    rec = struct('ts', tnow(), 'rec', "e74_gen", 'geracao', g, ...
        'estrategia', str2double(tag(2)), 'fe', bud.fe, 'arquivo', bud.fe, ...
        'n_cand', n_cand, 'aceito', n_ok, 'slot_perdido', slot_perdido, ...
        'spr', inst.spr, 'n_treino', inst.n_treino, ...
        'tempo_fit_s', inst.tempo_fit_s, 'tempo_busca_s', inst.tempo_busca_s, ...
        ... % ── DI-10: minimo comum dos 21 (S.7.1) — molde b3/b4_instrument ──
        ... % [DI-19.2] f_best/n_front1 = ARQUIVO REAL POS-ciclo (ObjPos =
        ... % Arc.objs POS-Evaluation deste bloco). Os DOIS 'n_front' antigos
        ... % (s2 = pseudo-front da DE interna; s3 = front-1 dos offspring)
        ... % ficam como estao — semantica DIFERENTE, nome DIFERENTE.
        'f_best', min(ObjPos, [], 1), ...
        'n_front1', n_front1_e74(ObjPos), ...
        'fe_treino_max', opt_null_e74(ftm), ...
        'tempo_geracao_s', tger_s, 'tempo_pred_sonda_s', tps, ...
        'dist_min_arquivo', dist_min_e74(x_cand, ArcDecPre), ...
        'modelo_hp', hp_e74(tag, inst, double(Problem.M)));
    switch tag
        case 's1'
            rec.count = inst.count;
            rec.frac_nivel1 = inst.frac_n1;
            rec.n_desalinhado = inst.n_desalinhado;   % mascara(Offspring)×Parent (fix opcional NAO aplicado)
            rec.flag_copia = inst.flag_copia;
            rec.cand_classe = inst.cand_classe(:).';
            rec.cand_dist_dec = inst.cand_dist(:).';
            % [DI-10 §6.1] n_por_nivel do PNN — contagem POR NIVEL (1..4, as
            % classes fixas do Data_Process) dos CANDIDATOS classificados
            % (cand_classe, que o s1 ja exporta) + contexto dos pais.
            rec.n_por_nivel = contagem_niveis_e74(inst.cand_classe);
            rec.n_por_nivel_pop = contagem_niveis_e74(inst.classe_pop);
        case 's2'
            rec.Ymin = inst.Ymin;  rec.Ymax = inst.Ymax;
            rec.range0 = inst.range0;
            rec.hv_base = inst.hv_base;
            rec.n_front = numel(inst.score);
            rec.score = resumo(inst.score);
            if ~isempty(inst.score) && ~isempty(inst.chosen)
                rec.score_best = inst.score(inst.chosen);
                rec.hv_gain = inst.score(inst.chosen) - inst.hv_base;
            end
        case 's3'
            rec.n_front = sum(inst.front_mask);
            rec.cand_eucli = inst.cand_eucli(:).';
            % [DI-10 §6.1] k_local EFETIVO = o parametro que o call-site passa
            % (JA e min(20,|Arc|) pelo patch L.8; como |Arc| >= 11D-1 >= 21,
            % vale 20 em todo o grid — mas grava-se o REAL, nao a constante).
            % ⚠ NAO e o n_treino do s3: aquele e o |x_train| da RBF-local
            % (N vizinhos do RefPoint) — outra grandeza, que segue em n_treino.
            rec.k_local_efetivo = double(field_or_e74(inst, 'k_local', NaN));
    end
    jline(fid, rec);
end


function r = srow(bud, x, varargin)
% Linha ③ com real_solution_id nullable resolvido AQUI (dedup bit-a-bit D57):
% presente so se o x ja e uma solucao real (membro do arquivo / infill aceito).
    sid = bud.solutionIdOf(x);
    rsi = [];
    if sid >= 0, rsi = int32(sid); end
    r = RunBuffer.mkSurrogateRow(x, 'real_solution_id', rsi, varargin{:});
end

function t = sonda_tempo_e74(d)
% [DI-13.10] Tempo de sonda pendente a descontar da ④. No e74 o data.snd e um
% STRUCT de handles POR CABECA ('boot'/'s1'/'s2'/'s3' — DI-19.1): soma o
% takePendingTime de cada campo, com guard por campo (cabeca desligada/ausente
% conta 0). Aceita tambem o SondaState ESCALAR (molde legado dos outros run_*).
    t = 0;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end
    s = d.snd;
    if isa(s, 'SondaState')
        t = s.takePendingTime();
    elseif isstruct(s)
        fns = fieldnames(s);
        for i = 1:numel(fns)
            h = s.(fns{i});
            if isa(h, 'SondaState')
                t = t + h.takePendingTime();
            end
        end
    end
end

function v = ftm_of(inst)
% [DI-09/A1] fe_treino_max calculado NO PONTO DO FIT (e74_sonda, que devolve
% mesmo em run sem artefato) e transportado no inst da estrategia ('ftm').
% [] => NULL (ex.: ciclo do s3 sem fit — Arc.best vazio, laco 0x).
    v = [];
    if isfield(inst, 'ftm') && ~isempty(inst.ftm), v = double(inst.ftm); end
end

function n = n_front1_e74(PopObj)
% [DI-10] |ND| do ARQUIVO REAL pos-ciclo (DI-19.2). NDSort resolve na arvore
% 4.1 propria do e74 (path dedicado); deterministico, zero-RNG; o `1` para no
% 1o front (mesmo helper do b4/b3).
    n = NaN;
    try, n = sum(NDSort(PopObj, 1) == 1); catch, end
    n = double(n);
end

function dmin = dist_min_e74(X, ArcDecPre)
% [DI-10/B3] dist de cada candidato ao arquivo PRE-infill — espaco de DECISAO,
% NATIVO (DI-19.4). [] quando nao ha candidato (edge stock do s1) ou sem
% ArcDecPre. pdist2 e legitimo: o e74 ja exige a Statistics Toolbox.
    dmin = [];
    if isempty(X) || isempty(ArcDecPre), return; end
    try
        dmin = min(pdist2(X, ArcDecPre), [], 2).';
    catch
        n = size(X, 1);
        dmin = zeros(1, n);
        for i = 1:n
            dif = ArcDecPre - X(i, :);
            dmin(i) = sqrt(min(sum(dif .* dif, 2)));
        end
    end
end

function v = opt_null_e74(x)
    if isempty(x), v = []; else, v = double(x); end
end

function hp = hp_e74(tag, inst, M)
% [DI-10/B1] hp EFETIVOS por estrategia — MESMOS campos que a sonda publica
% (e74_sonda, switch das cabecas), para as duas leituras baterem:
% n_neuronios == size(x_train,1) do fit == inst.n_treino.
    switch char(tag)
        case 'boot'
            hp = struct('tipo', "newrbe", 'spread', inst.spr, ...
                'n_neuronios', double(inst.n_treino), 'M_saidas', 1, ...
                'n_redes', M, 'tempo_fit_s', inst.tempo_fit_s);
        case 's1'
            hp = struct('tipo', "newpnn", 'spread', inst.spr, ...
                'n_neuronios', double(inst.n_treino), 'M_saidas', 1, ...
                'tempo_fit_s', inst.tempo_fit_s);
        otherwise   % s2 (RBF global, arquivo inteiro) / s3 (RBF local, N vizinhos)
            hp = struct('tipo', "newrbe", 'spread', inst.spr, ...
                'n_neuronios', double(inst.n_treino), 'M_saidas', M, ...
                'tempo_fit_s', inst.tempo_fit_s);
    end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (formato do logger do FEBudget/c141_instrument).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', tnow(), 'rec', "guard", 'name', string(name), 'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function jline(fid, rec)
    if isempty(fid) || fid <= 2, return; end
    try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
end

function r = resumo(v)
    if isempty(v)
        r = [];
    else
        r = struct('min', min(v), 'med', median(v), 'max', max(v));
    end
end

function v = field_or_e74(s, f, d)
    if isstruct(s) && isfield(s, f), v = s.(f); else, v = d; end
end

function v = contagem_niveis_e74(classes)
% [DI-10] histograma FIXO nos 4 niveis do PNN (Data_Process: quotas 10/30/40/20%).
    v = zeros(1, 4);
    if isempty(classes), return; end
    c = double(classes(:));
    for k = 1:4
        v(k) = sum(c == k);
    end
end

function s = tnow()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
